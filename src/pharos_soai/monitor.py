"""Poll new blocks and report ERC-20 Transfer events. Read-only."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from pharos_soai import abi
from pharos_soai.constants import TRANSFER_TOPIC0
from pharos_soai.queries import QueryError, _safe_decimals, decode_transfer_log
from pharos_soai.rpc import RpcClient


def matches_filters(
    event: dict[str, Any],
    watch: str | None,
    min_value: int,
) -> bool:
    if watch and not (
        abi.same_address(event["from"], watch) or abi.same_address(event["to"], watch)
    ):
        return False
    return int(event["valueRaw"]) >= min_value


def fetch_transfers_in_range(
    client: RpcClient,
    token: str,
    from_block: int,
    to_block: int,
) -> list[dict[str, Any]]:
    logs = client.call(
        "eth_getLogs",
        [
            {
                "fromBlock": abi.int_to_hex(from_block),
                "toBlock": abi.int_to_hex(to_block),
                "address": token,
                "topics": [TRANSFER_TOPIC0],
            }
        ],
    )
    return [decode_transfer_log(item) for item in (logs or [])]


def monitor_transfers(
    client: RpcClient,
    token: str,
    watch: str | None = None,
    min_value: int = 0,
    interval: float = 5.0,
    once: bool = False,
    lookback: int = 5,
    max_iterations: int | None = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.time,
) -> list[dict[str, Any]]:
    if not abi.is_address(token):
        raise QueryError(f"Invalid token address: {token!r}")
    if watch is not None and not abi.is_address(watch):
        raise QueryError(f"Invalid watch address: {watch!r}")
    if min_value < 0:
        raise QueryError("min-value must be >= 0")
    if interval <= 0:
        raise QueryError("interval must be > 0")
    if lookback < 0:
        raise QueryError("lookback must be >= 0")

    decimals = _safe_decimals(client, token)
    latest = abi.hex_to_int(client.call("eth_blockNumber"))
    next_block = max(0, latest - lookback)
    seen: set[tuple[str, int | None]] = set()
    matched: list[dict[str, Any]] = []
    iterations = 0

    while True:
        current = abi.hex_to_int(client.call("eth_blockNumber"))
        if current >= next_block:
            events = fetch_transfers_in_range(client, token, next_block, current)
            for event in events:
                key = (event["transactionHash"], event["logIndex"])
                if key in seen:
                    continue
                seen.add(key)
                if not matches_filters(event, watch, min_value):
                    continue
                event["value"] = abi.format_units(int(event["valueRaw"]), decimals)
                event["decimals"] = decimals
                event["watched"] = watch
                event["observedAt"] = int(now())
                matched.append(event)
            next_block = current + 1
        iterations += 1
        if once or (max_iterations is not None and iterations >= max_iterations):
            break
        sleep(interval)
    return matched

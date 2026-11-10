"""Command-line interface. JSON on stdout. Never accepts keys or signing flags."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from pharos_soai import queries
from pharos_soai.constants import DEFAULT_RPC_URL, OFFICIAL_TOKENS
from pharos_soai.monitor import monitor_transfers
from pharos_soai.queries import QueryError
from pharos_soai.rpc import RpcClient, RpcError

FORBIDDEN_FLAGS = (
    "--private-key",
    "--private_key",
    "--privkey",
    "--secret",
    "--mnemonic",
    "--seed",
    "--wallet",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pharos-soai",
        description=(
            "Read-only Pharos Atlantic Testnet queries and Transfer monitor. "
            "Uses the public RPC only. Does not accept private keys and cannot sign."
        ),
    )
    parser.add_argument(
        "--rpc",
        default=DEFAULT_RPC_URL,
        help=f"JSON-RPC URL (default: official Atlantic endpoint {DEFAULT_RPC_URL})",
    )
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("chain", help="Show chain id, latest block, and RPC check")
    block = sub.add_parser("block", help="Show a block (default: latest)")
    block.add_argument("number", nargs="?", default="latest")

    balance = sub.add_parser("balance", help="Native token balance of a public address")
    balance.add_argument("address")

    tx = sub.add_parser("tx", help="Transaction details by hash")
    tx.add_argument("tx_hash")

    receipt = sub.add_parser("receipt", help="Transaction receipt by hash")
    receipt.add_argument("tx_hash")

    token = sub.add_parser("token", help="ERC-20 name, symbol, decimals, totalSupply")
    token.add_argument("token")

    token_balance = sub.add_parser("token-balance", help="ERC-20 balance of a holder")
    token_balance.add_argument("token")
    token_balance.add_argument("holder")

    transfers = sub.add_parser("transfers", help="Recent Transfer events of a token")
    transfers.add_argument("token")
    transfers.add_argument("--from-block", type=int)
    transfers.add_argument("--to-block", type=int)
    transfers.add_argument("--watch", help="Only transfers where this address is sender or recipient")
    transfers.add_argument("--limit", type=int, default=20)

    monitor = sub.add_parser(
        "monitor",
        help="Poll new blocks and print matching Transfer events as JSON lines",
    )
    monitor.add_argument("token")
    monitor.add_argument("--watch", help="Only transfers involving this public address")
    monitor.add_argument(
        "--min-value",
        default="0",
        help="Minimum raw token amount (integer in the token's smallest unit)",
    )
    monitor.add_argument("--interval", type=float, default=5.0, help="Seconds between polls")
    monitor.add_argument(
        "--lookback",
        type=int,
        default=5,
        help="How many already-produced blocks to scan on the first poll",
    )
    monitor.add_argument(
        "--once",
        action="store_true",
        help="Scan once and exit (useful for demos and tests)",
    )
    monitor.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Stop after this many polls even without --once",
    )

    tokens = sub.add_parser("tokens", help="Print official Atlantic Testnet token registry")
    tokens_ns = tokens  # keep linters happy
    del tokens_ns
    return parser


def dispatch(args: argparse.Namespace) -> Any:
    client = RpcClient(url=args.rpc, timeout=args.timeout)
    command = args.command
    if command == "chain":
        return queries.get_chain_info(client)
    if command == "block":
        return queries.get_block(client, args.number)
    if command == "balance":
        return queries.get_balance(client, args.address)
    if command == "tx":
        return queries.get_transaction(client, args.tx_hash)
    if command == "receipt":
        return queries.get_receipt(client, args.tx_hash)
    if command == "token":
        return queries.get_token_info(client, args.token)
    if command == "token-balance":
        return queries.get_token_balance(client, args.token, args.holder)
    if command == "transfers":
        return queries.get_transfers(
            client,
            args.token,
            from_block=args.from_block,
            to_block=args.to_block,
            watch=args.watch,
            limit=args.limit,
        )
    if command == "monitor":
        events = monitor_transfers(
            client,
            args.token,
            watch=args.watch,
            min_value=int(args.min_value),
            interval=args.interval,
            once=args.once,
            lookback=args.lookback,
            max_iterations=args.max_iterations,
        )
        return {
            "token": args.token,
            "watch": args.watch,
            "minValueRaw": args.min_value,
            "count": len(events),
            "events": events,
        }
    if command == "tokens":
        return {"source": "https://docs.pharos.xyz/getting-started/token-registry", "tokens": OFFICIAL_TOKENS}
    raise QueryError(f"Unknown command: {command}")


def reject_secrets(argv: list[str]) -> None:
    lowered = [item.lower() for item in argv]
    for flag in FORBIDDEN_FLAGS:
        if flag in lowered:
            raise QueryError(
                "This tool is read-only and refuses key or wallet flags. "
                "Pass only public addresses and transaction hashes."
            )


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        reject_secrets(argv)
        parser = build_parser()
        args = parser.parse_args(argv)
        payload = dispatch(args)
        print(json.dumps({"ok": True, "result": payload}, ensure_ascii=False, indent=2))
        return 0
    except (QueryError, RpcError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

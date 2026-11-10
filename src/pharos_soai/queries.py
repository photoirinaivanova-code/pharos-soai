"""Read-only onchain queries against a public JSON-RPC endpoint."""

from __future__ import annotations

from typing import Any

from pharos_soai import abi
from pharos_soai.constants import (
    ERC20_SELECTORS,
    EXPECTED_CHAIN_ID,
    EXPLORER_URL,
    NATIVE_SYMBOL,
    NETWORK_NAME,
    TRANSFER_TOPIC0,
)
from pharos_soai.rpc import RpcClient


class QueryError(ValueError):
    """Invalid user input for a query."""


def get_chain_info(client: RpcClient) -> dict[str, Any]:
    chain_hex = client.call("eth_chainId")
    block_hex = client.call("eth_blockNumber")
    chain_id = abi.hex_to_int(chain_hex)
    return {
        "network": NETWORK_NAME,
        "rpc": client.url,
        "chainId": chain_id,
        "chainIdHex": chain_hex,
        "expectedChainId": EXPECTED_CHAIN_ID,
        "chainIdMatch": chain_id == EXPECTED_CHAIN_ID,
        "latestBlock": abi.hex_to_int(block_hex),
        "latestBlockHex": block_hex,
        "nativeSymbol": NATIVE_SYMBOL,
        "explorer": EXPLORER_URL,
    }


def get_block(client: RpcClient, number: str | int | None = None) -> dict[str, Any]:
    tag = _block_tag(number)
    block = client.call("eth_getBlockByNumber", [tag, False])
    if block is None:
        raise QueryError(f"Block not found: {tag}")
    txs = block.get("transactions") or []
    return {
        "number": abi.hex_to_int(block.get("number")),
        "hash": block.get("hash"),
        "parentHash": block.get("parentHash"),
        "timestamp": abi.hex_to_int(block.get("timestamp")),
        "miner": block.get("miner"),
        "gasUsed": abi.hex_to_int(block.get("gasUsed")),
        "gasLimit": abi.hex_to_int(block.get("gasLimit")),
        "transactionCount": len(txs),
        "transactions": txs,
        "explorer": f"{EXPLORER_URL.rstrip('/')}/block/{abi.hex_to_int(block.get('number'))}",
    }


def get_balance(client: RpcClient, address: str) -> dict[str, Any]:
    if not abi.is_address(address):
        raise QueryError(f"Invalid address: {address!r}")
    raw = client.call("eth_getBalance", [address, "latest"])
    wei = abi.hex_to_int(raw)
    return {
        "address": address,
        "balanceWei": str(wei),
        "balance": abi.format_units(wei, 18),
        "symbol": NATIVE_SYMBOL,
        "explorer": f"{EXPLORER_URL.rstrip('/')}/address/{address}",
    }


def get_transaction(client: RpcClient, tx_hash: str) -> dict[str, Any]:
    if not abi.is_tx_hash(tx_hash):
        raise QueryError(f"Invalid transaction hash: {tx_hash!r}")
    tx = client.call("eth_getTransactionByHash", [tx_hash])
    if tx is None:
        raise QueryError(f"Transaction not found: {tx_hash}")
    value = abi.hex_to_int(tx.get("value"))
    return {
        "hash": tx.get("hash"),
        "from": tx.get("from"),
        "to": tx.get("to"),
        "valueWei": str(value),
        "value": abi.format_units(value, 18),
        "nonce": abi.hex_to_int(tx.get("nonce")),
        "blockNumber": abi.hex_to_int(tx.get("blockNumber")) if tx.get("blockNumber") else None,
        "blockHash": tx.get("blockHash"),
        "gas": abi.hex_to_int(tx.get("gas")),
        "input": tx.get("input"),
        "explorer": f"{EXPLORER_URL.rstrip('/')}/tx/{tx_hash}",
    }


def get_receipt(client: RpcClient, tx_hash: str) -> dict[str, Any]:
    if not abi.is_tx_hash(tx_hash):
        raise QueryError(f"Invalid transaction hash: {tx_hash!r}")
    receipt = client.call("eth_getTransactionReceipt", [tx_hash])
    if receipt is None:
        raise QueryError(f"Receipt not found: {tx_hash}")
    status_hex = receipt.get("status")
    return {
        "transactionHash": receipt.get("transactionHash"),
        "status": abi.hex_to_int(status_hex) if status_hex is not None else None,
        "blockNumber": abi.hex_to_int(receipt.get("blockNumber")) if receipt.get("blockNumber") else None,
        "from": receipt.get("from"),
        "to": receipt.get("to"),
        "contractAddress": receipt.get("contractAddress"),
        "gasUsed": abi.hex_to_int(receipt.get("gasUsed")) if receipt.get("gasUsed") else None,
        "logsCount": len(receipt.get("logs") or []),
        "explorer": f"{EXPLORER_URL.rstrip('/')}/tx/{tx_hash}",
    }


def get_token_info(client: RpcClient, token: str) -> dict[str, Any]:
    if not abi.is_address(token):
        raise QueryError(f"Invalid token address: {token!r}")
    name = _eth_call_string(client, token, ERC20_SELECTORS["name"])
    symbol = _eth_call_string(client, token, ERC20_SELECTORS["symbol"])
    decimals = _eth_call_uint(client, token, ERC20_SELECTORS["decimals"])
    supply = _eth_call_uint(client, token, ERC20_SELECTORS["totalSupply"])
    return {
        "address": token,
        "name": name,
        "symbol": symbol,
        "decimals": decimals,
        "totalSupplyRaw": str(supply),
        "totalSupply": abi.format_units(supply, decimals) if decimals is not None else None,
        "explorer": f"{EXPLORER_URL.rstrip('/')}/token/{token}",
    }


def get_token_balance(client: RpcClient, token: str, holder: str) -> dict[str, Any]:
    if not abi.is_address(token):
        raise QueryError(f"Invalid token address: {token!r}")
    if not abi.is_address(holder):
        raise QueryError(f"Invalid holder address: {holder!r}")
    info = get_token_info(client, token)
    data = ERC20_SELECTORS["balanceOf"] + abi.pad_address_arg(holder)[2:]
    raw = client.call("eth_call", [{"to": token, "data": data}, "latest"])
    amount = abi.decode_uint256(raw)
    decimals = info.get("decimals") or 0
    return {
        "token": token,
        "holder": holder,
        "symbol": info.get("symbol"),
        "decimals": decimals,
        "balanceRaw": str(amount),
        "balance": abi.format_units(amount, decimals),
        "explorer": f"{EXPLORER_URL.rstrip('/')}/address/{holder}",
    }


def get_transfers(
    client: RpcClient,
    token: str,
    from_block: int | None = None,
    to_block: int | None = None,
    watch: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    if not abi.is_address(token):
        raise QueryError(f"Invalid token address: {token!r}")
    if watch is not None and not abi.is_address(watch):
        raise QueryError(f"Invalid watch address: {watch!r}")
    if limit < 1:
        raise QueryError("limit must be >= 1")

    latest = abi.hex_to_int(client.call("eth_blockNumber"))
    end = latest if to_block is None else to_block
    start = max(0, end - 200) if from_block is None else from_block
    if start > end:
        raise QueryError("from-block must be <= to-block")

    logs: list[dict[str, Any]] = []
    # Page in 1000-block windows (Pharos MCP documents this cap for get_logs).
    cursor = start
    while cursor <= end:
        window_end = min(cursor + 999, end)
        chunk = client.call(
            "eth_getLogs",
            [
                {
                    "fromBlock": abi.int_to_hex(cursor),
                    "toBlock": abi.int_to_hex(window_end),
                    "address": token,
                    "topics": [TRANSFER_TOPIC0],
                }
            ],
        )
        logs.extend(chunk or [])
        cursor = window_end + 1

    events = [decode_transfer_log(item) for item in logs]
    if watch:
        events = [
            event
            for event in events
            if abi.same_address(event["from"], watch) or abi.same_address(event["to"], watch)
        ]
    events = events[-limit:]
    decimals = _safe_decimals(client, token)
    for event in events:
        event["value"] = abi.format_units(int(event["valueRaw"]), decimals)
        event["decimals"] = decimals
    return {
        "token": token,
        "fromBlock": start,
        "toBlock": end,
        "watch": watch,
        "count": len(events),
        "events": events,
    }


def decode_transfer_log(log: dict[str, Any]) -> dict[str, Any]:
    topics = log.get("topics") or []
    if len(topics) < 3:
        raise QueryError("Log is not a standard ERC-20 Transfer event")
    value_raw = abi.decode_uint256(log.get("data") or "0x")
    return {
        "address": (log.get("address") or "").lower(),
        "from": abi.topic_to_address(topics[1]),
        "to": abi.topic_to_address(topics[2]),
        "valueRaw": str(value_raw),
        "blockNumber": abi.hex_to_int(log.get("blockNumber")),
        "transactionHash": log.get("transactionHash"),
        "logIndex": abi.hex_to_int(log.get("logIndex")) if log.get("logIndex") is not None else None,
        "explorer": (
            f"{EXPLORER_URL.rstrip('/')}/tx/{log.get('transactionHash')}"
            if log.get("transactionHash")
            else None
        ),
    }


def _block_tag(number: str | int | None) -> str:
    if number in (None, "", "latest"):
        return "latest"
    if isinstance(number, int):
        return abi.int_to_hex(number)
    text = str(number)
    if text.startswith("0x"):
        return text
    if text.isdigit():
        return abi.int_to_hex(int(text))
    if text in {"latest", "earliest", "pending", "safe", "finalized"}:
        return text
    raise QueryError(f"Invalid block number: {number!r}")


def _eth_call_string(client: RpcClient, token: str, selector: str) -> str:
    raw = client.call("eth_call", [{"to": token, "data": selector}, "latest"])
    return abi.decode_abi_string(raw)


def _eth_call_uint(client: RpcClient, token: str, selector: str) -> int:
    raw = client.call("eth_call", [{"to": token, "data": selector}, "latest"])
    return abi.decode_uint256(raw)


def _safe_decimals(client: RpcClient, token: str) -> int:
    try:
        return _eth_call_uint(client, token, ERC20_SELECTORS["decimals"])
    except Exception:
        return 18

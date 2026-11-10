# Event Monitoring Instructions

> Read-only. Uses `eth_getLogs` for ERC-20 `Transfer(address,address,uint256)`.
> Topic0 is the canonical keccak hash `0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef`.

---

## Transfers

### Overview
Fetches recent Transfer events of a token contract, optionally filtered by a watched public address.

### Command Template

```bash
python -m pharos_soai transfers 0xcfC8330f4BCAB529c625D12781b1C19466A9Fc8B --limit 10
python -m pharos_soai transfers 0xcfC8330f4BCAB529c625D12781b1C19466A9Fc8B --from-block 32580000 --to-block 32580200 --watch 0xADDRESS
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| token | address | Yes | ERC-20 contract |
| --from-block | int | No | Start height; default is latest minus 200 |
| --to-block | int | No | End height; default is latest |
| --watch | address | No | Keep only transfers where this address is sender or recipient |
| --limit | int | No | Maximum events to return (from the end of the range) |

### Output Parsing

| Field | Description |
|-------|-------------|
| events[].from / to | Indexed Transfer addresses |
| events[].valueRaw | Amount in the token's smallest unit |
| events[].value | Human-readable amount using `decimals()` |

Ranges larger than 1000 blocks are requested in 1000-block pages, matching the window documented for Pharos MCP `get_logs`.

---

## Monitor

### Overview
Polls `eth_blockNumber`, reads new Transfer logs, and keeps events that match an optional watched address and a minimum raw amount (threshold filter).

### Command Template

```bash
python -m pharos_soai monitor 0xcfC8330f4BCAB529c625D12781b1C19466A9Fc8B --lookback 20 --once
python -m pharos_soai monitor 0xcfC8330f4BCAB529c625D12781b1C19466A9Fc8B --watch 0xADDRESS --min-value 1000000 --interval 5 --once
```

`--min-value` is the raw token amount, not a USD price. For official USDC (6 decimals), `1000000` means 1 USDC.

### Agent Guidelines

1. Confirm chain ID first (`python -m pharos_soai chain`).
2. Prefer `--once` for demos and tests so the process exits.
3. Do not ask the user for a wallet connection.
4. If no events appear, say so honestly: the range may simply contain no transfers.

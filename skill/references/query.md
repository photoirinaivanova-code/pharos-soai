# Query Operation Instructions

> Network configuration is read from `assets/networks.json`.
> Private keys are not used. Do not pass `--private-key`.

---

## Chain

### Overview
Checks that the client is talking to Pharos Atlantic Testnet and reports the latest block.

### Command Template

```bash
python -m pharos_soai chain
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --rpc | URL | No | Override RPC URL. Default is the official Atlantic public endpoint. |

### Output Parsing

| Field | Description |
|-------|-------------|
| chainId | Must equal 688689 |
| chainIdMatch | `true` if the node matches the official chain ID |
| latestBlock | Current height |

### Error Handling

| Error Signature | Cause | Suggested Action |
|-----------------|-------|------------------|
| RPC transport error | Network or TLS problem | Retry; confirm https://atlantic.dplabs-internal.com |
| chainIdMatch false | Wrong network | Stop and check `--rpc` |

> **Agent Guidelines**:
> 1. Run this first in any session.
> 2. Do not continue if `chainIdMatch` is false.

---

## Block

### Overview
Returns header fields and transaction hashes for a block.

### Command Template

```bash
python -m pharos_soai block latest
python -m pharos_soai block 32580000
```

---

## Balance

### Overview
Reads the native balance of a public address via `eth_getBalance`.

### Command Template

```bash
python -m pharos_soai balance 0x0000000000000000000000000000000000000000
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| address | address | Yes | Public address, `0x` + 40 hex characters |

---

## Transaction

### Overview
Reads a transaction by hash via `eth_getTransactionByHash`.

### Command Template

```bash
python -m pharos_soai tx 0xTRANSACTION_HASH
```

---

## Receipt

### Overview
Reads a receipt via `eth_getTransactionReceipt`.

### Command Template

```bash
python -m pharos_soai receipt 0xTRANSACTION_HASH
```

---

## Token

### Overview
Calls ERC-20 `name`, `symbol`, `decimals`, and `totalSupply` with `eth_call`.

### Command Template

```bash
python -m pharos_soai token 0xcfC8330f4BCAB529c625D12781b1C19466A9Fc8B
```

Official USDC on Atlantic Testnet comes from the token registry.

---

## Token Balance

### Overview
Calls ERC-20 `balanceOf(address)` for a public holder address.

### Command Template

```bash
python -m pharos_soai token-balance 0xcfC8330f4BCAB529c625D12781b1C19466A9Fc8B 0xHOLDER
```

# Pharos Season of AI — Read-Only Onchain Data Skill

> Read-only skill for Pharos Atlantic Testnet. It never asks for, stores, or uses a private key or seed phrase. It cannot sign or broadcast transactions.

This package follows the Skill Engine layout described in the official guide:
https://docs.pharos.xyz/tooling-and-infrastructure/pharos-skill-engine-guide

The official Skill Engine uses Foundry `cast` / `forge` and documents write operations that require a private key. This skill deliberately implements only the query and event-monitoring path, through the Python CLI in this repository. Do not add write commands.

## Prerequisites

- Python 3.10 or newer
- A virtual environment with `requests` installed (see the repository README)
- Network access to the official public RPC

Do **not** install random third-party wallets or paste keys into the terminal for this skill.

## Network Configuration

Read `assets/networks.json`. Default network is Atlantic Testnet:

| Parameter | Value | Source |
|-----------|-------|--------|
| RPC | https://atlantic.dplabs-internal.com | [Atlantic Testnet](https://docs.pharos.xyz/getting-started/network/atlantic-testnet) |
| Chain ID | 688689 | same page |
| Explorer | https://atlantic.pharosscan.xyz/ | same page |
| Tokens | `assets/tokens.json` | [Token Registry](https://docs.pharos.xyz/getting-started/token-registry) |

Always verify `eth_chainId` equals `0xa8231` (688689) before reporting data.

The hosted Pharos MCP at `https://mcp.pharos.xyz/mcp` is documented against **Pacific Mainnet** (chain ID 1672). See [Pharos MCP](https://docs.pharos.xyz/tooling-and-infrastructure/mcp). This skill queries Atlantic Testnet directly so Easy-level work stays on the public testnet RPC.

## Capability Index

| User Need | Capability | Detailed Instructions |
|-----------|------------|----------------------|
| Check network / latest block / "what chain is this?" | `python -m pharos_soai chain` | → references/query.md#chain |
| Show a block | `python -m pharos_soai block [number]` | → references/query.md#block |
| Native balance of an address | `python -m pharos_soai balance <address>` | → references/query.md#balance |
| Transaction details | `python -m pharos_soai tx <hash>` | → references/query.md#transaction |
| Transaction receipt | `python -m pharos_soai receipt <hash>` | → references/query.md#receipt |
| ERC-20 token info | `python -m pharos_soai token <token>` | → references/query.md#token |
| ERC-20 balance | `python -m pharos_soai token-balance <token> <holder>` | → references/query.md#token-balance |
| Recent Transfer events | `python -m pharos_soai transfers <token>` | → references/monitor.md#transfers |
| Monitor new Transfer events / threshold filter | `python -m pharos_soai monitor <token> --watch <addr> --min-value <raw> --once` | → references/monitor.md#monitor |
| Official token list | `python -m pharos_soai tokens` | → assets/tokens.json |

## Security Reminders

- Never request a seed phrase or private key.
- Never pass `--private-key` to any command. This CLI rejects such flags.
- Use only public addresses and transaction hashes.
- Do not send transactions, deploy contracts, or spend funds.
- Do not point the RPC URL at a provider URL that embeds an API key in committed files.
- Confirm domains against official docs: `docs.pharos.xyz`, `ai.pharos.xyz`, `pharos.xyz`.

## Write Operation Pre-checks

Write operations are **not supported**. If a user asks to send tokens, deploy a contract, or sign anything, refuse and explain that this skill is read-only.

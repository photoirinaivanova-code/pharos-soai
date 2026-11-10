"""Official Atlantic Testnet parameters from Pharos docs.

Sources:
- https://docs.pharos.xyz/getting-started/network/atlantic-testnet
- https://docs.pharos.xyz/getting-started/token-registry
- https://docs.pharos.xyz/tooling-and-infrastructure/pharos-skill-engine-guide
"""

DEFAULT_RPC_URL = "https://atlantic.dplabs-internal.com"
DEFAULT_WS_URL = "wss://atlantic.dplabs-internal.com"
EXPECTED_CHAIN_ID = 688689
EXPLORER_URL = "https://atlantic.pharosscan.xyz/"
NATIVE_SYMBOL = "PHRS"  # used in official Skill Engine query examples
NETWORK_NAME = "Pharos Atlantic Testnet"

# keccak256("Transfer(address,address,uint256)")
TRANSFER_TOPIC0 = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)

ERC20_SELECTORS = {
    "name": "0x06fdde03",
    "symbol": "0x95d89b41",
    "decimals": "0x313ce567",
    "totalSupply": "0x18160ddd",
    "balanceOf": "0x70a08231",
}

# Official Atlantic Testnet Token Registry
OFFICIAL_TOKENS = {
    "USDC": {
        "name": "USD Coin",
        "decimals": 6,
        "address": "0xcfC8330f4BCAB529c625D12781b1C19466A9Fc8B",
    },
    "USDT": {
        "name": "Tether USD",
        "decimals": 6,
        "address": "0xE7E84B8B4f39C507499c40B4ac199B050e2882d5",
    },
    "WBTC": {
        "name": "Wrapped BTC",
        "decimals": 18,
        "address": "0x0c64F03EEa5c30946D5c55B4b532D08ad74638a4",
    },
    "WETH": {
        "name": "Wrapped ETH",
        "decimals": 18,
        "address": "0x7d211F77525ea39A0592794f793cC1036eEaccD5",
    },
    "WPHRS": {
        "name": "Wrapped PHRS",
        "decimals": 18,
        "address": "0x838800b758277CC111B2d48Ab01e5E164f8E9471",
    },
}

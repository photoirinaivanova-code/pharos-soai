from pharos_soai import abi
from pharos_soai.constants import EXPECTED_CHAIN_ID, TRANSFER_TOPIC0
from pharos_soai.queries import (
    QueryError,
    decode_transfer_log,
    get_balance,
    get_block,
    get_chain_info,
    get_token_balance,
    get_token_info,
    get_transaction,
    get_transfers,
)
from pharos_soai.monitor import matches_filters


class FakeClient:
    def __init__(self, mapping):
        self.url = "https://atlantic.dplabs-internal.com"
        self.mapping = {}
        for method, params, result in mapping:
            self.mapping[(method, _freeze(params))] = result
        self.calls = []

    def call(self, method, params=None):
        self.calls.append((method, params or []))
        key = (method, _freeze(params or []))
        if key not in self.mapping:
            raise AssertionError(f"unexpected call {method} {params}")
        return self.mapping[key]


def _freeze(value):
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    return value


def test_hex_and_units():
    assert abi.hex_to_int("0xa8231") == EXPECTED_CHAIN_ID
    assert abi.format_units(1_500_000, 6) == "1.5"
    assert abi.parse_units("1.5", 6) == 1_500_000
    assert abi.decode_abi_string(
        "0x"
        + "0" * 62
        + "20"
        + "0" * 63
        + "4"
        + "55534443"
        + "0" * 56
    ) == "USDC"


def test_get_chain_info():
    client = FakeClient(
        [
            ("eth_chainId", [], "0xa8231"),
            ("eth_blockNumber", [], "0x10"),
        ]
    )
    info = get_chain_info(client)
    assert info["chainId"] == EXPECTED_CHAIN_ID
    assert info["chainIdMatch"] is True
    assert info["latestBlock"] == 16


def test_get_balance_and_block():
    address = "0x1111111111111111111111111111111111111111"
    client = FakeClient(
        [
            ("eth_getBalance", [address, "latest"], hex(2 * 10**18)),
            (
                "eth_getBlockByNumber",
                ["latest", False],
                {
                    "number": "0x5",
                    "hash": "0xabc",
                    "parentHash": "0xdef",
                    "timestamp": "0x64",
                    "miner": address,
                    "gasUsed": "0x1",
                    "gasLimit": "0x2",
                    "transactions": ["0xaaa"],
                },
            ),
        ]
    )
    balance = get_balance(client, address)
    assert balance["balance"] == "2"
    block = get_block(client, "latest")
    assert block["number"] == 5
    assert block["transactionCount"] == 1


def test_invalid_address():
    try:
        get_balance(FakeClient([]), "not-an-address")
        assert False
    except QueryError:
        pass


def test_transaction_and_token():
    tx_hash = "0x" + "ab" * 32
    token = "0xcfC8330f4BCAB529c625D12781b1C19466A9Fc8B"
    holder = "0x2222222222222222222222222222222222222222"
    symbol_data = (
        "0x0000000000000000000000000000000000000000000000000000000000000020"
        "0000000000000000000000000000000000000000000000000000000000000004"
        "5553444300000000000000000000000000000000000000000000000000000000"
    )
    name_data = (
        "0x0000000000000000000000000000000000000000000000000000000000000020"
        "0000000000000000000000000000000000000000000000000000000000000008"
        "55534420436f696e000000000000000000000000000000000000000000000000"
    )
    client = FakeClient(
        [
            (
                "eth_getTransactionByHash",
                [tx_hash],
                {
                    "hash": tx_hash,
                    "from": holder,
                    "to": token,
                    "value": "0x0",
                    "nonce": "0x1",
                    "blockNumber": "0x9",
                    "blockHash": "0xbb",
                    "gas": "0x5208",
                    "input": "0x",
                },
            ),
            ("eth_call", [{"to": token, "data": "0x06fdde03"}, "latest"], name_data),
            ("eth_call", [{"to": token, "data": "0x95d89b41"}, "latest"], symbol_data),
            ("eth_call", [{"to": token, "data": "0x313ce567"}, "latest"], "0x6"),
            ("eth_call", [{"to": token, "data": "0x18160ddd"}, "latest"], hex(1000)),
            (
                "eth_call",
                [
                    {
                        "to": token,
                        "data": "0x70a08231" + "0" * 24 + holder[2:].lower(),
                    },
                    "latest",
                ],
                hex(1_500_000),
            ),
        ]
    )
    tx = get_transaction(client, tx_hash)
    assert tx["from"] == holder
    info = get_token_info(client, token)
    assert info["symbol"] == "USDC"
    assert info["decimals"] == 6
    bal = get_token_balance(client, token, holder)
    assert bal["balance"] == "1.5"


def test_decode_transfer_and_filters():
    token = "0xcfc8330f4bcab529c625d12781b1c19466a9fc8b"
    sender = "0x1111111111111111111111111111111111111111"
    recipient = "0x2222222222222222222222222222222222222222"
    event = decode_transfer_log(
        {
            "address": token,
            "blockNumber": "0xa",
            "transactionHash": "0x" + "cd" * 32,
            "logIndex": "0x1",
            "data": hex(2_000_000),
            "topics": [
                TRANSFER_TOPIC0,
                "0x" + "0" * 24 + sender[2:],
                "0x" + "0" * 24 + recipient[2:],
            ],
        }
    )
    assert event["from"] == sender
    assert event["to"] == recipient
    assert event["valueRaw"] == "2000000"
    assert matches_filters(event, sender, 1_000_000) is True
    assert matches_filters(event, sender, 3_000_000) is False
    assert matches_filters(event, "0x3333333333333333333333333333333333333333", 0) is False


def test_get_transfers_pages_and_filters():
    token = "0xcfC8330f4BCAB529c625D12781b1C19466A9Fc8B"
    watch = "0x1111111111111111111111111111111111111111"
    other = "0x2222222222222222222222222222222222222222"
    log = {
        "address": token,
        "blockNumber": "0x5",
        "transactionHash": "0x" + "ee" * 32,
        "logIndex": "0x0",
        "data": hex(10),
        "topics": [
            TRANSFER_TOPIC0,
            "0x" + "0" * 24 + watch[2:],
            "0x" + "0" * 24 + other[2:],
        ],
    }
    client = FakeClient(
        [
            ("eth_blockNumber", [], "0x5"),
            (
                "eth_getLogs",
                [
                    {
                        "fromBlock": "0x0",
                        "toBlock": "0x5",
                        "address": token,
                        "topics": [TRANSFER_TOPIC0],
                    }
                ],
                [log],
            ),
            ("eth_call", [{"to": token, "data": "0x313ce567"}, "latest"], "0x0"),
        ]
    )
    result = get_transfers(client, token, from_block=0, to_block=5, watch=watch, limit=10)
    assert result["count"] == 1
    assert result["events"][0]["from"] == watch

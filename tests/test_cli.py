import json

from pharos_soai.cli import main
from pharos_soai.monitor import monitor_transfers
from pharos_soai.constants import TRANSFER_TOPIC0
from tests.test_queries import FakeClient


def test_cli_rejects_private_key(capsys):
    code = main(["--private-key", "0xabc", "chain"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert code == 1
    assert payload["ok"] is False
    assert "read-only" in payload["error"]


def test_cli_invalid_address(capsys):
    code = main(["balance", "oops"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 1
    assert payload["ok"] is False


def test_monitor_once_with_fake_client():
    token = "0xcfC8330f4BCAB529c625D12781b1C19466A9Fc8B"
    watch = "0x1111111111111111111111111111111111111111"
    other = "0x2222222222222222222222222222222222222222"
    log = {
        "address": token.lower(),
        "blockNumber": "0x14",
        "transactionHash": "0x" + "11" * 32,
        "logIndex": "0x2",
        "data": hex(50),
        "topics": [
            TRANSFER_TOPIC0,
            "0x" + "0" * 24 + watch[2:],
            "0x" + "0" * 24 + other[2:],
        ],
    }
    client = FakeClient(
        [
            ("eth_call", [{"to": token, "data": "0x313ce567"}, "latest"], "0x0"),
            ("eth_blockNumber", [], "0x14"),
            (
                "eth_getLogs",
                [
                    {
                        "fromBlock": "0xf",
                        "toBlock": "0x14",
                        "address": token,
                        "topics": [TRANSFER_TOPIC0],
                    }
                ],
                [log],
            ),
        ]
    )
    events = monitor_transfers(client, token, watch=watch, min_value=10, once=True, lookback=5)
    assert len(events) == 1
    assert events[0]["valueRaw"] == "50"

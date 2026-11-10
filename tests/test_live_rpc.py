import pytest

from pharos_soai.constants import DEFAULT_RPC_URL, EXPECTED_CHAIN_ID, OFFICIAL_TOKENS
from pharos_soai.queries import get_chain_info, get_token_info, get_transfers
from pharos_soai.rpc import RpcClient


@pytest.mark.live
def test_live_chain_id_and_usdc():
    client = RpcClient(url=DEFAULT_RPC_URL, timeout=25)
    info = get_chain_info(client)
    assert info["chainId"] == EXPECTED_CHAIN_ID
    assert info["chainIdMatch"] is True
    assert info["latestBlock"] > 0

    usdc = OFFICIAL_TOKENS["USDC"]["address"]
    token = get_token_info(client, usdc)
    assert token["symbol"]
    assert token["decimals"] == 6

    transfers = get_transfers(client, usdc, limit=5)
    assert transfers["toBlock"] >= transfers["fromBlock"]
    assert isinstance(transfers["events"], list)

from pharos_soai.rpc import RpcClient, RpcError


class DummyResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class DummySession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def post(self, url, json, timeout, headers):
        self.calls.append({"url": url, "json": json, "timeout": timeout, "headers": headers})
        return DummyResponse(self.payload)


def test_call_returns_result():
    session = DummySession({"jsonrpc": "2.0", "id": 1, "result": "0xa8231"})
    client = RpcClient(url="https://example.test", session=session)
    assert client.call("eth_chainId") == "0xa8231"
    assert session.calls[0]["json"]["method"] == "eth_chainId"


def test_call_raises_on_rpc_error():
    session = DummySession({"error": {"code": -32000, "message": "nope"}})
    client = RpcClient(session=session)
    try:
        client.call("eth_blockNumber")
        assert False, "expected RpcError"
    except RpcError as exc:
        assert "nope" in str(exc)

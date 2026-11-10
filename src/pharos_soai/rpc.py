"""Minimal JSON-RPC client. Read-only: no signing, no private keys."""

from __future__ import annotations

from typing import Any

import requests

from pharos_soai.constants import DEFAULT_RPC_URL


class RpcError(RuntimeError):
    """Raised when the node returns a JSON-RPC error or a transport failure."""


class RpcClient:
    def __init__(
        self,
        url: str = DEFAULT_RPC_URL,
        timeout: float = 20.0,
        session: requests.Session | None = None,
    ) -> None:
        self.url = url
        self.timeout = timeout
        self.session = session or requests.Session()
        self._next_id = 1

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id,
            "method": method,
            "params": params or [],
        }
        self._next_id += 1
        try:
            response = self.session.post(
                self.url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            body = response.json()
        except requests.RequestException as exc:
            raise RpcError(f"RPC transport error: {exc}") from exc
        except ValueError as exc:
            raise RpcError("RPC returned non-JSON response") from exc

        if "error" in body and body["error"]:
            raise RpcError(f"RPC error: {body['error']}")
        if "result" not in body:
            raise RpcError(f"RPC response missing result: {body}")
        return body["result"]

from __future__ import annotations
import json, urllib.error, urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional

def _json_request(url, method="GET", payload=None):
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url=url, method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        raise RuntimeError(f"HTTP {e.code} for {url}: {body}") from e

@dataclass(frozen=True)
class ProofnetClient:
    base_url: str = "http://127.0.0.1:8788/pwos/proofnet"
    def status(self): return _json_request(f"{self.base_url}/api/status")
    def core_info(self): return _json_request(f"{self.base_url}/core/info")
    def block_tip(self): return _json_request(f"{self.base_url}/core/block/tip")
    def assets(self): return _json_request(f"{self.base_url}/core/assets")
    def vnova_prices(self): return _json_request(f"{self.base_url}/vnova/prices")
    def ai_chat(self, msg): return _json_request(f"{self.base_url}/ai/chat", "POST", {"message": msg})
    def ai_search(self, q): return _json_request(f"{self.base_url}/ai/docs/search?q={q}")
    def ai_qbit_context(self): return _json_request(f"{self.base_url}/ai/qbit/context")

@dataclass(frozen=True)
class WalletClient:
    base_url: str = "http://127.0.0.1:8788/pwos/wallet"
    def ready(self): return _json_request(f"{self.base_url}/readyz")

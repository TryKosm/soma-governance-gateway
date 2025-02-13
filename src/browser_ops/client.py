from __future__ import annotations

from typing import Any

import httpx


class SomaOSGatewayClient:
    """Minimal client for demos and integration tests."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}"}

    def evaluate_action(self, actor: str, action: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        with httpx.Client(base_url=self._base, headers=self._headers, timeout=30.0) as c:
            r = c.post(
                "/v1/evaluate-action",
                json={"actor": actor, "action": action, "context": context or {}},
            )
            r.raise_for_status()
            return r.json()

    def confirm_approval(self, approval_id: str) -> dict[str, Any]:
        with httpx.Client(base_url=self._base, headers=self._headers, timeout=30.0) as c:
            r = c.post(f"/v1/approvals/{approval_id}/confirm")
            r.raise_for_status()
            return r.json()

    def get_run(self, run_id: str) -> dict[str, Any]:
        with httpx.Client(base_url=self._base, headers=self._headers, timeout=30.0) as c:
            r = c.get(f"/v1/runs/{run_id}")
            r.raise_for_status()
            return r.json()

"""Tiny Python SDK for the SomaOS Governance Gateway.

Usage:
    from somaos_client import SomaOSClient
    client = SomaOSClient("http://localhost:8080", api_key="sk_demo_...")
    decision = client.evaluate_action("ops-admin", "export_customer_data", {"region": "EU"})
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class SomaOSError(RuntimeError):
    """Raised when the gateway returns a non-2xx response."""

    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(f"SomaOS error {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


@dataclass
class EvaluateDecision:
    run_id: str
    decision: str
    risk_score: int
    reason: str
    approval_id: str | None
    workspace_id: str


class SomaOSClient:
    """Minimal synchronous client for the SomaOS Governance Gateway."""

    def __init__(self, base_url: str, api_key: str, *, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._timeout = timeout

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        with httpx.Client(base_url=self._base_url, headers=self._headers, timeout=self._timeout) as c:
            response = c.request(method, path, **kwargs)
            if response.status_code >= 400:
                try:
                    detail = response.json()
                except Exception:  # noqa: BLE001
                    detail = response.text
                raise SomaOSError(response.status_code, detail)
            return response.json()

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/v1/health")

    def evaluate_action(
        self,
        actor: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> EvaluateDecision:
        payload = self._request(
            "POST",
            "/v1/evaluate-action",
            json={"actor": actor, "action": action, "context": context or {}},
        )
        return EvaluateDecision(
            run_id=payload["run_id"],
            decision=payload["decision"],
            risk_score=payload["risk_score"],
            reason=payload["reason"],
            approval_id=payload.get("approval_id"),
            workspace_id=payload["workspace_id"],
        )

    def confirm_approval(self, approval_id: str) -> dict[str, Any]:
        return self._request("POST", f"/v1/approvals/{approval_id}/confirm")

    def get_run(self, run_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/runs/{run_id}")

    def get_events(self, run_id: str) -> list[dict[str, Any]]:
        payload = self._request("GET", f"/v1/runs/{run_id}/events")
        return payload.get("events", [])

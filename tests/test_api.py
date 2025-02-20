from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from browser_ops.api import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("GOVERNANCE_DEMO_KEY", "sk_test_demo")
    monkeypatch.delenv("GOVERNANCE_API_KEYS", raising=False)
    monkeypatch.delenv("GOVERNANCE_API_KEYS_JSON", raising=False)
    return TestClient(create_app())


@pytest.fixture
def auth() -> dict[str, str]:
    return {"Authorization": "Bearer sk_test_demo"}


def test_health_no_auth(client: TestClient) -> None:
    r = client.get("/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "ai-governance-gateway"}


def test_evaluate_requires_auth(client: TestClient) -> None:
    r = client.post("/v1/evaluate-action", json={"actor": "a", "action": "list_files"})
    assert r.status_code == 401
    assert r.json()["detail"] == "missing_bearer_token"


def test_invalid_api_key_is_401(client: TestClient) -> None:
    r = client.post(
        "/v1/evaluate-action",
        headers={"Authorization": "Bearer not-a-key"},
        json={"actor": "a", "action": "list_files"},
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid_api_key"


def test_allow_low_risk(client: TestClient, auth: dict[str, str]) -> None:
    r = client.post(
        "/v1/evaluate-action",
        headers=auth,
        json={"actor": "agent:ops", "action": "list_files"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "allow"
    assert body["approval_id"] is None
    assert body["workspace_id"] == "ws_demo"

    events = client.get(f"/v1/runs/{body['run_id']}/events", headers=auth).json()["events"]
    types = [e["event_type"] for e in events]
    assert types == ["run_started", "policy_evaluated", "auto_allowed", "run_completed"]


def test_blocked_action(client: TestClient, auth: dict[str, str]) -> None:
    r = client.post(
        "/v1/evaluate-action",
        headers=auth,
        json={"actor": "ops-admin", "action": "disable_guardrails"},
    )
    assert r.status_code == 200
    assert r.json()["decision"] == "blocked"
    assert r.json()["approval_id"] is None


def test_approval_flow_completes_run(client: TestClient, auth: dict[str, str]) -> None:
    r = client.post(
        "/v1/evaluate-action",
        headers=auth,
        json={
            "actor": "agent:marketing-bot",
            "action": "publish_campaign",
            "context": {"audience_size": 25_000, "contains_pii": True},
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "review_required"
    approval_id = body["approval_id"]
    assert approval_id

    run = client.get(f"/v1/runs/{body['run_id']}", headers=auth).json()
    assert run["status"] == "awaiting_approval"

    confirmed = client.post(f"/v1/approvals/{approval_id}/confirm", headers=auth)
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "approved"

    final_run = client.get(f"/v1/runs/{body['run_id']}", headers=auth).json()
    assert final_run["status"] == "completed"

    events = client.get(f"/v1/runs/{body['run_id']}/events", headers=auth).json()["events"]
    types = [e["event_type"] for e in events]
    assert "approval_requested" in types
    assert "approval_confirmed" in types
    assert types[-1] == "run_completed"


def test_double_confirm_is_409(client: TestClient, auth: dict[str, str]) -> None:
    r = client.post(
        "/v1/evaluate-action",
        headers=auth,
        json={"actor": "ops-admin", "action": "send_external_email"},
    )
    aid = r.json()["approval_id"]
    assert client.post(f"/v1/approvals/{aid}/confirm", headers=auth).status_code == 200
    second = client.post(f"/v1/approvals/{aid}/confirm", headers=auth)
    assert second.status_code == 409


def test_unknown_run_is_404(client: TestClient, auth: dict[str, str]) -> None:
    assert client.get("/v1/runs/missing", headers=auth).status_code == 404
    assert client.get("/v1/runs/missing/events", headers=auth).status_code == 404


def test_rate_limit_returns_429(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "GOVERNANCE_API_KEYS_JSON",
        '{"sk_tight": {"workspace_id": "ws_tight", "rate_limit_tier": "free"}}',
    )
    monkeypatch.delenv("GOVERNANCE_DEMO_KEY", raising=False)
    monkeypatch.delenv("GOVERNANCE_API_KEYS", raising=False)
    c = TestClient(create_app())
    headers = {"Authorization": "Bearer sk_tight"}
    last = None
    for _ in range(35):
        last = c.get("/v1/runs/missing", headers=headers)
    assert last is not None
    assert last.status_code == 429
    assert last.json()["detail"] == "rate_limit_exceeded"


def test_throughput_smoke(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Local benchmark; not a strict SLA assertion, just a guardrail."""
    monkeypatch.setenv(
        "GOVERNANCE_API_KEYS_JSON",
        '{"sk_bench": {"workspace_id": "ws_bench", "rate_limit_tier": "enterprise"}}',
    )
    monkeypatch.delenv("GOVERNANCE_DEMO_KEY", raising=False)
    monkeypatch.delenv("GOVERNANCE_API_KEYS", raising=False)
    c = TestClient(create_app())
    headers = {"Authorization": "Bearer sk_bench"}

    n = 200
    start = time.perf_counter()
    for _ in range(n):
        r = c.post(
            "/v1/evaluate-action",
            headers=headers,
            json={"actor": "agent:bench", "action": "list_files"},
        )
        assert r.status_code == 200, r.json()
    elapsed = time.perf_counter() - start
    rps = n / elapsed
    capsys.readouterr()
    print(f"\n[bench] {n} evaluate-action calls in {elapsed:.3f}s ({rps:.1f} req/s)")
    assert rps > 50  # generous floor for laptop CI; manual runs typically see >100 rps

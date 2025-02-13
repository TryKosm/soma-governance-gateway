import os

import pytest
from fastapi.testclient import TestClient

from browser_ops.api import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("SOMAOS_DEMO_KEY", "test-key-demo")
    # Recreate app so auth picks up env
    app = create_app()
    return TestClient(app)


def test_health_no_auth(client: TestClient) -> None:
    r = client.get("/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_evaluate_requires_auth(client: TestClient) -> None:
    r = client.post("/v1/evaluate-action", json={"actor": "a", "action": "list_files"})
    assert r.status_code == 401


def test_evaluate_allow_low_risk(client: TestClient) -> None:
    r = client.post(
        "/v1/evaluate-action",
        headers={"Authorization": "Bearer test-key-demo"},
        json={"actor": "agent:ops", "action": "list_files", "context": {}},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["decision"] == "allow"
    assert data["approval_id"] is None
    run_id = data["run_id"]
    ev = client.get(
        f"/v1/runs/{run_id}/events",
        headers={"Authorization": "Bearer test-key-demo"},
    )
    assert ev.status_code == 200
    assert len(ev.json()["events"]) >= 2


def test_evaluate_blocked(client: TestClient) -> None:
    r = client.post(
        "/v1/evaluate-action",
        headers={"Authorization": "Bearer test-key-demo"},
        json={"actor": "agent:ops", "action": "disable_guardrails"},
    )
    assert r.status_code == 200
    assert r.json()["decision"] == "blocked"


def test_approval_flow(client: TestClient) -> None:
    r = client.post(
        "/v1/evaluate-action",
        headers={"Authorization": "Bearer test-key-demo"},
        json={"actor": "agent:ops", "action": "execute_browser_action", "context": {"url": "https://example.com"}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "review_required"
    aid = body["approval_id"]
    assert aid
    c = client.post(
        f"/v1/approvals/{aid}/confirm",
        headers={"Authorization": "Bearer test-key-demo"},
    )
    assert c.status_code == 200
    run = client.get(
        f"/v1/runs/{body['run_id']}",
        headers={"Authorization": "Bearer test-key-demo"},
    )
    assert run.json()["status"] == "completed"

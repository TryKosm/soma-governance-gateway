# Twitter / X demo script (~2 minutes)

Use this while screen-recording: terminal on the left, optional browser with `/docs` on the right.

## Setup (before record)

```bash
cd agentic-browser-ops-platform
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export SOMAOS_DEMO_KEY="sk_demo_local"
uvicorn browser_ops.api:app --host 127.0.0.1 --port 8080
```

## Voice-over beats

1. **Hook** — “Agents can browse and act. SomaOS-style governance means every sensitive action hits policy first: allow, human review, or hard block—with an audit trail you can replay.”
2. **Health** — Show `GET /v1/health` (no key) to prove the service is up.
3. **Safe path** — `evaluate-action` with `list_files`: instant **allow**, no approval.
4. **Risk path** — Same API with `execute_browser_action`: **review_required** plus `approval_id`.
5. **Approval** — `POST .../approvals/{id}/confirm`, then `GET .../runs/{run_id}/events` to show the timeline.
6. **Block** — One call with `disable_guardrails`: **blocked** by policy.
7. **Close** — “API-key gated, OpenAPI at `/docs`, code on GitHub under TryKosm.”

## Copy-paste curls (replace `RUN_ID` / `APPROVAL_ID` from JSON)

```bash
export H="Authorization: Bearer sk_demo_local"
curl -s http://127.0.0.1:8080/v1/health | jq .

curl -s -X POST http://127.0.0.1:8080/v1/evaluate-action \
  -H "Content-Type: application/json" -H "$H" \
  -d '{"actor":"agent:demo","action":"list_files","context":{}}' | jq .

curl -s -X POST http://127.0.0.1:8080/v1/evaluate-action \
  -H "Content-Type: application/json" -H "$H" \
  -d '{"actor":"agent:marketing-bot","action":"publish_campaign","context":{"contains_pii":true}}' | jq .

curl -s -X POST "http://127.0.0.1:8080/v1/approvals/APPROVAL_ID/confirm" -H "$H" | jq .
curl -s "http://127.0.0.1:8080/v1/runs/RUN_ID/events" -H "$H" | jq .

curl -s -X POST http://127.0.0.1:8080/v1/evaluate-action \
  -H "Content-Type: application/json" -H "$H" \
  -d '{"actor":"ops-admin","action":"disable_guardrails","context":{}}' | jq .
```

For a fully scripted (no-paste) walkthrough, just run [`examples/client_example.py`](../examples/client_example.py) against the same server.

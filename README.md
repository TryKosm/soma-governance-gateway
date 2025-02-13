# agentic-browser-ops-platform

Platform scaffold for agentic browser operations with policy-aware execution and observability.

## SomaOS Governance Gateway (demo API)

A small **FastAPI** surface you can record for a Twitter/X demo: API-key auth, policy evaluation, optional human-in-the-loop approval, and an in-memory audit timeline (suitable for explaining **governed agent workflows** from the SomaOS whitepaper narrative).

### Run locally

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
export SOMAOS_DEMO_KEY="your-secret-demo-key"
uvicorn browser_ops.api:app --reload --port 8765
```

Open [http://127.0.0.1:8765/docs](http://127.0.0.1:8765/docs) for OpenAPI. Send `Authorization: Bearer <same key>` on `/v1/*` routes (comma-separated keys also supported via `SOMAOS_API_KEYS`).

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/health` | Liveness (no API key) |
| POST | `/v1/evaluate-action` | Policy + risk; may return `approval_id` |
| POST | `/v1/approvals/{id}/confirm` | Confirm pending approval |
| GET | `/v1/runs/{runId}` | Run summary |
| GET | `/v1/runs/{runId}/events` | Audit / replay |

### Screen-record checklist

See [docs/twitter-demo-script.md](docs/twitter-demo-script.md) for a **~2 minute** voice-over and curl sequence.

### Library usage (existing)

```python
from browser_ops import run
from browser_ops.models import BrowserTask

print(run(BrowserTask(url="https://example.com", goal="smoke")))
```

# SomaOS Governance Gateway

![CI](https://github.com/TryKosm/agentic-browser-ops-platform/actions/workflows/ci.yml/badge.svg)

SomaOS Governance Gateway is an API-key-gated governance layer for AI workflow execution: policy checks, approval routing, and replayable audit trails.

[![CI](https://github.com/TryKosm/agentic-browser-ops-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/TryKosm/agentic-browser-ops-platform/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Why this exists

Most AI workflow systems optimize for generation quality but leave operational governance as an afterthought. This gateway makes governance a first-class API primitive:

- deterministic policy decisions (`allow`, `review_required`, `blocked`)
- explicit human-in-the-loop approval flow
- replayable run/event timeline for observability and audits

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export SOMAOS_DEMO_KEY="sk_demo_local"
uvicorn browser_ops.api:app --port 8080
```

## API endpoints

- `GET /v1/health`
- `POST /v1/evaluate-action`
- `POST /v1/approvals/{approvalId}/confirm`
- `GET /v1/runs/{runId}`
- `GET /v1/runs/{runId}/events`

Full details: [`docs/api.md`](docs/api.md)

## Example flow

```bash
export H="Authorization: Bearer sk_demo_local"

# evaluate action
curl -s -X POST http://127.0.0.1:8080/v1/evaluate-action \
  -H "Content-Type: application/json" -H "$H" \
  -d '{"actor":"agent:marketing-bot","action":"publish_campaign","context":{"contains_pii":true}}'
```

Also see [`examples/client_example.py`](examples/client_example.py) and [`docs/twitter-demo-script.md`](docs/twitter-demo-script.md).

## Roadmap

- [ ] Persist approvals + audit events to Postgres ([#1](https://github.com/TryKosm/agentic-browser-ops-platform/issues/1))
- [ ] Add signed `approval_required` webhooks ([#2](https://github.com/TryKosm/agentic-browser-ops-platform/issues/2))
- [ ] Publish Postman collection + OpenAPI export ([#3](https://github.com/TryKosm/agentic-browser-ops-platform/issues/3))

## Development

```bash
pytest -q
make check
```

## License

MIT — see [LICENSE](LICENSE).

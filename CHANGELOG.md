# Changelog

All notable changes to this project are documented in this file.

## 0.2.0 - 2026-05-01

### Added
- AI Governance Gateway API with:
  - `POST /v1/evaluate-action`
  - `POST /v1/approvals/{approvalId}/confirm`
  - `GET /v1/runs/{runId}`
  - `GET /v1/runs/{runId}/events`
  - `GET /v1/health`
- API key authentication and per-key rate limits.
- Deterministic policy decision engine (`allow`, `review_required`, `blocked`) and risk scoring.
- In-memory approval and audit stores for replayable event timelines.
- Python SDK at `sdk/python/gateway_client.py`.
- Example walkthrough at `examples/client_example.py`.
- API documentation in `docs/api.md`.

### Changed
- Rebranded project-facing docs and package metadata to AI Governance Gateway.
- Expanded README with architecture, production notes, and benchmark context.

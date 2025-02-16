# SomaOS — Governance Gateway API (V1)

SomaOS is a governed execution platform for AI workflows. This API reference covers the Governance Gateway slice: policy evaluation, approval routing, and replayable audit events for each run.

All `/v1/*` endpoints (except `/v1/health`) require an API key:

```http
Authorization: Bearer <SOMAOS_API_KEY>
```

Keys map to a `workspace_id` and a `rate_limit_tier`. Cross-workspace reads return `404`.

## Decision states

| Decision | Meaning | `approval_id` |
|---|---|---|
| `allow` | Within policy bounds; auto-completed. | `null` |
| `review_required` | Must be confirmed by a human. | UUID |
| `blocked` | Disallowed by policy. | `null` |

## Error codes

| Status | Meaning |
|---|---|
| `400` | Invalid body (missing `actor` / `action`). |
| `401` | Missing or invalid bearer token. |
| `404` | Approval or run not found / not in your workspace. |
| `409` | Approval already resolved. |
| `429` | Rate limit exceeded (per-key per-minute). |

---

## `GET /v1/health`

No auth. Liveness probe.

```json
{ "status": "ok", "service": "somaos-governance-gateway" }
```

## `POST /v1/evaluate-action`

Request:

```json
{
  "actor": "ops-admin",
  "action": "export_customer_data",
  "context": { "region": "EU", "contains_pii": true }
}
```

Response (`review_required` example):

```json
{
  "run_id": "5f8c…",
  "decision": "review_required",
  "risk_score": 9,
  "reason": "trust_threshold_requires_human",
  "approval_id": "8a6b…",
  "workspace_id": "ws_demo"
}
```

## `POST /v1/approvals/{approvalId}/confirm`

Confirm a pending approval. Idempotent against `pending` only; subsequent calls return `409`.

```json
{ "status": "approved", "approval_id": "8a6b…", "run_id": "5f8c…" }
```

## `GET /v1/runs/{runId}`

Run summary:

```json
{
  "run_id": "5f8c…",
  "workspace_id": "ws_demo",
  "actor": "ops-admin",
  "action": "export_customer_data",
  "decision": "review_required",
  "risk_score": 9,
  "status": "completed",
  "approval_id": "8a6b…"
}
```

## `GET /v1/runs/{runId}/events`

Replayable, append-only event timeline:

```json
{
  "run_id": "5f8c…",
  "events": [
    {"ts": "...", "event_type": "run_started", "actor": "ops-admin", "action": "export_customer_data"},
    {"ts": "...", "event_type": "policy_evaluated", "decision": "review_required", "risk_score": 9, "reason": null},
    {"ts": "...", "event_type": "approval_requested", "approval_id": "8a6b…", "reason": "trust_threshold_requires_human"},
    {"ts": "...", "event_type": "approval_confirmed", "approval_id": "8a6b…", "by": "ws_demo"},
    {"ts": "...", "event_type": "run_completed", "outcome": "approved_execution", "by": "ws_demo"}
  ]
}
```

## API-key environment

Choose one of:

```bash
# 1. Single demo key (auto-mapped to ws_demo / pro tier)
export SOMAOS_DEMO_KEY="sk_demo_pick_anything"

# 2. Comma-separated keys (default ws_default / free tier)
export SOMAOS_API_KEYS="sk_alpha,sk_beta"

# 3. Full JSON map with per-key workspace + tier
export SOMAOS_API_KEYS_JSON='{"sk_team_eu":{"workspace_id":"ws_eu","rate_limit_tier":"enterprise"}}'
```

Tiers: `free` (30 rpm), `pro` (120 rpm), `enterprise` (600 rpm).

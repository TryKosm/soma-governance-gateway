from __future__ import annotations

import uuid
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .audit import store
from .auth import verify_api_key
from .governance import evaluate


def _auth_dep(authorization: str | None = Header(default=None)) -> str:
    try:
        return verify_api_key(authorization)
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


class EvaluateActionBody(BaseModel):
    actor: str = Field(..., min_length=1, examples=["agent:checkout"])
    action: str = Field(..., min_length=1, examples=["execute_browser_action"])
    context: dict[str, Any] = Field(default_factory=dict)


class EvaluateActionResponse(BaseModel):
    run_id: str
    decision: str
    risk_score: int
    reason: str
    approval_id: str | None = None


class RunSummary(BaseModel):
    run_id: str
    actor: str
    action: str
    decision: str
    risk_score: int
    status: str
    approval_id: str | None


def create_app() -> FastAPI:
    app = FastAPI(
        title="SomaOS Governance Gateway",
        version="1.0.0",
        description="API-key gated policy, approvals, and audit trail for agentic workflows.",
    )

    @app.get("/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "somaos-governance-gateway"}

    @app.post("/v1/evaluate-action", response_model=EvaluateActionResponse)
    def evaluate_action(body: EvaluateActionBody, _key: str = Depends(_auth_dep)) -> EvaluateActionResponse:
        result = evaluate(body.actor, body.action, body.context)
        approval_id: str | None = None
        if result.requires_approval and result.decision != "blocked":
            approval_id = str(uuid.uuid4())
        record = store.create_run(
            body.actor,
            body.action,
            body.context,
            result.decision,
            result.risk_score,
            approval_id,
        )
        if result.decision == "blocked":
            store.append_event(record.run_id, "blocked", {"reason": result.reason})
        elif approval_id:
            store.append_event(
                record.run_id,
                "approval_created",
                {"approval_id": approval_id, "reason": result.reason},
            )
        else:
            store.append_event(record.run_id, "auto_allowed", {"reason": result.reason})
        return EvaluateActionResponse(
            run_id=record.run_id,
            decision=result.decision,
            risk_score=result.risk_score,
            reason=result.reason,
            approval_id=approval_id,
        )

    @app.post("/v1/approvals/{approval_id}/confirm")
    def confirm_approval(approval_id: str, _key: str = Depends(_auth_dep)) -> dict[str, Any]:
        run = store.confirm_approval(approval_id)
        if not run:
            raise HTTPException(status_code=404, detail="approval not found or not pending")
        return {"status": "approved", "run_id": run.run_id}

    @app.get("/v1/runs/{run_id}")
    def get_run(run_id: str, _key: str = Depends(_auth_dep)) -> RunSummary:
        run = store.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="run not found")
        return RunSummary(
            run_id=run.run_id,
            actor=run.actor,
            action=run.action,
            decision=run.decision,
            risk_score=run.risk_score,
            status=run.status,
            approval_id=run.approval_id,
        )

    @app.get("/v1/runs/{run_id}/events")
    def get_events(run_id: str, _key: str = Depends(_auth_dep)) -> dict[str, Any]:
        run = store.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="run not found")
        return {"run_id": run_id, "events": run.events}

    return app


app = create_app()

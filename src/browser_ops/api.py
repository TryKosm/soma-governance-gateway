from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .approvals import approvals
from .audit import audit
from .auth import ApiKeyPrincipal, AuthError, RateLimitError, authenticate
from .governance import Decision, evaluate


def _principal(authorization: str | None = Header(default=None)) -> ApiKeyPrincipal:
    try:
        return authenticate(authorization)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e)) from e


class EvaluateActionBody(BaseModel):
    actor: str = Field(..., min_length=1, examples=["agent:checkout"])
    action: str = Field(..., min_length=1, examples=["execute_browser_action"])
    context: dict[str, Any] = Field(default_factory=dict)


class EvaluateActionResponse(BaseModel):
    run_id: str
    decision: Decision
    risk_score: int
    reason: str
    approval_id: str | None = None
    workspace_id: str


class ConfirmApprovalResponse(BaseModel):
    status: str
    approval_id: str
    run_id: str


class RunSummary(BaseModel):
    run_id: str
    workspace_id: str
    actor: str
    action: str
    decision: str
    risk_score: int
    status: str
    approval_id: str | None


class EventsResponse(BaseModel):
    run_id: str
    events: list[dict[str, Any]]


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Governance Gateway",
        version="1.0.0",
        description=(
            "API-key gated policy decisions, human-in-the-loop approvals, "
            "and replayable audit trail for governed agent workflows."
        ),
    )

    @app.get("/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "ai-governance-gateway"}

    @app.post("/v1/evaluate-action", response_model=EvaluateActionResponse)
    def evaluate_action(
        body: EvaluateActionBody,
        principal: ApiKeyPrincipal = Depends(_principal),
    ) -> EvaluateActionResponse:
        result = evaluate(body.actor, body.action, body.context)
        approval_id: str | None = None

        record = audit.create_run(
            workspace_id=principal.workspace_id,
            actor=body.actor,
            action=body.action,
            context=body.context,
            decision=result.decision.value,
            risk_score=result.risk_score,
            pending_approval=result.requires_approval and result.decision != Decision.BLOCKED,
        )

        if result.decision == Decision.BLOCKED:
            audit.append_event(record.run_id, "blocked", {"reason": result.reason})
        elif result.requires_approval:
            approval = approvals.create(record.run_id)
            approval_id = approval.approval_id
            record.approval_id = approval_id
            audit.append_event(
                record.run_id,
                "approval_requested",
                {"approval_id": approval_id, "reason": result.reason},
            )
        else:
            audit.append_event(record.run_id, "auto_allowed", {"reason": result.reason})
            audit.mark_completed(record.run_id, outcome="auto_allowed", by="policy_engine")

        return EvaluateActionResponse(
            run_id=record.run_id,
            decision=result.decision,
            risk_score=result.risk_score,
            reason=result.reason,
            approval_id=approval_id,
            workspace_id=principal.workspace_id,
        )

    @app.post("/v1/approvals/{approval_id}/confirm", response_model=ConfirmApprovalResponse)
    def confirm_approval(
        approval_id: str,
        principal: ApiKeyPrincipal = Depends(_principal),
    ) -> ConfirmApprovalResponse:
        approval = approvals.get(approval_id)
        if not approval:
            raise HTTPException(status_code=404, detail="approval_not_found")
        run = audit.get_run(approval.run_id)
        if not run or run.workspace_id != principal.workspace_id:
            raise HTTPException(status_code=404, detail="approval_not_found")
        if approval.status != "pending":
            raise HTTPException(status_code=409, detail=f"approval_{approval.status}")
        approvals.confirm(approval_id)
        audit.append_event(
            run.run_id,
            "approval_confirmed",
            {"approval_id": approval_id, "by": principal.workspace_id},
        )
        audit.mark_completed(run.run_id, outcome="approved_execution", by=principal.workspace_id)
        return ConfirmApprovalResponse(status="approved", approval_id=approval_id, run_id=run.run_id)

    @app.get("/v1/runs/{run_id}", response_model=RunSummary)
    def get_run(run_id: str, principal: ApiKeyPrincipal = Depends(_principal)) -> RunSummary:
        run = audit.get_run(run_id)
        if not run or run.workspace_id != principal.workspace_id:
            raise HTTPException(status_code=404, detail="run_not_found")
        return RunSummary(
            run_id=run.run_id,
            workspace_id=run.workspace_id,
            actor=run.actor,
            action=run.action,
            decision=run.decision,
            risk_score=run.risk_score,
            status=run.status,
            approval_id=run.approval_id,
        )

    @app.get("/v1/runs/{run_id}/events", response_model=EventsResponse)
    def get_events(run_id: str, principal: ApiKeyPrincipal = Depends(_principal)) -> EventsResponse:
        run = audit.get_run(run_id)
        if not run or run.workspace_id != principal.workspace_id:
            raise HTTPException(status_code=404, detail="run_not_found")
        return EventsResponse(run_id=run_id, events=run.events)

    return app


app = create_app()

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RunRecord:
    run_id: str
    actor: str
    action: str
    context: dict[str, Any]
    decision: str
    risk_score: int
    status: str  # completed | awaiting_approval
    approval_id: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


class AuditStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._runs: dict[str, RunRecord] = {}
        self._approvals: dict[str, tuple[str, str]] = {}  # approval_id -> (run_id, status)

    def append_event(self, run_id: str, event_type: str, payload: dict[str, Any]) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return
            run.events.append({"ts": _now(), "type": event_type, **payload})

    def create_run(
        self,
        actor: str,
        action: str,
        context: dict[str, Any],
        decision: str,
        risk_score: int,
        approval_id: str | None,
    ) -> RunRecord:
        run_id = str(uuid.uuid4())
        record = RunRecord(
            run_id=run_id,
            actor=actor,
            action=action,
            context=context,
            decision=decision,
            risk_score=risk_score,
            status="awaiting_approval" if approval_id else "completed",
            approval_id=approval_id,
            events=[
                {
                    "ts": _now(),
                    "type": "run_started",
                    "actor": actor,
                    "action": action,
                },
                {
                    "ts": _now(),
                    "type": "policy_evaluated",
                    "decision": decision,
                    "risk_score": risk_score,
                },
            ],
        )
        with self._lock:
            self._runs[run_id] = record
            if approval_id:
                self._approvals[approval_id] = (run_id, "pending")
        return record

    def get_run(self, run_id: str) -> RunRecord | None:
        with self._lock:
            return self._runs.get(run_id)

    def confirm_approval(self, approval_id: str) -> RunRecord | None:
        with self._lock:
            row = self._approvals.get(approval_id)
            if not row or row[1] != "pending":
                return None
            run_id, _ = row
            run = self._runs.get(run_id)
            if not run:
                return None
            self._approvals[approval_id] = (run_id, "approved")
            run.status = "completed"
            run.events.append(
                {
                    "ts": _now(),
                    "type": "approval_confirmed",
                    "approval_id": approval_id,
                    "by": "api_operator",
                }
            )
            run.events.append({"ts": _now(), "type": "run_completed", "outcome": "approved_execution"})
            return run


store = AuditStore()

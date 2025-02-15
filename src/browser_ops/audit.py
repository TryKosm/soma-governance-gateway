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
    workspace_id: str
    actor: str
    action: str
    context: dict[str, Any]
    decision: str
    risk_score: int
    status: str  # completed | awaiting_approval
    approval_id: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


class AuditStore:
    """In-memory append-only event log with run lookups."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._runs: dict[str, RunRecord] = {}

    def create_run(
        self,
        *,
        workspace_id: str,
        actor: str,
        action: str,
        context: dict[str, Any],
        decision: str,
        risk_score: int,
        pending_approval: bool,
    ) -> RunRecord:
        run_id = str(uuid.uuid4())
        record = RunRecord(
            run_id=run_id,
            workspace_id=workspace_id,
            actor=actor,
            action=action,
            context=context,
            decision=decision,
            risk_score=risk_score,
            status="awaiting_approval" if pending_approval else "completed",
            approval_id=None,
            events=[
                {
                    "ts": _now(),
                    "event_type": "run_started",
                    "actor": actor,
                    "action": action,
                },
                {
                    "ts": _now(),
                    "event_type": "policy_evaluated",
                    "decision": decision,
                    "risk_score": risk_score,
                    "reason": None,
                },
            ],
        )
        with self._lock:
            self._runs[run_id] = record
        return record

    def append_event(self, run_id: str, event_type: str, payload: dict[str, Any]) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return
            run.events.append({"ts": _now(), "event_type": event_type, **payload})

    def mark_completed(self, run_id: str, *, outcome: str, by: str) -> RunRecord | None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return None
            run.status = "completed"
            run.events.append(
                {
                    "ts": _now(),
                    "event_type": "run_completed",
                    "outcome": outcome,
                    "by": by,
                }
            )
            return run

    def get_run(self, run_id: str) -> RunRecord | None:
        with self._lock:
            return self._runs.get(run_id)


audit = AuditStore()

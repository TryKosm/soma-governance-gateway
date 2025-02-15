from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Approval:
    approval_id: str
    run_id: str
    status: str  # pending | approved | rejected
    created_at: str
    resolved_at: str | None = None


class ApprovalStore:
    """Thread-safe in-memory pending-approval registry."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._items: dict[str, Approval] = {}

    def create(self, run_id: str) -> Approval:
        approval_id = str(uuid.uuid4())
        approval = Approval(
            approval_id=approval_id,
            run_id=run_id,
            status="pending",
            created_at=_now(),
        )
        with self._lock:
            self._items[approval_id] = approval
        return approval

    def get(self, approval_id: str) -> Approval | None:
        with self._lock:
            return self._items.get(approval_id)

    def confirm(self, approval_id: str) -> Approval | None:
        with self._lock:
            approval = self._items.get(approval_id)
            if not approval or approval.status != "pending":
                return None
            approval.status = "approved"
            approval.resolved_at = _now()
            return approval

    def reject(self, approval_id: str) -> Approval | None:
        with self._lock:
            approval = self._items.get(approval_id)
            if not approval or approval.status != "pending":
                return None
            approval.status = "rejected"
            approval.resolved_at = _now()
            return approval


approvals = ApprovalStore()

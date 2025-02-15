from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Decision(str, Enum):
    ALLOW = "allow"
    REVIEW_REQUIRED = "review_required"
    BLOCKED = "blocked"


BLOCKED_ACTIONS: frozenset[str] = frozenset(
    {"disable_guardrails", "export_raw_pii", "delete_production_data"}
)

REVIEW_ACTIONS: frozenset[str] = frozenset(
    {
        "export_customer_summary",
        "send_external_email",
        "publish_campaign",
        "execute_browser_action",
        "export_customer_data",
    }
)

REVIEW_RISK_THRESHOLD = 7


@dataclass(frozen=True)
class EvaluationResult:
    decision: Decision
    risk_score: int
    reason: str
    requires_approval: bool


def risk_score(actor: str, action: str, context: dict[str, Any]) -> int:
    """Deterministic, easily-testable risk heuristic in [1, 10]."""
    score = 1
    actor_l = actor.lower()
    action_l = action.lower()
    if "admin" in actor_l or "root" in actor_l:
        score += 3
    if any(token in action_l for token in ("export", "delete", "publish", "external", "transfer")):
        score += 4
    if context.get("contains_pii") is True:
        score += 3
    if context.get("region") in {"EU", "eu"}:
        score += 1
    return max(1, min(score, 10))


def evaluate(actor: str, action: str, context: dict[str, Any]) -> EvaluationResult:
    """Return policy decision, risk score, and human-readable reason."""
    rs = risk_score(actor, action, context)
    if action in BLOCKED_ACTIONS:
        return EvaluationResult(Decision.BLOCKED, rs, "action_blocked_by_policy", False)
    if action in REVIEW_ACTIONS or rs >= REVIEW_RISK_THRESHOLD:
        return EvaluationResult(
            Decision.REVIEW_REQUIRED, rs, "trust_threshold_requires_human", True
        )
    return EvaluationResult(Decision.ALLOW, rs, "within_policy_bounds", False)

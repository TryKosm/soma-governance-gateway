from __future__ import annotations

from dataclasses import dataclass
from typing import Any


BLOCKED_ACTIONS = frozenset({"disable_guardrails", "export_raw_pii", "delete_production_data"})
REVIEW_ACTIONS = frozenset(
    {
        "export_customer_summary",
        "send_external_email",
        "publish_campaign",
        "execute_browser_action",
    }
)


@dataclass
class EvaluationResult:
    decision: str  # allow | review_required | blocked
    risk_score: int
    reason: str
    requires_approval: bool


def risk_score(actor: str, action: str, context: dict[str, Any]) -> int:
    score = 1
    if "admin" in actor.lower():
        score += 3
    if any(x in action.lower() for x in ("export", "delete", "publish", "external")):
        score += 4
    if context.get("contains_pii") is True:
        score += 3
    return min(score, 10)


def evaluate(actor: str, action: str, context: dict[str, Any]) -> EvaluationResult:
    rs = risk_score(actor, action, context)
    if action in BLOCKED_ACTIONS:
        return EvaluationResult("blocked", rs, "action_blocked_by_policy", False)
    if action in REVIEW_ACTIONS or rs >= 7:
        return EvaluationResult("review_required", rs, "trust_threshold_requires_human", True)
    return EvaluationResult("allow", rs, "within_policy_bounds", False)

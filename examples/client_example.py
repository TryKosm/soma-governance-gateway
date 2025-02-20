"""Two end-to-end AI Governance Gateway scenarios.

Start the gateway in another terminal:

    export GOVERNANCE_DEMO_KEY="sk_demo_local"
    uvicorn browser_ops.api:app --port 8080

Then run:

    python examples/client_example.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "sdk" / "python"))

from gateway_client import GovernanceGatewayClient  # noqa: E402


def marketing_workflow_review(client: GovernanceGatewayClient) -> None:
    print("\n=== Scenario 1: marketing campaign requires review ===")
    decision = client.evaluate_action(
        actor="agent:marketing-bot",
        action="publish_campaign",
        context={"channel": "email", "audience_size": 25_000, "contains_pii": True},
    )
    print(f"decision={decision.decision} risk={decision.risk_score} reason={decision.reason}")
    if decision.approval_id is None:
        print("(unexpected) no approval id returned")
        return

    print(f"awaiting human approval -> approval_id={decision.approval_id}")
    confirmed = client.confirm_approval(decision.approval_id)
    print(f"confirm response: {confirmed}")

    events = client.get_events(decision.run_id)
    print(f"replay ({len(events)} events):")
    for ev in events:
        print(f"  - {ev['event_type']:<22} {ev}")


def operations_action_blocked(client: GovernanceGatewayClient) -> None:
    print("\n=== Scenario 2: operations action blocked by policy ===")
    decision = client.evaluate_action(
        actor="ops-admin",
        action="disable_guardrails",
        context={"reason": "debugging"},
    )
    print(f"decision={decision.decision} risk={decision.risk_score} reason={decision.reason}")
    summary = client.get_run(decision.run_id)
    print(f"run status: {summary['status']}")


def main() -> None:
    base_url = os.environ.get("GOVERNANCE_BASE_URL", "http://127.0.0.1:8080")
    api_key = os.environ.get("GOVERNANCE_DEMO_KEY") or os.environ.get("GOVERNANCE_API_KEY")
    if not api_key:
        raise SystemExit("Set GOVERNANCE_DEMO_KEY or GOVERNANCE_API_KEY before running this example.")

    client = GovernanceGatewayClient(base_url, api_key=api_key)
    print(f"health: {client.health()}")

    marketing_workflow_review(client)
    operations_action_blocked(client)


if __name__ == "__main__":
    main()

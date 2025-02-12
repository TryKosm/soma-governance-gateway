from browser_ops.models import BrowserTask
from browser_ops.planner import plan_steps


def test_plan_contains_navigation_step() -> None:
    steps = plan_steps(BrowserTask("1", "collect", "https://example.com"))
    assert steps[0].startswith("navigate:")

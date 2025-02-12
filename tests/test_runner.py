from browser_ops.models import BrowserTask
from browser_ops.runner import run


def test_blocked_url_returns_blocked_status() -> None:
    out = run(BrowserTask("t1", "check", "https://internal-only.example"))
    assert out["status"] == "blocked"

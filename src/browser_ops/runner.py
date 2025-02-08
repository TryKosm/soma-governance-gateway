from .models import BrowserTask
from .planner import plan_steps
from .policy import is_allowed_url


def run(task: BrowserTask) -> dict[str, object]:
    if not is_allowed_url(task.url):
        return {"status": "blocked", "steps": []}
    return {"status": "ok", "steps": plan_steps(task)}

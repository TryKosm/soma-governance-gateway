from .models import BrowserTask


def plan_steps(task: BrowserTask) -> list[str]:
    return [
        f"navigate:{task.url}",
        "snapshot:page",
        "execute:objective",
        "verify:result",
    ]

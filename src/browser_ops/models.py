from dataclasses import dataclass


@dataclass
class BrowserTask:
    task_id: str
    objective: str
    url: str

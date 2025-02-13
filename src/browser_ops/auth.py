from __future__ import annotations

import os


def load_valid_keys() -> set[str]:
    raw = os.environ.get("SOMAOS_API_KEYS", "")
    keys = {k.strip() for k in raw.split(",") if k.strip()}
    demo = os.environ.get("SOMAOS_DEMO_KEY", "").strip()
    if demo:
        keys.add(demo)
    return keys


def verify_api_key(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise PermissionError("missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if not token or token not in load_valid_keys():
        raise PermissionError("invalid api key")
    return token

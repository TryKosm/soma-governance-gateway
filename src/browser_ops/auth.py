from __future__ import annotations

import json
import os
import time
from collections import deque
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class ApiKeyPrincipal:
    """Identity material attached to a valid API key."""

    api_key: str
    workspace_id: str
    rate_limit_tier: str
    rate_limit_per_minute: int


_TIERS: dict[str, int] = {"free": 30, "pro": 120, "enterprise": 600}


def _load_keymap() -> dict[str, ApiKeyPrincipal]:
    """Load keys from `SOMAOS_API_KEYS_JSON` (preferred) or simpler env vars.

    `SOMAOS_API_KEYS_JSON` example:
      {"sk_demo_123": {"workspace_id": "ws_demo", "rate_limit_tier": "pro"}}
    """
    raw = os.environ.get("SOMAOS_API_KEYS_JSON", "").strip()
    keymap: dict[str, ApiKeyPrincipal] = {}
    if raw:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {}
        for k, v in payload.items():
            tier = (v or {}).get("rate_limit_tier", "free")
            keymap[k] = ApiKeyPrincipal(
                api_key=k,
                workspace_id=(v or {}).get("workspace_id", "ws_default"),
                rate_limit_tier=tier,
                rate_limit_per_minute=_TIERS.get(tier, _TIERS["free"]),
            )

    fallback_keys = os.environ.get("SOMAOS_API_KEYS", "")
    for k in (s.strip() for s in fallback_keys.split(",") if s.strip()):
        keymap.setdefault(
            k,
            ApiKeyPrincipal(
                api_key=k,
                workspace_id="ws_default",
                rate_limit_tier="free",
                rate_limit_per_minute=_TIERS["free"],
            ),
        )

    demo = os.environ.get("SOMAOS_DEMO_KEY", "").strip()
    if demo:
        keymap.setdefault(
            demo,
            ApiKeyPrincipal(
                api_key=demo,
                workspace_id="ws_demo",
                rate_limit_tier="pro",
                rate_limit_per_minute=_TIERS["pro"],
            ),
        )
    return keymap


class AuthError(Exception):
    pass


class RateLimitError(Exception):
    pass


class _RateLimiter:
    """Sliding-window per-key counter; sufficient for V1 demos."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._hits: dict[str, deque[float]] = {}

    def check(self, key: str, limit_per_minute: int) -> None:
        now = time.monotonic()
        cutoff = now - 60.0
        with self._lock:
            bucket = self._hits.setdefault(key, deque())
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= limit_per_minute:
                raise RateLimitError("rate_limit_exceeded")
            bucket.append(now)


_rate_limiter = _RateLimiter()


def authenticate(authorization: str | None) -> ApiKeyPrincipal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("missing_bearer_token")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise AuthError("missing_bearer_token")
    keymap = _load_keymap()
    principal = keymap.get(token)
    if not principal:
        raise AuthError("invalid_api_key")
    _rate_limiter.check(token, principal.rate_limit_per_minute)
    return principal

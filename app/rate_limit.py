"""Simple per-client token bucket (no external dependency).

``RATE_LIMIT_PER_MINUTE`` requests per client IP; ``0`` disables the limiter.
This protects the demo deployment and the Token Factory credits behind it.
"""

from __future__ import annotations

import threading
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings

EXEMPT_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}


class TokenBucket:
    def __init__(self, capacity: int, refill_per_second: float) -> None:
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self.tokens = float(capacity)
        self.updated = time.monotonic()

    def take(self) -> bool:
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.refill_per_second)
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class RateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, per_minute: int) -> bool:
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None or bucket.capacity != per_minute:
                bucket = TokenBucket(per_minute, per_minute / 60.0)
                self._buckets[key] = bucket
            return bucket.take()

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        per_minute = get_settings().rate_limit_per_minute
        if per_minute <= 0 or request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        client = request.client.host if request.client else "anonymous"
        if not limiter.allow(client, per_minute):
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded: {per_minute} requests per minute. Try again shortly."},
                headers={"Retry-After": "60"},
            )
        return await call_next(request)

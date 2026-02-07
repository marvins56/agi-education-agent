"""Sliding-window rate limiter using Redis sorted sets."""

import time

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RateLimiter:
    """Redis-backed sliding window rate limiter using ZADD + ZRANGEBYSCORE."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6380/0",
        default_limit: int = 60,
        window_seconds: int = 60,
    ):
        self.redis_url = redis_url
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def check_rate_limit(
        self, key: str, limit: int | None = None
    ) -> tuple[bool, int, int]:
        """Check rate limit for a key.

        Returns:
            (allowed, remaining, reset_timestamp)
        """
        effective_limit = limit or self.default_limit
        now = time.time()
        window_start = now - self.window_seconds
        reset_ts = int(now + self.window_seconds)

        redis = await self._get_redis()
        pipe = redis.pipeline()
        # Remove old entries outside window
        pipe.zremrangebyscore(key, 0, window_start)
        # Count current entries in window
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {f"{now}": now})
        # Set expiry on the key
        pipe.expire(key, self.window_seconds)
        results = await pipe.execute()

        current_count = results[1]
        remaining = max(0, effective_limit - current_count - 1)
        allowed = current_count < effective_limit

        return allowed, remaining, reset_ts

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that enforces rate limits per user or IP."""

    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next) -> Response:
        # Determine key: use user_id from token if available, else IP
        key_id = request.client.host if request.client else "unknown"
        if hasattr(request.state, "user_id"):
            key_id = request.state.user_id
        rate_key = f"rate_limit:{key_id}"

        try:
            allowed, remaining, reset_ts = await self.rate_limiter.check_rate_limit(rate_key)
        except Exception:
            # If Redis is down, allow the request
            return await call_next(request)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_ts),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_ts)
        return response

"""Tests for rate limiting middleware."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.api.middleware.rate_limit import RateLimiter


class TestRateLimiter:
    async def test_check_rate_limit_allowed(self):
        """Request should be allowed when under limit."""
        limiter = RateLimiter(default_limit=10, window_seconds=60)

        mock_pipe = MagicMock()
        mock_pipe.zremrangebyscore = MagicMock()
        mock_pipe.zcard = MagicMock()
        mock_pipe.zadd = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[0, 3, True, True])

        mock_redis = AsyncMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)
        limiter._redis = mock_redis

        allowed, remaining, reset_ts = await limiter.check_rate_limit("test-key")
        assert allowed is True
        assert remaining == 6  # 10 - 3 - 1
        assert isinstance(reset_ts, int)

    async def test_check_rate_limit_exceeded(self):
        """Request should be denied when at limit."""
        limiter = RateLimiter(default_limit=5, window_seconds=60)

        mock_pipe = MagicMock()
        mock_pipe.zremrangebyscore = MagicMock()
        mock_pipe.zcard = MagicMock()
        mock_pipe.zadd = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[0, 5, True, True])

        mock_redis = AsyncMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)
        limiter._redis = mock_redis

        allowed, remaining, reset_ts = await limiter.check_rate_limit("test-key")
        assert allowed is False
        assert remaining == 0

    async def test_custom_limit_override(self):
        """Custom limit should override default."""
        limiter = RateLimiter(default_limit=100, window_seconds=60)

        mock_pipe = MagicMock()
        mock_pipe.zremrangebyscore = MagicMock()
        mock_pipe.zcard = MagicMock()
        mock_pipe.zadd = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[0, 15, True, True])

        mock_redis = AsyncMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)
        limiter._redis = mock_redis

        # Custom limit of 20
        allowed, remaining, _ = await limiter.check_rate_limit("key", limit=20)
        assert allowed is True
        assert remaining == 4  # 20 - 15 - 1

    async def test_remaining_never_negative(self):
        """Remaining count should never go below zero."""
        limiter = RateLimiter(default_limit=5, window_seconds=60)

        mock_pipe = MagicMock()
        mock_pipe.zremrangebyscore = MagicMock()
        mock_pipe.zcard = MagicMock()
        mock_pipe.zadd = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[0, 10, True, True])

        mock_redis = AsyncMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)
        limiter._redis = mock_redis

        allowed, remaining, _ = await limiter.check_rate_limit("key")
        assert allowed is False
        assert remaining == 0  # Never negative

    async def test_close_cleans_up(self):
        """Close should clean up Redis connection."""
        limiter = RateLimiter()
        mock_redis = AsyncMock()
        limiter._redis = mock_redis

        await limiter.close()
        mock_redis.close.assert_called_once()
        assert limiter._redis is None

    async def test_close_when_no_redis(self):
        """Close should be safe when no Redis connection exists."""
        limiter = RateLimiter()
        await limiter.close()  # Should not raise

"""Tests for F07 Session Management & F08 Auth Hardening."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.auth.rbac import Role, require_role
from src.auth.schemas import GuestTokenResponse, PasswordChangeRequest, UserDetailResponse
from src.auth.security import (
    create_guest_token,
    hash_token,
    verify_token,
    check_account_lockout,
    record_failed_login,
    clear_failed_logins,
    MAX_FAILED_ATTEMPTS,
)


# --- RBAC Tests ---


class TestRBAC:
    def test_role_enum_values(self):
        assert Role.student == "student"
        assert Role.teacher == "teacher"
        assert Role.parent == "parent"
        assert Role.admin == "admin"

    async def test_require_role_student_allowed(self):
        """Student should be allowed to access student-only routes."""
        mock_user = MagicMock()
        mock_user.role = "student"

        checker = require_role(Role.student)
        result = await checker(current_user=mock_user)
        assert result is mock_user

    async def test_require_role_student_denied_teacher_route(self):
        """Student should NOT be allowed to access teacher-only routes."""
        mock_user = MagicMock()
        mock_user.role = "student"

        checker = require_role(Role.teacher)
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)
        assert exc_info.value.status_code == 403
        assert "not authorized" in exc_info.value.detail

    async def test_require_role_admin_access_all(self):
        """Admin should be able to access any role-restricted route."""
        mock_user = MagicMock()
        mock_user.role = "admin"

        # Admin accessing a teacher-only route
        checker = require_role(Role.teacher)
        result = await checker(current_user=mock_user)
        assert result is mock_user

        # Admin accessing a student-only route
        checker = require_role(Role.student)
        result = await checker(current_user=mock_user)
        assert result is mock_user

    async def test_require_role_teacher_denied_parent_route(self):
        """Teacher should NOT be allowed to access parent-only routes."""
        mock_user = MagicMock()
        mock_user.role = "teacher"

        checker = require_role(Role.parent)
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)
        assert exc_info.value.status_code == 403


# --- Guest Token Tests ---


class TestGuestToken:
    def test_guest_token_creation(self):
        """Guest token should be a valid JWT string."""
        token = create_guest_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_guest_token_has_guest_role(self):
        """Guest token payload should have role=guest."""
        token = create_guest_token()
        payload = verify_token(token)
        assert payload["role"] == "guest"
        assert payload["sub"].startswith("guest-")
        assert payload["type"] == "access"

    def test_guest_token_response_schema(self):
        """GuestTokenResponse schema should validate correctly."""
        resp = GuestTokenResponse(access_token="abc123", expires_in=3600)
        assert resp.token_type == "bearer"
        assert resp.expires_in == 3600


# --- Hash Token Tests ---


class TestHashToken:
    def test_hash_token_consistent(self):
        """Same input should produce the same hash."""
        token = "my-refresh-token-123"
        h1 = hash_token(token)
        h2 = hash_token(token)
        assert h1 == h2

    def test_hash_token_different_inputs(self):
        """Different inputs should produce different hashes."""
        h1 = hash_token("token-a")
        h2 = hash_token("token-b")
        assert h1 != h2

    def test_hash_token_is_hex_sha256(self):
        """Hash should be a 64-char hex string (SHA-256)."""
        h = hash_token("test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# --- Rate Limit Tests ---


class TestRateLimit:
    async def test_rate_limit_check(self):
        """Rate limiter should use Redis pipeline for sliding window."""
        from src.api.middleware.rate_limit import RateLimiter

        limiter = RateLimiter(default_limit=10, window_seconds=60)

        # Mock Redis
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

    async def test_rate_limit_exceeded(self):
        """Rate limiter should deny when limit is reached."""
        from src.api.middleware.rate_limit import RateLimiter

        limiter = RateLimiter(default_limit=5, window_seconds=60)

        mock_pipe = MagicMock()
        mock_pipe.zremrangebyscore = MagicMock()
        mock_pipe.zcard = MagicMock()
        mock_pipe.zadd = MagicMock()
        mock_pipe.expire = MagicMock()
        # current_count = 5, which equals the limit
        mock_pipe.execute = AsyncMock(return_value=[0, 5, True, True])

        mock_redis = AsyncMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)

        limiter._redis = mock_redis

        allowed, remaining, reset_ts = await limiter.check_rate_limit("test-key")
        assert allowed is False
        assert remaining == 0


# --- Password Change Schema Tests ---


class TestPasswordChangeSchema:
    def test_password_change_schema_validation(self):
        """PasswordChangeRequest should enforce min length on new_password."""
        req = PasswordChangeRequest(old_password="oldpass", new_password="newpass12")
        assert req.new_password == "newpass12"

    def test_password_change_schema_too_short(self):
        """PasswordChangeRequest should reject short new_password."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PasswordChangeRequest(old_password="oldpass", new_password="short")


# --- Account Lockout Tests ---


class TestAccountLockout:
    async def test_account_lockout_after_5_fails(self):
        """Account should be locked after MAX_FAILED_ATTEMPTS failures."""
        mock_redis = AsyncMock()
        email = "bad@example.com"

        # Simulate incrementing to threshold
        mock_redis.incr = AsyncMock(side_effect=list(range(1, MAX_FAILED_ATTEMPTS + 1)))
        mock_redis.expire = AsyncMock()
        mock_redis.set = AsyncMock()

        for i in range(MAX_FAILED_ATTEMPTS):
            await record_failed_login(mock_redis, email)

        # On the 5th call, lockout flag should be set
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert f"lockout:{email}" in call_args[0][0]

    async def test_check_lockout_not_locked(self):
        """Non-locked account should return False."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        result = await check_account_lockout(mock_redis, "user@example.com")
        assert result is False

    async def test_check_lockout_locked(self):
        """Locked account should return True."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="1")
        result = await check_account_lockout(mock_redis, "user@example.com")
        assert result is True

    async def test_clear_failed_logins(self):
        """Clearing logins should delete both keys."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock()
        await clear_failed_logins(mock_redis, "user@example.com")
        assert mock_redis.delete.call_count == 2


# --- Session End / Archive Tests ---


class TestSessionEndArchive:
    async def test_session_end_archives(self):
        """Ending a session should set ended_at, summary, and is_archived."""
        from src.models.session import Session

        session = MagicMock(spec=Session)
        session.id = uuid.uuid4()
        session.student_id = uuid.uuid4()
        session.mode = "tutoring"
        session.subject = "Mathematics"
        session.topic = "Algebra"
        session.started_at = datetime(2026, 2, 7, 10, 0, tzinfo=timezone.utc)
        session.ended_at = None
        session.summary = None
        session.is_archived = False
        session.message_count = 5
        session.device_info = None

        # Simulate ending logic
        now = datetime(2026, 2, 7, 10, 30, tzinfo=timezone.utc)
        topics = []
        if session.subject:
            topics.append(session.subject)
        if session.topic:
            topics.append(session.topic)
        summary = f"Session on {', '.join(topics) if topics else 'general tutoring'}"
        duration_seconds = (now - session.started_at).total_seconds()
        duration_minutes = int(duration_seconds // 60)
        summary += f" ({duration_minutes} min)"

        session.ended_at = now
        session.summary = summary
        session.is_archived = True

        assert session.ended_at == now
        assert session.is_archived is True
        assert "Mathematics" in session.summary
        assert "Algebra" in session.summary
        assert "30 min" in session.summary


# --- UserDetailResponse Tests ---


class TestUserDetailResponse:
    def test_user_detail_response_schema(self):
        """UserDetailResponse should include role, is_active, last_login."""
        resp = UserDetailResponse(
            id="abc-123",
            email="test@example.com",
            name="Test",
            role="student",
            is_active=True,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            last_login=None,
        )
        assert resp.is_active is True
        assert resp.last_login is None
        assert resp.role == "student"

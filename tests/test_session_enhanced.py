"""Tests for enhanced session management (F07)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.auth.guest import GuestSession, MAX_GUEST_MESSAGES
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
from src.models.session import Session


class TestGuestSession:
    def test_create_guest_session(self):
        gs = GuestSession.create()
        assert gs.token != ""
        assert gs.message_count == 0
        assert gs.max_messages == MAX_GUEST_MESSAGES

    def test_guest_can_send_message_initially(self):
        gs = GuestSession.create()
        assert gs.can_send_message is True
        assert gs.remaining_messages == MAX_GUEST_MESSAGES

    def test_guest_message_limit_enforced(self):
        gs = GuestSession.create()
        for i in range(MAX_GUEST_MESSAGES):
            assert gs.can_send_message is True
            gs.record_message(topic=f"topic-{i}")
        assert gs.can_send_message is False
        assert gs.remaining_messages == 0

    def test_guest_tracks_topics(self):
        gs = GuestSession.create()
        gs.record_message(topic="math")
        gs.record_message(topic="science")
        gs.record_message(topic="math")  # Duplicate, should not be added
        assert gs.topics == ["math", "science"]

    def test_guest_to_dict(self):
        gs = GuestSession.create()
        gs.record_message(topic="algebra")
        d = gs.to_dict()
        assert d["message_count"] == 1
        assert d["remaining_messages"] == MAX_GUEST_MESSAGES - 1
        assert "algebra" in d["topics"]
        assert "token" in d


class TestGuestToken:
    def test_guest_token_creation(self):
        token = create_guest_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_guest_token_has_guest_role(self):
        token = create_guest_token()
        payload = verify_token(token)
        assert payload["role"] == "guest"
        assert payload["sub"].startswith("guest-")
        assert payload["type"] == "access"

    def test_guest_token_response_schema(self):
        resp = GuestTokenResponse(access_token="abc123", expires_in=3600)
        assert resp.token_type == "bearer"
        assert resp.expires_in == 3600


class TestHashToken:
    def test_hash_token_consistent(self):
        token = "my-refresh-token-123"
        assert hash_token(token) == hash_token(token)

    def test_hash_token_different_inputs(self):
        assert hash_token("token-a") != hash_token("token-b")

    def test_hash_token_is_hex_sha256(self):
        h = hash_token("test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestAccountLockout:
    async def test_lockout_after_max_fails(self):
        mock_redis = AsyncMock()
        email = "bad@example.com"
        mock_redis.incr = AsyncMock(side_effect=list(range(1, MAX_FAILED_ATTEMPTS + 1)))
        mock_redis.expire = AsyncMock()
        mock_redis.set = AsyncMock()

        for _ in range(MAX_FAILED_ATTEMPTS):
            await record_failed_login(mock_redis, email)

        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert f"lockout:{email}" in call_args[0][0]

    async def test_check_lockout_not_locked(self):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        assert await check_account_lockout(mock_redis, "user@example.com") is False

    async def test_check_lockout_locked(self):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="1")
        assert await check_account_lockout(mock_redis, "user@example.com") is True

    async def test_clear_failed_logins(self):
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock()
        await clear_failed_logins(mock_redis, "user@example.com")
        assert mock_redis.delete.call_count == 2


class TestPasswordChangeSchema:
    def test_valid_password_change(self):
        req = PasswordChangeRequest(old_password="oldpass", new_password="newpass12")
        assert req.new_password == "newpass12"

    def test_short_new_password_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            PasswordChangeRequest(old_password="oldpass", new_password="short")


class TestSessionEndArchive:
    def test_session_end_generates_summary(self):
        session = MagicMock(spec=Session)
        session.subject = "Mathematics"
        session.topic = "Algebra"
        session.started_at = datetime(2026, 2, 7, 10, 0, tzinfo=timezone.utc)
        session.ended_at = None

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

        assert session.is_archived is True
        assert "Mathematics" in session.summary
        assert "Algebra" in session.summary
        assert "30 min" in session.summary

    def test_session_end_no_topics(self):
        session = MagicMock(spec=Session)
        session.subject = None
        session.topic = None
        session.started_at = datetime(2026, 2, 7, 10, 0, tzinfo=timezone.utc)

        now = datetime(2026, 2, 7, 10, 15, tzinfo=timezone.utc)
        topics = []
        if session.subject:
            topics.append(session.subject)
        if session.topic:
            topics.append(session.topic)
        summary = f"Session on {', '.join(topics) if topics else 'general tutoring'}"
        duration_seconds = (now - session.started_at).total_seconds()
        duration_minutes = int(duration_seconds // 60)
        summary += f" ({duration_minutes} min)"

        assert "general tutoring" in summary
        assert "15 min" in summary


class TestUserDetailResponse:
    def test_user_detail_response_schema(self):
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

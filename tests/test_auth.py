"""Auth endpoint tests."""

import pytest

from src.auth.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    def test_hash_password(self):
        hashed = hash_password("mysecretpassword")
        assert hashed != "mysecretpassword"
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        hashed = hash_password("mysecretpassword")
        assert verify_password("mysecretpassword", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("mysecretpassword")
        assert verify_password("wrongpassword", hashed) is False


class TestJWT:
    def test_create_access_token(self):
        token = create_access_token({"sub": "user-123", "email": "test@test.com"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token(self):
        token = create_access_token({"sub": "user-123", "email": "test@test.com"})
        payload = verify_token(token)
        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@test.com"
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        token = create_refresh_token({"sub": "user-123", "email": "test@test.com"})
        payload = verify_token(token)
        assert payload["type"] == "refresh"

    def test_verify_invalid_token(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid-token-string")
        assert exc_info.value.status_code == 401

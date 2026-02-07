"""Password hashing and JWT token utilities."""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt

from src.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def hash_token(token: str) -> str:
    """SHA-256 hash for refresh token storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_guest_token() -> str:
    """Create a short-lived JWT for guest access (1 hour, role=guest)."""
    guest_id = f"guest-{uuid.uuid4()}"
    data = {"sub": guest_id, "role": "guest"}
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    data.update({"exp": expire, "type": "access"})
    return jwt.encode(data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


LOCKOUT_PREFIX = "login_fails:"
LOCKOUT_FLAG_PREFIX = "lockout:"
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_TTL_SECONDS = 900  # 15 minutes


async def check_account_lockout(redis, email: str) -> bool:
    """Check if the account is locked out due to failed login attempts."""
    locked = await redis.get(f"{LOCKOUT_FLAG_PREFIX}{email}")
    return locked is not None


async def record_failed_login(redis, email: str) -> None:
    """Increment fail counter. Set lockout flag after MAX_FAILED_ATTEMPTS."""
    key = f"{LOCKOUT_PREFIX}{email}"
    count = await redis.incr(key)
    await redis.expire(key, LOCKOUT_TTL_SECONDS)
    if count >= MAX_FAILED_ATTEMPTS:
        await redis.set(
            f"{LOCKOUT_FLAG_PREFIX}{email}", "1", ex=LOCKOUT_TTL_SECONDS
        )


async def clear_failed_logins(redis, email: str) -> None:
    """Clear failed login counter and lockout flag on successful login."""
    await redis.delete(f"{LOCKOUT_PREFIX}{email}")
    await redis.delete(f"{LOCKOUT_FLAG_PREFIX}{email}")

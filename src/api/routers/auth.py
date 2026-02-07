"""Authentication endpoints: register, login, refresh, guest, logout, change-password, me."""

from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    ACCESS_TOKEN_BLACKLIST_PREFIX,
    get_auth_redis,
    get_current_user,
)
from src.auth.schemas import (
    GuestTokenResponse,
    LoginRequest,
    PasswordChangeRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserDetailResponse,
    UserResponse,
)
from src.auth.security import (
    check_account_lockout,
    clear_failed_logins,
    create_access_token,
    create_guest_token,
    create_refresh_token,
    hash_password,
    hash_token,
    record_failed_login,
    verify_password,
    verify_token,
)
from src.config import settings
from src.models.database import get_db
from src.models.refresh_token import RefreshToken
from src.models.user import StudentProfile, User

router = APIRouter(tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
    )
    db.add(user)
    await db.flush()

    profile = StudentProfile(user_id=user.id)
    db.add(profile)
    await db.flush()

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        created_at=user.created_at,
    )


async def _store_refresh_token(db: AsyncSession, user_id, refresh_jwt: str) -> None:
    """Persist a hashed refresh token in the database."""
    payload = verify_token(refresh_jwt)
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    token_record = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(refresh_jwt),
        expires_at=expires_at,
    )
    db.add(token_record)
    await db.flush()


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    r: aioredis.Redis = Depends(get_auth_redis),
):
    # C1 fix: Check account lockout before attempting authentication
    if await check_account_lockout(r, body.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to too many failed login attempts",
        )

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalars().first()

    if user is None or not verify_password(body.password, user.password_hash):
        # C1 fix: Record failed login attempt
        await record_failed_login(r, body.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # H1 fix: Reject disabled accounts during login
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # C1 fix: Clear failed login counter on success
    await clear_failed_logins(r, body.email)

    # Update login tracking fields
    user.last_login = datetime.now(timezone.utc)
    user.login_count = (user.login_count or 0) + 1

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # C3 fix: Store hashed refresh token in DB
    await _store_refresh_token(db, user.id, refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = verify_token(body.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # C3 fix: Validate refresh token against DB
    token_hash = hash_token(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    stored_token = result.scalars().first()
    if stored_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or revoked",
        )

    # H2 fix: Revoke the old refresh token (rotation)
    stored_token.is_revoked = True

    # H3 fix: Read role from DB, not from old JWT
    user_id = payload["sub"]
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,  # Fresh role from DB
    }
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    # H2 fix: Store the new refresh token
    await _store_refresh_token(db, user.id, new_refresh)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
    )


@router.post("/guest", response_model=GuestTokenResponse)
async def guest_session():
    """Create a guest session with a short-lived token."""
    token = create_guest_token()
    return GuestTokenResponse(
        access_token=token,
        expires_in=3600,  # 1 hour
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    r: aioredis.Redis = Depends(get_auth_redis),
):
    """Logout: revoke refresh tokens + blacklist current access token."""
    # C4 fix: Revoke all refresh tokens for this user
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id, RefreshToken.is_revoked == False)  # noqa: E712
        .values(is_revoked=True)
    )

    # C4 fix: Blacklist current access token in Redis
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = verify_token(token)
            jti = payload.get("jti")
            if jti:
                # TTL = remaining token lifetime
                exp = payload.get("exp", 0)
                now = datetime.now(timezone.utc).timestamp()
                ttl = max(int(exp - now), 1)
                await r.set(f"{ACCESS_TOKEN_BLACKLIST_PREFIX}{jti}", "1", ex=ttl)
        except Exception:
            pass  # Token already invalid or Redis down

    return None


@router.post("/change-password")
async def change_password(
    body: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password."""
    if not verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.password_hash = hash_password(body.new_password)

    # H4 fix: Invalidate all existing refresh tokens for this user
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id, RefreshToken.is_revoked == False)  # noqa: E712
        .values(is_revoked=True)
    )

    await db.flush()
    return {"detail": "Password changed successfully"}


@router.get("/me", response_model=UserDetailResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return current user details."""
    return UserDetailResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=getattr(current_user, "last_login", None),
    )

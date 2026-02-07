"""Authentication endpoints: register, login, refresh, guest, logout, change-password, me."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
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
    create_access_token,
    create_guest_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from src.models.database import get_db
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


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalars().first()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    payload = verify_token(body.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    token_data = {
        "sub": payload["sub"],
        "email": payload["email"],
        "role": payload["role"],
    }
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
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
async def logout(current_user: User = Depends(get_current_user)):
    """Logout the current user (token revocation handled client-side or via Redis blacklist)."""
    # In production, the token would be added to a Redis blacklist.
    # For now, the client should discard the token.
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

"""Auth-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class GuestTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class UserDetailResponse(UserResponse):
    is_active: bool
    last_login: datetime | None = None

    model_config = {"from_attributes": True}

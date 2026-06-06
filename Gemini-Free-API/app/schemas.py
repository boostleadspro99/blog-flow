from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Auth ──

class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=255)
    username: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    created_at: datetime
    has_cookies: bool = False
    cookies_valid: bool = False

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Cookies ──

class CookieUpdateRequest(BaseModel):
    secure_1psid: str = Field(..., min_length=1)
    secure_1psidts: str = Field(..., min_length=1)


class CookieResponse(BaseModel):
    has_cookies: bool
    is_valid: bool
    last_validated_at: Optional[datetime] = None
    error_message: Optional[str] = None


# ── Error ──

class ErrorResponse(BaseModel):
    detail: str

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.db_models import User, UserCookie
from app.dependencies import get_current_user
from app.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

logger = logging.getLogger("auth_routes")
router = APIRouter(prefix="/auth", tags=["auth"])


def _user_to_response(user: User, has_cookies: bool = False, cookies_valid: bool = False) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        created_at=user.created_at,
        has_cookies=has_cookies,
        cookies_valid=cookies_valid,
    )


async def _get_user_with_cookies(db: AsyncSession, user_id):
    """Fetch user with eagerly loaded cookies relationship."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.cookies))
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")
    # Check username uniqueness
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken.")

    user = User(
        email=body.email,
        username=body.username,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.commit()

    # Re-fetch with relationships loaded
    fresh = await _get_user_with_cookies(db, user.id)
    token = create_access_token(str(fresh.id), fresh.email)
    has_cookies = fresh.cookies is not None
    logger.info(f"New user registered: {fresh.email} ({fresh.id})")
    return TokenResponse(
        access_token=token,
        user=_user_to_response(
            fresh,
            has_cookies=has_cookies,
            cookies_valid=fresh.cookies.is_valid if has_cookies else False,
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).options(selectinload(User.cookies)).where(User.email == body.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated.")

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    has_cookies = user.cookies is not None
    token = create_access_token(str(user.id), user.email)
    logger.info(f"User logged in: {user.email}")
    return TokenResponse(
        access_token=token,
        user=_user_to_response(
            user,
            has_cookies=has_cookies,
            cookies_valid=user.cookies.is_valid if has_cookies else False,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await _get_user_with_cookies(db, current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    has_cookies = user.cookies is not None
    return _user_to_response(
        user,
        has_cookies=has_cookies,
        cookies_valid=user.cookies.is_valid if has_cookies else False,
    )

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import User, UserCookie
from app.dependencies import get_current_user
from app.encryption import encrypt_value, decrypt_value
from app.schemas import CookieResponse, CookieUpdateRequest

logger = logging.getLogger("cookies_routes")
router = APIRouter(prefix="/user", tags=["cookies"])


@router.get("/cookies", response_model=CookieResponse)
async def get_cookies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cookie_row = db.execute(
        select(UserCookie).where(UserCookie.user_id == current_user.id)
    ).scalar_one_or_none()

    if not cookie_row:
        return CookieResponse(has_cookies=False, is_valid=False)

    return CookieResponse(
        has_cookies=True,
        is_valid=cookie_row.is_valid,
        last_validated_at=cookie_row.last_validated_at,
        error_message=cookie_row.error_message,
    )


@router.post("/cookies", response_model=CookieResponse)
async def update_cookies(
    body: CookieUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.main import gemini_pool

    # Encrypt cookies
    encrypted_1psid = encrypt_value(body.secure_1psid)
    encrypted_1psidts = encrypt_value(body.secure_1psidts)

    cookie_row = db.execute(
        select(UserCookie).where(UserCookie.user_id == current_user.id)
    ).scalar_one_or_none()

    if cookie_row:
        cookie_row.encrypted_1psid = encrypted_1psid
        cookie_row.encrypted_1psidts = encrypted_1psidts
    else:
        cookie_row = UserCookie(
            user_id=current_user.id,
            encrypted_1psid=encrypted_1psid,
            encrypted_1psidts=encrypted_1psidts,
        )
        db.add(cookie_row)

    db.commit()
    db.refresh(cookie_row)

    # Validate cookies via Gemini client
    is_valid = False
    error_msg = None

    if gemini_pool:
        try:
            pooled = await gemini_pool.get_or_create(
                str(current_user.id),
                body.secure_1psid,
                body.secure_1psidts,
            )
            await pooled.get_client()
            is_valid = True
            logger.info(f"Cookies validated for user {current_user.id}")
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Cookie validation failed for user {current_user.id}: {e}")

    cookie_row.is_valid = is_valid
    cookie_row.last_validated_at = datetime.now(timezone.utc) if is_valid else cookie_row.last_validated_at
    cookie_row.error_message = error_msg
    db.commit()

    return CookieResponse(
        has_cookies=True,
        is_valid=is_valid,
        last_validated_at=cookie_row.last_validated_at,
        error_message=error_msg,
    )

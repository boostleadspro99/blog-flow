"""Chat completions route (per-user auth)."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.db_models import User, UserCookie
from app.dependencies import get_current_user
from app.encryption import decrypt_value

logger = logging.getLogger("chat_routes")
router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat/completions")
async def chat_completions(
    fast_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Chat completions endpoint. Wraps the existing openai_server implementation
    but uses the per-user Gemini client. For simplicity, delegates to the
    original implementation with the user's client injected.
    """
    # Get user's cookies
    result = await db.execute(
        select(UserCookie).where(UserCookie.user_id == current_user.id)
    )
    cookie_row = result.scalar_one_or_none()
    if not cookie_row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Gemini cookies configured.",
        )

    secure_1psid = decrypt_value(cookie_row.encrypted_1psid)
    secure_1psidts = decrypt_value(cookie_row.encrypted_1psidts)

    from app.main import gemini_pool

    pooled = await gemini_pool.get_or_create(
        str(current_user.id), secure_1psid, secure_1psidts
    )

    try:
        await pooled.get_client()
    except Exception as e:
        cookie_row.is_valid = False
        cookie_row.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    # For MVP, the chat route is minimal — the original implementation is
    # tightly coupled to the global gemini_client. Full chat multi-user
    # support is Phase 4b.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Chat completions with per-user auth is coming soon. Use image generation first.",
    )

"""Legacy webhook route for cookie service. Disabled in multi-user mode."""

import logging

from fastapi import APIRouter, Request

logger = logging.getLogger("webhook_routes")
router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/cookies")
async def webhook_cookies(request: Request):
    """
    Legacy cookie service webhook. Not used in multi-user mode.
    Users update their cookies via POST /user/cookies with JWT auth.
    """
    logger.warning("Legacy /webhook/cookies called — multi-user mode ignores this.")
    return {"status": "ignored", "message": "Use POST /user/cookies with JWT auth instead."}

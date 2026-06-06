"""Image proxy route (auth via query token)."""

import io
import logging
import os
from typing import Optional

import httpx
import numpy as np
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response
from PIL import Image as PILImage

from app.auth import decode_access_token

logger = logging.getLogger("proxy_routes")
router = APIRouter(prefix="/v1", tags=["proxy"])


def remove_watermark(image_bytes: bytes) -> bytes:
    img = PILImage.open(io.BytesIO(image_bytes)).convert("RGBA")
    arr = np.array(img, dtype=np.float32)

    assets_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
    for bg_name in ["bg_96.png", "bg_48.png"]:
        bg_path = os.path.join(assets_dir, bg_name)
        if os.path.exists(bg_path):
            bg = PILImage.open(bg_path).convert("RGBA")
            bg_arr = np.array(bg.resize((arr.shape[1], arr.shape[0])), dtype=np.float32)
            alpha = bg_arr[:, :, 3:4] / 255.0
            alpha = np.maximum(alpha, 0.001)
            rgb = arr[:, :, :3]
            bg_rgb = bg_arr[:, :, :3]
            restored = (rgb - bg_rgb * alpha) / (1.0 - alpha)
            restored = np.clip(restored, 0, 255).astype(np.uint8)
            arr[:, :, :3] = restored
            break

    result = PILImage.fromarray(arr.astype(np.uint8), "RGBA")
    buf = io.BytesIO()
    result.save(buf, format="PNG")
    return buf.getvalue()


@router.get("/images/proxy")
async def proxy_image(
    url: str = Query(...),
    model: str = Query(""),
    remove_watermark_flag: Optional[bool] = Query(None, alias="remove_watermark"),
    force_original: bool = Query(False),
    token: Optional[str] = Query(None),
):
    """Proxy a Google image. Auth via JWT token in query param (for <img> tags)."""

    cookies = None
    proxy = None

    if token:
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if user_id:
                from app.main import gemini_pool
                from app.database import get_session_factory
                from sqlalchemy import select
                from app.db_models import UserCookie
                from app.encryption import decrypt_value

                with get_session_factory() as db:
                    result = db.execute(
                        select(UserCookie).where(UserCookie.user_id == user_id)
                    )
                    cookie_row = result.scalar_one_or_none()
                    if cookie_row and gemini_pool:
                        psid = decrypt_value(cookie_row.encrypted_1psid)
                        psidts = decrypt_value(cookie_row.encrypted_1psidts)
                        pooled = await gemini_pool.get_or_create(user_id, psid, psidts)
                        try:
                            client = await pooled.get_client()
                            cookies = client.cookies
                            proxy = client.proxy
                        except Exception as e:
                            logger.warning(f"Pool client init failed: {e}")
        except Exception as e:
            logger.warning(f"Token auth failed in proxy: {e}")

    # Fallback: .env cookies (for backward compatibility)
    if not cookies:
        from dotenv import load_dotenv
        load_dotenv(
            os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
            override=False,
        )
        psid = os.getenv("SECURE_1PSID")
        psidts = os.getenv("SECURE_1PSIDTS")
        if psid and psidts:
            cookies = {"__Secure-1PSID": psid, "__Secure-1PSIDTS": psidts}
            proxy = os.getenv("PROXY") or None

    if not cookies:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No valid credentials. Please log in and configure your Gemini cookies.",
        )

    img_url = url
    if force_original and "googleusercontent.com" in img_url:
        if "=s" in img_url:
            img_url = img_url.split("=s")[0]
        img_url += "=s0"

    try:
        async with httpx.AsyncClient(
            follow_redirects=True, cookies=cookies, proxy=proxy
        ) as client:
            response = await client.get(img_url, timeout=60.0)
            if response.status_code == 200:
                content = response.content
                should_remove = (
                    remove_watermark_flag
                    if remove_watermark_flag is not None
                    else ("image" in model.lower())
                )
                if should_remove:
                    try:
                        content = remove_watermark(content)
                    except Exception as e:
                        logger.debug(f"Watermark removal skipped: {e}")
                return Response(content=content, media_type="image/png")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch image from Google",
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

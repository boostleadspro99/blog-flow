import base64
import json
import logging
import re
import time
from typing import Any, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.db_models import User, UserCookie
from app.dependencies import get_current_user, get_optional_user
from app.encryption import decrypt_value
from app.config import settings

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gemini_webapi.constants import Model, Endpoint

logger = logging.getLogger("image_routes")
router = APIRouter(prefix="/v1", tags=["images"])


# ── Pydantic models (OpenAI-compatible) ──

class ImageRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    prompt: str
    model: Optional[str] = "gemini-3-pro-image"
    n: Optional[int] = 1
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"
    response_format: Optional[str] = "url"
    user: Optional[str] = None


class ImageData(BaseModel):
    url: Optional[str] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None


class ImageResponse(BaseModel):
    created: int
    data: List[ImageData]


# ── Helpers ──

def get_proxy_url(request: Request, image_url: str, model: str = "", token: str = "") -> str:
    """Build a proxy URL that routes through this server. Includes JWT for auth in <img> tags."""
    base = str(request.base_url).rstrip("/")
    url = f"{base}/v1/images/proxy?url={image_url}&model={model}"
    if token:
        url += f"&token={token}"
    return url


def remove_gemini_watermark(image_bytes: bytes) -> bytes:
    """Reverse alpha blend to remove Gemini watermark."""
    from PIL import Image as PILImage
    import numpy as np
    import os

    img = PILImage.open(__import__("io").BytesIO(image_bytes)).convert("RGBA")
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
    buf = __import__("io").BytesIO()
    result.save(buf, format="PNG")
    return buf.getvalue()


# ── Route ──

@router.post("/images/generations", response_model=ImageResponse)
async def image_generations(
    request: ImageRequest,
    fast_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if settings.disable_auth:
        # Fallback to legacy global client
        return await _generate_legacy(request, fast_request)

    # Get user's cookies
    result = await db.execute(
        select(UserCookie).where(UserCookie.user_id == current_user.id)
    )
    cookie_row = result.scalar_one_or_none()
    if not cookie_row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Gemini cookies configured. Please go to Settings and add your cookies.",
        )
    if not cookie_row.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Your Gemini cookies are invalid: {cookie_row.error_message or 'Unknown error'}. "
                   "Please update them in Settings.",
        )

    secure_1psid = decrypt_value(cookie_row.encrypted_1psid)
    secure_1psidts = decrypt_value(cookie_row.encrypted_1psidts)

    from app.main import gemini_pool

    pooled = await gemini_pool.get_or_create(
        str(current_user.id), secure_1psid, secure_1psidts
    )

    try:
        gemini_client = await pooled.get_client()
    except Exception as e:
        cookie_row.is_valid = False
        cookie_row.error_message = str(e)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to initialize Gemini client with your cookies: {e}",
        )

    # NOTE: Watermark removal disabled — the alpha-blend reverse algorithm
    # doesn't work on gg-dl/ images and causes corruption (divide by zero).
    should_remove_watermark = False  # "image" in request.model.lower()
    gen_prompt = f"Generate an image: {request.prompt}"

    try:
        response = await gemini_client.generate_content(gen_prompt, model=Model.G_2_5_FLASH)
    except Exception as e:
        logger.error(f"Gemini generate_content failed for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    image_urls = []
    if response.images:
        for img in response.images:
            if hasattr(img, "url") and img.url:
                image_urls.append(img.url)

    if not image_urls:
        # Fallback: extract from raw response
        logger.info("No images from parser, trying raw response extraction...")
        try:
            raw = await gemini_client.client.post(
                Endpoint.GENERATE.value,
                headers=Model.G_2_5_FLASH.model_header,
                data={
                    "at": gemini_client.access_token,
                    "f.req": json.dumps([
                        None,
                        json.dumps([[gen_prompt], None, None]),
                    ]),
                },
            )
            found = re.findall(
                r'https?://[^"\s\\\[\]]+googleusercontent[^"\s\\\[\]]+', raw.text
            )
            seen = set()
            for u in found:
                u = u.rstrip('",.\\')
                if u not in seen:
                    seen.add(u)
                    image_urls.append(u)
            logger.info(f"Raw extraction: {len(image_urls)} URLs found")
        except Exception as e:
            logger.error(f"Raw extraction failed: {e}")

    if not image_urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gemini did not return any images. Try a more descriptive prompt.",
        )

    # Extract JWT from request for proxy URL auth (browser <img> tags can't send headers)
    auth_header = fast_request.headers.get("Authorization", "")
    jwt_token = auth_header.replace("Bearer ", "", 1) if auth_header.startswith("Bearer ") else ""

    image_data = []
    for img_url in image_urls:
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                cookies=gemini_client.cookies,
                proxy=gemini_client.proxy,
            ) as client:
                # Don't modify gg-dl/ URLs — they're already original quality.
                # Adding =s0 can break them or return lower quality.
                clean_url = img_url
                if "googleusercontent.com" in clean_url and "gg-dl/" not in clean_url:
                    if "=s" in clean_url:
                        clean_url = clean_url.split("=s")[0]
                    clean_url += "=s0"

                logger.info(f"Fetching: {clean_url[:120]}...")
                img_response = await client.get(clean_url, timeout=30.0)
                if img_response.status_code == 200:
                    content = img_response.content
                    if should_remove_watermark:
                        try:
                            content = remove_gemini_watermark(content)
                        except Exception as e:
                            logger.warning(f"Watermark removal failed: {e}")
                    b64 = base64.b64encode(content).decode("utf-8")
                    # Always return b64_json to avoid proxy auth issues with <img> tags
                    image_data.append(ImageData(
                        b64_json=b64,
                        url=f"data:image/png;base64,{b64}",
                        revised_prompt=response.text,
                    ))
        except Exception as e:
            logger.error(f"Image download failed: {e}")
            image_data.append(ImageData(
                url=get_proxy_url(fast_request, img_url, request.model, jwt_token),
                revised_prompt=response.text,
            ))

    return ImageResponse(created=int(time.time()), data=image_data)


async def _generate_legacy(request: ImageRequest, fast_request: Request) -> ImageResponse:
    """Fallback to the global Gemini client (for backward compatibility)."""
    # Import and use the old global client
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    import importlib
    openai_mod = importlib.import_module("openai_server")
    gemini_client = getattr(openai_mod, "gemini_client", None)
    if not gemini_client:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Gemini client not initialized")

    # Delegate to old route — this is a fallback, not ideal but works
    return await openai_mod.image_generations(request, fast_request)

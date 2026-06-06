import time
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/v1", tags=["models"])


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "google"


class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelInfo]


@router.get("/models", response_model=ModelList)
async def list_models():
    return ModelList(
        data=[
            ModelInfo(id="gemini-3-flash", created=int(time.time())),
            ModelInfo(id="gemini-3-pro", created=int(time.time())),
            ModelInfo(id="gemini-3-pro-high", created=int(time.time())),
            ModelInfo(id="gemini-3-flash-image", created=int(time.time())),
            ModelInfo(id="gemini-3-pro-image", created=int(time.time())),
        ]
    )

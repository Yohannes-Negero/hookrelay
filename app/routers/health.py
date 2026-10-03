from fastapi import APIRouter, Depends, HTTPException
from pymongo.asynchronous.database import AsyncDatabase

from app.db import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(db: AsyncDatabase = Depends(get_db)) -> dict:
    try:
        await db.command("ping")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(503, "Database unavailable") from exc
    return {"status": "ready"}

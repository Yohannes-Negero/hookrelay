from fastapi import Depends, Header, HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings, get_settings
from app.db import get_db
from app.security import hash_api_key, tokens_match


async def require_admin(
    x_admin_token: str = Header(default=""),
    settings: Settings = Depends(get_settings),
) -> None:
    if not x_admin_token or not tokens_match(x_admin_token, settings.admin_token):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid admin token")


async def current_merchant(
    x_api_key: str = Header(default=""),
    db: AsyncDatabase = Depends(get_db),
) -> dict:
    if not x_api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing API key")
    merchant = await db.merchants.find_one({"api_key_hash": hash_api_key(x_api_key)})
    if merchant is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
    return merchant

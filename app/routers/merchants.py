from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from pymongo.asynchronous.database import AsyncDatabase

from app.db import get_db
from app.deps import current_merchant, require_admin
from app.security import generate_api_key, hash_api_key

router = APIRouter(prefix="/merchants", tags=["merchants"])


class MerchantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class MerchantCreated(BaseModel):
    id: str
    name: str
    api_key: str  # returned only once


class MerchantOut(BaseModel):
    id: str
    name: str
    created_at: datetime


@router.post(
    "",
    response_model=MerchantCreated,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_merchant(body: MerchantCreate, db: AsyncDatabase = Depends(get_db)):
    api_key = generate_api_key()
    doc = {
        "name": body.name,
        "api_key_hash": hash_api_key(api_key),
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.merchants.insert_one(doc)
    return MerchantCreated(id=str(result.inserted_id), name=body.name, api_key=api_key)


@router.get("/me", response_model=MerchantOut)
async def me(merchant: dict = Depends(current_merchant)):
    return MerchantOut(
        id=str(merchant["_id"]),
        name=merchant["name"],
        created_at=merchant["created_at"],
    )

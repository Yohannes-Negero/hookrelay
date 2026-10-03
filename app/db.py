from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.config import get_settings

_client: AsyncMongoClient | None = None


async def connect() -> None:
    """Open the Mongo connection and make sure indexes exist."""
    global _client
    settings = get_settings()
    _client = AsyncMongoClient(settings.mongo_uri)
    db = _client[settings.mongo_db]
    await db.merchants.create_index("api_key_hash", unique=True)
    # Idempotency: the same provider event can only be stored once.
    await db.events.create_index(
        [("provider", 1), ("provider_event_id", 1)], unique=True
    )


async def disconnect() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


def get_db() -> AsyncDatabase:
    if _client is None:
        raise RuntimeError("Database is not connected")
    return _client[get_settings().mongo_db]

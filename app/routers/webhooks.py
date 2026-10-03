import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.config import Settings, get_settings
from app.db import get_db
from app.providers import PROVIDERS

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger("hookrelay.webhooks")


@router.post("/{provider_name}")
async def receive_webhook(
    provider_name: str,
    request: Request,
    db: AsyncDatabase = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    provider = PROVIDERS.get(provider_name)
    if provider is None:
        raise HTTPException(404, "Unknown provider")

    secret = settings.webhook_secret_for(provider_name)
    if not secret:
        raise HTTPException(503, "Webhook secret is not configured")

    # The signature covers the exact raw bytes, so read them before any JSON parsing.
    body = await request.body()

    if not provider.verify(body, request.headers, secret):
        logger.warning("Rejected %s webhook: invalid signature", provider_name)
        raise HTTPException(400, "Invalid signature")

    try:
        payload = json.loads(body)
    except ValueError:
        raise HTTPException(400, "Body is not valid JSON")
    if not isinstance(payload, dict):
        raise HTTPException(400, "Unexpected payload shape")

    parsed = provider.parse(payload)
    if parsed is None:
        raise HTTPException(400, "Missing event id or type")

    document = {
        "provider": provider_name,
        "provider_event_id": parsed.event_id,
        "event_type": parsed.event_type,
        "payload": payload,
        "status": "received",
        "received_at": datetime.now(timezone.utc),
    }
    try:
        await db.events.insert_one(document)
    except DuplicateKeyError:
        # Providers retry. Answering 2xx tells them to stop; we simply don't process it twice.
        logger.info("Duplicate %s event %s ignored", provider_name, parsed.event_id)
        return {"status": "duplicate"}

    logger.info("Stored %s event %s (%s)", provider_name, parsed.event_id, parsed.event_type)
    return {"status": "received"}

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import db
from app.routers import health, merchants, webhooks

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()


app = FastAPI(
    title="HookRelay",
    description="Receives, verifies and reliably relays payment webhooks.",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(merchants.router)
app.include_router(webhooks.router)

import json
import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError

from app.config import Settings, get_settings
from app.db import get_db
from app.main import app
from app.providers.stripe_provider import compute_signature, verify_signature

SECRET = "whsec_test_secret"
EVENT = {
    "id": "evt_123",
    "type": "payment_intent.succeeded",
    "data": {"object": {"id": "pi_1", "amount": 5000}},
}


def sign(body: bytes, secret: str = SECRET, timestamp: int | None = None) -> str:
    ts = int(time.time()) if timestamp is None else timestamp
    return f"t={ts},v1={compute_signature(secret, ts, body)}"


# ---- signature verification (pure functions) ----

def test_valid_signature_is_accepted():
    body = b'{"a": 1}'
    assert verify_signature(body, sign(body), SECRET)


def test_tampered_body_is_rejected():
    body = b'{"amount": 100}'
    header = sign(body)
    assert not verify_signature(b'{"amount": 999}', header, SECRET)


def test_wrong_secret_is_rejected():
    body = b"{}"
    assert not verify_signature(body, sign(body, secret="whsec_other"), SECRET)


def test_old_timestamp_is_rejected():
    body = b"{}"
    old = int(time.time()) - 3600
    assert not verify_signature(body, sign(body, timestamp=old), SECRET)


def test_missing_or_malformed_header_is_rejected():
    assert not verify_signature(b"{}", "", SECRET)
    assert not verify_signature(b"{}", "garbage", SECRET)
    assert not verify_signature(b"{}", "t=abc,v1=ff", SECRET)


def test_any_matching_v1_signature_is_accepted():
    body = b"{}"
    ts = int(time.time())
    good = compute_signature(SECRET, ts, body)
    assert verify_signature(body, f"t={ts},v1=deadbeef,v1={good}", SECRET)


# ---- the endpoint, with an in-memory fake database ----

class FakeEvents:
    def __init__(self):
        self.docs = []

    async def insert_one(self, doc):
        key = (doc["provider"], doc["provider_event_id"])
        if any((d["provider"], d["provider_event_id"]) == key for d in self.docs):
            raise DuplicateKeyError("duplicate")
        self.docs.append(doc)
        return SimpleNamespace(inserted_id=len(self.docs))


@pytest.fixture
def fake_db():
    return SimpleNamespace(events=FakeEvents())


@pytest.fixture
def client(fake_db):
    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_settings] = lambda: Settings(stripe_webhook_secret=SECRET)
    yield TestClient(app)
    app.dependency_overrides.clear()


def post(client, body: bytes, signature: str, provider: str = "stripe"):
    return client.post(
        f"/webhooks/{provider}",
        content=body,
        headers={"stripe-signature": signature, "content-type": "application/json"},
    )


def test_valid_event_is_stored(client, fake_db):
    body = json.dumps(EVENT).encode()
    response = post(client, body, sign(body))
    assert response.status_code == 200
    assert response.json() == {"status": "received"}
    assert len(fake_db.events.docs) == 1
    assert fake_db.events.docs[0]["provider_event_id"] == "evt_123"


def test_same_event_twice_is_processed_once(client, fake_db):
    body = json.dumps(EVENT).encode()
    first = post(client, body, sign(body))
    second = post(client, body, sign(body))
    assert first.json() == {"status": "received"}
    assert second.status_code == 200
    assert second.json() == {"status": "duplicate"}
    assert len(fake_db.events.docs) == 1


def test_tampered_signature_is_rejected_and_not_stored(client, fake_db):
    body = json.dumps(EVENT).encode()
    response = post(client, body, sign(body, secret="whsec_attacker"))
    assert response.status_code == 400
    assert fake_db.events.docs == []


def test_unknown_provider_returns_404(client):
    body = json.dumps(EVENT).encode()
    assert post(client, body, sign(body), provider="nope").status_code == 404


def test_valid_signature_but_invalid_json_returns_400(client, fake_db):
    body = b"this is not json"
    response = post(client, body, sign(body))
    assert response.status_code == 400
    assert fake_db.events.docs == []


def test_missing_secret_returns_503(fake_db):
    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_settings] = lambda: Settings(stripe_webhook_secret="")
    try:
        body = json.dumps(EVENT).encode()
        response = post(TestClient(app), body, sign(body))
        assert response.status_code == 503
    finally:
        app.dependency_overrides.clear()

from fastapi.testclient import TestClient

from app.main import app
from app.security import API_KEY_PREFIX, generate_api_key, hash_api_key, tokens_match


def test_health_does_not_need_database():
    # No `with` block, so the lifespan (DB connect) is not run.
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_keys_are_unique_and_prefixed():
    a, b = generate_api_key(), generate_api_key()
    assert a != b
    assert a.startswith(API_KEY_PREFIX)


def test_hash_is_deterministic_and_not_the_key():
    key = generate_api_key()
    assert hash_api_key(key) == hash_api_key(key)
    assert hash_api_key(key) != key


def test_tokens_match():
    assert tokens_match("abc", "abc")
    assert not tokens_match("abc", "abd")


def test_create_merchant_requires_admin_token():
    client = TestClient(app)
    response = client.post("/merchants", json={"name": "Acme"})
    assert response.status_code == 401

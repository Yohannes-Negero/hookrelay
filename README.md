# HookRelay

Receives, verifies and reliably relays payment webhooks (Stripe first).

**Status:** Day 1 — scaffold, Mongo connection, merchant API keys.

## Run locally

```bash
cp .env.example .env        # then set ADMIN_TOKEN
docker compose up --build
```

Open http://localhost:8000/docs

## Try it

```bash
# create a merchant (admin only) — the API key is shown once
curl -X POST localhost:8000/merchants \
  -H "X-Admin-Token: <ADMIN_TOKEN>" -H "Content-Type: application/json" \
  -d '{"name": "Acme Store"}'

# authenticate as that merchant
curl localhost:8000/merchants/me -H "X-API-Key: <api_key>"
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

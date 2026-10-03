# HookRelay

Receives, verifies and reliably relays payment webhooks (Stripe first).

**Status:** Day 2 — Stripe webhook receiver with signature verification and idempotent storage.

## Features so far

- Merchant API keys (hashed in the database, shown once)
- `POST /webhooks/stripe`: verifies the `Stripe-Signature` header (HMAC-SHA256, 5-minute replay window), stores the event, and ignores duplicates thanks to a unique index on `(provider, provider_event_id)`

## Run locally

```bash
cp .env.example .env        # set ADMIN_TOKEN and STRIPE_WEBHOOK_SECRET
docker compose up --build
```

Open http://localhost:8000/docs

### Receive real Stripe test events

```bash
stripe login
stripe listen --forward-to localhost:8000/webhooks/stripe   # prints the whsec_ secret
stripe trigger payment_intent.succeeded
```

## Tests

```bash
docker compose run --rm api sh -c "pip install -q -r requirements-dev.txt && python -m pytest -q"
```

Covered: valid / tampered / expired / wrong-secret signatures, duplicate events processed once, malformed payloads.

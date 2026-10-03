"""Stripe webhook signature verification, implemented from Stripe's spec.

Header format:  Stripe-Signature: t=<unix time>,v1=<hex hmac>[,v1=<hex hmac>...]
Signed string:  "<t>.<raw request body>"   (HMAC-SHA256 keyed with the whsec_ secret)
"""

import hashlib
import hmac
import time
from typing import Mapping

from app.providers.base import ParsedEvent

DEFAULT_TOLERANCE_SECONDS = 300  # reject old signatures to stop replay attacks


def parse_signature_header(header: str) -> tuple[int | None, list[str]]:
    timestamp: int | None = None
    signatures: list[str] = []
    for part in header.split(","):
        key, _, value = part.strip().partition("=")
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError:
                return None, []
        elif key == "v1":
            signatures.append(value)
    return timestamp, signatures


def compute_signature(secret: str, timestamp: int, body: bytes) -> str:
    signed_payload = str(timestamp).encode() + b"." + body
    return hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()


def verify_signature(
    body: bytes,
    header: str,
    secret: str,
    tolerance: int = DEFAULT_TOLERANCE_SECONDS,
    now: float | None = None,
) -> bool:
    if not header or not secret:
        return False
    timestamp, signatures = parse_signature_header(header)
    if timestamp is None or not signatures:
        return False
    current = time.time() if now is None else now
    if abs(current - timestamp) > tolerance:
        return False
    expected = compute_signature(secret, timestamp, body).encode()
    # Stripe may send several v1 signatures (during secret rotation); any match is OK.
    return any(hmac.compare_digest(expected, sig.encode()) for sig in signatures)


class StripeProvider:
    name = "stripe"

    def verify(self, body: bytes, headers: Mapping[str, str], secret: str) -> bool:
        return verify_signature(body, headers.get("stripe-signature", ""), secret)

    def parse(self, payload: dict) -> ParsedEvent | None:
        event_id = payload.get("id")
        event_type = payload.get("type")
        if not isinstance(event_id, str) or not isinstance(event_type, str):
            return None
        return ParsedEvent(event_id=event_id, event_type=event_type)

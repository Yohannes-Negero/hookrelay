import hashlib
import secrets

API_KEY_PREFIX = "hr_"


def generate_api_key() -> str:
    """Return a new random API key. Shown to the merchant once, never stored."""
    return API_KEY_PREFIX + secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """API keys are high-entropy, so a plain SHA-256 is enough for lookup."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def tokens_match(a: str, b: str) -> bool:
    """Constant-time comparison to avoid timing leaks."""
    return secrets.compare_digest(a.encode(), b.encode())

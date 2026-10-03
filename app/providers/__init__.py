from app.providers.base import ParsedEvent, WebhookProvider
from app.providers.stripe_provider import StripeProvider

# Add new payment providers here (Day 3 builds on this registry).
PROVIDERS: dict[str, WebhookProvider] = {
    "stripe": StripeProvider(),
}

__all__ = ["PROVIDERS", "ParsedEvent", "WebhookProvider"]

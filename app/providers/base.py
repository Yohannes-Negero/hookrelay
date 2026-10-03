from dataclasses import dataclass
from typing import Mapping, Protocol


@dataclass(frozen=True)
class ParsedEvent:
    """The few fields every provider's event must give us."""

    event_id: str
    event_type: str


class WebhookProvider(Protocol):
    name: str

    def verify(self, body: bytes, headers: Mapping[str, str], secret: str) -> bool:
        """Return True only if the request really came from the provider."""

    def parse(self, payload: dict) -> ParsedEvent | None:
        """Pull out the event id and type, or None if the payload is malformed."""

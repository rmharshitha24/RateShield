from dataclasses import dataclass
from typing import Protocol

from app.models.rate_limit_rule import RateLimitRule


@dataclass(frozen=True)
class RateLimitResult:
    """Result of a rate limit decision."""

    allowed: bool
    retry_after: int = 0
    remaining: int = 0


class RateLimitStrategy(Protocol):
    """Common contract implemented by all rate limiting algorithms."""

    name: str

    def allow_request(self, user_id: int, endpoint: str, rule: RateLimitRule) -> RateLimitResult:
        """Return whether a request may pass for the supplied scope."""
        ...

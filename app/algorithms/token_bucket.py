import math

from app.algorithms.base import RateLimitResult
from app.algorithms.state import get_or_create_state, seconds_between, utc_now
from app.database.session import db
from app.models.rate_limit_rule import RateLimitRule


class TokenBucket:
    """Refills tokens over time and consumes one token per request."""

    name = "token_bucket"

    def allow_request(self, user_id: int, endpoint: str, rule: RateLimitRule) -> RateLimitResult:
        now = utc_now()
        state = get_or_create_state(user_id, endpoint, self.name)
        capacity = float(rule.bucket_capacity)
        refill_rate = rule.refill_rate or (rule.max_requests / rule.time_window)

        current_tokens = capacity if state.tokens is None else state.tokens
        elapsed = seconds_between(now, state.last_updated)
        tokens = min(capacity, current_tokens + elapsed * refill_rate)

        if tokens < 1:
            retry_after = max(math.ceil((1 - tokens) / refill_rate), 1) if refill_rate > 0 else rule.time_window
            state.tokens = tokens
            state.last_updated = now
            db.session.flush()
            return RateLimitResult(False, retry_after=retry_after, remaining=0)

        tokens -= 1
        state.tokens = tokens
        state.last_updated = now
        db.session.flush()
        return RateLimitResult(True, remaining=math.floor(tokens))

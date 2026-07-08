import math

from app.algorithms.base import RateLimitResult
from app.algorithms.state import get_or_create_state, seconds_between, utc_now
from app.database.session import db
from app.models.rate_limit_rule import RateLimitRule


class LeakyBucket:
    """Queues requests in a bucket that drains at a steady rate."""

    name = "leaky_bucket"

    def allow_request(self, user_id: int, endpoint: str, rule: RateLimitRule) -> RateLimitResult:
        now = utc_now()
        state = get_or_create_state(user_id, endpoint, self.name)
        capacity = float(rule.bucket_capacity)
        leak_rate = rule.refill_rate or (rule.max_requests / rule.time_window)

        water_level = 0.0 if state.water_level is None else state.water_level
        leaked = seconds_between(now, state.last_updated) * leak_rate
        water_level = max(0.0, water_level - leaked)

        if water_level + 1 > capacity:
            retry_after = max(math.ceil((water_level + 1 - capacity) / leak_rate), 1) if leak_rate > 0 else rule.time_window
            state.water_level = water_level
            state.last_updated = now
            db.session.flush()
            return RateLimitResult(False, retry_after=retry_after, remaining=0)

        water_level += 1
        state.water_level = water_level
        state.last_updated = now
        remaining = max(math.floor(capacity - water_level), 0)
        db.session.flush()
        return RateLimitResult(True, remaining=remaining)

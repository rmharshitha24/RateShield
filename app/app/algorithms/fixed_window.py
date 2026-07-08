import math
from datetime import timedelta

from app.algorithms.base import RateLimitResult
from app.algorithms.state import get_or_create_state, seconds_between, utc_now
from app.database.session import db
from app.models.rate_limit_rule import RateLimitRule


class FixedWindowCounter:
    """Counts requests in a fixed-size time window."""

    name = "fixed_window"

    def allow_request(self, user_id: int, endpoint: str, rule: RateLimitRule) -> RateLimitResult:
        now = utc_now()
        state = get_or_create_state(user_id, endpoint, self.name)

        if state.window_start is None or seconds_between(now, state.window_start) >= rule.time_window:
            state.window_start = now
            state.request_count = 0

        if state.request_count >= rule.max_requests:
            elapsed = seconds_between(now, state.window_start)
            retry_after = max(math.ceil(rule.time_window - elapsed), 1)
            db.session.flush()
            return RateLimitResult(False, retry_after=retry_after, remaining=0)

        state.request_count += 1
        state.last_updated = now
        remaining = max(rule.max_requests - state.request_count, 0)
        db.session.flush()
        return RateLimitResult(True, remaining=remaining)

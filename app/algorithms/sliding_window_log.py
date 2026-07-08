import math
from datetime import timedelta

from app.algorithms.base import RateLimitResult
from app.algorithms.state import utc_now
from app.models.rate_limit_rule import RateLimitRule
from app.models.request_log import RequestLog


class SlidingWindowLog:
    """Stores timestamps and allows only max_requests inside the moving window."""

    name = "sliding_window_log"

    def allow_request(self, user_id: int, endpoint: str, rule: RateLimitRule) -> RateLimitResult:
        now = utc_now()
        window_start = now - timedelta(seconds=rule.time_window)
        recent_logs = (
            RequestLog.query.filter(
                RequestLog.user_id == user_id,
                RequestLog.endpoint == endpoint,
                RequestLog.algorithm == self.name,
                RequestLog.allowed.is_(True),
                RequestLog.timestamp >= window_start,
            )
            .order_by(RequestLog.timestamp.asc())
            .all()
        )

        if len(recent_logs) >= rule.max_requests:
            oldest = recent_logs[0].timestamp
            if oldest.tzinfo is None:
                oldest = oldest.replace(tzinfo=now.tzinfo)
            retry_after = max(math.ceil((oldest + timedelta(seconds=rule.time_window) - now).total_seconds()), 1)
            return RateLimitResult(False, retry_after=retry_after, remaining=0)

        return RateLimitResult(True, remaining=max(rule.max_requests - len(recent_logs) - 1, 0))

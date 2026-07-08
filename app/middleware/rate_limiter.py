import time

from flask import Flask, g, request

from app.database.session import db
from app.services.log_service import LogService
from app.services.rate_limit_service import RateLimitService
from app.services.user_service import UserService
from app.utils.exceptions import AuthenticationError, RateLimitExceeded

EXEMPT_ENDPOINTS = {
    "health.health",
    "users.create_user",
    "users.list_users",
    "users.get_user",
    "users.update_rate_limit",
    "users.delete_user",
    "logs.get_logs",
    "stats.get_stats",
    "static",
}


def register_rate_limiter(app: Flask) -> None:
    """Register request hooks that protect selected endpoints."""

    @app.before_request
    def check_rate_limit():
        g.start_time = time.perf_counter()
        g.rate_limit_user = None
        g.rate_limit_rule = None
        g.rate_limit_allowed = True

        if request.endpoint in EXEMPT_ENDPOINTS:
            return None

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise AuthenticationError("Missing X-API-Key header.")

        user = UserService.get_by_api_key(api_key)
        if user is None:
            raise AuthenticationError("Invalid API key.")

        rule, decision = RateLimitService.check(user, request.path)
        g.rate_limit_user = user
        g.rate_limit_rule = rule
        g.rate_limit_allowed = decision.allowed
        g.rate_limit_remaining = decision.remaining

        if not decision.allowed:
            raise RateLimitExceeded("Rate limit exceeded.", decision.retry_after)

        return None

    @app.after_request
    def persist_request_log(response):
        if request.endpoint in EXEMPT_ENDPOINTS:
            return response

        latency_ms = (time.perf_counter() - getattr(g, "start_time", time.perf_counter())) * 1000
        user = getattr(g, "rate_limit_user", None)
        rule = getattr(g, "rate_limit_rule", None)
        allowed = response.status_code < 400 and getattr(g, "rate_limit_allowed", True)
        algorithm = rule.algorithm if rule is not None else "unknown"

        LogService.log_request(
            user_id=user.id if user else None,
            username=user.username if user else None,
            endpoint=request.path,
            algorithm=algorithm,
            allowed=allowed,
            response_time_ms=latency_ms,
        )
        db.session.commit()

        if hasattr(g, "rate_limit_remaining"):
            response.headers["X-RateLimit-Remaining"] = str(g.rate_limit_remaining)
        return response

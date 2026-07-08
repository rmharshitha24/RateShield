from app.algorithms.base import RateLimitResult
from app.algorithms.factory import RateLimitStrategyFactory
from app.database.session import db
from app.models.rate_limit_rule import RateLimitRule
from app.models.user import User
from app.services.lock_registry import lock_registry
from app.utils.exceptions import ValidationError


class RateLimitService:
    """Selects policies and executes rate limit strategies."""

    @staticmethod
    def resolve_rule(user: User, endpoint: str) -> RateLimitRule:
        endpoint_rule = RateLimitRule.query.filter_by(user_id=user.id, endpoint=endpoint).one_or_none()
        if endpoint_rule is not None:
            return endpoint_rule
        default_rule = RateLimitRule.query.filter_by(user_id=user.id, endpoint=None).one_or_none()
        if default_rule is None:
            raise ValidationError(f"No rate limit rule configured for user {user.id}.")
        return default_rule

    @staticmethod
    def check(user: User, endpoint: str) -> tuple[RateLimitRule, RateLimitResult]:
        rule = RateLimitService.resolve_rule(user, endpoint)
        strategy = RateLimitStrategyFactory.get(rule.algorithm)
        lock_key = f"{user.id}:{endpoint}:{rule.algorithm}"
        with lock_registry.get_lock(lock_key):
            result = strategy.allow_request(user.id, endpoint, rule)
            db.session.flush()
            return rule, result

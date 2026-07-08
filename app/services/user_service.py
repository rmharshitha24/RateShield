import secrets

from sqlalchemy.exc import IntegrityError

from app.algorithms.factory import RateLimitStrategyFactory
from app.database.session import db
from app.models.rate_limit_rule import RateLimitRule
from app.models.user import User
from app.utils.exceptions import NotFoundError, ValidationError


class UserService:
    """Business operations for API users and their rate limit rules."""

    @staticmethod
    def create_user(payload: dict, defaults: dict) -> User:
        username = (payload.get("username") or "").strip()
        if not username:
            raise ValidationError("username is required.")

        user = User(
            username=username,
            api_key=payload.get("api_key") or secrets.token_urlsafe(32),
            plan=payload.get("plan", "free"),
        )
        db.session.add(user)
        db.session.flush()

        rule_payload = payload.get("rate_limit", {})
        rule = RateLimitRule(
            user_id=user.id,
            endpoint=rule_payload.get("endpoint"),
            algorithm=rule_payload.get("algorithm", defaults["algorithm"]),
            max_requests=int(rule_payload.get("max_requests", defaults["max_requests"])),
            time_window=int(rule_payload.get("time_window", defaults["time_window"])),
            refill_rate=float(rule_payload.get("refill_rate", defaults["refill_rate"])),
            bucket_capacity=int(rule_payload.get("bucket_capacity", defaults["bucket_capacity"])),
        )
        UserService._validate_rule(rule)
        db.session.add(rule)
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise ValidationError("username or api_key already exists.") from exc
        return user

    @staticmethod
    def list_users() -> list[User]:
        return User.query.order_by(User.id.asc()).all()

    @staticmethod
    def get_user(user_id: int) -> User:
        user = db.session.get(User, user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} was not found.")
        return user

    @staticmethod
    def get_by_api_key(api_key: str) -> User | None:
        return User.query.filter_by(api_key=api_key).one_or_none()

    @staticmethod
    def delete_user(user_id: int) -> None:
        user = UserService.get_user(user_id)
        db.session.delete(user)
        db.session.commit()

    @staticmethod
    def upsert_rate_limit(user_id: int, payload: dict) -> RateLimitRule:
        user = UserService.get_user(user_id)
        endpoint = payload.get("endpoint")
        rule = RateLimitRule.query.filter_by(user_id=user.id, endpoint=endpoint).one_or_none()
        if rule is None:
            rule = RateLimitRule(user_id=user.id, endpoint=endpoint)
            db.session.add(rule)

        rule.algorithm = payload.get("algorithm", rule.algorithm or "fixed_window")
        rule.max_requests = int(payload.get("max_requests", rule.max_requests or 100))
        rule.time_window = int(payload.get("time_window", rule.time_window or 60))
        rule.refill_rate = float(payload.get("refill_rate", rule.refill_rate or 0))
        rule.bucket_capacity = int(payload.get("bucket_capacity", rule.bucket_capacity or rule.max_requests))

        UserService._validate_rule(rule)
        db.session.commit()
        return rule

    @staticmethod
    def _validate_rule(rule: RateLimitRule) -> None:
        if rule.algorithm not in RateLimitStrategyFactory.supported_algorithms():
            raise ValidationError(f"Unsupported algorithm '{rule.algorithm}'.")
        if rule.max_requests <= 0:
            raise ValidationError("max_requests must be greater than zero.")
        if rule.time_window <= 0:
            raise ValidationError("time_window must be greater than zero.")
        if rule.bucket_capacity <= 0:
            raise ValidationError("bucket_capacity must be greater than zero.")
        if rule.refill_rate < 0:
            raise ValidationError("refill_rate cannot be negative.")

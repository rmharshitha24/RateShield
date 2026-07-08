from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import db


class RateLimitRule(db.Model):
    """Per-user, optionally per-endpoint, rate limit configuration."""

    __tablename__ = "rate_limit_rules"
    __table_args__ = (
        UniqueConstraint("user_id", "endpoint", name="uq_rate_limit_rules_user_endpoint"),
        CheckConstraint("max_requests > 0", name="ck_rate_limit_max_requests_positive"),
        CheckConstraint("time_window > 0", name="ck_rate_limit_time_window_positive"),
        CheckConstraint("bucket_capacity > 0", name="ck_rate_limit_bucket_capacity_positive"),
        CheckConstraint("refill_rate >= 0", name="ck_rate_limit_refill_rate_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    max_requests: Mapped[int] = mapped_column(Integer, nullable=False)
    time_window: Mapped[int] = mapped_column(Integer, nullable=False)
    refill_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    bucket_capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    user = relationship("User", back_populates="rules")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "algorithm": self.algorithm,
            "max_requests": self.max_requests,
            "time_window": self.time_window,
            "refill_rate": self.refill_rate,
            "bucket_capacity": self.bucket_capacity,
        }

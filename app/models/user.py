from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import db


class User(db.Model):
    """API consumer with an API key and one or more rate limit policies."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    api_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    rules = relationship("RateLimitRule", back_populates="user", cascade="all, delete-orphan")
    logs = relationship("RequestLog", back_populates="user", cascade="all, delete-orphan")
    states = relationship("AlgorithmState", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "api_key": self.api_key,
            "plan": self.plan,
            "created_at": self.created_at.isoformat(),
            "rate_limits": [rule.to_dict() for rule in self.rules],
        }

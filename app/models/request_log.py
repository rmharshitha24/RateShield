from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import db


class RequestLog(db.Model):
    """Audit record for every protected API request."""

    __tablename__ = "request_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    response_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    user = relationship("User", back_populates="logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "timestamp": self.timestamp.isoformat(),
            "allowed": self.allowed,
            "algorithm": self.algorithm,
            "response_time_ms": round(self.response_time_ms, 2),
        }

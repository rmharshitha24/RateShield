from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import db


class AlgorithmState(db.Model):
    """Persistent mutable state used by counter and bucket algorithms."""

    __tablename__ = "algorithm_states"
    __table_args__ = (UniqueConstraint("user_id", "endpoint", "algorithm", name="uq_algorithm_state_scope"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens: Mapped[float] = mapped_column(Float, nullable=True)
    water_level: Mapped[float] = mapped_column(Float, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user = relationship("User", back_populates="states")

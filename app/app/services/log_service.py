import logging

from app.database.session import db
from app.models.request_log import RequestLog

logger = logging.getLogger(__name__)


class LogService:
    """Persists and emits request logs."""

    @staticmethod
    def log_request(
        user_id: int | None,
        username: str | None,
        endpoint: str,
        algorithm: str,
        allowed: bool,
        response_time_ms: float,
    ) -> RequestLog:
        log = RequestLog(
            user_id=user_id,
            endpoint=endpoint,
            allowed=allowed,
            algorithm=algorithm,
            response_time_ms=response_time_ms,
        )
        db.session.add(log)
        logger.info(
            "request user=%s endpoint=%s algorithm=%s decision=%s latency_ms=%.2f",
            username or "unknown",
            endpoint,
            algorithm,
            "allowed" if allowed else "rejected",
            response_time_ms,
        )
        return log

    @staticmethod
    def list_logs(limit: int = 100) -> list[RequestLog]:
        safe_limit = min(max(limit, 1), 1000)
        return RequestLog.query.order_by(RequestLog.timestamp.desc()).limit(safe_limit).all()

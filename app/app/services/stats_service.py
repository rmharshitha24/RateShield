from sqlalchemy import desc, func

from app.database.session import db
from app.models.request_log import RequestLog
from app.models.user import User


class StatsService:
    """Aggregates request statistics."""

    @staticmethod
    def get_stats() -> dict:
        total = db.session.query(func.count(RequestLog.id)).scalar() or 0
        allowed = db.session.query(func.count(RequestLog.id)).filter(RequestLog.allowed.is_(True)).scalar() or 0
        rejected = db.session.query(func.count(RequestLog.id)).filter(RequestLog.allowed.is_(False)).scalar() or 0

        per_algorithm = {
            algorithm: count
            for algorithm, count in db.session.query(RequestLog.algorithm, func.count(RequestLog.id))
            .group_by(RequestLog.algorithm)
            .all()
        }

        most_active_users = [
            {"user_id": user_id, "username": username, "requests": count}
            for user_id, username, count in db.session.query(
                User.id, User.username, func.count(RequestLog.id).label("request_count")
            )
            .join(RequestLog, RequestLog.user_id == User.id)
            .group_by(User.id, User.username)
            .order_by(desc("request_count"))
            .limit(10)
            .all()
        ]

        return {
            "total_requests": total,
            "allowed_requests": allowed,
            "rejected_requests": rejected,
            "requests_per_algorithm": per_algorithm,
            "most_active_users": most_active_users,
        }

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from app.database.session import db
from app.utils.exceptions import RateLimitExceeded, RateShieldError
from app.utils.responses import error_response


def register_error_handlers(app: Flask) -> None:
    """Register consistent JSON error handlers."""

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(error: RateLimitExceeded):
        return error_response(
            error.message,
            error.status_code,
            error.error,
            headers={"Retry-After": str(error.retry_after)},
        )

    @app.errorhandler(RateShieldError)
    def handle_rateshield_error(error: RateShieldError):
        return error_response(error.message, error.status_code, error.error)

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error: SQLAlchemyError):
        db.session.rollback()
        app.logger.exception("Database error: %s", error)
        return error_response("A database error occurred.", 500, "database_error")

    @app.errorhandler(404)
    def handle_404(_):
        return error_response("Resource not found.", 404, "not_found")

    @app.errorhandler(405)
    def handle_405(_):
        return error_response("Method not allowed.", 405, "method_not_allowed")

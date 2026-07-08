class RateShieldError(Exception):
    """Base exception rendered as a JSON API error."""

    status_code = 500
    error = "internal_error"

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code
        self.message = message


class ValidationError(RateShieldError):
    status_code = 400
    error = "validation_error"


class AuthenticationError(RateShieldError):
    status_code = 401
    error = "authentication_error"


class NotFoundError(RateShieldError):
    status_code = 404
    error = "not_found"


class RateLimitExceeded(RateShieldError):
    status_code = 429
    error = "rate_limit_exceeded"

    def __init__(self, message: str, retry_after: int) -> None:
        super().__init__(message, self.status_code)
        self.retry_after = retry_after

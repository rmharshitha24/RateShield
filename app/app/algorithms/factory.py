from app.algorithms.base import RateLimitStrategy
from app.algorithms.fixed_window import FixedWindowCounter
from app.algorithms.leaky_bucket import LeakyBucket
from app.algorithms.sliding_window_log import SlidingWindowLog
from app.algorithms.token_bucket import TokenBucket
from app.utils.exceptions import ValidationError


class RateLimitStrategyFactory:
    """Creates rate limiting strategy instances by configured algorithm name."""

    _strategies: dict[str, RateLimitStrategy] = {
        FixedWindowCounter.name: FixedWindowCounter(),
        SlidingWindowLog.name: SlidingWindowLog(),
        TokenBucket.name: TokenBucket(),
        LeakyBucket.name: LeakyBucket(),
    }

    @classmethod
    def get(cls, algorithm: str) -> RateLimitStrategy:
        strategy = cls._strategies.get(algorithm)
        if strategy is None:
            supported = ", ".join(sorted(cls._strategies))
            raise ValidationError(f"Unsupported algorithm '{algorithm}'. Supported algorithms: {supported}")
        return strategy

    @classmethod
    def supported_algorithms(cls) -> list[str]:
        return sorted(cls._strategies)

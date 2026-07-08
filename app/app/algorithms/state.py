from datetime import datetime, timezone

from app.database.session import db
from app.models.algorithm_state import AlgorithmState


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_or_create_state(user_id: int, endpoint: str, algorithm: str) -> AlgorithmState:
    state = AlgorithmState.query.filter_by(
        user_id=user_id, endpoint=endpoint, algorithm=algorithm
    ).one_or_none()
    if state is not None:
        return state

    state = AlgorithmState(user_id=user_id, endpoint=endpoint, algorithm=algorithm, last_updated=utc_now())
    db.session.add(state)
    db.session.flush()
    return state


def seconds_between(later: datetime, earlier: datetime | None) -> float:
    if earlier is None:
        return 0
    if earlier.tzinfo is None:
        earlier = earlier.replace(tzinfo=timezone.utc)
    if later.tzinfo is None:
        later = later.replace(tzinfo=timezone.utc)
    return max((later - earlier).total_seconds(), 0)

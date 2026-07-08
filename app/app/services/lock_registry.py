from collections import defaultdict
from threading import Lock


class LockRegistry:
    """Provides in-process locks by key for thread-safe rate limit mutations."""

    def __init__(self) -> None:
        self._registry_lock = Lock()
        self._locks: dict[str, Lock] = defaultdict(Lock)

    def get_lock(self, key: str) -> Lock:
        with self._registry_lock:
            return self._locks[key]


lock_registry = LockRegistry()

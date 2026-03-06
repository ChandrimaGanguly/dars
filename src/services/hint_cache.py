"""In-memory hint cache for Claude-generated Socratic hints.

PHASE5-A-1

Cache key:   (problem_id: int, hint_number: int, language: str)
Cache value: (hint_text: str, cached_at: datetime)
TTL:         7 days

Language is included in the key so English and Bengali hints are stored
independently — a cache entry populated by an English request will not
serve the wrong language to a Bengali student.

Phase 0: in-memory dict — sufficient for 50-student pilot (~1,680 max
entries: 280 problems x 3 hints x 2 languages). No size cap needed.
Phase 1+: Replace _store with Redis without changing the public API.
"""

from datetime import UTC, datetime, timedelta

_TTL: timedelta = timedelta(days=7)


class HintCache:
    """Thread-safe in-memory cache for Claude-generated hints.

    Keyed on (problem_id, hint_number, language). Entries older than 7 days
    are treated as expired and evicted on next access (lazy eviction).

    Attributes:
        _store: Internal mapping from cache key to (text, timestamp).
        _hits:  Running count of cache hits.
        _misses: Running count of cache misses.
    """

    def __init__(self) -> None:
        """Initialise empty cache with zero hit/miss counters."""
        self._store: dict[tuple[int, int, str], tuple[str, datetime]] = {}
        self._hits: int = 0
        self._misses: int = 0

    def get(self, problem_id: int, hint_number: int, language: str = "en") -> str | None:
        """Return cached hint text, or None if missing or expired.

        Args:
            problem_id: Problem primary key.
            hint_number: Hint level (1, 2, or 3).
            language: Language code ("en" or "bn").

        Returns:
            Cached hint string, or None.
        """
        entry = self._store.get((problem_id, hint_number, language))
        if entry is None:
            self._misses += 1
            return None
        hint_text, cached_at = entry
        if datetime.now(UTC) - cached_at > _TTL:
            del self._store[(problem_id, hint_number, language)]
            self._misses += 1
            return None
        self._hits += 1
        return hint_text

    def set(self, problem_id: int, hint_number: int, language: str, hint_text: str) -> None:
        """Store hint text with the current UTC timestamp.

        Overwrites any existing entry for the same key.

        Args:
            problem_id: Problem primary key.
            hint_number: Hint level (1, 2, or 3).
            language: Language code ("en" or "bn").
            hint_text: Generated hint string to cache.
        """
        self._store[(problem_id, hint_number, language)] = (hint_text, datetime.now(UTC))

    @property
    def hit_rate(self) -> float:
        """Cache hit rate (hits / total requests); 0.0 if no requests yet."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def stats(self) -> dict[str, int]:
        """Return a snapshot of cache statistics.

        Returns:
            Dict with keys "hits", "misses", and "entries".
        """
        return {
            "hits": self._hits,
            "misses": self._misses,
            "entries": len(self._store),
        }

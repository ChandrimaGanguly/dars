"""Unit tests for HintCache (PHASE5-A-1 / PHASE5-C-3)."""

from datetime import UTC, datetime, timedelta

import pytest

from src.services.hint_cache import _TTL, HintCache


class TestHintCacheBasic:
    """Basic get/set behaviour."""

    def test_miss_returns_none(self) -> None:
        cache = HintCache()
        assert cache.get(1, 1) is None

    def test_set_then_get_returns_text(self) -> None:
        cache = HintCache()
        cache.set(1, 1, "en", "Think about it.")
        assert cache.get(1, 1, "en") == "Think about it."

    def test_different_hint_numbers_stored_separately(self) -> None:
        cache = HintCache()
        cache.set(1, 1, "en", "Hint 1")
        cache.set(1, 2, "en", "Hint 2")
        assert cache.get(1, 1, "en") == "Hint 1"
        assert cache.get(1, 2, "en") == "Hint 2"

    def test_different_problems_stored_separately(self) -> None:
        cache = HintCache()
        cache.set(10, 1, "en", "P10 H1")
        cache.set(20, 1, "en", "P20 H1")
        assert cache.get(10, 1, "en") == "P10 H1"
        assert cache.get(20, 1, "en") == "P20 H1"

    def test_overwrite_existing_entry(self) -> None:
        cache = HintCache()
        cache.set(1, 1, "en", "Old")
        cache.set(1, 1, "en", "New")
        assert cache.get(1, 1, "en") == "New"

    def test_languages_stored_independently(self) -> None:
        """English and Bengali hints for the same problem/number are separate entries."""
        cache = HintCache()
        cache.set(1, 1, "en", "Think about it.")
        cache.set(1, 1, "bn", "এটা নিয়ে ভাবো।")
        assert cache.get(1, 1, "en") == "Think about it."
        assert cache.get(1, 1, "bn") == "এটা নিয়ে ভাবো।"

    def test_english_entry_does_not_serve_bengali_request(self) -> None:
        """An English cache entry must not be returned for a Bengali request."""
        cache = HintCache()
        cache.set(1, 1, "en", "English hint")
        assert cache.get(1, 1, "bn") is None

    def test_get_default_language_is_en(self) -> None:
        cache = HintCache()
        cache.set(1, 1, "en", "default lang hint")
        assert cache.get(1, 1) == "default lang hint"


class TestHintCacheTTL:
    """TTL and expiry behaviour."""

    def test_entry_within_ttl_is_returned(self) -> None:
        cache = HintCache()
        cache.set(1, 1, "en", "Fresh hint")
        assert cache.get(1, 1, "en") == "Fresh hint"

    def test_expired_entry_returns_none(self) -> None:
        cache = HintCache()
        past = datetime.now(UTC) - _TTL - timedelta(seconds=1)
        cache._store[(1, 1, "en")] = ("Stale hint", past)
        assert cache.get(1, 1, "en") is None

    def test_expired_entry_evicted_from_store(self) -> None:
        cache = HintCache()
        past = datetime.now(UTC) - _TTL - timedelta(seconds=1)
        cache._store[(1, 1, "en")] = ("Stale hint", past)
        cache.get(1, 1, "en")
        assert (1, 1, "en") not in cache._store


class TestHintCacheStats:
    """Hit/miss counters and hit_rate."""

    def test_initial_stats_are_zero(self) -> None:
        cache = HintCache()
        assert cache.stats == {"hits": 0, "misses": 0, "entries": 0}

    def test_miss_increments_misses(self) -> None:
        cache = HintCache()
        cache.get(999, 1, "en")
        assert cache.stats["misses"] == 1
        assert cache.stats["hits"] == 0

    def test_hit_increments_hits(self) -> None:
        cache = HintCache()
        cache.set(1, 1, "en", "x")
        cache.get(1, 1, "en")
        assert cache.stats["hits"] == 1
        assert cache.stats["misses"] == 0

    def test_expired_entry_counts_as_miss(self) -> None:
        cache = HintCache()
        past = datetime.now(UTC) - _TTL - timedelta(seconds=1)
        cache._store[(1, 1, "en")] = ("Old", past)
        cache.get(1, 1, "en")
        assert cache.stats["misses"] == 1
        assert cache.stats["hits"] == 0

    def test_hit_rate_zero_when_no_requests(self) -> None:
        cache = HintCache()
        assert cache.hit_rate == 0.0

    def test_hit_rate_calculation(self) -> None:
        cache = HintCache()
        cache.set(1, 1, "en", "hint")
        cache.get(1, 1, "en")  # hit
        cache.get(1, 2, "en")  # miss
        assert cache.hit_rate == pytest.approx(0.5)

    def test_entries_count_matches_store_size(self) -> None:
        cache = HintCache()
        cache.set(1, 1, "en", "a")
        cache.set(1, 2, "en", "b")
        cache.set(2, 1, "en", "c")
        assert cache.stats["entries"] == 3

    def test_en_and_bn_count_as_separate_entries(self) -> None:
        cache = HintCache()
        cache.set(1, 1, "en", "en hint")
        cache.set(1, 1, "bn", "bn hint")
        assert cache.stats["entries"] == 2

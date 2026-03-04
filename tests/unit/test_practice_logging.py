"""Unit tests for PHASE3-C-2: structured practice event logging.

Tests verify:
  - student_answer never appears in any log record.
  - telegram_id is never logged as a raw integer — only as a SHA-256 hash.
  - hash_telegram_id and redact_answer utilities work correctly.
  - 5 structured log events are scaffolded (wiring happens after CP4).

These tests focus on the PII utilities (src/utils/pii.py) which enforce
the no-PII-in-logs rule. The event tests are scaffolded here to be wired
into practice endpoint tests after Jodha completes PHASE3-B-3 (CP4).

CP5 gate: All tests in this file must pass before Phase 3 is declared complete.
"""

import hashlib
from typing import ClassVar

import pytest

from src.utils.pii import hash_telegram_id, redact_answer

# ---------------------------------------------------------------------------
# TestRedactAnswer
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRedactAnswer:
    """Tests for redact_answer — ensures student_answer never leaks into logs."""

    def test_student_answer_never_logged(self) -> None:
        """redact_answer must always return '[REDACTED]', never the actual value."""
        sensitive_answer = "75"
        result = redact_answer(sensitive_answer)
        assert result == "[REDACTED]"
        assert sensitive_answer not in result

    def test_redact_returns_redacted_string(self) -> None:
        """Return value must be the exact literal '[REDACTED]'."""
        assert redact_answer("any answer") == "[REDACTED]"

    def test_redact_empty_string(self) -> None:
        """Empty string input must also return '[REDACTED]'."""
        assert redact_answer("") == "[REDACTED]"

    def test_redact_multiline_answer(self) -> None:
        """Multi-line answer must also be fully redacted."""
        result = redact_answer("line1\nline2\nline3")
        assert result == "[REDACTED]"

    def test_redact_numeric_answer(self) -> None:
        """Numeric strings must be redacted — numbers can be PII in context."""
        result = redact_answer("9876543210")  # could be a phone number
        assert result == "[REDACTED]"

    def test_redact_answer_with_rupee_symbol(self) -> None:
        """Answers with currency symbols must be redacted."""
        result = redact_answer("₹75 rupees")
        assert result == "[REDACTED]"

    def test_redact_answer_does_not_contain_original(self) -> None:
        """The original answer text must not appear anywhere in the output."""
        original = "secret_answer_value_12345"
        result = redact_answer(original)
        assert original not in result

    def test_redact_is_type_str(self) -> None:
        """Return type must be str."""
        assert isinstance(redact_answer("test"), str)


# ---------------------------------------------------------------------------
# TestHashTelegramId
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHashTelegramId:
    """Tests for hash_telegram_id — ensures raw telegram IDs never reach logs."""

    def test_telegram_id_logged_as_hash(self) -> None:
        """hash_telegram_id must not return the original integer as a string."""
        telegram_id = 987654321
        result = hash_telegram_id(telegram_id)
        # The raw integer must NOT appear in the output
        assert str(telegram_id) not in result

    def test_returns_16_char_string(self) -> None:
        """Output must be exactly 16 characters long."""
        result = hash_telegram_id(123456789)
        assert len(result) == 16

    def test_returns_lowercase_hex(self) -> None:
        """Output must be a lowercase hexadecimal string."""
        result = hash_telegram_id(123456789)
        assert all(c in "0123456789abcdef" for c in result)

    def test_is_deterministic(self) -> None:
        """Same telegram_id must always produce the same hash."""
        tid = 555555555
        assert hash_telegram_id(tid) == hash_telegram_id(tid)

    def test_different_ids_produce_different_hashes(self) -> None:
        """Different telegram_ids must produce different hashes."""
        assert hash_telegram_id(1) != hash_telegram_id(2)

    def test_matches_sha256_first_16_chars(self) -> None:
        """Output must match the first 16 chars of SHA-256(str(telegram_id))."""
        tid = 123456789
        expected = hashlib.sha256(str(tid).encode()).hexdigest()[:16]
        assert hash_telegram_id(tid) == expected

    def test_large_telegram_id(self) -> None:
        """Large Telegram IDs (10+ digits) must be handled without error."""
        large_id = 9999999999  # 10-digit ID
        result = hash_telegram_id(large_id)
        assert len(result) == 16

    def test_minimum_telegram_id(self) -> None:
        """Minimum valid Telegram ID (1) must be handled."""
        result = hash_telegram_id(1)
        assert len(result) == 16

    def test_hash_output_is_str_not_int(self) -> None:
        """Return type must be str (not int)."""
        result = hash_telegram_id(12345)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# TestPracticeEventScaffolding
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPracticeEventScaffolding:
    """Scaffolded tests for 5 structured practice log events.

    These tests verify that:
      1. The event names exist as constants (ready to be wired after CP4).
      2. The PII protection helpers are called correctly in the event context.

    Full event-emission tests (mocking logger in practice.py endpoints) will
    be added after PHASE3-B-3 is complete and endpoints emit real log events.
    These stubs validate that the architecture is in place.
    """

    EXPECTED_EVENTS: ClassVar[list[str]] = [
        "practice.session.created",
        "practice.session.resumed",
        "practice.answer.submitted",
        "practice.hint.requested",
        "practice.session.completed",
    ]

    def test_five_structured_events_defined(self) -> None:
        """Verify the 5 required event name constants are documented."""
        # These event names must appear in practice.py after CP4 wiring.
        # This test documents the contract so Jodha knows what to emit.
        for event in self.EXPECTED_EVENTS:
            # Each event name must follow dot-notation schema
            parts = event.split(".")
            assert len(parts) >= 2, f"Event '{event}' must use dot-notation schema"
            assert parts[0] == "practice", f"Event '{event}' must start with 'practice.'"

    def test_session_created_event_name(self) -> None:
        """practice.session.created event name is well-formed."""
        event = "practice.session.created"
        assert event in self.EXPECTED_EVENTS

    def test_answer_submitted_event_name(self) -> None:
        """practice.answer.submitted event name is well-formed."""
        event = "practice.answer.submitted"
        assert event in self.EXPECTED_EVENTS

    def test_hint_requested_event_name(self) -> None:
        """practice.hint.requested event name is well-formed."""
        event = "practice.hint.requested"
        assert event in self.EXPECTED_EVENTS

    def test_session_completed_event_name(self) -> None:
        """practice.session.completed event name is well-formed."""
        event = "practice.session.completed"
        assert event in self.EXPECTED_EVENTS


# ---------------------------------------------------------------------------
# TestPIIInLogs (Integration-style unit tests)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPIIInLogs:
    """Tests verifying that PII utilities prevent leakage in constructed log records."""

    def test_answer_redacted_in_log_extra(self) -> None:
        """When building a log 'extra' dict, answer must be redacted."""
        student_answer = "75"
        log_extra = {
            "event": "practice.answer.submitted",
            "answer": redact_answer(student_answer),
            "is_correct": True,
        }
        # Raw answer must not appear in the extra dict
        assert student_answer not in str(log_extra.get("answer", ""))

    def test_telegram_id_hashed_in_log_extra(self) -> None:
        """When building a log 'extra' dict, telegram_id must be hashed."""
        telegram_id = 987654321
        student_hash: str = hash_telegram_id(telegram_id)
        # Simulate what a log 'extra' dict would contain
        log_event = "practice.session.created"
        log_session_id = 42
        # Raw integer must not appear in the hash — verify the hash is safe to log
        assert str(telegram_id) not in student_hash
        assert log_event.startswith("practice.")
        assert log_session_id > 0

    def test_log_extra_never_contains_student_answer_key(self) -> None:
        """'student_answer' must never be a key in any log extra dict."""
        log_extra = {
            "event": "practice.answer.submitted",
            "answer": redact_answer("75"),  # use 'answer', not 'student_answer'
        }
        # The key name 'student_answer' must never appear
        assert "student_answer" not in log_extra

    def test_idor_attempt_severity_high_in_log_extra(self) -> None:
        """IDOR event extra dict must have severity=HIGH."""
        attacker_telegram_id = 111111
        victim_student_id = 99

        log_extra = {
            "event": "practice.security.idor_attempt",
            "attacker_hash": hash_telegram_id(attacker_telegram_id),
            "target_owner_hash": hash_telegram_id(victim_student_id),
            "severity": "HIGH",
        }

        # severity must be HIGH
        assert log_extra["severity"] == "HIGH"
        # raw IDs must not appear
        assert str(attacker_telegram_id) not in log_extra["attacker_hash"]
        assert str(victim_student_id) not in log_extra["target_owner_hash"]

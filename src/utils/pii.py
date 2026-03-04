"""PII protection utilities for safe logging.

PHASE3-C-2: Helpers that enforce the logging PII rules:
  - telegram_id must NEVER appear raw in any log line.
  - student_answer must NEVER appear in any log line.

Usage:
    from src.utils.pii import hash_telegram_id, redact_answer

    logger.info("Student action", extra={
        "student_hash": hash_telegram_id(telegram_id),
        "answer": redact_answer(student_answer),  # always "[REDACTED]"
    })

Rules enforced:
  1. hash_telegram_id — deterministic 16-char SHA-256 prefix; safe for
     correlation in logs without exposing the raw Telegram user ID.
  2. redact_answer — returns the literal string "[REDACTED]" regardless of
     input. Student answers must never appear in logs because they can contain
     personally identifiable or sensitive content (name, phone number, etc.).
"""

import hashlib


def hash_telegram_id(telegram_id: int) -> str:
    """Return a 16-char SHA-256 prefix for safe logging of a telegram_id.

    Use this function every time a student's Telegram ID would appear in a
    log message. The 16-char prefix is long enough to correlate events across
    log lines for the same student while being short enough to be unambiguous.

    This function is deterministic: the same telegram_id always produces the
    same hash, so log analysis can group events by student without decoding.

    Args:
        telegram_id: Integer Telegram user ID (positive, from Telegram API).

    Returns:
        16-character lowercase hex string (first 64 bits of SHA-256 digest).

    Example:
        >>> hash_telegram_id(987654321)
        'a3f8bc2e1d094f56'  # deterministic, example only
    """
    return hashlib.sha256(str(telegram_id).encode()).hexdigest()[:16]


def redact_answer(answer: str) -> str:
    """Return "[REDACTED]" unconditionally.

    Student answers must NEVER appear in logs. Use this wrapper whenever
    the answer value would otherwise be included in log output.

    The input parameter is accepted to make the call-site pattern natural
    but is not used in any way:
        logger.info("answer received", extra={"answer": redact_answer(answer)})

    Args:
        answer: Student's raw answer string (unused).

    Returns:
        The literal string "[REDACTED]" always.
    """
    # Deliberately ignore `answer` — it must not appear in output.
    _ = answer
    return "[REDACTED]"

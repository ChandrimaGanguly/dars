"""Bilingual encouragement message library for the Dars tutoring platform.

Provides student-facing motivational messages in English ('en') and Bengali ('bn')
for correct answers, incorrect answers, session start, and streak milestones.

All selection is deterministic — no randomness — so messages are reproducible
and easy to test. The selection index is derived from a context value (streak,
hints_used, or grade) modulo the pool length.

REQ-009 (streak tracking), REQ-010 (streak display), REQ-012 (milestones).
REQ-013 (non-repeat): async variants get_unique_correct_message() and
get_unique_incorrect_message() track sent variants via the SentMessage DB table.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.sent_message import SentMessage

# ---------------------------------------------------------------------------
# Correct-answer message templates
# ---------------------------------------------------------------------------
# Indices 0-2: generic messages (streak < 7).
# Indices 3-5: streak-aware messages (streak >= 7); contain {streak} placeholder.

_CORRECT_TEMPLATES: dict[str, list[str]] = {
    "en": [
        "Correct! \u2705 Well done!",
        "Perfect! \u2705 You got it!",
        "Excellent! \u2705 Keep it up!",
        "Correct! \u2705 \U0001f525 {streak}-day streak! Amazing!",
        "Perfect! \u2705 \U0001f525 {streak} days in a row! Superb!",
        "Excellent! \u2705 \U0001f525 {streak}-day streak! You\u2019re on fire!",
    ],
    "bn": [
        "\u09b8\u09a0\u09bf\u0995! \u2705 \u09b6\u09be\u09ac\u09be\u09b6!",
        "\u09a6\u09be\u09b0\u09c1\u09a3! \u2705 \u09a0\u09bf\u0995 \u0989\u09a4\u09cd\u09a4\u09b0!",
        "\u0985\u09b8\u09be\u09a7\u09be\u09b0\u09a3! \u2705 \u099a\u09be\u09b2\u09bf\u09df\u09c7 \u09af\u09be\u0993!",
        "\u09b8\u09a0\u09bf\u0995! \u2705 \U0001f525 {streak} \u09a6\u09bf\u09a8\u09c7\u09b0 \u09a7\u09be\u09b0\u09be! \u0985\u09b8\u09be\u09a7\u09be\u09b0\u09a3!",
        "\u09a6\u09be\u09b0\u09c1\u09a3! \u2705 \U0001f525 {streak} \u09a6\u09bf\u09a8 \u09a7\u09b0\u09c7 \u099a\u09b2\u099b\u09c7! \u0985\u09ac\u09bf\u09b6\u09cd\u09ac\u09be\u09b8\u09cd\u09af!",
        "\u0985\u09b8\u09be\u09a7\u09be\u09b0\u09a3! \u2705 \U0001f525 {streak} \u09a6\u09bf\u09a8\u09c7\u09b0 \u09a7\u09be\u09b0\u09be! \u09a4\u09c1\u09ae\u09bf \u0985\u09a6\u09cd\u09ad\u09c1\u09a4!",
    ],
}

# ---------------------------------------------------------------------------
# Incorrect-answer message templates
# ---------------------------------------------------------------------------
# {hints_used} is not embedded — messages are generic nudges.
# Pool size = 3; selected by hints_used % 3.

_INCORRECT_TEMPLATES: dict[str, list[str]] = {
    "en": [
        "Not quite right. Think about it again \u2014 you can do it!",
        "Almost! Check your working and try again.",
        "Keep trying! Would you like a hint to help?",
    ],
    "bn": [
        "\u098f\u0996\u09a8\u09cb \u09a0\u09bf\u0995 \u09b9\u09df\u09a8\u09bf\u0964 \u098f\u0995\u099f\u09c1 \u09ad\u09be\u09ac\u09cb \u2014 \u09a4\u09c1\u09ae\u09bf \u09aa\u09be\u09b0\u09ac\u09c7!",
        "\u09aa\u09cd\u09b0\u09be\u09df \u09a0\u09bf\u0995! \u09b9\u09bf\u09b8\u09c7\u09ac\u099f\u09be \u098f\u0995\u09ac\u09be\u09b0 \u09a6\u09c7\u0996\u09cb\u0964",
        "\u099a\u09c7\u09b7\u09cd\u099f\u09be \u0995\u09b0\u09c7 \u09af\u09be\u0993! \u09b8\u09be\u09b9\u09be\u09af\u09cd\u09af\u09c7\u09b0 \u099c\u09a8\u09cd\u09af hint \u099a\u09be\u0987\u09a4\u09c7 \u09aa\u09be\u09b0\u09cb\u0964",
    ],
}

# ---------------------------------------------------------------------------
# Session-start message templates
# ---------------------------------------------------------------------------
# Contains {grade} and {topics} placeholders.
# Pool size = 3; selected by grade % 3.

_SESSION_START_TEMPLATES: dict[str, list[str]] = {
    "en": [
        "Let\u2019s practice! Grade {grade} \u2014 today\u2019s topics: {topics}. Ready? \U0001f4aa",
        "Time to learn! Today we\u2019re covering: {topics} (Grade {grade}). Let\u2019s go! \U0001f4d6",
        "Good to see you! Grade {grade} practice: {topics}. You\u2019ve got this! \u2b50",
    ],
    "bn": [
        "\u099a\u09b2\u09cb \u0985\u09a8\u09c1\u09b6\u09c0\u09b2\u09a8 \u0995\u09b0\u09bf! \u09b6\u09cd\u09b0\u09c7\u09a3\u09c0 {grade} \u2014 \u0986\u099c\u0995\u09c7\u09b0 \u09ac\u09bf\u09b7\u09df: {topics}\u0964 \u09a4\u09c8\u09b0\u09bf? \U0001f4aa",
        "\u09b6\u09c7\u0996\u09be\u09b0 \u09b8\u09ae\u09df! \u0986\u099c \u0986\u09ae\u09b0\u09be \u09aa\u09dc\u09be\u09ac: {topics} (\u09b6\u09cd\u09b0\u09c7\u09a3\u09c0 {grade})\u0964 \u099a\u09b2\u09cb! \U0001f4d6",
        "\u09a4\u09cb\u09ae\u09be\u0995\u09c7 \u09a6\u09c7\u0996\u09c7 \u09ad\u09be\u09b2\u09cb \u09b2\u09be\u0997\u09c7! \u09b6\u09cd\u09b0\u09c7\u09a3\u09c0 {grade} \u0985\u09a8\u09c1\u09b6\u09c0\u09b2\u09a8: {topics}\u0964 \u09a4\u09c1\u09ae\u09bf \u09aa\u09be\u09b0\u09ac\u09c7! \u2b50",
    ],
}

# ---------------------------------------------------------------------------
# Milestone message templates
# ---------------------------------------------------------------------------
# Keyed by milestone_days (7, 14, 30).

_MILESTONE_MESSAGES: dict[int, dict[str, str]] = {
    7: {
        "en": ("\U0001f525 Amazing! 7-day streak! You\u2019re building a great learning habit!"),
        "bn": (
            "\U0001f525 \u0985\u09b8\u09be\u09a7\u09be\u09b0\u09a3! \u09ed \u09a6\u09bf\u09a8\u09c7\u09b0 "
            "\u09a7\u09be\u09b0\u09be! \u09a4\u09c1\u09ae\u09bf \u09a6\u09be\u09b0\u09c1\u09a3 \u0985\u09ad\u09cd\u09af\u09be\u09b8 "
            "\u0997\u09dc\u099b\u09cb!"
        ),
    },
    14: {
        "en": (
            "\U0001f31f Incredible! 14-day streak! Two weeks of daily learning \u2014 keep going!"
        ),
        "bn": (
            "\U0001f31f \u0985\u09ac\u09bf\u09b6\u09cd\u09ac\u09be\u09b8\u09cd\u09af! \u09e7\u09ea \u09a6\u09bf\u09a8\u09c7\u09b0 "
            "\u09a7\u09be\u09b0\u09be! \u09a6\u09c1\u0987 \u09b8\u09aa\u09cd\u09a4\u09be\u09b9 \u09aa\u09cd\u09b0\u09a4\u09bf\u09a6\u09bf\u09a8 "
            "\u09b6\u09c7\u0996\u09be \u2014 \u099c\u09be\u09b0\u09bf \u09a5\u09be\u0995\u09cb!"
        ),
    },
    30: {
        "en": (
            "\U0001f3c6 Champion! 30-day streak! A whole month of learning \u2014 you\u2019re unstoppable!"
        ),
        "bn": (
            "\U0001f3c6 \u099a\u09cd\u09af\u09be\u09ae\u09cd\u09aa\u09bf\u09df\u09a8! \u09e9\u09e6 \u09a6\u09bf\u09a8\u09c7\u09b0 "
            "\u09a7\u09be\u09b0\u09be! \u09aa\u09c1\u09b0\u09cb \u098f\u0995 \u09ae\u09be\u09b8 \u09b6\u09c7\u0996\u09be "
            "\u2014 \u09a4\u09cb\u09ae\u09be\u0995\u09c7 \u09a5\u09be\u09ae\u09be\u09a8\u09cb \u09af\u09be\u09df \u09a8\u09be!"
        ),
    },
}

_FALLBACK_LANGUAGE = "en"


def _pick(templates: list[str], index: int) -> str:
    """Select a template from the pool using modulo to stay in bounds.

    Args:
        templates: Non-empty list of message strings.
        index: Context-derived integer used as selection key.

    Returns:
        The selected message string.
    """
    return templates[index % len(templates)]


class EncouragementService:
    """Provides bilingual motivational messages for student interactions.

    All methods return non-empty strings. Unknown languages fall back to English.
    Selection is deterministic — no randomness is used.

    Example::

        svc = EncouragementService()
        msg = svc.get_correct_message(streak=7, language="bn")
    """

    def get_correct_message(self, streak: int, language: str) -> str:
        """Return a celebratory message after a correct answer.

        For streaks >= 7 the message highlights the streak count.

        Args:
            streak: Student's current streak (number of consecutive practice days).
            language: Preferred language code ('en' or 'bn').

        Returns:
            Formatted encouragement string in the requested language.
        """
        templates = _CORRECT_TEMPLATES.get(language, _CORRECT_TEMPLATES[_FALLBACK_LANGUAGE])
        if streak >= 7:
            pool = templates[3:]
            return _pick(pool, streak).format(streak=streak)
        pool = templates[:3]
        return _pick(pool, streak)

    async def _get_unique_message(
        self,
        db: AsyncSession,
        student_id: int,
        pool: list[str],
        prefix: str,
        default_idx: int,
        streak: int | None = None,
    ) -> str:
        """Select an unseen message variant and record it in SentMessage.

        Queries SentMessage rows for this student within the last 7 days to find
        which variants have been sent. Cycles to the first unseen variant; if all
        have been seen, falls back to the deterministic default_idx and records
        it anyway (repeat is acceptable after exhaustion).

        The row is flushed but not committed — the caller's transaction commit
        persists it. Trade-off: if the caller's transaction rolls back after this
        returns, the SentMessage row is lost and the variant may repeat on the
        next call. Callers should commit promptly after sending the message.

        Args:
            db: Async database session (within an open transaction).
            student_id: Student primary key for tracking.
            pool: Ordered list of message template strings.
            prefix: Key prefix used to identify this message type (e.g. 'correct_streak_low').
            default_idx: Fallback index when all variants have been seen recently.
            streak: If provided, substituted into '{streak}' placeholders in the text.

        Returns:
            Selected message string, formatted if applicable.
        """
        cutoff = datetime.now(UTC) - timedelta(days=7)
        result = await db.execute(
            select(SentMessage.message_key).where(
                SentMessage.student_id == student_id,
                SentMessage.sent_at >= cutoff,
                SentMessage.message_key.like(f"{prefix}_%"),
            )
        )
        recently_sent: set[str] = {row[0] for row in result.fetchall()}

        chosen_idx = default_idx
        for i in range(len(pool)):
            if f"{prefix}_{i}" not in recently_sent:
                chosen_idx = i
                break

        text = pool[chosen_idx]
        if streak is not None and "{streak}" in text:
            text = text.format(streak=streak)

        db.add(SentMessage(student_id=student_id, message_key=f"{prefix}_{chosen_idx}"))
        await db.flush()
        return text

    async def get_unique_correct_message(
        self,
        db: AsyncSession,
        student_id: int,
        streak: int,
        language: str,
    ) -> str:
        """Return a correct-answer message not sent to this student in the last 7 days.

        Delegates to _get_unique_message with the appropriate pool and prefix
        for the student's current streak level.

        Args:
            db: Async database session (within an open transaction).
            student_id: Student primary key for tracking.
            streak: Student's current streak for streak-aware variant selection.
            language: Preferred language code ('en' or 'bn').

        Returns:
            Encouragement string in the requested language.
        """
        templates = _CORRECT_TEMPLATES.get(language, _CORRECT_TEMPLATES[_FALLBACK_LANGUAGE])
        if streak >= 7:
            pool, prefix = templates[3:], "correct_streak_high"
        else:
            pool, prefix = templates[:3], "correct_streak_low"
        return await self._get_unique_message(
            db, student_id, pool, prefix, default_idx=streak % len(pool), streak=streak
        )

    async def get_unique_incorrect_message(
        self,
        db: AsyncSession,
        student_id: int,
        hints_used: int,
        language: str,
    ) -> str:
        """Return an incorrect-answer nudge not sent to this student in the last 7 days.

        Delegates to _get_unique_message with the incorrect-answer template pool.

        Args:
            db: Async database session (within an open transaction).
            student_id: Student primary key for tracking.
            hints_used: Number of hints already used (0-3).
            language: Preferred language code ('en' or 'bn').

        Returns:
            Supportive message string in the requested language.
        """
        templates = _INCORRECT_TEMPLATES.get(language, _INCORRECT_TEMPLATES[_FALLBACK_LANGUAGE])
        return await self._get_unique_message(
            db, student_id, templates, "incorrect", default_idx=hints_used % len(templates)
        )

    def get_incorrect_message(self, hints_used: int, language: str) -> str:
        """Return a supportive nudge after an incorrect answer.

        Args:
            hints_used: Number of hints the student has already used (0-3).
            language: Preferred language code ('en' or 'bn').

        Returns:
            Supportive message string in the requested language.
        """
        templates = _INCORRECT_TEMPLATES.get(language, _INCORRECT_TEMPLATES[_FALLBACK_LANGUAGE])
        return _pick(templates, hints_used)

    def get_session_start_message(
        self,
        grade: int,
        topics: list[str],
        language: str,
    ) -> str:
        """Return a session-start topic preview message.

        Args:
            grade: Student's grade level (6, 7, or 8).
            topics: List of topic names covered in today's session.
            language: Preferred language code ('en' or 'bn').

        Returns:
            Formatted session-start string in the requested language.
        """
        templates = _SESSION_START_TEMPLATES.get(
            language, _SESSION_START_TEMPLATES[_FALLBACK_LANGUAGE]
        )
        topics_str = ", ".join(topics) if topics else "General Practice"
        template = _pick(templates, grade)
        return template.format(grade=grade, topics=topics_str)

    def get_milestone_message(self, milestone_days: int, language: str) -> str:
        """Return a celebration message for a streak milestone.

        Supported milestones: 7, 14, 30.  Unknown milestones fall back to a
        generic message rather than raising an error.

        Args:
            milestone_days: The milestone reached (7, 14, or 30).
            language: Preferred language code ('en' or 'bn').

        Returns:
            Milestone celebration string in the requested language.
        """
        milestone_entry = _MILESTONE_MESSAGES.get(milestone_days)
        if milestone_entry is None:
            # Generic fallback for unrecognised milestones
            if language == "bn":
                return f"\U0001f3c6 {milestone_days} \u09a6\u09bf\u09a8\u09c7\u09b0 \u09a7\u09be\u09b0\u09be! \u0985\u09b8\u09be\u09a7\u09be\u09b0\u09a3!"
            return f"\U0001f3c6 {milestone_days}-day streak! Outstanding!"
        return milestone_entry.get(language, milestone_entry[_FALLBACK_LANGUAGE])

"""Integration tests for Telegram /practice command wiring.

Verifies that the webhook correctly routes Telegram commands to the
practice session handlers and returns appropriate bilingual responses.

PHASE3-B-4
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from src.models.problem import Problem
from src.models.session import Session, SessionStatus
from src.models.student import Student
from src.routes.webhook import (
    _active_sessions,
    _handle_message,
    _pending_topic_choice,
    handle_answer_message,
    handle_hint_command,
    handle_practice_command,
    handle_topic_choice,
)
from src.schemas.telegram import TelegramMessage

TELEGRAM_ID = 555444333
STUDENT_NAME = "PracticeTestUser"


def _make_message(text: str) -> TelegramMessage:
    """Create a TelegramMessage fixture.

    Args:
        text: Message text.

    Returns:
        TelegramMessage instance.
    """
    return TelegramMessage.model_validate(
        {
            "message_id": 42,
            "date": int(datetime.now(UTC).timestamp()),
            "chat": {"id": 999888777, "type": "private"},
            "from": {
                "id": TELEGRAM_ID,
                "is_bot": False,
                "first_name": STUDENT_NAME,
            },
            "text": text,
        }
    )


async def _create_student(db_session, language: str = "en") -> Student:
    """Create a test student.

    Args:
        db_session: Async SQLAlchemy session.
        language: 'en' or 'bn'.

    Returns:
        Created Student instance.
    """
    student = Student(
        telegram_id=TELEGRAM_ID,
        name=STUDENT_NAME,
        grade=7,
        language=language,
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)
    return student


async def _populate_problems(db_session, count: int = 5) -> list[Problem]:
    """Create test problems in the database.

    Args:
        db_session: Async SQLAlchemy session.
        count: Number of problems to create.

    Returns:
        List of created Problem instances.
    """
    for i in range(count):
        p = Problem(
            grade=7,
            topic=f"Topic {i}",
            question_en=f"What is {i} + {i}?",
            question_bn=f"{i} + {i} কত?",
            answer=str(i * 2),
            hints=[
                {
                    "hint_number": 1,
                    "text_en": f"Hint 1 for {i}",
                    "text_bn": f"প্রশ্ন {i} এর hint 1",
                    "is_ai_generated": False,
                },
                {
                    "hint_number": 2,
                    "text_en": f"Hint 2 for {i}",
                    "text_bn": f"প্রশ্ন {i} এর hint 2",
                    "is_ai_generated": False,
                },
                {
                    "hint_number": 3,
                    "text_en": f"Hint 3 for {i}",
                    "text_bn": f"প্রশ্ন {i} এর hint 3",
                    "is_ai_generated": False,
                },
            ],
            difficulty=(i % 3) + 1,
            estimated_time_minutes=5,
        )
        db_session.add(p)
    await db_session.commit()
    result = await db_session.execute(select(Problem).where(Problem.grade == 7).limit(count))
    return list(result.scalars().all())


@pytest.mark.integration
class TestPracticeCommandWiring:
    """Integration tests for /practice command via handle_practice_command."""

    async def test_practice_command_sends_topic_menu(self, db_session) -> None:
        """handle_practice_command returns a topic selection menu."""
        await _create_student(db_session)
        await _populate_problems(db_session, 5)

        _active_sessions.pop(TELEGRAM_ID, None)
        _pending_topic_choice.pop(TELEGRAM_ID, None)

        reply = await handle_practice_command(TELEGRAM_ID, db_session)

        assert reply is not None
        assert len(reply) > 0
        # Should show a numbered topic list
        assert "1." in reply

    async def test_practice_command_stores_session_after_topic_choice(self, db_session) -> None:
        """Session state is stored in _active_sessions after topic is chosen."""
        await _create_student(db_session)
        await _populate_problems(db_session, 5)

        _active_sessions.pop(TELEGRAM_ID, None)
        _pending_topic_choice.pop(TELEGRAM_ID, None)

        await handle_practice_command(TELEGRAM_ID, db_session)
        # Now pick topic 1
        await handle_topic_choice(TELEGRAM_ID, "1", db_session)

        assert TELEGRAM_ID in _active_sessions
        state = _active_sessions[TELEGRAM_ID]
        assert "session_id" in state
        assert "current_problem_id" in state

    async def test_practice_command_after_completed_shows_topic_menu(self, db_session) -> None:
        """After a completed session, /practice shows topic menu (not 'complete' gate)."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before _populate_problems commits
        await _populate_problems(db_session, 5)

        session = Session(
            student_id=student_id,
            date=datetime.now(UTC),
            status=SessionStatus.COMPLETED,
            problem_ids=[1, 2, 3, 4, 5],
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            completed_at=datetime.now(UTC),
        )
        db_session.add(session)
        await db_session.commit()

        _active_sessions.pop(TELEGRAM_ID, None)
        _pending_topic_choice.pop(TELEGRAM_ID, None)
        reply = await handle_practice_command(TELEGRAM_ID, db_session)

        # With topic-based flow, user always gets a topic menu (no hard "already done" gate)
        assert "1." in reply

    async def test_practice_command_unregistered_student(self, db_session) -> None:
        """handle_practice_command for unknown student returns register message."""
        _active_sessions.pop(TELEGRAM_ID, None)
        reply = await handle_practice_command(TELEGRAM_ID, db_session)

        assert "start" in reply.lower() or "নিবন্ধন" in reply


@pytest.mark.integration
class TestAnswerMessageWiring:
    """Integration tests for free-text answer message handling."""

    async def test_answer_message_evaluates(self, db_session) -> None:
        """Free-text answer message returns evaluation feedback."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before populate_problems expires student
        problems = await _populate_problems(db_session, 1)
        problem = problems[0]
        problem_id = problem.problem_id  # capture before commit expires problem

        session = Session(
            student_id=student_id,
            date=datetime.now(UTC),
            status=SessionStatus.IN_PROGRESS,
            problem_ids=[problem_id],
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        await db_session.refresh(problem)  # re-load problem after commit expires it

        # Set up active session state
        _active_sessions[TELEGRAM_ID] = {
            "session_id": session.session_id,
            "current_problem_id": problem_id,
            "topic": "",
        }

        reply = await handle_answer_message(TELEGRAM_ID, problem.answer, db_session)

        assert reply is not None
        # Should contain feedback
        assert len(reply) > 0

    async def test_answer_no_active_session(self, db_session) -> None:
        """Answer without active session returns 'no active practice' message."""
        await _create_student(db_session)
        _active_sessions.pop(TELEGRAM_ID, None)

        reply = await handle_answer_message(TELEGRAM_ID, "42", db_session)

        assert "practice" in reply.lower() or "অনুশীলন" in reply

    async def test_completing_session_sends_score(self, db_session) -> None:
        """Answering last problem triggers score summary in reply."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before populate_problems expires student
        problems = await _populate_problems(db_session, 1)  # Just 1 problem session
        problem = problems[0]
        problem_id = problem.problem_id  # capture before commit expires problem

        session = Session(
            student_id=student_id,
            date=datetime.now(UTC),
            status=SessionStatus.IN_PROGRESS,
            problem_ids=[problem_id],
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        await db_session.refresh(problem)  # re-load problem after commit expires it

        _active_sessions[TELEGRAM_ID] = {
            "session_id": session.session_id,
            "current_problem_id": problem_id,
            "topic": "",
        }

        reply = await handle_answer_message(TELEGRAM_ID, problem.answer, db_session)

        # Score summary should show concluded prompt
        assert "concluded" in reply.lower() or "শেষ" in reply
        # Should be removed from active sessions
        assert TELEGRAM_ID not in _active_sessions


@pytest.mark.integration
class TestHintCommandWiring:
    """Integration tests for /hint command handling."""

    async def test_hint_command_returns_hint(self, db_session) -> None:
        """handle_hint_command returns hint text from the DB."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before populate_problems expires student
        problems = await _populate_problems(db_session, 1)
        problem = problems[0]
        problem_id = problem.problem_id  # capture before commit expires problem

        session = Session(
            student_id=student_id,
            date=datetime.now(UTC),
            status=SessionStatus.IN_PROGRESS,
            problem_ids=[problem_id],
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        _active_sessions[TELEGRAM_ID] = {
            "session_id": session.session_id,
            "current_problem_id": problem_id,
        }

        reply = await handle_hint_command(TELEGRAM_ID, db_session)

        assert reply is not None
        assert "Hint 1" in reply or "hint" in reply.lower()

    async def test_hint_no_active_session(self, db_session) -> None:
        """handle_hint_command without active session returns error message."""
        await _create_student(db_session)
        _active_sessions.pop(TELEGRAM_ID, None)

        reply = await handle_hint_command(TELEGRAM_ID, db_session)

        assert "practice" in reply.lower() or "অনুশীলন" in reply


@pytest.mark.integration
class TestWebhookMessageRouting:
    """Tests for full _handle_message routing via webhook."""

    async def test_practice_command_via_handle_message(self, db_session) -> None:
        """_handle_message routes /practice to practice handler."""
        await _create_student(db_session)
        await _populate_problems(db_session, 5)

        _active_sessions.pop(TELEGRAM_ID, None)

        message = _make_message("/practice")

        with patch("src.routes.webhook.TelegramClient") as mock_tg_class:
            mock_tg = MagicMock()
            mock_tg.send_message = AsyncMock()
            mock_tg_class.return_value = mock_tg

            await _handle_message(message, db_session)

            # send_message should have been called
            mock_tg.send_message.assert_called_once()
            call_args = mock_tg.send_message.call_args
            sent_text = call_args[0][1] if call_args[0] else call_args[1].get("text", "")
            # Should contain a question
            assert len(sent_text) > 0

    async def test_hint_command_via_handle_message(self, db_session) -> None:
        """_handle_message routes /hint to hint handler."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before populate_problems expires student
        problems = await _populate_problems(db_session, 1)
        problem = problems[0]
        problem_id = problem.problem_id  # capture before commit expires problem

        session = Session(
            student_id=student_id,
            date=datetime.now(UTC),
            status=SessionStatus.IN_PROGRESS,
            problem_ids=[problem_id],
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        _active_sessions[TELEGRAM_ID] = {
            "session_id": session.session_id,
            "current_problem_id": problem_id,
        }

        message = _make_message("/hint")

        with patch("src.routes.webhook.TelegramClient") as mock_tg_class:
            mock_tg = MagicMock()
            mock_tg.send_message = AsyncMock()
            mock_tg_class.return_value = mock_tg

            await _handle_message(message, db_session)

            mock_tg.send_message.assert_called_once()

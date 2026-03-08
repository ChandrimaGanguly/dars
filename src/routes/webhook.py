"""Telegram webhook endpoint.

Security (SEC-002):
- Webhook is protected by X-Telegram-Bot-Api-Secret-Token verification
- All requests must include valid secret token
- Prevents unauthorized webhook calls

PHASE3-B-4: Adds /practice, /hint, and free-text answer routing.
"""

from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.telegram import verify_telegram_webhook
from src.database import get_session
from src.logging import get_logger
from src.models.response import Response
from src.models.session import Session, SessionStatus
from src.models.streak import Streak
from src.models.student import Student
from src.repositories import ProblemRepository, ResponseRepository, SessionRepository
from src.repositories.streak_repository import StreakRepository
from src.schemas.telegram import TelegramMessage, TelegramUpdate, WebhookResponse
from src.services import StudentService, TelegramClient
from src.services.answer_evaluator import AnswerEvaluator, EvaluationResult
from src.services.cost_tracker import CostTracker
from src.services.encouragement import EncouragementService
from src.services.hint_state import hint_generator as _hint_generator
from src.services.messages import MessageKey, get_message
from src.services.problem_selector import ProblemSelector
from src.utils.pii import hash_telegram_id, redact_answer

router = APIRouter()
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# In-memory session state for 50-student pilot (PHASE3-B-4.2)
# Maps telegram_id → {"session_id": int, "current_problem_id": int}
# ---------------------------------------------------------------------------
_active_sessions: dict[int, dict[str, int]] = {}

# ---------------------------------------------------------------------------
# Language selection pending state (PHASE7-A-1 / REQ-021)
# Maps telegram_id → True while awaiting "1"/"2"/"en"/"bn" reply
# ---------------------------------------------------------------------------
_pending_language_choice: dict[int, bool] = {}
# Cap matches _active_sessions to bound memory on the 50-student pilot
_PENDING_LANGUAGE_CAP: int = 200

# ---------------------------------------------------------------------------
# Onboarding state — multi-step /start flow (PHASE8)
# Maps telegram_id → {"stage": "grade"|"language", "name": str, "grade": int}
# ---------------------------------------------------------------------------
_pending_onboarding: dict[int, dict[str, Any]] = {}
_PENDING_ONBOARDING_CAP: int = 200

# ---------------------------------------------------------------------------
# Streak calendar constants (PHASE6-B-1 / REQ-010)
# ---------------------------------------------------------------------------
_MILESTONES: list[int] = [7, 14, 30]
_DAY_NAMES_EN: list[str] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_DAY_NAMES_BN: list[str] = ["সোম", "মঙ্গল", "বুধ", "বৃহ", "শুক্র", "শনি", "রবি"]


# ---------------------------------------------------------------------------
# Practice command handlers
# ---------------------------------------------------------------------------


async def handle_practice_command(telegram_id: int, db: AsyncSession) -> str:
    """Handle /practice Telegram command.

    Runs the full problem selection flow for the student, stores state in
    _active_sessions, and returns the first problem as a formatted string.

    Args:
        telegram_id: Telegram user ID.
        db: Async database session.

    Returns:
        Formatted message string for the Telegram user.
    """
    # Fetch student
    result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
    student = result.scalar_one_or_none()
    if student is None:
        return get_message(MessageKey.REGISTER_FIRST, "en")

    problem_repo = ProblemRepository()
    session_repo = SessionRepository()
    response_repo = ResponseRepository()

    # Expire stale sessions
    await session_repo.expire_stale_sessions(db)

    # Check for existing session
    existing = await session_repo.get_active_session_for_today(db, student.student_id)

    if existing is not None and existing.status == SessionStatus.COMPLETED:
        # Already done today
        return get_message(MessageKey.ALREADY_COMPLETED, student.language)

    if existing is not None and existing.status == SessionStatus.IN_PROGRESS:
        # Resume existing session
        answered_ids = await response_repo.get_answered_problem_ids(db, existing.session_id)
        remaining_ids = [pid for pid in existing.problem_ids if pid not in answered_ids]
        if not remaining_ids:
            # All answered but not marked complete — edge case
            await session_repo.mark_session_complete(db, existing)
            await db.commit()
            return get_message(MessageKey.ALREADY_COMPLETED, student.language)

        problems = await problem_repo.get_problems_by_ids(db, remaining_ids)
        first_problem = problems[0]

        _active_sessions[telegram_id] = {
            "session_id": existing.session_id,
            "current_problem_id": first_problem.problem_id,
        }

        return _format_problem_message(first_problem, student.language, len(remaining_ids))

    # Start new session
    selector = ProblemSelector(problem_repo, response_repo)
    selected_problems = await selector.select_problems(db, student.student_id, student.grade)

    if not selected_problems:
        return get_message(MessageKey.NO_PROBLEMS_FOUND, student.language)

    problem_ids = [p.problem_id for p in selected_problems]
    first_problem_id = problem_ids[0]
    student_language = student.language
    num_selected = len(selected_problems)
    session = await session_repo.create_session(db, student.student_id, problem_ids)
    new_session_id = session.session_id  # capture before commit expires session
    await db.commit()

    _active_sessions[telegram_id] = {
        "session_id": new_session_id,
        "current_problem_id": first_problem_id,
    }

    logger.info(
        "Telegram /practice session started",
        hashed_telegram_id=hash_telegram_id(telegram_id),
        session_id=new_session_id,
    )

    first_problem_fetched = await problem_repo.get_problem_by_id(db, first_problem_id)
    if first_problem_fetched is None:
        return get_message(MessageKey.NO_PROBLEMS_FOUND, student_language)
    return _format_problem_message(first_problem_fetched, student_language, num_selected)


async def handle_answer_message(telegram_id: int, text: str, db: AsyncSession) -> str:
    """Handle a free-text answer from a student in an active practice session.

    Args:
        telegram_id: Telegram user ID.
        text: The raw message text (student's answer).
        db: Async database session.

    Returns:
        Formatted feedback message (with next problem if applicable).
    """
    state = _active_sessions.get(telegram_id)
    if state is None:
        lang_result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
        lang_student = lang_result.scalar_one_or_none()
        return get_message(
            MessageKey.NO_ACTIVE_SESSION, lang_student.language if lang_student else "en"
        )

    session_id = state["session_id"]
    current_problem_id = state["current_problem_id"]

    # Fetch student
    result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
    student = result.scalar_one_or_none()
    if student is None:
        _active_sessions.pop(telegram_id, None)
        return get_message(MessageKey.ERROR_STUDENT_NOT_FOUND, "en")

    problem_repo = ProblemRepository()
    session_repo = SessionRepository()
    response_repo = ResponseRepository()

    session = await session_repo.get_session_by_id(db, session_id)
    if session is None or session.is_expired():
        _active_sessions.pop(telegram_id, None)
        return get_message(MessageKey.SESSION_EXPIRED, student.language)

    problem = await problem_repo.get_problem_by_id(db, current_problem_id)
    if problem is None:
        _active_sessions.pop(telegram_id, None)
        return get_message(MessageKey.ERROR_PROBLEM_NOT_FOUND, student.language)

    existing_response = await response_repo.get_response_for_problem(
        db, session_id, current_problem_id
    )
    hints_used = existing_response.hints_used if existing_response else 0

    evaluator = AnswerEvaluator()
    eval_result = evaluator.evaluate(problem, text, hints_used)

    logger.info(
        "Telegram answer evaluated",
        hashed_telegram_id=hash_telegram_id(telegram_id),
        problem_id=current_problem_id,
        redacted_answer=redact_answer(text),
        is_correct=eval_result.is_correct,
    )

    # Persist response (if not already answered by this student)
    await _persist_answer_response(
        db,
        response_repo,
        session_repo,
        session,
        existing_response,
        session_id,
        current_problem_id,
        text,
        eval_result,
    )

    feedback = eval_result.feedback_bn if student.language == "bn" else eval_result.feedback_en

    # Determine next problem
    answered_ids = await response_repo.get_answered_problem_ids(db, session_id)
    remaining_ids = [pid for pid in session.problem_ids if pid not in answered_ids]

    if not remaining_ids:
        # Session complete
        await session_repo.mark_session_complete(db, session)
        correct = session.problems_correct  # capture before commit
        total = len(session.problem_ids)  # capture before commit
        student_language = student.language  # capture before commit
        student_id_int = student.student_id  # capture before commit

        # Record streak practice (flush inside, commit below covers it)
        _, new_milestones = await StreakRepository().record_practice(
            db, student_id_int, date.today()
        )

        # Build milestone messages before commit
        milestone_msg = ""
        if new_milestones:
            enc = EncouragementService()
            milestone_msg = "\n" + "\n".join(
                enc.get_milestone_message(m, student_language) for m in new_milestones
            )

        await db.commit()
        _active_sessions.pop(telegram_id, None)

        if student_language == "bn":
            return (
                f"{feedback}\n\n"
                f"অনুশীলন শেষ! তুমি {total}টির মধ্যে {correct}টি সঠিক করেছ। "
                f"\U0001f3c6 কাল আবার এসো!{milestone_msg}"
            )
        return (
            f"{feedback}\n\n"
            f"Practice complete! You got {correct}/{total} correct. "
            f"\U0001f3c6 See you tomorrow!{milestone_msg}"
        )

    # Move to next problem
    next_problem_id = remaining_ids[0]
    student_language = student.language  # capture before commit
    next_problem = await problem_repo.get_problem_by_id(db, next_problem_id)
    await db.commit()

    _active_sessions[telegram_id] = {
        "session_id": session_id,
        "current_problem_id": next_problem_id,
    }

    if next_problem is None:
        return feedback

    await db.refresh(next_problem)  # re-load expired object after commit
    remaining_count = len(remaining_ids)
    return f"{feedback}\n\n" + _format_problem_message(
        next_problem, student_language, remaining_count
    )


async def handle_hint_command(telegram_id: int, db: AsyncSession) -> str:
    """Handle /hint Telegram command.

    Requests the next available hint for the current problem.

    Args:
        telegram_id: Telegram user ID.
        db: Async database session.

    Returns:
        Hint text or an error message.
    """
    state = _active_sessions.get(telegram_id)
    if state is None:
        lang_result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
        lang_student = lang_result.scalar_one_or_none()
        return get_message(
            MessageKey.NO_ACTIVE_SESSION, lang_student.language if lang_student else "en"
        )

    session_id = state["session_id"]
    current_problem_id = state["current_problem_id"]

    # Fetch student
    result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
    student = result.scalar_one_or_none()
    if student is None:
        return get_message(MessageKey.ERROR_STUDENT_NOT_FOUND, "en")

    problem_repo = ProblemRepository()
    session_repo = SessionRepository()
    response_repo = ResponseRepository()

    session = await session_repo.get_session_by_id(db, session_id)
    if session is None or session.is_expired():
        _active_sessions.pop(telegram_id, None)
        return get_message(MessageKey.SESSION_EXPIRED, student.language)

    problem = await problem_repo.get_problem_by_id(db, current_problem_id)
    if problem is None:
        return get_message(MessageKey.ERROR_PROBLEM_NOT_FOUND, student.language)

    existing_response = await response_repo.get_response_for_problem(
        db, session_id, current_problem_id
    )
    hints_already_used = existing_response.hints_used if existing_response else 0

    if hints_already_used >= 3:
        return get_message(MessageKey.HINTS_EXHAUSTED, student.language)

    next_hint_number = hints_already_used + 1

    # Capture primitives before any await that could expire ORM objects
    student_id = student.student_id
    student_language = student.language

    # Generate hint via AI (with cache + fallback) — PHASE5-B-2
    hint_text, is_ai, in_tok, out_tok = await _hint_generator.get_hint(
        db=db,
        problem=problem,
        student_answer="",
        hint_number=next_hint_number,
        student_id=student_id,
        language=student_language,
    )

    # Create or update response with hint count (idempotent — only on new level)
    if existing_response is None:
        existing_response = await response_repo.create_response(
            db=db,
            session_id=session_id,
            problem_id=current_problem_id,
            student_answer="",
            is_correct=False,
            hints_used=0,
            time_spent_seconds=0,
            confidence_level="high",
        )

    if next_hint_number > hints_already_used:
        hint_dict = {
            "text_en": hint_text if student_language == "en" else "",
            "text_bn": hint_text if student_language == "bn" else "",
        }
        await response_repo.update_hint_count(db, existing_response, next_hint_number, hint_dict)

    # Record cost
    cost_tracker = CostTracker()
    await cost_tracker.record_hint_cost(
        db,
        student_id,
        session_id,
        next_hint_number,
        is_ai_generated=is_ai,
        input_tokens=in_tok,
        output_tokens=out_tok,
    )
    await cost_tracker.check_budget_alert(db, student_id)

    await db.commit()

    remaining = 3 - next_hint_number
    if student_language == "bn":
        return f"Hint {next_hint_number}: {hint_text}\n(আরও {remaining}টি hint বাকি আছে)"
    return f"Hint {next_hint_number}: {hint_text}\n({remaining} hints remaining)"


def _format_streak_message(
    streak: Streak | None,
    last_7_days: list[date],
    language: str,
) -> str:
    """Format streak data into a Telegram-friendly calendar view.

    Renders current/longest streak, a 7-day ●/○ calendar, and the next
    milestone countdown. Handles zero-streak and all-milestones-achieved
    edge cases.

    Args:
        streak: Streak ORM object, or None if student has no streak row yet.
        last_7_days: Dates (UTC) when student practiced in the last 7 days.
        language: 'en' or 'bn'.

    Returns:
        Formatted multi-line message string.
    """
    current = streak.current_streak if streak is not None else 0
    longest = streak.longest_streak if streak is not None else 0

    if current == 0:
        if language == "bn":
            return "\U0001f4da প্রথম ধারা শুরু করো! আজকের অনুশীলন সম্পন্ন করো।"
        return (
            "\U0001f4da Start your first streak! Complete today's practice to begin your journey."
        )

    # Build 7-day calendar — use UTC date explicitly (Fix 1)
    today = datetime.now(UTC).date()
    practiced_set: set[date] = set(last_7_days)
    day_names = _DAY_NAMES_BN if language == "bn" else _DAY_NAMES_EN
    calendar_parts: list[str] = []
    for offset in range(6, -1, -1):
        d = today - timedelta(days=offset)
        dot = "\u25cf" if d in practiced_set else "\u25cb"
        name = day_names[d.weekday()]
        calendar_parts.append(f"{name} {dot}")
    calendar_row = "  ".join(calendar_parts)

    # Next milestone
    next_milestone = next((m for m in _MILESTONES if m > current), None)

    if language == "bn":
        # Literal Bengali Unicode — readable and spot-checkable without a decoder
        # Note: দীর্ঘতম (longest) corrected from original \u09a6\u09c0\u09b0\u09cd\u09a6\u09a4\u09ae (দীর্দতম, a typo)
        header = f"🔥 বর্তমান ধারা: {current} দিন\n⭐ দীর্ঘতম ধারা: {longest} দিন"
        cal_header = "\n\n📅 গত ৭ দিন:\n"  # noqa: RUF001 — Bengali digit 7 is intentional
        if next_milestone is not None:
            days_away = next_milestone - current
            milestone_line = (
                f"\n\n🎯 পরবর্তী মাইলস্টোন: {next_milestone} দিন ({days_away} দিন বাকি!)"
            )
        else:
            milestone_line = "\n\n🏆 সব মাইলস্টোন অর্জিত!"
    else:
        header = f"🔥 Current Streak: {current} days\n⭐ Longest Streak: {longest} days"
        cal_header = "\n\n📅 Last 7 Days:\n"
        if next_milestone is not None:
            days_away = next_milestone - current
            milestone_line = (
                f"\n\n🎯 Next Milestone: {next_milestone} days ({days_away} days away!)"
            )
        else:
            milestone_line = "\n\n🏆 All milestones achieved!"

    return header + cal_header + calendar_row + milestone_line


async def handle_streak_command(telegram_id: int, db: AsyncSession) -> str:
    """Handle /streak Telegram command — formatted calendar view.

    Fetches the student's streak data and the last 7 practice days, then
    returns a human-readable calendar view (REQ-010).

    Args:
        telegram_id: Telegram user ID.
        db: Async database session.

    Returns:
        Formatted streak message string.
    """
    result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
    student = result.scalar_one_or_none()
    if student is None:
        # Fix 3: bilingual — language unknown for unregistered users
        return (
            "Student not found. Please type /start to register.\n"
            "আপনাকে খুঁজে পাওয়া যাচ্ছে না। /start লিখে নিবন্ধন করুন।"
        )

    streak_repo = StreakRepository()
    streak = await streak_repo.get_for_student(db, student.student_id)
    # Skip get_last_7_days on zero-streak path — _format_streak_message doesn't use it
    current = streak.current_streak if streak else 0
    last_7_days = await streak_repo.get_last_7_days(db, student.student_id) if current > 0 else []

    logger.info(
        "Handled /streak",
        hashed_telegram_id=hash_telegram_id(telegram_id),
        current_streak=streak.current_streak if streak else 0,
    )
    return _format_streak_message(streak, last_7_days, student.language)


async def handle_unknown_message(telegram_id: int, text: str, student_language: str = "en") -> str:
    """Return a helpful response for unknown commands.

    Args:
        telegram_id: Telegram user ID.
        text: The raw message text.
        student_language: 'bn' or 'en'.

    Returns:
        Help message string.
    """
    return get_message(MessageKey.UNKNOWN_COMMAND, student_language)


# ---------------------------------------------------------------------------
# Onboarding flow handlers (PHASE8 / multi-step /start)
# ---------------------------------------------------------------------------


async def handle_start_new_student(telegram_id: int, name: str) -> str:
    """Begin onboarding for a new student — ask for grade.

    Stores pending state and returns the grade prompt.

    Args:
        telegram_id: Telegram user ID.
        name: Student's first name from Telegram profile.

    Returns:
        Grade selection prompt (bilingual).
    """
    if len(_pending_onboarding) >= _PENDING_ONBOARDING_CAP:
        oldest = next(iter(_pending_onboarding))
        del _pending_onboarding[oldest]
    _pending_onboarding[telegram_id] = {"stage": "grade", "name": name}
    return get_message(MessageKey.ONBOARDING_GRADE_PROMPT, "en")


async def handle_onboarding_reply(telegram_id: int, text: str, db: AsyncSession) -> str:
    """Handle a reply during the multi-step onboarding flow.

    Stage "grade": expects "6", "7", or "8" → advances to "language".
    Stage "language": expects "1"/"2"/"en"/"bn" → creates student, done.

    Args:
        telegram_id: Telegram user ID.
        text: Raw message text.
        db: Async database session.

    Returns:
        Next prompt, confirmation, or error message.
    """
    state = _pending_onboarding.get(telegram_id)
    if state is None:
        return get_message(MessageKey.ERROR_GENERIC, "en")

    stage = state["stage"]
    name = state["name"]

    if stage == "grade":
        cleaned = text.strip()
        if cleaned not in ("6", "7", "8"):
            return get_message(MessageKey.ONBOARDING_INVALID_GRADE, "en")
        _pending_onboarding[telegram_id] = {
            "stage": "language",
            "name": name,
            "grade": int(cleaned),
        }
        return get_message(MessageKey.LANGUAGE_PROMPT, "en")

    # stage == "language"
    grade = int(state.get("grade", 7))
    lang_map = {"1": "en", "2": "bn", "en": "en", "bn": "bn"}
    language = lang_map.get(text.strip().lower())
    if language is None:
        return get_message(MessageKey.LANGUAGE_INVALID, "en")

    # Create the student with collected preferences
    student_service = StudentService()
    student = await student_service.get_or_create(
        db, telegram_id, name, grade=grade, language=language
    )
    _pending_onboarding.pop(telegram_id, None)

    return get_message(MessageKey.ONBOARDING_COMPLETE, student.language, name=student.name)


# ---------------------------------------------------------------------------
# Language command handlers (PHASE7-A-1 / REQ-021)
# ---------------------------------------------------------------------------


async def handle_language_command(telegram_id: int, db: AsyncSession) -> str:
    """Handle /language Telegram command — show bilingual language selection prompt.

    Sets `_pending_language_choice[telegram_id] = True` to signal that the
    next message from this user is a language selection reply.

    Args:
        telegram_id: Telegram user ID.
        db: Async database session.

    Returns:
        Language selection prompt string.
    """
    result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
    student = result.scalar_one_or_none()
    if student is None:
        return get_message(MessageKey.REGISTER_FIRST, "en")
    # Evict oldest entry when cap reached (DoS guard)
    if len(_pending_language_choice) >= _PENDING_LANGUAGE_CAP:
        oldest = next(iter(_pending_language_choice))
        del _pending_language_choice[oldest]
    _pending_language_choice[telegram_id] = True
    return get_message(MessageKey.LANGUAGE_PROMPT, student.language)


async def handle_language_choice(telegram_id: int, text: str, db: AsyncSession) -> str:
    """Handle a language selection reply ("1", "2", "en", "bn").

    Validates input, updates student.language in the DB, clears the pending
    state, and confirms in the *new* language.  Invalid input re-prompts once
    (leaves pending state active for the next message).

    Args:
        telegram_id: Telegram user ID.
        text: Raw message text from the student.
        db: Async database session.

    Returns:
        Confirmation message in the newly selected language, or a re-prompt.
    """
    result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
    student = result.scalar_one_or_none()
    if student is None:
        _pending_language_choice.pop(telegram_id, None)
        return get_message(MessageKey.REGISTER_FIRST, "en")

    normalized = text.strip().lower()
    if normalized in ("1", "en", "english"):
        new_language = "en"
    elif normalized in ("2", "bn", "bengali", "বাংলা"):
        new_language = "bn"
    else:
        # Invalid — leave pending state active for one more try
        return get_message(MessageKey.LANGUAGE_INVALID, student.language)

    student.language = new_language
    await db.flush()
    await db.commit()
    await db.refresh(student)

    _pending_language_choice.pop(telegram_id, None)
    logger.info(
        "Language updated",
        hashed_telegram_id=hash_telegram_id(telegram_id),
        new_language=new_language,
    )

    key = (
        MessageKey.LANGUAGE_CONFIRMED_EN
        if new_language == "en"
        else MessageKey.LANGUAGE_CONFIRMED_BN
    )
    return get_message(key, new_language)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


async def _persist_answer_response(
    db: AsyncSession,
    response_repo: ResponseRepository,
    session_repo: SessionRepository,
    session: Session,
    existing_response: Response | None,
    session_id: int,
    problem_id: int,
    student_answer: str,
    eval_result: EvaluationResult,
) -> None:
    """Persist an answer response and update the session correct count.

    Creates a new Response row if none exists for this problem, or updates
    the stub response created during hint delivery. Increments the session
    correct count only once per correct answer.

    Args:
        db: Async database session.
        response_repo: ResponseRepository instance.
        session_repo: SessionRepository instance.
        session: Current Session ORM object.
        existing_response: Existing Response row for this problem (or None).
        session_id: Session primary key.
        problem_id: Problem primary key.
        student_answer: Raw answer text.
        eval_result: Result from AnswerEvaluator.evaluate().
    """
    if existing_response is not None and existing_response.student_answer:
        # Already answered — idempotent, do nothing
        return

    if existing_response is None:
        await response_repo.create_response(
            db=db,
            session_id=session_id,
            problem_id=problem_id,
            student_answer=student_answer,
            is_correct=eval_result.is_correct,
            hints_used=0,
            time_spent_seconds=0,
            confidence_level=eval_result.confidence_level,
        )
    else:
        # Update stub response created by earlier hint delivery
        existing_response.student_answer = student_answer
        existing_response.is_correct = eval_result.is_correct
        existing_response.confidence_level = eval_result.confidence_level
        await db.flush()

    if eval_result.is_correct:
        await session_repo.increment_correct_count(db, session)


def _format_problem_message(
    problem: "Problem",  # type: ignore[name-defined]  # noqa: F821
    language: str,
    remaining: int,
) -> str:
    """Format a problem as a Telegram message string.

    Args:
        problem: Problem ORM instance.
        language: Student's preferred language ('bn' or 'en').
        remaining: Number of problems remaining (including this one).

    Returns:
        Formatted question string.
    """
    question = problem.question_bn if language == "bn" else problem.question_en

    difficulty_labels = {
        1: ("সহজ", "Easy"),
        2: ("মাঝারি", "Medium"),
        3: ("কঠিন", "Hard"),
    }
    diff_bn, diff_en = difficulty_labels.get(problem.difficulty, ("মাঝারি", "Medium"))
    diff_label = diff_bn if language == "bn" else diff_en

    if language == "bn":
        return (
            f"\U0001f4da প্রশ্ন ({remaining}টি বাকি) [{diff_label}]\n\n"
            f"{question}\n\n"
            f"উত্তর পাঠাও, অথবা hint এর জন্য /hint লেখো।"
        )
    return (
        f"\U0001f4da Question ({remaining} remaining) [{diff_label}]\n\n"
        f"{question}\n\n"
        f"Send your answer, or type /hint for a hint."
    )


# ---------------------------------------------------------------------------
# Main webhook route
# ---------------------------------------------------------------------------


@router.post("/webhook", response_model=WebhookResponse, tags=["Telegram"])
async def telegram_webhook(
    update: TelegramUpdate,
    _authenticated: bool = Depends(verify_telegram_webhook),
    db: AsyncSession = Depends(get_session),
) -> WebhookResponse:
    """Receive and process Telegram bot updates.

    Routes messages to the appropriate handler:
    - /start → student registration
    - /practice → start or resume a practice session
    - /hint → request a hint for the current problem
    - Free text → answer evaluation if in active session

    Security (SEC-002):
    - Requires X-Telegram-Bot-Api-Secret-Token header
    - Token must match TELEGRAM_SECRET_TOKEN environment variable
    - Returns 401 if missing or invalid

    Args:
        update: Telegram update object.
        _authenticated: Authentication dependency (injected by FastAPI).
        db: Database session (injected by FastAPI).

    Returns:
        WebhookResponse confirming processing.
    """
    logger.info("Received Telegram update", update_id=update.update_id)

    message_id: int | None = None
    try:
        if update.message and update.message.text:
            await _handle_message(update.message, db)
            message_id = update.message.message_id
    except Exception as e:
        logger.error("Error processing message", error=str(e), exc_info=True)
        # Still return 200 to avoid Telegram retrying endlessly

    return WebhookResponse(status="ok", message_id=message_id)


async def _handle_message(message: TelegramMessage, db: AsyncSession) -> None:
    """Route a Telegram message to the correct handler.

    Args:
        message: Telegram message object.
        db: Database session.
    """
    text = message.text or ""
    chat_id = message.chat.id
    telegram_id = message.from_.id
    first_name = message.from_.first_name

    telegram = TelegramClient()

    # Fetch student language for localisation (default 'en' if not registered)
    result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
    existing_student = result.scalar_one_or_none()
    student_language = existing_student.language if existing_student else "en"

    if text.startswith("/start"):
        # Cancel any pending flows
        _pending_language_choice.pop(telegram_id, None)
        _pending_onboarding.pop(telegram_id, None)

        if existing_student:
            # Returning student — show welcome message
            welcome_msg = get_message(
                MessageKey.WELCOME, existing_student.language, name=existing_student.name
            )
            await telegram.send_message(chat_id, welcome_msg)
        else:
            # New student — begin multi-step onboarding
            reply = await handle_start_new_student(telegram_id, first_name)
            await telegram.send_message(chat_id, reply)

        logger.info(
            "Handled /start",
            hashed_telegram_id=hash_telegram_id(telegram_id),
            is_new=existing_student is None,
        )

    elif _pending_onboarding.get(telegram_id):
        reply = await handle_onboarding_reply(telegram_id, text, db)
        await telegram.send_message(chat_id, reply)
        logger.info(
            "Handled onboarding reply",
            hashed_telegram_id=hash_telegram_id(telegram_id),
        )

    elif text.startswith("/practice"):
        _pending_language_choice.pop(telegram_id, None)
        reply = await handle_practice_command(telegram_id, db)
        await telegram.send_message(chat_id, reply)
        logger.info(
            "Handled /practice",
            hashed_telegram_id=hash_telegram_id(telegram_id),
        )

    elif text.startswith("/hint"):
        _pending_language_choice.pop(telegram_id, None)
        reply = await handle_hint_command(telegram_id, db)
        await telegram.send_message(chat_id, reply)
        logger.info(
            "Handled /hint",
            hashed_telegram_id=hash_telegram_id(telegram_id),
        )

    elif text.startswith("/streak"):
        _pending_language_choice.pop(telegram_id, None)
        reply = await handle_streak_command(telegram_id, db)
        await telegram.send_message(chat_id, reply)

    elif _pending_language_choice.get(telegram_id):
        reply = await handle_language_choice(telegram_id, text, db)
        await telegram.send_message(chat_id, reply)
        logger.info(
            "Handled language choice",
            hashed_telegram_id=hash_telegram_id(telegram_id),
        )

    elif text.startswith("/language"):
        reply = await handle_language_command(telegram_id, db)
        await telegram.send_message(chat_id, reply)
        logger.info(
            "Handled /language",
            hashed_telegram_id=hash_telegram_id(telegram_id),
        )

    elif telegram_id in _active_sessions:
        # Free-text message in active session → treat as answer
        reply = await handle_answer_message(telegram_id, text, db)
        await telegram.send_message(chat_id, reply)
        logger.info(
            "Handled answer",
            hashed_telegram_id=hash_telegram_id(telegram_id),
        )

    else:
        # Unknown command / no active session
        reply = await handle_unknown_message(telegram_id, text, student_language)
        await telegram.send_message(chat_id, reply)
        logger.info(
            "Unknown message",
            hashed_telegram_id=hash_telegram_id(telegram_id),
        )

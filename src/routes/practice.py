"""Practice session endpoints.

Implements the complete practice session lifecycle:
- GET /practice — select 5 problems (or resume existing session)
- POST /practice/{problem_id}/answer — evaluate and persist an answer
- POST /practice/{problem_id}/hint — deliver a pre-written hint from the DB

Security (SEC-003, SEC-005):
- All endpoints require student authentication (SEC-003)
- Hint endpoint rate limited to 10 requests/day per student (SEC-005)
- Basic 403/404/410 ownership and expiry checks on every write endpoint

PHASE3-B-3
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.student import verify_student
from src.database import get_session
from src.logging import get_logger
from src.models.student import Student
from src.repositories import ProblemRepository, ResponseRepository, SessionRepository
from src.repositories.streak_repository import StreakRepository
from src.schemas.practice import (
    AnswerRequest,
    AnswerResponse,
    HintRequest,
    HintResponse,
    PracticeResponse,
    ProblemWithoutAnswer,
)
from src.services.answer_evaluator import AnswerEvaluator
from src.services.cost_tracker import CostTracker
from src.services.encouragement import EncouragementService
from src.services.hint_state import hint_generator as _hint_generator
from src.services.problem_selector import ProblemSelector
from src.utils.pii import hash_telegram_id, redact_answer

router = APIRouter()
logger = get_logger(__name__)


# Rate limiter key function for student-specific limiting (SEC-005)
def get_student_rate_limit_key(request: Request) -> str:
    """Rate limit key based on student ID (not IP).

    Returns:
        Rate limit key in format: "student:{telegram_id}"
    """
    student_id = request.headers.get("X-Student-ID", "unknown")
    return f"student:{student_id}"


# Rate limiter instance (SEC-005) - uses student ID, not IP
limiter = Limiter(key_func=get_student_rate_limit_key)


async def _get_student_by_telegram_id(db: AsyncSession, telegram_id: int) -> Student:
    """Fetch Student row by telegram_id.

    Args:
        db: Async database session.
        telegram_id: The telegram ID returned by verify_student.

    Returns:
        Student instance.

    Raises:
        HTTPException: 404 if not found (should not happen after verify_student).
    """
    result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


def _cached_answer_response(
    existing_response: "Response",  # type: ignore[name-defined]  # noqa: F821
    session: "Session",  # type: ignore[name-defined]  # noqa: F821
    next_id: int | None,
    language: str,
) -> AnswerResponse:
    """Return a cached AnswerResponse for a problem the student already answered.

    Args:
        existing_response: The already-persisted Response row.
        session: The practice Session (for problem ordering).
        next_id: Next unanswered problem ID (or None if session complete).
        language: Student's preferred language ('en' or 'bn').

    Returns:
        AnswerResponse with cached correctness and language-appropriate feedback.
    """
    if language == "bn":
        feedback = (
            "সঠিক! \u2705 শাবাশ!"
            if existing_response.is_correct
            else "ঠিক হয়নি। আবার চেষ্টা করো বা hint চাও।"
        )
    else:
        feedback = (
            "Correct! \u2705 Well done!"
            if existing_response.is_correct
            else "Not quite. Try again or ask for a hint."
        )
    return AnswerResponse(
        is_correct=existing_response.is_correct,
        feedback_text=feedback,
        next_problem_id=next_id,
    )


def _problem_to_schema(problem: "Problem") -> ProblemWithoutAnswer:  # type: ignore[name-defined]  # noqa: F821
    """Convert a Problem ORM instance to the API schema (no answer included).

    Args:
        problem: Problem ORM instance.

    Returns:
        ProblemWithoutAnswer schema.
    """
    answer_type = getattr(problem, "answer_type", "numeric") or "numeric"
    mc_options = getattr(problem, "multiple_choice_options", None)

    return ProblemWithoutAnswer(
        problem_id=problem.problem_id,
        grade=problem.grade,
        topic=problem.topic,
        question_en=problem.question_en,
        question_bn=problem.question_bn,
        difficulty=problem.difficulty,
        answer_type=answer_type,
        multiple_choice_options=mc_options,
    )


@router.get("/practice", response_model=PracticeResponse, tags=["Student Practice"])
async def get_practice_problems(
    student_id: int = Depends(verify_student),  # SEC-003: Database verification
    db: AsyncSession = Depends(get_session),
) -> PracticeResponse:
    """Get daily practice problems.

    Returns 5 problems for the student's daily practice session.
    Resumes an existing IN_PROGRESS session or returns an already-COMPLETED
    session summary if the student has already finished today.

    Security (SEC-003):
    - Student must be authenticated via X-Student-ID header
    - Student existence verified in database (prevents IDOR)

    Args:
        student_id: Verified student telegram ID (from dependency).
        db: Database session (from dependency).

    Returns:
        PracticeResponse with selected problems and session metadata.

    Raises:
        HTTPException: If student not found or problem selection fails.
    """
    student = await _get_student_by_telegram_id(db, student_id)

    problem_repo = ProblemRepository()
    session_repo = SessionRepository()
    response_repo = ResponseRepository()

    # Expire any stale sessions first
    await session_repo.expire_stale_sessions(db)

    hashed_tid = hash_telegram_id(student_id)

    # Check for existing session today
    existing = await session_repo.get_active_session_for_today(db, student.student_id)

    if existing is not None:
        from src.models.session import SessionStatus

        if existing.status == SessionStatus.COMPLETED:
            logger.info(
                "Student already completed practice today",
                hashed_telegram_id=hashed_tid,
            )
            return PracticeResponse(
                session_id=existing.session_id,
                problems=[],
                problem_count=0,
                expires_at=existing.expires_at,
                session_start_message=None,
            )

        if existing.status == SessionStatus.IN_PROGRESS:
            # Resume: return only unanswered problems
            answered_ids = await response_repo.get_answered_problem_ids(db, existing.session_id)
            remaining_ids = [pid for pid in existing.problem_ids if pid not in answered_ids]
            remaining_problems = await problem_repo.get_problems_by_ids(db, remaining_ids)
            logger.info(
                "Resuming mid-session",
                hashed_telegram_id=hashed_tid,
                remaining=len(remaining_problems),
            )
            return PracticeResponse(
                session_id=existing.session_id,
                problems=[_problem_to_schema(p) for p in remaining_problems],
                problem_count=len(remaining_problems),
                expires_at=existing.expires_at,
                session_start_message=None,
            )

    # No existing session — run selection algorithm with adaptive difficulty
    difficulty_level = student.difficulty_level  # REQ-004: read before commit expires attrs
    selector = ProblemSelector(problem_repo, response_repo)
    selected_problems = await selector.select_problems(
        db, student.student_id, student.grade, difficulty_level=difficulty_level
    )

    if not selected_problems:
        raise HTTPException(
            status_code=404,
            detail="No problems found for your grade level. Please contact your teacher.",
        )

    # Build session-start encouragement message
    topics = list({p.topic for p in selected_problems})
    student_language = student.language
    start_message = EncouragementService().get_session_start_message(
        grade=student.grade, topics=topics, language=student_language
    )

    # Create new session
    problem_ids = [p.problem_id for p in selected_problems]
    session = await session_repo.create_session(db, student.student_id, problem_ids)
    # Capture values before commit (commit expires ORM attributes)
    new_session_id = session.session_id
    new_expires_at = session.expires_at
    await db.commit()

    logger.info(
        "Created new practice session",
        hashed_telegram_id=hashed_tid,
        session_id=new_session_id,
        problem_count=len(selected_problems),
        difficulty_level=difficulty_level,
    )

    return PracticeResponse(
        session_id=new_session_id,
        problems=[_problem_to_schema(p) for p in selected_problems],
        problem_count=len(selected_problems),
        expires_at=new_expires_at,
        session_start_message=start_message,
    )


@router.post(
    "/practice/{problem_id}/answer",
    response_model=AnswerResponse,
    tags=["Student Practice"],
)
async def submit_answer(
    problem_id: int,
    request: AnswerRequest,
    student_id: int = Depends(verify_student),  # SEC-003: Database verification
    db: AsyncSession = Depends(get_session),
) -> AnswerResponse:
    """Submit answer to a problem.

    Evaluates the student's answer and provides bilingual feedback.
    Updates session progress and persists the response.

    Args:
        problem_id: ID of the problem being answered.
        request: Answer submission containing student_answer and session_id.
        student_id: Verified student telegram ID (from dependency).
        db: Database session (from dependency).

    Returns:
        AnswerResponse with evaluation result, feedback, and next problem ID.

    Raises:
        HTTPException:
            - 404 if session or problem not found
            - 403 if session belongs to a different student
            - 410 if session has expired
    """
    student = await _get_student_by_telegram_id(db, student_id)

    problem_repo = ProblemRepository()
    session_repo = SessionRepository()
    response_repo = ResponseRepository()

    # Fetch and validate session
    session = await session_repo.get_session_by_id(db, request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Basic ownership check (full Depends wired by Noor in C-1)
    if session.student_id != student.student_id:
        logger.warning(
            "IDOR attempt: student tried to answer another student's session",
            hashed_telegram_id=hash_telegram_id(student_id),
        )
        raise HTTPException(status_code=403, detail="Forbidden: session belongs to another student")

    if session.is_expired():
        raise HTTPException(status_code=410, detail="ERR_SESSION_EXPIRED: session has expired")

    # Verify problem is in this session
    if problem_id not in session.problem_ids:
        raise HTTPException(status_code=404, detail="Problem not found in this session")

    # Check for duplicate submission (idempotent: return cached result)
    existing_response = await response_repo.get_response_for_problem(
        db, request.session_id, problem_id
    )
    if existing_response is not None and existing_response.student_answer:
        # Already answered — return cached result
        answered_ids = await response_repo.get_answered_problem_ids(db, request.session_id)
        next_id = next(
            (pid for pid in session.problem_ids if pid not in answered_ids),
            None,
        )
        return _cached_answer_response(existing_response, session, next_id, student.language)

    # Fetch problem
    problem = await problem_repo.get_problem_by_id(db, problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    # Determine hints already used for this problem
    hints_used = existing_response.hints_used if existing_response else 0

    # Evaluate the answer
    evaluator = AnswerEvaluator()
    result = evaluator.evaluate(problem, request.student_answer, hints_used)

    # Log answer (redacted for PII)
    logger.info(
        "Evaluating answer",
        hashed_telegram_id=hash_telegram_id(student_id),
        problem_id=problem_id,
        redacted_answer=redact_answer(request.student_answer),
        is_correct=result.is_correct,
    )

    # Persist response
    await response_repo.create_response(
        db=db,
        session_id=request.session_id,
        problem_id=problem_id,
        student_answer=request.student_answer,
        is_correct=result.is_correct,
        hints_used=hints_used,
        time_spent_seconds=request.time_spent_seconds or 0,
        confidence_level=result.confidence_level,
    )

    # Update session correct count
    if result.is_correct:
        await session_repo.increment_correct_count(db, session)

    # Determine next problem
    answered_ids = await response_repo.get_answered_problem_ids(db, request.session_id)
    next_id = next(
        (pid for pid in session.problem_ids if pid not in answered_ids),
        None,
    )

    # Complete session if all problems answered
    milestone_msg = ""
    if next_id is None:
        await session_repo.mark_session_complete(db, session)
        # Record streak practice (flush inside, commit below)
        _, new_milestones = await StreakRepository().record_practice(
            db, student.student_id, date.today()
        )
        # Build milestone message (captured before commit)
        if new_milestones:
            enc = EncouragementService()
            lang = student.language
            milestone_msg = "\n\n" + "\n".join(
                enc.get_milestone_message(m, lang) for m in new_milestones
            )

    await db.commit()

    # Pick feedback language
    feedback = result.feedback_bn if student.language == "bn" else result.feedback_en

    return AnswerResponse(
        is_correct=result.is_correct,
        feedback_text=feedback + milestone_msg,
        next_problem_id=next_id,
    )


@router.post(
    "/practice/{problem_id}/hint",
    response_model=HintResponse,
    tags=["Student Practice"],
)
@limiter.limit("10/day")  # SEC-005: Rate limit hint requests per student
async def request_hint(
    req: Request,  # Required by slowapi rate limiter
    problem_id: int,
    request: HintRequest,
    student_id: int = Depends(verify_student),  # SEC-003: Database verification
    db: AsyncSession = Depends(get_session),
) -> HintResponse:
    """Deliver the next Socratic hint via Claude Haiku (cached + fallback).

    Calls Claude Haiku with a Socratic prompt; serves from the shared
    HintCache on repeat requests; falls back to pre-written hints when
    the API key is absent, the daily rate limit is reached, or all
    retries fail. Maximum 3 hints per problem.

    Security (SEC-005):
    - Rate limited to 10 requests/day per student
    - Returns 429 Too Many Requests if limit exceeded

    Args:
        req: FastAPI request object (required by rate limiter).
        problem_id: ID of the problem.
        request: Hint request containing session_id and hint_number (1-3).
        student_id: Verified student telegram ID (from dependency).
        db: Database session (from dependency).

    Returns:
        HintResponse with hint text in student's language.

    Raises:
        HTTPException:
            - 400 if hint limit exceeded (>3 hints)
            - 403 if session belongs to another student
            - 404 if session or problem not found
            - 410 if session expired
            - 429 if rate limit exceeded
    """
    student = await _get_student_by_telegram_id(db, student_id)

    problem_repo = ProblemRepository()
    session_repo = SessionRepository()
    response_repo = ResponseRepository()

    # Fetch and validate session
    session = await session_repo.get_session_by_id(db, request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.student_id != student.student_id:
        logger.warning(
            "IDOR attempt on hint endpoint",
            hashed_telegram_id=hash_telegram_id(student_id),
        )
        raise HTTPException(status_code=403, detail="Forbidden: session belongs to another student")

    if session.is_expired():
        raise HTTPException(status_code=410, detail="ERR_SESSION_EXPIRED: session has expired")

    # Verify problem belongs to this session
    if problem_id not in session.problem_ids:
        raise HTTPException(status_code=404, detail="Problem not found in this session")

    # Fetch problem and verify it exists
    problem = await problem_repo.get_problem_by_id(db, problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    # Check existing response for hint count
    existing_response = await response_repo.get_response_for_problem(
        db, request.session_id, problem_id
    )
    hints_already_used = existing_response.hints_used if existing_response else 0

    # Enforce hint limit
    if hints_already_used >= 3:
        raise HTTPException(status_code=400, detail="ERR_HINT_LIMIT_EXCEEDED")

    # Generate hint via Claude Haiku (with cache + fallback) — PHASE5-B-2
    hint_text, is_ai, in_tok, out_tok = await _hint_generator.get_hint(
        db=db,
        problem=problem,
        student_answer="",  # REST endpoint doesn't carry last answer; use empty
        hint_number=request.hint_number,
        student_id=student.student_id,
        language=student.language,
    )

    if not hint_text:
        raise HTTPException(
            status_code=400,
            detail=f"Hint {request.hint_number} not available for this problem",
        )

    # Create response stub if first interaction
    if existing_response is None:
        existing_response = await response_repo.create_response(
            db=db,
            session_id=request.session_id,
            problem_id=problem_id,
            student_answer="",
            is_correct=False,
            hints_used=0,
            time_spent_seconds=0,
            confidence_level="high",
        )

    # Only increment hint count if this is a new hint level
    if request.hint_number > hints_already_used:
        hint_dict = {
            "text_en": hint_text if student.language == "en" else "",
            "text_bn": hint_text if student.language == "bn" else "",
            "hint_number": request.hint_number,
        }
        await response_repo.update_hint_count(
            db, existing_response, hints_already_used + 1, hint_dict
        )

    # Record cost with real token data when AI-generated
    cost_tracker = CostTracker()
    await cost_tracker.record_hint_cost(
        db,
        student.student_id,
        request.session_id,
        request.hint_number,
        is_ai_generated=is_ai,
        input_tokens=in_tok,
        output_tokens=out_tok,
    )
    await cost_tracker.check_budget_alert(db, student.student_id)

    await db.commit()

    logger.info(
        "Hint served",
        hashed_telegram_id=hash_telegram_id(student_id),
        problem_id=problem_id,
        hint_number=request.hint_number,
    )

    return HintResponse(
        hint_text=hint_text,
        hint_number=request.hint_number,
        hints_remaining=3 - request.hint_number,
    )

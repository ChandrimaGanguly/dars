"""Practice session endpoints.

Security (SEC-003, SEC-005):
- All endpoints require student authentication (SEC-003)
- Hint endpoint rate limited to 10 requests/day per student (SEC-005)
- Prevents abuse of expensive Claude API calls
- Prevents IDOR attacks
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.student import verify_student
from src.database import get_session
from src.logging import get_logger
from src.schemas.practice import (
    AnswerRequest,
    AnswerResponse,
    HintRequest,
    HintResponse,
    PracticeResponse,
    ProblemWithoutAnswer,
)

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


@router.get("/practice", response_model=PracticeResponse, tags=["Student Practice"])
async def get_practice_problems(
    student_id: int = Depends(verify_student),  # SEC-003: Database verification
    db: AsyncSession = Depends(get_session),
) -> PracticeResponse:
    """Get daily practice problems.

    Returns 5 problems for the student's daily practice session.
    Problems are selected based on grade level, performance history,
    and adaptive difficulty algorithm.

    Security (SEC-003):
    - Student must be authenticated via X-Student-ID header
    - Student existence verified in database (prevents IDOR)

    Args:
        student_id: Verified student telegram ID (from dependency).
        db: Database session (from dependency).

    Returns:
        PracticeResponse with 5 selected problems.

    Raises:
        HTTPException: If student not found or problem selection fails.
    """
    # TODO: Implement problem selection
    # - Run problem selection algorithm (REQ-008)
    # - Create new session in database
    # - Return problems without answers
    # Note: Student validation now handled by Depends(verify_student)

    # Mock data for now
    mock_problems = [
        ProblemWithoutAnswer(
            problem_id=1,
            grade=7,
            topic="Profit & Loss",
            question_en="A shopkeeper buys 15 mangoes for Rs. 300...",
            question_bn="একজন দোকানদার 15টি আম ₹300 এর জন্য ক্রয় করেন...",
            difficulty=1,
            answer_type="numeric",
            multiple_choice_options=None,
        ),
    ]

    return PracticeResponse(
        session_id=1,
        problems=mock_problems,
        problem_count=len(mock_problems),
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
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

    Evaluates the student's answer and provides feedback.
    Updates session progress and difficulty level.

    Args:
        problem_id: ID of the problem being answered.
        request: Answer submission with student's answer.
        x_student_id: Student telegram ID from header.

    Returns:
        AnswerResponse with evaluation result and feedback.

    Raises:
        HTTPException: If problem not found or session invalid.
    """
    # TODO: Implement answer evaluation
    # - Validate problem exists and belongs to session
    # - Evaluate answer (numeric ±5%, MC exact, text semantic)
    # - Update session progress
    # - Update adaptive difficulty
    # - Store response in database
    # - Generate feedback message

    # Mock response
    is_correct = len(request.student_answer) > 0
    feedback = "Correct! Well done!" if is_correct else "Not quite. Try again or ask for a hint."

    return AnswerResponse(
        is_correct=is_correct,
        feedback_text=feedback,
        next_problem_id=problem_id + 1 if problem_id < 5 else None,
    )


@router.post(
    "/practice/{problem_id}/hint",
    response_model=HintResponse,
    tags=["Student Practice"],
)
@limiter.limit("10/day")  # SEC-005: Rate limit expensive Claude API calls
async def request_hint(
    req: Request,  # Required by slowapi rate limiter
    problem_id: int,
    request: HintRequest,
    student_id: int = Depends(verify_student),  # SEC-003: Database verification
    db: AsyncSession = Depends(get_session),
) -> HintResponse:
    """Request a Socratic hint for a problem.

    Generates or retrieves a hint to guide the student toward the answer
    without revealing it directly. Maximum 3 hints per problem.

    Security (SEC-005):
    - Rate limited to 10 requests/day per IP address
    - Prevents abuse of expensive Claude API calls
    - Returns 429 Too Many Requests if limit exceeded

    Args:
        req: FastAPI request object (required by rate limiter).
        problem_id: ID of the problem.
        request: Hint request with hint number.
        x_student_id: Student telegram ID from header.

    Returns:
        HintResponse with hint text.

    Raises:
        HTTPException:
            - 400 if too many hints requested (>3)
            - 429 if rate limit exceeded (>10/day)
            - 404 if problem not found
    """
    logger.info(
        f"Student {student_id} requested hint {request.hint_number} for problem {problem_id}"
    )

    # TODO: Implement hint generation
    # - Validate problem exists and session is active
    # - Check hints_used < 3
    # - Generate hint via Claude API (REQ-015)
    # - Check cache first (REQ-016)
    # - Store hint usage in database
    # - Track cost

    if request.hint_number > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 hints allowed per problem")

    # Mock hint
    hints = {
        1: "Think about the cost of each item first.",
        2: "Calculate the total selling price, then compare with cost.",
        3: "Profit = Selling Price - Cost Price. Now calculate step by step.",
    }

    return HintResponse(
        hint_text=hints.get(request.hint_number, "No more hints available."),
        hint_number=request.hint_number,
        hints_remaining=3 - request.hint_number,
    )

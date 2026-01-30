"""Practice session schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ProblemWithoutAnswer(BaseModel):
    """Problem without answer (for student display)."""

    problem_id: int = Field(..., description="Problem ID")
    grade: int = Field(..., description="Grade level", ge=6, le=8)
    topic: str = Field(..., description="Problem topic")
    question_en: str = Field(..., description="Question in English")
    question_bn: str = Field(..., description="Question in Bengali")
    difficulty: int = Field(
        ..., description="Difficulty level (1=Easy, 2=Medium, 3=Hard)", ge=1, le=3
    )
    answer_type: str | None = Field(
        "numeric", description="Answer type", examples=["numeric", "multiple_choice", "text"]
    )
    multiple_choice_options: list[dict[str, str | int]] | None = Field(
        None, description="Multiple choice options"
    )


class PracticeResponse(BaseModel):
    """Response with practice problems for the day."""

    session_id: int = Field(..., description="Session ID")
    problems: list[ProblemWithoutAnswer] = Field(..., description="List of 5 problems")
    problem_count: int = Field(..., description="Number of problems", examples=[5])
    expires_at: datetime = Field(..., description="Session expiration time")


class AnswerRequest(BaseModel):
    """Request to submit an answer."""

    session_id: int = Field(..., description="Session ID")
    student_answer: str = Field(..., description="Student's submitted answer")
    time_spent_seconds: int | None = Field(None, description="Time spent on problem", ge=0)


class AnswerResponse(BaseModel):
    """Response after answer evaluation."""

    is_correct: bool = Field(..., description="Whether answer is correct")
    feedback_text: str = Field(..., description="Feedback message")
    next_problem_id: int | None = Field(
        None, description="Next problem ID (null if session complete)"
    )


class HintRequest(BaseModel):
    """Request for a hint."""

    session_id: int = Field(..., description="Session ID")
    student_answer: str | None = Field(None, description="Student's current answer attempt")
    hint_number: int = Field(..., description="Hint number (1, 2, or 3)", ge=1, le=3)


class HintResponse(BaseModel):
    """Response with generated hint."""

    hint_text: str = Field(..., description="Hint text")
    hint_number: int = Field(..., description="Hint number", ge=1, le=3)
    hints_remaining: int = Field(..., description="Number of hints remaining", ge=0, le=3)

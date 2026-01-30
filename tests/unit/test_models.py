"""
Unit tests for database models.

Tests model creation, validation, and relationships.
"""

from datetime import UTC, datetime, timedelta

from src.models import (
    CostRecord,
    Hint,
    Problem,
    Response,
    Session,
    Streak,
    Student,
)
from src.models.cost_record import ApiProvider, OperationType
from src.models.session import SessionStatus


class TestStudent:
    """Tests for Student model."""

    def test_student_creation(self) -> None:
        """Student can be created with valid data."""
        student = Student(
            telegram_id=123456789,
            name="Test Student",
            grade=7,
            language="bn",
        )

        assert student.telegram_id == 123456789
        assert student.name == "Test Student"
        assert student.grade == 7
        assert student.language == "bn"

    def test_student_repr(self) -> None:
        """Student has readable string representation."""
        student = Student(
            student_id=1,
            telegram_id=123456789,
            name="Test Student",
            grade=7,
            language="bn",
        )

        repr_str = repr(student)
        assert "student_id=1" in repr_str or "id=1" in repr_str
        assert "telegram_id=123456789" in repr_str
        assert "name='Test Student'" in repr_str


class TestProblem:
    """Tests for Problem model."""

    def test_problem_creation(self) -> None:
        """Problem can be created with bilingual content."""
        hints_data = [
            {
                "hint_number": 1,
                "text_en": "Think about the cost per item",
                "text_bn": "প্রতিটি আইটেমের খরচ সম্পর্কে চিন্তা করুন",
                "is_ai_generated": False,
            },
            {
                "hint_number": 2,
                "text_en": "Calculate selling price",
                "text_bn": "বিক্রয় মূল্য গণনা করুন",
                "is_ai_generated": False,
            },
            {
                "hint_number": 3,
                "text_en": "Find the difference",
                "text_bn": "পার্থক্য খুঁজুন",
                "is_ai_generated": False,
            },
        ]

        problem = Problem(
            grade=7,
            topic="Profit & Loss",
            question_en="A shopkeeper buys 15 mangoes for Rs. 300...",
            question_bn="একজন দোকানদার 15টি আম ₹300 এর জন্য...",
            answer="75",
            hints=hints_data,
            difficulty=2,
        )

        assert problem.grade == 7
        assert problem.topic == "Profit & Loss"
        assert len(problem.hints) == 3

    def test_problem_get_question(self) -> None:
        """Problem returns question in correct language."""
        problem = Problem(
            grade=7,
            topic="Test",
            question_en="English question",
            question_bn="Bengali question",
            answer="42",
            hints=[],
            difficulty=1,
        )

        assert problem.get_question("en") == "English question"
        assert problem.get_question("bn") == "Bengali question"

    def test_hint_creation(self) -> None:
        """Hint objects can be created and converted."""
        hint = Hint(
            hint_number=1,
            text_en="English hint",
            text_bn="Bengali hint",
            is_ai_generated=True,
        )

        assert hint.hint_number == 1
        assert hint.text_en == "English hint"
        assert hint.is_ai_generated is True

        # Test to_dict
        hint_dict = hint.to_dict()
        assert hint_dict["hint_number"] == 1
        assert hint_dict["is_ai_generated"] is True

        # Test from_dict
        restored_hint = Hint.from_dict(hint_dict)
        assert restored_hint.hint_number == hint.hint_number
        assert restored_hint.text_en == hint.text_en


class TestSession:
    """Tests for Session model."""

    def test_session_creation(self) -> None:
        """Session can be created with problem IDs."""
        now = datetime.now(UTC)
        expires = now + timedelta(minutes=30)

        session = Session(
            student_id=1,
            date=now,
            status=SessionStatus.IN_PROGRESS,
            problem_ids=[1, 2, 3, 4, 5],
            expires_at=expires,
            problems_correct=0,  # Explicitly set default for unit test
            total_time_seconds=0,  # Explicitly set default for unit test
        )

        assert session.student_id == 1
        assert session.status == SessionStatus.IN_PROGRESS
        assert len(session.problem_ids) == 5
        assert session.problems_correct == 0

    def test_session_is_expired(self) -> None:
        """Session correctly identifies if it has expired."""
        now = datetime.now(UTC)

        # Not expired
        session_active = Session(
            student_id=1,
            date=now,
            status=SessionStatus.IN_PROGRESS,
            problem_ids=[1, 2, 3, 4, 5],
            expires_at=now + timedelta(minutes=30),
        )
        assert not session_active.is_expired()

        # Expired
        session_expired = Session(
            student_id=1,
            date=now - timedelta(hours=1),
            status=SessionStatus.IN_PROGRESS,
            problem_ids=[1, 2, 3, 4, 5],
            expires_at=now - timedelta(minutes=30),
        )
        assert session_expired.is_expired()

    def test_session_get_accuracy(self) -> None:
        """Session calculates accuracy correctly."""
        session = Session(
            student_id=1,
            date=datetime.now(UTC),
            status=SessionStatus.COMPLETED,
            problem_ids=[1, 2, 3, 4, 5],
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            problems_correct=4,
        )

        # No responses yet
        assert session.get_accuracy() == 0.0

        # Add mock responses
        session.responses = [
            Response(
                session_id=1,
                problem_id=i,
                student_answer="test",
                is_correct=(i <= 4),
                time_spent_seconds=30,
            )
            for i in range(1, 6)
        ]

        assert session.get_accuracy() == 80.0


class TestResponse:
    """Tests for Response model."""

    def test_response_creation(self) -> None:
        """Response can be created with answer data."""
        response = Response(
            session_id=1,
            problem_id=1,
            student_answer="75",
            is_correct=True,
            time_spent_seconds=45,
            hints_used=1,
        )

        assert response.session_id == 1
        assert response.student_answer == "75"
        assert response.is_correct is True
        assert response.hints_used == 1


class TestStreak:
    """Tests for Streak model."""

    def test_streak_creation(self) -> None:
        """Streak can be created with initial values."""
        streak = Streak(
            student_id=1,
            current_streak=5,
            longest_streak=10,
            milestones_achieved=[],  # Explicitly set default for unit test
        )

        assert streak.student_id == 1
        assert streak.current_streak == 5
        assert streak.longest_streak == 10
        assert streak.milestones_achieved == []

    def test_streak_add_milestone(self) -> None:
        """Streak correctly tracks milestones."""
        streak = Streak(
            student_id=1,
            current_streak=7,
            longest_streak=7,
            milestones_achieved=[],  # Explicitly set default for unit test
        )

        # Add first milestone
        streak.add_milestone(7)
        assert 7 in streak.milestones_achieved

        # Adding duplicate doesn't create duplicates
        streak.add_milestone(7)
        assert streak.milestones_achieved.count(7) == 1

        # Add another milestone
        streak.add_milestone(14)
        assert len(streak.milestones_achieved) == 2
        assert streak.milestones_achieved == [7, 14]

    def test_streak_get_next_milestone(self) -> None:
        """Streak identifies next milestone correctly."""
        streak = Streak(
            student_id=1,
            current_streak=10,
            longest_streak=10,
        )

        next_milestone = streak.get_next_milestone()
        assert next_milestone == 14

        # Update streak
        streak.current_streak = 15
        next_milestone = streak.get_next_milestone()
        assert next_milestone == 30


class TestCostRecord:
    """Tests for CostRecord model."""

    def test_cost_record_creation(self) -> None:
        """CostRecord can be created with API metrics."""
        cost_record = CostRecord(
            student_id=1,
            session_id=1,
            operation=OperationType.HINT_GENERATION,
            api_provider=ApiProvider.CLAUDE,
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.0015,
        )

        assert cost_record.student_id == 1
        assert cost_record.operation == OperationType.HINT_GENERATION
        assert cost_record.api_provider == ApiProvider.CLAUDE
        assert cost_record.input_tokens == 100
        assert cost_record.cost_usd == 0.0015

    def test_cost_record_repr(self) -> None:
        """CostRecord has readable string representation."""
        cost_record = CostRecord(
            cost_id=1,
            student_id=1,
            operation=OperationType.HINT_GENERATION,
            api_provider=ApiProvider.CLAUDE,
            cost_usd=0.0015,
        )

        repr_str = repr(cost_record)
        assert "cost_id=1" in repr_str or "id=1" in repr_str
        assert "hint_generation" in repr_str
        assert "0.0015" in repr_str

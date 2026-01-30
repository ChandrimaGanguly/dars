"""Integration tests for authentication with database (SEC-003).

Tests verify that student authentication properly queries the database
to prevent IDOR (Insecure Direct Object Reference) vulnerabilities.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.auth.student import verify_student
from src.models.base import Base
from src.models.student import Student


@pytest.fixture
async def async_db_session() -> AsyncSession:  # type: ignore
    """Create async database session for integration tests.

    Uses in-memory SQLite database for fast, isolated tests.
    """
    # Create in-memory async SQLite database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
class TestStudentDatabaseVerification:
    """Integration tests for SEC-003: Student database verification.

    These tests verify that verify_student() correctly queries the database
    to ensure students exist before allowing access to resources.
    """

    async def test_verify_student_exists_in_database(self, async_db_session: AsyncSession) -> None:
        """Test authentication succeeds when student exists in database.

        Security (SEC-003): Valid student IDs should be verified against database.
        """
        # Create a test student
        student = Student(
            telegram_id=123456789,
            name="Test Student",
            grade=7,
            language="en",
        )
        async_db_session.add(student)
        await async_db_session.commit()

        # Verify authentication succeeds
        result = await verify_student(x_student_id="123456789", db=async_db_session)
        assert result == 123456789

    async def test_verify_student_not_in_database_returns_404(
        self, async_db_session: AsyncSession
    ) -> None:
        """Test authentication fails with 404 when student not in database.

        Security (SEC-003): Prevents IDOR attacks by rejecting unknown student IDs.
        """
        # Try to authenticate with non-existent student ID
        with pytest.raises(HTTPException) as exc_info:
            await verify_student(x_student_id="999999999", db=async_db_session)

        # Should return 404 Not Found (not 401 Unauthorized)
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    async def test_verify_student_multiple_students(self, async_db_session: AsyncSession) -> None:
        """Test authentication correctly identifies specific student.

        Security (SEC-003): Must query by exact telegram_id, not just existence.
        """
        # Create multiple students
        student1 = Student(
            telegram_id=111111111,
            name="Student One",
            grade=6,
            language="bn",
        )
        student2 = Student(
            telegram_id=222222222,
            name="Student Two",
            grade=7,
            language="en",
        )
        async_db_session.add_all([student1, student2])
        await async_db_session.commit()

        # Verify first student
        result1 = await verify_student(x_student_id="111111111", db=async_db_session)
        assert result1 == 111111111

        # Verify second student
        result2 = await verify_student(x_student_id="222222222", db=async_db_session)
        assert result2 == 222222222

        # Verify third (non-existent) fails
        with pytest.raises(HTTPException) as exc_info:
            await verify_student(x_student_id="333333333", db=async_db_session)
        assert exc_info.value.status_code == 404

    async def test_verify_student_database_query_performance(
        self, async_db_session: AsyncSession
    ) -> None:
        """Test database query completes in acceptable time.

        Security (SEC-003): Indexed lookup should be <100ms.
        Performance: Verifies telegram_id index is working.
        """
        import time

        # Create student
        student = Student(
            telegram_id=555555555,
            name="Performance Test",
            grade=8,
            language="bn",
        )
        async_db_session.add(student)
        await async_db_session.commit()

        # Measure query time
        start = time.time()
        await verify_student(x_student_id="555555555", db=async_db_session)
        duration_ms = (time.time() - start) * 1000

        # Should complete in <100ms (generous for in-memory SQLite)
        assert duration_ms < 100, f"Database query took {duration_ms:.2f}ms (expected <100ms)"

    async def test_verify_student_handles_concurrent_requests(
        self, async_db_session: AsyncSession
    ) -> None:
        """Test authentication works correctly with concurrent requests.

        Security (SEC-003): Database verification must be thread-safe.
        """
        import asyncio

        # Create student
        student = Student(
            telegram_id=777777777,
            name="Concurrent Test",
            grade=7,
            language="en",
        )
        async_db_session.add(student)
        await async_db_session.commit()

        # Run 10 concurrent authentication requests
        tasks = [verify_student(x_student_id="777777777", db=async_db_session) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should succeed with same result
        assert all(r == 777777777 for r in results)
        assert len(results) == 10

    async def test_verify_student_prevents_idor_attack(
        self, async_db_session: AsyncSession
    ) -> None:
        """Test that attackers cannot access data by guessing student IDs.

        Security (SEC-003): Primary defense against IDOR vulnerabilities.

        Attack scenario:
        1. Attacker knows student IDs are integers
        2. Attacker tries sequential IDs (1, 2, 3, ...)
        3. System should reject all non-existent IDs with 404
        """
        # Create only one student with ID 100
        student = Student(
            telegram_id=100,
            name="Target Student",
            grade=7,
            language="en",
        )
        async_db_session.add(student)
        await async_db_session.commit()

        # Attacker tries sequential IDs
        for attack_id in [1, 2, 3, 99, 101, 102, 999]:
            with pytest.raises(HTTPException) as exc_info:
                await verify_student(x_student_id=str(attack_id), db=async_db_session)
            # All should return 404 (not 401 which reveals "this might be valid")
            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

        # Only valid ID should work
        result = await verify_student(x_student_id="100", db=async_db_session)
        assert result == 100

"""Integration tests for admin REST endpoints.

Uses in-memory SQLite + real ORM queries to verify that admin endpoints
return data derived from actual DB state rather than stub values.

PHASE7-C-2
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.main import app
from src.models.cost_record import ApiProvider, CostRecord, OperationType
from src.models.session import Session, SessionStatus
from src.models.student import Student
from src.services.cost_tracker import BUDGET_PER_STUDENT_USD

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ADMIN_ID = "999888777"
_ADMIN_HEADERS = {"X-Admin-ID": _ADMIN_ID}


async def _create_student(
    db: AsyncSession,
    telegram_id: int = 100,
    name: str = "Test",
    grade: int = 7,
    language: str = "en",
) -> Student:
    student = Student(telegram_id=telegram_id, name=name, grade=grade, language=language)
    db.add(student)
    await db.flush()
    return student


async def _create_session(
    db: AsyncSession,
    student_id: int,
    completed_at: datetime | None = None,
) -> Session:
    now = completed_at or datetime.now(UTC)
    sess = Session(
        student_id=student_id,
        date=now,
        status=SessionStatus.COMPLETED if completed_at else SessionStatus.IN_PROGRESS,
        completed_at=completed_at,
        problem_ids=[],
        expires_at=now + timedelta(hours=24),
    )
    db.add(sess)
    await db.flush()
    return sess


async def _create_cost_record(
    db: AsyncSession,
    student_id: int,
    cost_usd: float = 0.01,
    recorded_at: datetime | None = None,
) -> CostRecord:
    rec = CostRecord(
        student_id=student_id,
        operation=OperationType.HINT_GENERATION,
        api_provider=ApiProvider.CLAUDE,
        cost_usd=cost_usd,
        recorded_at=recorded_at or datetime.now(UTC),
    )
    db.add(rec)
    await db.flush()
    return rec


def _make_client(db: AsyncSession, admin_id: str = _ADMIN_ID) -> TestClient:
    """Create TestClient with mocked DB session and admin env."""

    async def _override() -> Any:
        yield db

    app.dependency_overrides[get_session] = _override
    import os

    os.environ["ADMIN_TELEGRAM_IDS"] = admin_id
    import src.config

    src.config._settings = None
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAdminStats:
    async def test_admin_stats_returns_correct_student_count(
        self, db_session: AsyncSession
    ) -> None:
        """Seeded student count must appear in /admin/stats response."""
        for i in range(5):
            await _create_student(db_session, telegram_id=1000 + i)
        await db_session.commit()

        client = _make_client(db_session)
        try:
            response = client.get("/admin/stats", headers=_ADMIN_HEADERS)
        finally:
            app.dependency_overrides.pop(get_session, None)

        assert response.status_code == 200
        data = response.json()
        assert data["total_students"] == 5

    async def test_admin_stats_active_week_counts_only_recent_sessions(
        self, db_session: AsyncSession
    ) -> None:
        """Only sessions in the last 7 days count as active this week."""
        student = await _create_student(db_session, telegram_id=2000)
        now = datetime.now(UTC)
        # Old session (10 days ago) — should NOT count
        await _create_session(db_session, student.student_id, completed_at=now - timedelta(days=10))
        # Recent session (today) — should count
        await _create_session(db_session, student.student_id, completed_at=now)
        await db_session.commit()

        client = _make_client(db_session)
        try:
            response = client.get("/admin/stats", headers=_ADMIN_HEADERS)
        finally:
            app.dependency_overrides.pop(get_session, None)

        assert response.status_code == 200
        data = response.json()
        assert data["active_this_week"] == 1

    async def test_admin_requires_auth(self, db_session: AsyncSession) -> None:
        """Missing X-Admin-ID returns 401; invalid ID returns 403."""
        client = _make_client(db_session)
        try:
            no_header = client.get("/admin/stats")
            assert no_header.status_code == 401

            bad_id = client.get("/admin/stats", headers={"X-Admin-ID": "000000"})
            assert bad_id.status_code == 403
        finally:
            app.dependency_overrides.pop(get_session, None)


@pytest.mark.integration
class TestAdminStudents:
    async def test_admin_students_paginates_correctly(self, db_session: AsyncSession) -> None:
        """Paginated student list returns correct slice."""
        for i in range(25):
            await _create_student(db_session, telegram_id=3000 + i, name=f"Student{i}")
        await db_session.commit()

        client = _make_client(db_session)
        try:
            r1 = client.get("/admin/students?page=1&limit=10", headers=_ADMIN_HEADERS)
            r3 = client.get("/admin/students?page=3&limit=10", headers=_ADMIN_HEADERS)
        finally:
            app.dependency_overrides.pop(get_session, None)

        assert r1.status_code == 200
        assert len(r1.json()["students"]) == 10

        assert r3.status_code == 200
        assert len(r3.json()["students"]) == 5

    async def test_admin_students_filters_by_grade(self, db_session: AsyncSession) -> None:
        """Grade filter returns only students of the requested grade."""
        for i in range(5):
            await _create_student(db_session, telegram_id=4000 + i, grade=7)
        for i in range(3):
            await _create_student(db_session, telegram_id=4100 + i, grade=8)
        await db_session.commit()

        client = _make_client(db_session)
        try:
            response = client.get("/admin/students?grade=7", headers=_ADMIN_HEADERS)
        finally:
            app.dependency_overrides.pop(get_session, None)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert all(s["grade"] == 7 for s in data["students"])


@pytest.mark.integration
class TestAdminCost:
    async def test_admin_cost_calculates_real_cost(self, db_session: AsyncSession) -> None:
        """Total cost sums actual CostRecord rows."""
        student = await _create_student(db_session, telegram_id=5000)
        for _ in range(3):
            await _create_cost_record(db_session, student.student_id, cost_usd=0.01)
        await db_session.commit()

        client = _make_client(db_session)
        try:
            response = client.get("/admin/cost?period=week", headers=_ADMIN_HEADERS)
        finally:
            app.dependency_overrides.pop(get_session, None)

        assert response.status_code == 200
        data = response.json()
        assert abs(data["total_cost_usd"] - 0.03) < 1e-6

    async def test_admin_cost_budget_alert_fires(self, db_session: AsyncSession) -> None:
        """budget_alert is True when per-student cost exceeds monthly budget."""
        student = await _create_student(db_session, telegram_id=6000)
        # Single record well above the monthly budget threshold
        # budget_alert = (per_student_avg * 30/7) > BUDGET_PER_STUDENT_USD
        # With days=7 period: per_student_avg needs to be > BUDGET/30*7
        # Use a cost that is clearly over budget when projected to month
        over_threshold = BUDGET_PER_STUDENT_USD * 2
        await _create_cost_record(db_session, student.student_id, cost_usd=over_threshold)
        await db_session.commit()

        client = _make_client(db_session)
        try:
            response = client.get("/admin/cost?period=week", headers=_ADMIN_HEADERS)
        finally:
            app.dependency_overrides.pop(get_session, None)

        assert response.status_code == 200
        assert response.json()["budget_alert"] is True

    async def test_admin_cost_no_alert_under_budget(self, db_session: AsyncSession) -> None:
        """budget_alert is False when cost is well within budget."""
        student = await _create_student(db_session, telegram_id=7000)
        # Tiny cost — far below budget
        await _create_cost_record(db_session, student.student_id, cost_usd=0.0001)
        await db_session.commit()

        client = _make_client(db_session)
        try:
            response = client.get("/admin/cost?period=week", headers=_ADMIN_HEADERS)
        finally:
            app.dependency_overrides.pop(get_session, None)

        assert response.status_code == 200
        assert response.json()["budget_alert"] is False

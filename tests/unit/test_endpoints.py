"""Unit tests for API endpoints."""

import os

import pytest
from fastapi.testclient import TestClient

from src.main import app

# Set up environment variables for testing
os.environ["ANTHROPIC_API_KEY"] = "test_key"
os.environ["DATABASE_URL"] = "postgresql://localhost/test"

client = TestClient(app)


@pytest.mark.unit
class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_returns_200(self) -> None:
        """Health check should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_json(self) -> None:
        """Health check should return JSON response."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_check_has_required_fields(self) -> None:
        """Health check should include status, db, claude, timestamp."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "db" in data
        assert "claude" in data
        assert "timestamp" in data

    def test_health_check_status_ok(self) -> None:
        """Health check should report OK status for stub."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"


@pytest.mark.unit
class TestWebhookEndpoint:
    """Tests for Telegram webhook endpoint."""

    def test_webhook_accepts_post(self) -> None:
        """Webhook should accept POST requests."""
        response = client.post(
            "/webhook",
            json={
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "date": 1643129200,
                    "chat": {"id": 987654321, "type": "private"},
                    "from": {
                        "id": 987654321,
                        "is_bot": False,
                        "first_name": "Test",
                    },
                    "text": "/start",
                },
            },
        )
        assert response.status_code == 200

    def test_webhook_returns_status_ok(self) -> None:
        """Webhook should return status ok."""
        response = client.post(
            "/webhook",
            json={
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "date": 1643129200,
                    "chat": {"id": 987654321, "type": "private"},
                    "from": {
                        "id": 987654321,
                        "is_bot": False,
                        "first_name": "Test",
                    },
                    "text": "/start",
                },
            },
        )
        data = response.json()
        assert data["status"] == "ok"

    def test_webhook_requires_update_id(self) -> None:
        """Webhook should require update_id field."""
        response = client.post("/webhook", json={})
        assert response.status_code == 422  # Validation error


@pytest.mark.unit
class TestPracticeEndpoints:
    """Tests for practice session endpoints."""

    def test_get_practice_requires_student_id(self) -> None:
        """Practice endpoint should require X-Student-ID header."""
        response = client.get("/practice")
        assert response.status_code == 422  # Missing required header

    def test_get_practice_returns_problems(self) -> None:
        """Practice endpoint should return problem list."""
        response = client.get("/practice", headers={"X-Student-ID": "123"})
        assert response.status_code == 200
        data = response.json()
        assert "problems" in data
        assert "session_id" in data
        assert "problem_count" in data

    def test_submit_answer_requires_body(self) -> None:
        """Submit answer should require request body."""
        response = client.post(
            "/practice/1/answer",
            headers={"X-Student-ID": "123"},
        )
        assert response.status_code == 422  # Missing body

    def test_submit_answer_returns_feedback(self) -> None:
        """Submit answer should return evaluation feedback."""
        response = client.post(
            "/practice/1/answer",
            headers={"X-Student-ID": "123"},
            json={
                "session_id": 1,
                "student_answer": "75",
                "time_spent_seconds": 45,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_correct" in data
        assert "feedback_text" in data

    def test_request_hint_returns_hint_text(self) -> None:
        """Request hint should return hint text."""
        response = client.post(
            "/practice/1/hint",
            headers={"X-Student-ID": "123"},
            json={
                "session_id": 1,
                "hint_number": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "hint_text" in data
        assert "hint_number" in data
        assert "hints_remaining" in data

    def test_request_hint_validates_hint_number(self) -> None:
        """Request hint should reject invalid hint numbers."""
        response = client.post(
            "/practice/1/hint",
            headers={"X-Student-ID": "123"},
            json={
                "session_id": 1,
                "hint_number": 5,  # Max is 3
            },
        )
        # Pydantic validation returns 422 for constraint violations
        assert response.status_code == 422


@pytest.mark.unit
class TestStreakEndpoint:
    """Tests for streak tracking endpoint."""

    def test_get_streak_requires_student_id(self) -> None:
        """Streak endpoint should require X-Student-ID header."""
        response = client.get("/streak")
        assert response.status_code == 422

    def test_get_streak_returns_streak_data(self) -> None:
        """Streak endpoint should return streak information."""
        response = client.get("/streak", headers={"X-Student-ID": "123"})
        assert response.status_code == 200
        data = response.json()
        assert "current_streak" in data
        assert "longest_streak" in data
        assert "student_id" in data


@pytest.mark.unit
class TestStudentEndpoints:
    """Tests for student profile endpoints."""

    def test_get_profile_requires_student_id(self) -> None:
        """Profile endpoint should require X-Student-ID header."""
        response = client.get("/student/profile")
        assert response.status_code == 422

    def test_get_profile_returns_profile_data(self) -> None:
        """Profile endpoint should return student profile."""
        response = client.get("/student/profile", headers={"X-Student-ID": "123"})
        assert response.status_code == 200
        data = response.json()
        assert "student_id" in data
        assert "name" in data
        assert "grade" in data
        assert "language" in data

    def test_update_profile_accepts_language(self) -> None:
        """Profile update should accept language change."""
        response = client.patch(
            "/student/profile",
            headers={"X-Student-ID": "123"},
            json={"language": "en"},
        )
        assert response.status_code == 200

    def test_update_profile_accepts_grade(self) -> None:
        """Profile update should accept grade change."""
        response = client.patch(
            "/student/profile",
            headers={"X-Student-ID": "123"},
            json={"grade": 8},
        )
        assert response.status_code == 200


@pytest.mark.unit
class TestAdminEndpoints:
    """Tests for admin dashboard endpoints."""

    def test_admin_stats_requires_admin_id(self) -> None:
        """Admin stats should require X-Admin-ID header."""
        response = client.get("/admin/stats")
        assert response.status_code == 422

    def test_admin_stats_returns_statistics(self) -> None:
        """Admin stats should return system statistics."""
        response = client.get("/admin/stats", headers={"X-Admin-ID": "123"})
        assert response.status_code == 200
        data = response.json()
        assert "total_students" in data
        assert "active_this_week" in data
        assert "avg_streak" in data

    def test_admin_students_supports_pagination(self) -> None:
        """Admin students should support pagination."""
        response = client.get(
            "/admin/students?page=1&limit=10",
            headers={"X-Admin-ID": "123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "students" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data

    def test_admin_students_supports_grade_filter(self) -> None:
        """Admin students should filter by grade."""
        response = client.get(
            "/admin/students?grade=7",
            headers={"X-Admin-ID": "123"},
        )
        assert response.status_code == 200

    def test_admin_cost_requires_admin_id(self) -> None:
        """Admin cost should require X-Admin-ID header."""
        response = client.get("/admin/cost")
        assert response.status_code == 422

    def test_admin_cost_returns_cost_data(self) -> None:
        """Admin cost should return cost summary."""
        response = client.get("/admin/cost", headers={"X-Admin-ID": "123"})
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "total_cost" in data
        assert "per_student_cost" in data
        assert "alert" in data

    def test_admin_cost_validates_period(self) -> None:
        """Admin cost should validate period parameter."""
        response = client.get(
            "/admin/cost?period=invalid",
            headers={"X-Admin-ID": "123"},
        )
        assert response.status_code == 422


@pytest.mark.unit
class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_200(self) -> None:
        """Root endpoint should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_api_info(self) -> None:
        """Root endpoint should return API information."""
        response = client.get("/")
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data

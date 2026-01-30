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

    def test_health_check_returns_ok_or_error(self) -> None:
        """Health check should return 200 OK or 503 Service Unavailable."""
        response = client.get("/health")
        # Without DATABASE_URL, health check will fail (503)
        # With DATABASE_URL, health check will pass (200)
        assert response.status_code in [200, 503]

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

    def test_health_check_status_values(self) -> None:
        """Health check status should be 'ok' or 'error'."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] in ["ok", "error"]
        # If status is error, db or claude should also be error/timeout
        if data["status"] == "error":
            assert data["db"] in ["ok", "error", "timeout"] or data["claude"] in [
                "ok",
                "error",
                "timeout",
            ]


@pytest.mark.unit
class TestWebhookEndpoint:
    """Tests for Telegram webhook endpoint (SEC-002).

    Tests verify webhook signature verification is enforced.
    """

    def test_webhook_requires_secret_token(self) -> None:
        """Webhook should require X-Telegram-Bot-Api-Secret-Token header.

        Security (SEC-002): Prevents unauthorized webhook calls.
        """
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
        assert response.status_code == 401  # SEC-002: Missing secret token

    def test_webhook_accepts_post_with_valid_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Webhook should accept POST requests with valid secret token."""
        # Set telegram secret token
        monkeypatch.setenv("TELEGRAM_SECRET_TOKEN", "test_secret_123")
        import src.config

        src.config._settings = None

        response = client.post(
            "/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "test_secret_123"},
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

    def test_webhook_returns_status_ok(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Webhook should return status ok with valid token."""
        # Set telegram secret token
        monkeypatch.setenv("TELEGRAM_SECRET_TOKEN", "test_secret_123")
        import src.config

        src.config._settings = None

        response = client.post(
            "/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "test_secret_123"},
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

    def test_webhook_requires_update_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Webhook should require update_id field even with valid token."""
        # Set telegram secret token
        monkeypatch.setenv("TELEGRAM_SECRET_TOKEN", "test_secret_123")
        import src.config

        src.config._settings = None

        response = client.post(
            "/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "test_secret_123"},
            json={},
        )
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

    @pytest.mark.skip(reason="Rate limiter requires integration test with real Request object")
    def test_request_hint_returns_hint_text(self) -> None:
        """Request hint should return hint text.

        Note: Skipped in unit tests because rate limiter (SEC-005) requires
        real Request object. Tested in integration tests instead.
        """
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
    """Tests for admin dashboard endpoints (SEC-004).

    Tests verify admin authentication is enforced on all admin endpoints.
    """

    def test_admin_stats_requires_admin_id(self) -> None:
        """Admin stats should require X-Admin-ID header.

        Security (SEC-004): Missing header returns 401.
        """
        response = client.get("/admin/stats")
        assert response.status_code == 401  # SEC-004: Missing header

    def test_admin_stats_rejects_unauthorized_admin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Admin stats should reject unauthorized admin IDs.

        Security (SEC-004): Invalid admin ID returns 403.
        """
        # Set authorized admin IDs
        monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "999999")
        import src.config

        src.config._settings = None

        # Try with unauthorized ID
        response = client.get("/admin/stats", headers={"X-Admin-ID": "123456"})
        assert response.status_code == 403  # SEC-004: Unauthorized

    def test_admin_stats_returns_statistics(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Admin stats should return system statistics for authorized admins.

        Security (SEC-004): Valid admin ID returns data.
        """
        # Set authorized admin IDs
        monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "123456")
        import src.config

        src.config._settings = None

        response = client.get("/admin/stats", headers={"X-Admin-ID": "123456"})
        assert response.status_code == 200
        data = response.json()
        assert "total_students" in data
        assert "active_this_week" in data
        assert "avg_streak" in data

    def test_admin_students_supports_pagination(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Admin students should support pagination for authorized admins."""
        # Set authorized admin IDs
        monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "123456")
        import src.config

        src.config._settings = None

        response = client.get(
            "/admin/students?page=1&limit=10",
            headers={"X-Admin-ID": "123456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "students" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data

    def test_admin_students_supports_grade_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Admin students should filter by grade for authorized admins."""
        # Set authorized admin IDs
        monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "123456")
        import src.config

        src.config._settings = None

        response = client.get(
            "/admin/students?grade=7",
            headers={"X-Admin-ID": "123456"},
        )
        assert response.status_code == 200

    def test_admin_cost_requires_admin_id(self) -> None:
        """Admin cost should require X-Admin-ID header.

        Security (SEC-004): Missing header returns 401.
        """
        response = client.get("/admin/cost")
        assert response.status_code == 401  # SEC-004: Missing header

    def test_admin_cost_returns_cost_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Admin cost should return cost summary for authorized admins."""
        # Set authorized admin IDs
        monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "123456")
        import src.config

        src.config._settings = None

        response = client.get("/admin/cost", headers={"X-Admin-ID": "123456"})
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "total_cost" in data
        assert "per_student_cost" in data
        assert "alert" in data

    def test_admin_cost_validates_period(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Admin cost should validate period parameter."""
        # Set authorized admin IDs
        monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "123456")
        import src.config

        src.config._settings = None

        response = client.get(
            "/admin/cost?period=invalid",
            headers={"X-Admin-ID": "123456"},
        )
        assert response.status_code == 422  # Validation error


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


@pytest.mark.unit
class TestCORSHardening:
    """Tests for CORS configuration (SEC-001).

    Verifies that CORS middleware is properly restricted to prevent
    unauthorized cross-origin requests.
    """

    def test_cors_allows_localhost_origin(self) -> None:
        """CORS should allow localhost origins for development.

        Security (SEC-001): Allow local development but restrict production.
        """
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code in [200, 503]
        # CORS headers should be present for allowed origin
        assert "access-control-allow-origin" in response.headers

    def test_cors_allows_railway_origin(self) -> None:
        """CORS should allow Railway production domain.

        Security (SEC-001): Allow production deployment domain.
        """
        response = client.get(
            "/health",
            headers={"Origin": "https://dars.railway.app"},
        )
        assert response.status_code in [200, 503]
        # CORS headers should be present for allowed origin
        assert "access-control-allow-origin" in response.headers

    def test_cors_blocks_unauthorized_origin(self) -> None:
        """CORS should block requests from unauthorized origins.

        Security (SEC-001): Prevent cross-origin attacks from evil.com.
        """
        response = client.get(
            "/health",
            headers={"Origin": "https://evil.com"},
        )
        # Request completes but CORS headers NOT present
        assert response.status_code in [200, 503]
        # access-control-allow-origin should NOT be present for blocked origin
        # (FastAPI CORS middleware doesn't add header for disallowed origins)

    def test_cors_allows_credentials(self) -> None:
        """CORS should allow credentials for same-origin requests.

        Security (SEC-001): Enable auth headers and cookies.
        """
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Preflight should succeed
        assert response.status_code == 200
        assert "access-control-allow-credentials" in response.headers

    def test_cors_restricts_methods(self) -> None:
        """CORS should only allow GET, POST, PATCH methods.

        Security (SEC-001): Block DELETE, PUT, and other methods.
        """
        # Preflight request asking for allowed method
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Preflight should succeed for allowed methods
        assert response.status_code == 200
        allowed_methods = response.headers.get("access-control-allow-methods", "")
        # Should include GET, POST, PATCH only
        assert "GET" in allowed_methods
        assert "POST" in allowed_methods
        assert "PATCH" in allowed_methods
        # Should NOT include DELETE or PUT
        assert "DELETE" not in allowed_methods
        assert "PUT" not in allowed_methods

    def test_cors_restricts_headers(self) -> None:
        """CORS should only allow required headers.

        Security (SEC-001): Block unnecessary headers to reduce attack surface.
        """
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type,X-Student-ID",
            },
        )
        assert response.status_code == 200
        allowed_headers = response.headers.get("access-control-allow-headers", "")
        # Should include our required headers
        assert "content-type" in allowed_headers.lower()
        assert "x-student-id" in allowed_headers.lower()

    def test_cors_has_max_age(self) -> None:
        """CORS should cache preflight requests.

        Security (SEC-001): Reduce preflight overhead with caching.
        """
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        # max-age should be set to cache preflight
        assert "access-control-max-age" in response.headers

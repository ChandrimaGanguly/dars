"""
Pytest fixtures and configuration for Dars tests.

This file provides shared fixtures for all tests:
- Database fixtures
- API client fixtures
- Mock Telegram updates
- Mock Claude API responses
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Note: Import actual models once src/ is created
# from src.database import Base
# from src.models import Student, Problem, Session, Response, Streak


@pytest.fixture(scope="session")
def event_loop() -> Generator:  # type: ignore
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Return in-memory SQLite database URL for tests."""
    return "sqlite:///:memory:"


@pytest.fixture
def test_db_engine(test_database_url: str):
    """Create test database engine."""
    engine = create_engine(test_database_url, connect_args={"check_same_thread": False})

    # Create tables
    # Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    # Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()

    yield session

    session.close()


@pytest.fixture
def mock_telegram_update() -> dict:
    """Return a mock Telegram update for testing."""
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "date": 1234567890,
            "chat": {
                "id": 987654321,
                "type": "private",
                "username": "testuser",
                "first_name": "Test",
                "last_name": "User",
            },
            "from": {
                "id": 987654321,
                "is_bot": False,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "language_code": "en",
            },
            "text": "/start",
        },
    }


@pytest.fixture
def mock_claude_response() -> dict:
    """Return a mock Claude API response."""
    return {
        "id": "msg_test123",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "This is a helpful hint that guides without giving the answer.",
            }
        ],
        "model": "claude-3-haiku-20240307",
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }


@pytest.fixture
def env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up required environment variables for tests."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123456:ABCDEFG")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123456789")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("ENVIRONMENT", "test")

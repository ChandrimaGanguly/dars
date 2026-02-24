"""
Pytest fixtures and configuration for Dars tests.

This file provides shared fixtures for all tests:
- Database fixtures (async)
- API client fixtures
- Mock Telegram updates
- Mock Claude API responses
"""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from src.models.base import Base


@pytest.fixture(scope="session")
def event_loop() -> Generator:  # type: ignore
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Return in-memory SQLite database URL for tests."""
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db_engine(test_database_url: str):
    """Create test async database engine."""
    engine = create_async_engine(
        test_database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:  # type: ignore
    """Create test database async session."""
    async with AsyncSession(test_db_engine) as session:
        yield session
        await session.close()


@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:  # type: ignore
    """Alias for db_session fixture for backward compatibility."""
    async with AsyncSession(test_db_engine) as session:
        yield session
        await session.close()


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

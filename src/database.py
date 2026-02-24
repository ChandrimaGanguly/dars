"""
Database connection and session management for Dars platform.

Provides async PostgreSQL connection using SQLAlchemy 2.0+ with asyncpg.
Handles connection pooling, session management, and environment configuration.
"""

import os
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from src.models.base import Base


def get_database_url() -> str:
    """Get database URL from environment variables.

    Returns:
        PostgreSQL connection string (asyncpg format).

    Raises:
        ValueError: If DATABASE_URL not set in environment.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable not set. "
            "Set it to a PostgreSQL connection string like: "
            "postgresql+asyncpg://user:pass@host:port/dbname"
        )

    # Replace postgres:// with postgresql+asyncpg:// if needed
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return database_url


def create_engine(
    database_url: str | None = None,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
) -> AsyncEngine:
    """Create async SQLAlchemy engine with connection pooling.

    Args:
        database_url: PostgreSQL connection string. If None, reads from env.
        echo: Whether to log SQL statements (useful for debugging).
        pool_size: Size of connection pool (default 5).
        max_overflow: Max overflow connections beyond pool_size (default 10).

    Returns:
        Configured AsyncEngine instance.
    """
    if database_url is None:
        database_url = get_database_url()

    # Configure connection pool
    # For Railway/production: Use AsyncAdaptedQueuePool (for async engines)
    # For SQLite/testing: Use NullPool to avoid connection issues
    is_sqlite = "sqlite" in database_url
    poolclass = NullPool if is_sqlite else AsyncAdaptedQueuePool

    # Build engine kwargs - don't pass pool parameters for NullPool
    engine_kwargs: dict[str, Any] = {
        "echo": echo,
        "future": True,
        "poolclass": poolclass,
    }

    if not is_sqlite:
        # Only pass pool parameters for QueuePool
        engine_kwargs["pool_size"] = pool_size
        engine_kwargs["max_overflow"] = max_overflow
        engine_kwargs["pool_pre_ping"] = True

    engine = create_async_engine(database_url, **engine_kwargs)

    return engine


# Global engine instance (lazy initialization)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or create global engine instance.

    Returns:
        Global AsyncEngine instance.
    """
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create session factory.

    Returns:
        Async session factory.
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session (dependency for FastAPI).

    Uses SQLAlchemy's recommended transaction pattern with automatic
    commit/rollback handling. The session.begin() context manager ensures:
    - Automatic commit on success
    - Automatic rollback on exception
    - No connection leaks even if commit hangs or times out

    Yields:
        AsyncSession instance for database operations.

    Example:
        ```python
        from fastapi import Depends
        from src.database import get_session

        @app.get("/students")
        async def list_students(db: AsyncSession = Depends(get_session)):
            result = await db.execute(select(Student))
            return result.scalars().all()
        ```
    """
    factory = get_session_factory()
    async with factory() as session, session.begin():
        # session.begin() handles commit/rollback automatically:
        # - Commits on normal exit from the with block
        # - Rolls back on exception
        # - Prevents connection leaks even on timeout
        yield session
        # session.close() called automatically by factory() context manager


async def init_db() -> None:
    """Initialize database (create all tables).

    Only use in development/testing. Production uses Alembic migrations.

    Example:
        ```python
        import asyncio
        from src.database import init_db

        asyncio.run(init_db())
        ```
    """
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all database tables.

    WARNING: Only use in development/testing. Destroys all data.

    Example:
        ```python
        import asyncio
        from src.database import drop_db

        asyncio.run(drop_db())
        ```
    """
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def check_connection() -> bool:
    """Check if database connection is working.

    Returns:
        True if connection successful, False otherwise.

    Example:
        ```python
        import asyncio
        from src.database import check_connection

        is_connected = asyncio.run(check_connection())
        print(f"Database connected: {is_connected}")
        ```
    """
    try:
        async with get_engine().begin() as conn:
            from sqlalchemy import text

            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

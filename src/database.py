"""
Database connection and session management for Dars platform.

Provides async PostgreSQL connection using SQLAlchemy 2.0+ with asyncpg.
Handles connection pooling, session management, and environment configuration.
"""

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

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
    # For Railway/production: Use QueuePool
    # For testing: Use NullPool to avoid connection issues
    poolclass = QueuePool if "test" not in database_url else NullPool

    engine = create_async_engine(
        database_url,
        echo=echo,
        future=True,
        poolclass=poolclass,
        pool_size=pool_size if poolclass == QueuePool else 0,
        max_overflow=max_overflow if poolclass == QueuePool else 0,
        pool_pre_ping=True,  # Verify connections before using
    )

    return engine


# Global engine instance (created on first import)
engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Get or create global engine instance.

    Returns:
        Global AsyncEngine instance.
    """
    global engine
    if engine is None:
        engine = create_engine()
    return engine


# Session factory
async_session_factory = async_sessionmaker(
    bind=get_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session (dependency for FastAPI).

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
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


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

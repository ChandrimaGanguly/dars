import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import models for autogenerate support
from src.models.base import Base

# Import all models to register them with Base.metadata
from src.models import (  # noqa: F401
    CostRecord,
    MessageTemplate,
    Problem,
    Response,
    SentMessage,
    Session,
    Streak,
    Student,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Prefer DATABASE_PUBLIC_URL for migrations (avoids private networking timeouts at startup).
# When set, use psycopg2 (sync) with sslmode=require — Railway's public proxy requires SSL
# and asyncpg's SSL negotiation is incompatible with Railway's proxy.
# Fall back to DATABASE_URL (private) with asyncpg when public URL is not available.
_public_url = os.getenv("DATABASE_PUBLIC_URL")
_private_url = os.getenv("DATABASE_URL")
_use_sync = bool(_public_url)

if _public_url:
    # Build psycopg2 URL with sslmode=require
    url = _public_url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}sslmode=disable"
    config.set_main_option("sqlalchemy.url", url)
elif _private_url:
    url = _private_url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    config.set_main_option("sqlalchemy.url", url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_sync() -> None:
    """Run migrations synchronously via psycopg2 (used for public URL)."""
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),  # type: ignore[arg-type]
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        do_run_migrations(connection)


async def run_async_migrations() -> None:
    """Run migrations asynchronously via asyncpg (used for private URL)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    if _use_sync:
        run_migrations_sync()
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

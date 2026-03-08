import asyncio
import os
import socket
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

# Use DATABASE_URL (private Railway internal) with psycopg2 for migrations.
# We always use the private URL — it's reliable from within Railway containers
# once we force IPv4 (postgres.railway.internal resolves to both IPv6 and IPv4;
# IPv6 routing is unreliable in Railway containers, IPv4 works fine).
_raw_url = os.getenv("DATABASE_URL", "")


def _build_migration_url(raw: str) -> str:
    """Convert DATABASE_URL to a psycopg2 URL with IPv4 resolution."""
    if not raw:
        return raw
    # Switch to psycopg2 (sync driver) — asyncpg has no benefit for migrations
    if raw.startswith("postgres://"):
        url = raw.replace("postgres://", "postgresql+psycopg2://", 1)
    elif raw.startswith("postgresql+asyncpg://"):
        url = raw.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    elif raw.startswith("postgresql://"):
        url = raw.replace("postgresql://", "postgresql+psycopg2://", 1)
    else:
        url = raw
    # Force IPv4 to avoid IPv6 timeout in Railway containers
    hostname = "postgres.railway.internal"
    if hostname in url:
        try:
            results = socket.getaddrinfo(hostname, None, family=socket.AF_INET)
            if results:
                ipv4 = results[0][4][0]
                url = url.replace(hostname, ipv4)
                print(f"[alembic] Resolved {hostname} → {ipv4}")
        except OSError as exc:
            print(f"[alembic] WARNING: could not resolve {hostname} to IPv4: {exc}")
    return url


_migration_url = _build_migration_url(_raw_url)
_use_sync = True  # always use psycopg2 for migrations

if _migration_url:
    config.set_main_option("sqlalchemy.url", _migration_url)

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
    # Always use psycopg2 (sync) — more reliable in Railway containers than asyncpg
    run_migrations_sync()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

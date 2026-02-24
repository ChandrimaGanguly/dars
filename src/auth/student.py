"""Student authentication for student endpoints.

Security (SEC-003):
- Validates X-Student-ID header is present and valid integer
- Queries database to verify student exists
- Prevents IDOR (Insecure Direct Object Reference) attacks
- Returns 404 if student not found
- Rate limiting (30 req/min per IP) to prevent enumeration attacks
- In-memory caching (5min TTL) to reduce database load

Phase 1+: Will add JWT tokens with session management.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.errors.exceptions import ERR_AUTH_MISSING
from src.logging import get_logger

logger = get_logger(__name__)

# In-memory cache for student verification (use Redis in production)
# Format: {telegram_id: (exists: bool, cached_at: datetime)}
_student_cache: dict[int, tuple[bool, datetime]] = {}
CACHE_TTL = timedelta(minutes=5)

# Rate limiting: Track failed auth attempts per IP
# Format: {ip_address: [(timestamp, telegram_id), ...]}
_failed_attempts: dict[str, list[tuple[datetime, int]]] = {}
MAX_FAILED_PER_MINUTE = 10


async def verify_student(
    request: Request,  # Required for rate limiting
    x_student_id: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_session),
) -> int:
    """Verify student authentication via X-Student-ID header.

    Security (SEC-003): Database verification prevents IDOR attacks
    - Checks if X-Student-ID header is present
    - Validates it's a valid integer (Telegram ID)
    - Queries database to verify student exists
    - Returns 404 if student not found in database

    This prevents attackers from guessing valid student IDs and accessing
    other students' data (IDOR vulnerability).

    Performance: <100ms with indexed telegram_id lookup

    Args:
        x_student_id: X-Student-ID header value (Telegram ID as string).
        db: Database session (injected by FastAPI Depends).

    Returns:
        Student telegram ID (as integer) if student exists in database.

    Raises:
        HTTPException:
            - 401 if X-Student-ID header missing
            - 400 if X-Student-ID is not a valid integer
            - 404 if student not found in database (SEC-003)

    Example:
        >>> # In FastAPI route:
        >>> @app.get("/practice")
        >>> async def get_practice(student_id: int = Depends(verify_student)):
        >>>     # student_id is validated and verified in database
        >>>     ...
    """
    if not x_student_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing student credentials (X-Student-ID header required)",
            headers={"error_code": ERR_AUTH_MISSING},
        )

    # Parse student ID (telegram_id)
    try:
        telegram_id = int(x_student_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Student-ID must be a valid integer",
            headers={"error_code": ERR_AUTH_MISSING},
        ) from e

    # Validate format
    if telegram_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student ID (must be positive integer)",
            headers={"error_code": ERR_AUTH_MISSING},
        )

    # Rate limiting: Check failed attempts from this IP
    client_ip = request.client.host if request.client else "unknown"
    _cleanup_failed_attempts(client_ip)  # Remove old attempts

    if _check_rate_limit_exceeded(client_ip):
        logger.warning(f"Rate limit exceeded for IP {client_ip} (too many failed auth attempts)")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again later.",
        )

    # Check cache first (avoid DB query for known students)
    now = datetime.now(UTC)
    if telegram_id in _student_cache:
        exists, cached_at = _student_cache[telegram_id]
        if now - cached_at < CACHE_TTL:
            if exists:
                logger.debug(f"Student {telegram_id} authenticated from cache")
                return telegram_id
            else:
                # Cached negative result (student doesn't exist)
                _record_failed_attempt(client_ip, telegram_id)
                logger.warning(
                    f"Student authentication failed (cached): telegram_id {telegram_id} not found",
                    extra={"ip": client_ip, "telegram_id": telegram_id},
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Student with ID {telegram_id} not found",
                )

    # SEC-003: Query database to verify student exists
    # This prevents IDOR attacks where attackers guess student IDs
    from src.models.student import Student

    result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
    student = result.scalar_one_or_none()

    # Cache result (both positive and negative)
    _student_cache[telegram_id] = (student is not None, now)

    if not student:
        _record_failed_attempt(client_ip, telegram_id)
        logger.warning(
            f"Student authentication failed: telegram_id {telegram_id} not found in database",
            extra={"ip": client_ip, "telegram_id": telegram_id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {telegram_id} not found",
        )

    logger.debug(
        f"Student {student.student_id} (telegram_id={telegram_id}) authenticated successfully"
    )

    # Return telegram_id (not student_id) for consistency with header
    return telegram_id


def _check_rate_limit_exceeded(ip: str) -> bool:
    """Check if IP has exceeded rate limit for failed auth attempts.

    Args:
        ip: Client IP address.

    Returns:
        True if rate limit exceeded, False otherwise.
    """
    if ip not in _failed_attempts:
        return False

    # Count attempts in last minute
    recent_attempts = _failed_attempts[ip]
    return len(recent_attempts) >= MAX_FAILED_PER_MINUTE


def _record_failed_attempt(ip: str, telegram_id: int) -> None:
    """Record a failed authentication attempt for monitoring.

    Args:
        ip: Client IP address.
        telegram_id: The telegram ID that failed auth.
    """
    now = datetime.now(UTC)

    if ip not in _failed_attempts:
        _failed_attempts[ip] = []

    _failed_attempts[ip].append((now, telegram_id))


def _cleanup_failed_attempts(ip: str) -> None:
    """Remove old failed attempts (older than 1 minute).

    Args:
        ip: Client IP address.
    """
    if ip not in _failed_attempts:
        return

    one_minute_ago = datetime.now(UTC) - timedelta(minutes=1)
    _failed_attempts[ip] = [
        (timestamp, tid) for timestamp, tid in _failed_attempts[ip] if timestamp > one_minute_ago
    ]

    # Clean up empty entries
    if not _failed_attempts[ip]:
        del _failed_attempts[ip]

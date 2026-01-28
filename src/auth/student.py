"""Student authentication for student endpoints.

Phase 0: Simple X-Student-ID header validation.
Phase 1+: JWT tokens with session management.
"""

from typing import Annotated

from fastapi import Header, HTTPException, status

from src.errors.exceptions import ERR_AUTH_MISSING


async def verify_student(x_student_id: Annotated[str | None, Header()] = None) -> int:
    """Verify student authentication via X-Student-ID header.

    Phase 0 Implementation:
    - Checks if X-Student-ID header is present
    - Validates it's a valid integer (Telegram ID)
    - Returns the student ID

    Note: This is a simple implementation for Phase 0. In Phase 1+,
    this will validate JWT tokens and check database for active sessions.

    Args:
        x_student_id: X-Student-ID header value (Telegram ID as string).

    Returns:
        Student Telegram ID (as integer).

    Raises:
        HTTPException: If authentication fails (401).

    Example:
        >>> # In FastAPI route:
        >>> @app.get("/practice")
        >>> async def get_practice(student_id: int = Depends(verify_student)):
        >>>     # student_id is validated student Telegram ID
        >>>     ...
    """
    if not x_student_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing student credentials (X-Student-ID header required)",
            headers={"error_code": ERR_AUTH_MISSING},
        )

    # Parse student ID
    try:
        student_id = int(x_student_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Student-ID must be a valid integer",
            headers={"error_code": ERR_AUTH_MISSING},
        ) from e

    # In Phase 0, we just validate the ID format
    # In Phase 1+, we'll check database for student existence and session validity
    if student_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student ID (must be positive integer)",
            headers={"error_code": ERR_AUTH_MISSING},
        )

    return student_id

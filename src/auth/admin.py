"""Admin authentication for admin endpoints.

Phase 0: Hardcoded admin Telegram IDs from environment variable.
Phase 1: JWT tokens with proper session management.
"""

from typing import Annotated

from fastapi import Header, HTTPException, status

from src.config import get_settings
from src.errors.exceptions import ERR_ADMIN_ONLY, ERR_AUTH_MISSING


async def verify_admin(x_admin_id: Annotated[str | None, Header()] = None) -> int:
    """Verify admin authentication via X-Admin-ID header.

    Phase 0 Implementation:
    - Checks if X-Admin-ID header is present
    - Validates the ID is in the hardcoded list of admin Telegram IDs
    - Returns the admin ID if valid

    Args:
        x_admin_id: X-Admin-ID header value (Telegram ID as string).

    Returns:
        Admin Telegram ID (as integer).

    Raises:
        HTTPException: If authentication fails (401 or 403).

    Example:
        >>> # In FastAPI route:
        >>> @app.get("/admin/stats")
        >>> async def get_stats(admin_id: int = Depends(verify_admin)):
        >>>     # admin_id is validated admin Telegram ID
        >>>     ...
    """
    if not x_admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing admin credentials (X-Admin-ID header required)",
            headers={"error_code": ERR_AUTH_MISSING},
        )

    # Parse admin ID
    try:
        admin_id = int(x_admin_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Admin-ID must be a valid integer",
            headers={"error_code": ERR_AUTH_MISSING},
        ) from e

    # Check if admin ID is in allowed list
    settings = get_settings()
    admin_ids = settings.get_admin_ids()

    if not admin_ids:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No admin IDs configured (set ADMIN_TELEGRAM_IDS environment variable)",
        )

    if admin_id not in admin_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized (admin access only)",
            headers={"error_code": ERR_ADMIN_ONLY},
        )

    return admin_id

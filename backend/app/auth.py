"""Authentication dependencies for FastAPI."""

from fastapi import Request


async def get_current_instructor(
    request: Request,
) -> str:
    """Temporary no-auth dependency used by protected endpoints."""
    _ = request
    return "instructor"

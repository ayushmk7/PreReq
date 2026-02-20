"""Authentication dependencies for FastAPI."""

import secrets

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import settings

security = HTTPBasic(auto_error=False)


async def get_current_instructor(
    request: Request,
    credentials: HTTPBasicCredentials | None = Depends(security),
) -> str:
    """Return authenticated instructor identity.

    - Development mode: keeps permissive local behavior.
    - Production mode: requires HTTP Basic credentials from settings.
    """
    _ = request
    if settings.APP_ENV.lower() != "production":
        return "instructor"

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    valid_user = secrets.compare_digest(credentials.username, settings.INSTRUCTOR_USERNAME)
    valid_pass = secrets.compare_digest(credentials.password, settings.INSTRUCTOR_PASSWORD)
    if not (valid_user and valid_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

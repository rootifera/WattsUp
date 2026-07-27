import hmac
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from wattsup.core.config import Settings, get_settings

bearer = HTTPBearer(auto_error=False)


def authenticate(username: str, password: str, settings: Settings) -> bool:
    return hmac.compare_digest(username, settings.admin_username) and hmac.compare_digest(
        password, settings.admin_password
    )


def create_access_token(settings: Settings) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(hours=settings.jwt_expiry_hours)
    token = jwt.encode(
        {
            "sub": settings.admin_username,
            "exp": expires_at,
            "iat": datetime.now(UTC),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    return token, expires_at


def require_authenticated(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
    except InvalidTokenError as error:
        raise unauthorized from error
    subject = payload.get("sub")
    if not isinstance(subject, str) or not hmac.compare_digest(subject, settings.admin_username):
        raise unauthorized
    return subject

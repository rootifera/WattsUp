import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy import select

from wattsup.core.config import Settings, get_settings
from wattsup.models.configuration import Administrator

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt_text, digest_text = encoded.split("$", 2)
        if algorithm != "scrypt":
            return False
        salt = base64.b64decode(salt_text)
        expected = base64.b64decode(digest_text)
        actual = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_access_token(username: str, settings: Settings) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(hours=settings.jwt_expiry_hours)
    token = jwt.encode(
        {"sub": username, "exp": expires_at, "iat": datetime.now(UTC)},
        settings.jwt_secret,
        algorithm="HS256",
    )
    return token, expires_at


async def require_authenticated(
    request: Request,
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
    if not isinstance(subject, str):
        raise unauthorized
    async with request.app.state.database.sessions() as session:
        administrator = await session.scalar(
            select(Administrator).where(Administrator.username == subject)
        )
    if administrator is None:
        raise unauthorized
    return subject

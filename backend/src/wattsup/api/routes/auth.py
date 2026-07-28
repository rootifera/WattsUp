from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select

from wattsup.core.auth import create_access_token, verify_password
from wattsup.core.config import Settings, get_settings
from wattsup.models.configuration import Administrator
from wattsup.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(tags=["Authentication"])


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    async with request.app.state.database.sessions() as session:
        administrator = await session.scalar(
            select(Administrator).where(Administrator.username == body.username)
        )
    if administrator is None or not verify_password(body.password, administrator.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token, expires_at = create_access_token(administrator.username, settings)
    return TokenResponse(access_token=token, expires_at=expires_at)

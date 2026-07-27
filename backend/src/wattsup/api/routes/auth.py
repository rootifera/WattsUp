from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from wattsup.core.auth import authenticate, create_access_token
from wattsup.core.config import Settings, get_settings
from wattsup.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(tags=["Authentication"])


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    if not authenticate(body.username, body.password, settings):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token, expires_at = create_access_token(settings)
    return TokenResponse(access_token=token, expires_at=expires_at)

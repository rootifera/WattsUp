from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from wattsup.core.auth import require_authenticated
from wattsup.core.config import Settings, get_settings
from wattsup.nut.exceptions import NutError
from wattsup.nut.protocol import NutClient
from wattsup.schemas.variables import UpsVariable

router = APIRouter(tags=["UPS"], dependencies=[Depends(require_authenticated)])


def get_nut_client(request: Request) -> NutClient:
    return request.app.state.nut_client  # type: ignore[no-any-return]


@router.get("/variables", response_model=list[UpsVariable])
async def get_variables(
    client: Annotated[NutClient, Depends(get_nut_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[UpsVariable]:
    try:
        variables = await client.get_variables(settings.ups_name)
    except NutError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
        ) from error
    return [
        UpsVariable(name=name, value=value, group=name.partition(".")[0])
        for name, value in sorted(variables.items())
    ]

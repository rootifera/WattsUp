from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from wattsup.core.auth import require_authenticated
from wattsup.nut.exceptions import NutError
from wattsup.schemas.variables import UpsVariable
from wattsup.services.ups import UpsManager

router = APIRouter(tags=["UPS"], dependencies=[Depends(require_authenticated)])


@router.get("/variables", response_model=list[UpsVariable])
async def get_variables(request: Request, ups: Annotated[int, Query()]) -> list[UpsVariable]:
    manager: UpsManager = request.app.state.ups_manager
    try:
        variables = await manager.variables(ups)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except NutError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
        ) from error
    return [
        UpsVariable(name=name, value=value, group=name.partition(".")[0])
        for name, value in sorted(variables.items())
    ]

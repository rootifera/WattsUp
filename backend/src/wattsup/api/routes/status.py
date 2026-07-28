from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from wattsup.core.auth import require_authenticated
from wattsup.schemas.status import UpsStatus
from wattsup.services.ups import UpsManager

router = APIRouter(tags=["UPS"], dependencies=[Depends(require_authenticated)])


def manager(request: Request) -> UpsManager:
    return request.app.state.ups_manager  # type: ignore[no-any-return]


@router.get("/ups")
async def list_ups(request: Request) -> list[dict[str, str | int]]:
    units = await manager(request).list_units()
    return [
        {
            "id": unit.id,
            "name": str(unit.id),
            "description": f"{unit.server_name} · {unit.name}",
        }
        for unit in units
    ]


@router.get("/status", response_model=UpsStatus)
async def get_status(
    request: Request,
    ups: Annotated[int, Query()],
) -> UpsStatus:
    try:
        return await manager(request).status(ups)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

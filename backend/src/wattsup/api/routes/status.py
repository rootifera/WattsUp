from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from wattsup.api.dependencies import StatusServiceDependency
from wattsup.core.auth import require_authenticated
from wattsup.core.config import Settings, get_settings
from wattsup.nut.exceptions import NutError
from wattsup.nut.protocol import NutClient
from wattsup.schemas.status import UpsStatus

router = APIRouter(tags=["UPS"], dependencies=[Depends(require_authenticated)])


@router.get("/ups")
async def list_ups(
    request: Request, settings: Annotated[Settings, Depends(get_settings)]
) -> list[dict[str, str]]:
    client: NutClient = request.app.state.nut_client
    try:
        units = await client.list_ups()
    except NutError:
        units = {settings.ups_name: settings.ups_name}
    if not units:
        units = {settings.ups_name: settings.ups_name}
    return [{"name": name, "description": description} for name, description in units.items()]


@router.get("/status", response_model=UpsStatus)
async def get_status(
    service: StatusServiceDependency,
    ups: Annotated[str | None, Query()] = None,
) -> UpsStatus:
    return await service.get_status(ups)

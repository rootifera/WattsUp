from fastapi import APIRouter, Depends

from wattsup.api.dependencies import StatusServiceDependency
from wattsup.core.auth import require_authenticated
from wattsup.schemas.status import UpsStatus

router = APIRouter(tags=["UPS"], dependencies=[Depends(require_authenticated)])


@router.get("/status", response_model=UpsStatus)
async def get_status(service: StatusServiceDependency) -> UpsStatus:
    return await service.get_status()

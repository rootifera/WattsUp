from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from wattsup.core.auth import require_authenticated
from wattsup.core.config import Settings, get_settings
from wattsup.models.configuration import ManagedUps
from wattsup.repositories.readings import ReadingRepository
from wattsup.schemas.history import HistoryReading

router = APIRouter(tags=["UPS"], dependencies=[Depends(require_authenticated)])


class EnergySummary(BaseModel):
    current_watts: float | None
    power_source: str | None
    today_kwh: float
    month_kwh: float
    today_cost: float
    month_cost: float
    currency: str


def get_repository(request: Request) -> ReadingRepository:
    return request.app.state.reading_repository  # type: ignore[no-any-return]


@router.get("/history", response_model=list[HistoryReading])
async def get_history(
    repository: Annotated[ReadingRepository, Depends(get_repository)],
    ups: Annotated[str, Query()],
    hours: Annotated[int, Query(ge=1, le=24 * 90)] = 24,
    limit: Annotated[int, Query(ge=1, le=10_000)] = 2_880,
) -> list[HistoryReading]:
    readings = await repository.list_since(
        ups,
        datetime.now(UTC) - timedelta(hours=hours),
        limit,
    )
    return [HistoryReading.model_validate(reading) for reading in readings]


@router.get("/energy", response_model=EnergySummary)
async def get_energy(
    request: Request,
    repository: Annotated[ReadingRepository, Depends(get_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
    ups: Annotated[int, Query()],
) -> EnergySummary:
    now = datetime.now(UTC)
    async with request.app.state.database.sessions() as session:
        unit = await session.scalar(
            select(ManagedUps).options(selectinload(ManagedUps.server)).where(ManagedUps.id == ups)
        )
    if unit is None:
        raise HTTPException(status_code=404, detail="UPS not found")
    today = await repository.energy_since(
        str(ups),
        now.replace(hour=0, minute=0, second=0, microsecond=0),
        settings.poll_interval_seconds,
    )
    month = await repository.energy_since(
        str(ups),
        now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        settings.poll_interval_seconds,
    )
    status_value = await request.app.state.ups_manager.status(ups)
    price = float(unit.server.price_per_kwh)
    return EnergySummary(
        current_watts=status_value.power_watts,
        power_source=status_value.power_source,
        today_kwh=today,
        month_kwh=month,
        today_cost=today * price,
        month_cost=month * price,
        currency=unit.server.currency,
    )

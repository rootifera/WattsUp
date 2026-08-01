import calendar
from datetime import UTC, date, datetime, timedelta
from typing import Annotated, cast
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from wattsup.core.auth import require_authenticated
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


class BillingDay(BaseModel):
    date: date
    energy_kwh: float
    cost: float
    currency: str
    sample_count: int
    max_power_watts: float | None


class BillingMonth(BaseModel):
    month: str
    energy_kwh: float
    cost: float
    currency: str
    days: list[BillingDay]


class BillingPoint(BaseModel):
    recorded_at: datetime
    power_watts: float | None
    energy_kwh: float | None
    cost: float | None


class BillingDayDetail(BaseModel):
    summary: BillingDay
    raw_available: bool
    points: list[BillingPoint]


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
    ups: Annotated[int, Query()],
) -> EnergySummary:
    now = datetime.now(UTC)
    async with request.app.state.database.sessions() as session:
        unit = await session.scalar(
            select(ManagedUps).options(selectinload(ManagedUps.server)).where(ManagedUps.id == ups)
        )
    if unit is None:
        raise HTTPException(status_code=404, detail="UPS not found")
    local_now = now.astimezone(ZoneInfo(unit.server.timezone))
    daily = await repository.daily(ups, local_now.date().replace(day=1), local_now.date())
    today_row = next((row for row in daily if row.local_date == local_now.date()), None)
    today = today_row.energy_kwh if today_row else 0
    month = sum(row.energy_kwh for row in daily)
    status_value = await request.app.state.ups_manager.status(ups)
    return EnergySummary(
        current_watts=status_value.power_watts,
        power_source=status_value.power_source,
        today_kwh=today,
        month_kwh=month,
        today_cost=today_row.cost if today_row else 0,
        month_cost=sum(row.cost for row in daily),
        currency=unit.server.currency,
    )


async def get_unit(request: Request, ups: int) -> ManagedUps:
    async with request.app.state.database.sessions() as session:
        unit = await session.scalar(
            select(ManagedUps).options(selectinload(ManagedUps.server)).where(ManagedUps.id == ups)
        )
    if unit is None:
        raise HTTPException(status_code=404, detail="UPS not found")
    return cast(ManagedUps, unit)


@router.get("/billing/month", response_model=BillingMonth)
async def billing_month(
    request: Request,
    repository: Annotated[ReadingRepository, Depends(get_repository)],
    ups: Annotated[int, Query()],
    month: Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")],
) -> BillingMonth:
    unit = await get_unit(request, ups)
    year, month_number = map(int, month.split("-"))
    try:
        last_day = calendar.monthrange(year, month_number)[1]
    except calendar.IllegalMonthError as error:
        raise HTTPException(status_code=422, detail="Invalid month") from error
    start, end = date(year, month_number, 1), date(year, month_number, last_day)
    indexed = {row.local_date: row for row in await repository.daily(ups, start, end)}
    days = [
        BillingDay(
            date=day,
            energy_kwh=(row.energy_kwh if (row := indexed.get(day)) else 0),
            cost=row.cost if row else 0,
            currency=row.currency if row else unit.server.currency,
            sample_count=row.sample_count if row else 0,
            max_power_watts=row.max_power_watts if row else None,
        )
        for number in range(1, last_day + 1)
        if (day := date(year, month_number, number))
    ]
    return BillingMonth(
        month=month,
        energy_kwh=sum(day.energy_kwh for day in days),
        cost=sum(day.cost for day in days),
        currency=unit.server.currency,
        days=days,
    )


@router.get("/billing/day", response_model=BillingDayDetail)
async def billing_day(
    request: Request,
    repository: Annotated[ReadingRepository, Depends(get_repository)],
    ups: Annotated[int, Query()],
    day: date,
) -> BillingDayDetail:
    unit = await get_unit(request, ups)
    rows = await repository.daily(ups, day, day)
    row = rows[0] if rows else None
    readings = await repository.day_readings(ups, day)
    summary = BillingDay(
        date=day,
        energy_kwh=row.energy_kwh if row else 0,
        cost=row.cost if row else 0,
        currency=row.currency if row else unit.server.currency,
        sample_count=row.sample_count if row else 0,
        max_power_watts=row.max_power_watts if row else None,
    )
    return BillingDayDetail(
        summary=summary,
        raw_available=bool(readings),
        points=[BillingPoint.model_validate(reading, from_attributes=True) for reading in readings],
    )

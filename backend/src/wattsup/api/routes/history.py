from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from wattsup.core.auth import require_authenticated
from wattsup.repositories.readings import ReadingRepository
from wattsup.schemas.history import HistoryReading

router = APIRouter(tags=["UPS"], dependencies=[Depends(require_authenticated)])


def get_repository(request: Request) -> ReadingRepository:
    return request.app.state.reading_repository  # type: ignore[no-any-return]


@router.get("/history", response_model=list[HistoryReading])
async def get_history(
    repository: Annotated[ReadingRepository, Depends(get_repository)],
    hours: Annotated[int, Query(ge=1, le=24 * 90)] = 24,
    limit: Annotated[int, Query(ge=1, le=10_000)] = 2_880,
) -> list[HistoryReading]:
    readings = await repository.list_since(datetime.now(UTC) - timedelta(hours=hours), limit)
    return [HistoryReading.model_validate(reading) for reading in readings]

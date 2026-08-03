import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from wattsup.core.auth import require_authenticated
from wattsup.nut.exceptions import NutError
from wattsup.schemas.commands import (
    BatteryTestSchedule,
    BatteryTestScheduleUpdate,
    CommandInfo,
    CommandResult,
    ExecuteCommandRequest,
)
from wattsup.services.battery_tests import BatteryTestScheduler
from wattsup.services.ups import UpsManager

router = APIRouter(tags=["Commands"], dependencies=[Depends(require_authenticated)])
logger = logging.getLogger(__name__)


@router.get("/commands", response_model=list[CommandInfo])
async def get_commands(request: Request, ups: Annotated[int, Query()]) -> list[CommandInfo]:
    manager: UpsManager = request.app.state.ups_manager
    try:
        return [CommandInfo(**item.__dict__) for item in await manager.commands(ups)]
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except NutError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/command/{name}", response_model=CommandResult)
async def execute_command(
    name: str,
    body: ExecuteCommandRequest,
    request: Request,
    ups: Annotated[int, Query()],
) -> CommandResult:
    manager: UpsManager = request.app.state.ups_manager
    try:
        await manager.execute(ups, name, body.confirmed)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except NutError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    scheduler: BatteryTestScheduler = request.app.state.battery_test_scheduler
    try:
        await scheduler.record_started(ups, name)
    except Exception:
        # Test bookkeeping must never make a successfully dispatched NUT command look failed.
        logger.exception("Could not record battery test command for UPS %s", ups)
    return CommandResult()


@router.get("/battery-test-schedule", response_model=BatteryTestSchedule)
async def get_battery_test_schedule(
    request: Request, ups: Annotated[int, Query()]
) -> BatteryTestSchedule:
    try:
        return await request.app.state.battery_test_scheduler.get(ups)  # type: ignore[no-any-return]
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.put("/battery-test-schedule", response_model=BatteryTestSchedule)
async def update_battery_test_schedule(
    body: BatteryTestScheduleUpdate, request: Request, ups: Annotated[int, Query()]
) -> BatteryTestSchedule:
    try:
        return await request.app.state.battery_test_scheduler.update(  # type: ignore[no-any-return]
            ups, quick_enabled=body.quick_enabled, deep_enabled=body.deep_enabled
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

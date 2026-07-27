from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from wattsup.core.auth import require_authenticated
from wattsup.nut.exceptions import NutError
from wattsup.schemas.commands import CommandInfo, CommandResult, ExecuteCommandRequest
from wattsup.services.commands import CommandService

router = APIRouter(tags=["Commands"], dependencies=[Depends(require_authenticated)])


def get_command_service(request: Request) -> CommandService:
    return request.app.state.command_service  # type: ignore[no-any-return]


CommandServiceDependency = Annotated[CommandService, Depends(get_command_service)]


@router.get("/commands", response_model=list[CommandInfo])
async def get_commands(
    service: CommandServiceDependency,
    ups: Annotated[str | None, Query()] = None,
) -> list[CommandInfo]:
    try:
        return [CommandInfo(**item.__dict__) for item in await service.list_commands(ups)]
    except NutError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
        ) from error


@router.post("/command/{name}", response_model=CommandResult)
async def execute_command(
    name: str,
    body: ExecuteCommandRequest,
    service: CommandServiceDependency,
    ups: Annotated[str | None, Query()] = None,
) -> CommandResult:
    try:
        await service.execute(name, confirmed=body.confirmed, ups_name=ups)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except NutError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    return CommandResult()

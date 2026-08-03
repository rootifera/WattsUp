from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from wattsup.api.routes.commands import execute_command
from wattsup.schemas.commands import ExecuteCommandRequest
from wattsup.services.commands import CommandService


async def test_dangerous_command_requires_confirmation() -> None:
    client = AsyncMock()
    client.get_supported_commands.return_value = ["load.off", "test.battery.start.quick"]
    service = CommandService(client, "ups")

    with pytest.raises(PermissionError):
        await service.execute("load.off", confirmed=False)

    client.execute_command.assert_not_awaited()


async def test_executes_discovered_safe_command() -> None:
    client = AsyncMock()
    client.get_supported_commands.return_value = ["test.battery.start.quick"]
    service = CommandService(client, "ups")

    await service.execute("test.battery.start.quick", confirmed=False)

    client.execute_command.assert_awaited_once_with("ups", "test.battery.start.quick")


async def test_successful_command_is_not_failed_by_schedule_bookkeeping() -> None:
    manager = SimpleNamespace(execute=AsyncMock())
    scheduler = SimpleNamespace(
        record_started=AsyncMock(side_effect=RuntimeError("db unavailable"))
    )
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(ups_manager=manager, battery_test_scheduler=scheduler)
        )
    )

    result = await execute_command(
        "test.battery.start.quick",
        ExecuteCommandRequest(),
        request,
        ups=1,
    )

    assert result.accepted
    manager.execute.assert_awaited_once_with(1, "test.battery.start.quick", False)

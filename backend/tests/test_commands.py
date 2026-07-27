from unittest.mock import AsyncMock

import pytest

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

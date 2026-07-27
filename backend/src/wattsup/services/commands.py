from dataclasses import dataclass

from wattsup.nut.protocol import NutClient

DANGEROUS_COMMANDS = {
    "driver.killpower",
    "load.off",
    "load.off.delay",
    "shutdown.reboot",
    "shutdown.return",
    "shutdown.stayoff",
    "shutdown.stop",
}

CATEGORY_PREFIXES = {
    "test.battery": "battery",
    "beeper": "beeper",
    "test.panel": "panel",
    "driver.": "driver",
}


@dataclass(frozen=True)
class SupportedCommand:
    name: str
    category: str
    dangerous: bool
    description: str | None


class CommandService:
    def __init__(self, client: NutClient, default_ups_name: str) -> None:
        self.client = client
        self.default_ups_name = default_ups_name

    async def list_commands(self, ups_name: str | None = None) -> list[SupportedCommand]:
        ups_name = ups_name or self.default_ups_name
        names = await self.client.get_supported_commands(ups_name)
        commands: list[SupportedCommand] = []
        for name in sorted(names):
            commands.append(
                SupportedCommand(
                    name=name,
                    category=self._category(name),
                    dangerous=name in DANGEROUS_COMMANDS,
                    description=await self.client.get_command_description(ups_name, name),
                )
            )
        return commands

    async def execute(self, command: str, *, confirmed: bool, ups_name: str | None = None) -> None:
        ups_name = ups_name or self.default_ups_name
        supported = {item.name: item for item in await self.list_commands(ups_name)}
        item = supported.get(command)
        if item is None:
            raise ValueError("Command is not supported by this UPS")
        if item.dangerous and not confirmed:
            raise PermissionError("Dangerous command requires explicit confirmation")
        await self.client.execute_command(ups_name, command)

    @staticmethod
    def _category(name: str) -> str:
        if name in DANGEROUS_COMMANDS:
            return "dangerous"
        for prefix, category in CATEGORY_PREFIXES.items():
            if name.startswith(prefix):
                return category
        return "other"

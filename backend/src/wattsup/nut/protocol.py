import asyncio
import contextlib
import shlex
from collections.abc import AsyncIterator

from wattsup.nut.exceptions import NutConnectionError, NutProtocolError


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


class NutClient:
    """Small async client for the text-based NUT upsd protocol."""

    def __init__(
        self,
        host: str,
        port: int = 3493,
        *,
        username: str | None = None,
        password: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout

    @contextlib.asynccontextmanager
    async def _connection(
        self, *, authenticate: bool = False
    ) -> AsyncIterator[tuple[asyncio.StreamReader, asyncio.StreamWriter]]:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=self.timeout
            )
        except (OSError, TimeoutError) as error:
            raise NutConnectionError(
                f"Could not connect to NUT at {self.host}:{self.port}"
            ) from error

        try:
            if authenticate:
                await self._authenticate(reader, writer)
            yield reader, writer
        finally:
            writer.close()
            with contextlib.suppress(OSError):
                await writer.wait_closed()

    async def _send(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, command: str
    ) -> str:
        writer.write(f"{command}\n".encode())
        await writer.drain()
        try:
            response = (await asyncio.wait_for(reader.readline(), self.timeout)).decode().strip()
        except (UnicodeDecodeError, TimeoutError) as error:
            raise NutProtocolError("Invalid response from NUT server") from error
        if not response:
            raise NutProtocolError("NUT server closed the connection")
        if response.startswith("ERR "):
            raise NutProtocolError(response.removeprefix("ERR "))
        return response

    async def _authenticate(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        if not self.username or not self.password:
            raise NutProtocolError("NUT credentials are required to execute commands")
        await self._expect_ok(reader, writer, f"USERNAME {_quote(self.username)}")
        await self._expect_ok(reader, writer, f"PASSWORD {_quote(self.password)}")

    async def _expect_ok(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, command: str
    ) -> None:
        response = await self._send(reader, writer, command)
        if response != "OK":
            raise NutProtocolError(f"Expected OK, received: {response}")

    async def get_variables(self, ups_name: str) -> dict[str, str]:
        async with self._connection() as (reader, writer):
            response = await self._send(reader, writer, f"LIST VAR {_quote(ups_name)}")
            if not response.startswith("BEGIN LIST VAR "):
                raise NutProtocolError(f"Unexpected response: {response}")

            variables: dict[str, str] = {}
            while True:
                response = await self._send_line(reader)
                if response.startswith("END LIST VAR "):
                    return variables
                parts = shlex.split(response)
                if len(parts) >= 4 and parts[0] == "VAR":
                    variables[parts[2]] = parts[3]
                else:
                    raise NutProtocolError(f"Unexpected variable response: {response}")

    async def get_supported_commands(self, ups_name: str) -> list[str]:
        async with self._connection() as (reader, writer):
            response = await self._send(reader, writer, f"LIST CMD {_quote(ups_name)}")
            if not response.startswith("BEGIN LIST CMD "):
                raise NutProtocolError(f"Unexpected response: {response}")
            commands: list[str] = []
            while True:
                response = await self._send_line(reader)
                if response.startswith("END LIST CMD "):
                    return commands
                parts = shlex.split(response)
                if len(parts) >= 3 and parts[0] == "CMD":
                    commands.append(parts[2])
                else:
                    raise NutProtocolError(f"Unexpected command response: {response}")

    async def get_command_description(self, ups_name: str, command: str) -> str | None:
        async with self._connection() as (reader, writer):
            try:
                response = await self._send(
                    reader,
                    writer,
                    f"GET CMDDESC {_quote(ups_name)} {_quote(command)}",
                )
            except NutProtocolError:
                return None
        parts = shlex.split(response)
        if len(parts) >= 4 and parts[0] == "CMDDESC":
            return parts[3]
        return None

    async def execute_command(self, ups_name: str, command: str) -> None:
        async with self._connection(authenticate=True) as (reader, writer):
            await self._expect_ok(
                reader,
                writer,
                f"INSTCMD {_quote(ups_name)} {_quote(command)}",
            )

    async def _send_line(self, reader: asyncio.StreamReader) -> str:
        try:
            response = (await asyncio.wait_for(reader.readline(), self.timeout)).decode().strip()
        except (UnicodeDecodeError, TimeoutError) as error:
            raise NutProtocolError("Invalid response from NUT server") from error
        if not response:
            raise NutProtocolError("NUT server closed the connection")
        if response.startswith("ERR "):
            raise NutProtocolError(response.removeprefix("ERR "))
        return response

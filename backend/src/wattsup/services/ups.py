from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from wattsup.core.secrets import SecretBox
from wattsup.models.configuration import ManagedUps, NutServer
from wattsup.nut.exceptions import NutError
from wattsup.nut.protocol import NutClient
from wattsup.schemas.status import UpsStatus
from wattsup.services.commands import CommandService, SupportedCommand
from wattsup.services.status import StatusService


@dataclass(frozen=True)
class UpsInfo:
    id: int
    name: str
    description: str
    server_name: str


class UpsManager:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        secret_box: SecretBox,
    ) -> None:
        self.sessions = sessions
        self.secret_box = secret_box
        self._status_services: dict[int, StatusService] = {}

    async def _unit(self, ups_id: int) -> ManagedUps:
        async with self.sessions() as session:
            unit = await session.scalar(
                select(ManagedUps)
                .options(selectinload(ManagedUps.server))
                .where(ManagedUps.id == ups_id, ManagedUps.enabled.is_(True))
            )
            if unit is None:
                raise LookupError("UPS not found")
            session.expunge(unit)
            return unit

    def _client(self, unit: ManagedUps) -> NutClient:
        return NutClient(
            unit.server.host,
            unit.server.port,
            username=self.secret_box.decrypt(unit.server.username_encrypted),
            password=self.secret_box.decrypt(unit.server.password_encrypted),
            timeout=unit.server.timeout_seconds,
        )

    async def list_units(self) -> list[UpsInfo]:
        async with self.sessions() as session:
            units = (
                await session.scalars(
                    select(ManagedUps)
                    .options(selectinload(ManagedUps.server))
                    .join(ManagedUps.server)
                    .where(ManagedUps.enabled.is_(True))
                    .order_by(ManagedUps.display_name)
                )
            ).all()
            return [
                UpsInfo(
                    id=unit.id,
                    name=unit.display_name,
                    description=unit.description or unit.nut_name,
                    server_name=unit.server.name,
                )
                for unit in units
            ]

    async def discover(self) -> None:
        async with self.sessions() as session:
            servers = (
                await session.scalars(select(NutServer).where(NutServer.enabled.is_(True)))
            ).all()
            for server in servers:
                client = NutClient(
                    server.host,
                    server.port,
                    username=self.secret_box.decrypt(server.username_encrypted),
                    password=self.secret_box.decrypt(server.password_encrypted),
                    timeout=server.timeout_seconds,
                )
                try:
                    discovered = await client.list_ups()
                except NutError:
                    continue
                existing = {
                    unit.nut_name: unit
                    for unit in (
                        await session.scalars(
                            select(ManagedUps).where(ManagedUps.server_id == server.id)
                        )
                    ).all()
                }
                for name, description in discovered.items():
                    if name not in existing:
                        session.add(
                            ManagedUps(
                                server_id=server.id,
                                nut_name=name,
                                display_name=description or name,
                                description=description,
                            )
                        )
                    else:
                        existing[name].description = description
            await session.commit()

    async def status(self, ups_id: int) -> UpsStatus:
        unit = await self._unit(ups_id)
        service = self._status_services.get(ups_id)
        if service is None:
            service = StatusService(self._client(unit), str(ups_id))
            self._status_services[ups_id] = service
        status = await service.get_status(unit.nut_name)
        return status.model_copy(update={"ups_name": str(ups_id)})

    async def variables(self, ups_id: int) -> dict[str, str]:
        unit = await self._unit(ups_id)
        return await self._client(unit).get_variables(unit.nut_name)

    async def commands(self, ups_id: int) -> list[SupportedCommand]:
        unit = await self._unit(ups_id)
        return await CommandService(self._client(unit), unit.nut_name).list_commands()

    async def execute(self, ups_id: int, command: str, confirmed: bool) -> None:
        unit = await self._unit(ups_id)
        await CommandService(self._client(unit), unit.nut_name).execute(
            command, confirmed=confirmed
        )

    def invalidate(self, ups_ids: set[int]) -> None:
        for ups_id in ups_ids:
            self._status_services.pop(ups_id, None)

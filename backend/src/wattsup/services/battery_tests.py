import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from wattsup.models.configuration import ManagedUps
from wattsup.schemas.commands import BatteryTestSchedule
from wattsup.schemas.status import UpsStatus
from wattsup.services.ups import UpsManager

logger = logging.getLogger(__name__)


class BatteryTestScheduler:
    def __init__(
        self, sessions: async_sessionmaker[AsyncSession], ups_manager: UpsManager
    ) -> None:
        self.sessions = sessions
        self.ups_manager = ups_manager

    async def observe(self, status: UpsStatus) -> None:
        ups_id = int(status.ups_name)
        now = datetime.now(UTC)
        command: str | None = None
        async with self.sessions() as session:
            unit = await session.scalar(select(ManagedUps).where(ManagedUps.id == ups_id))
            if unit is None:
                return
            if (
                status.battery_test_result
                and status.battery_test_result != unit.last_battery_test_result
            ):
                unit.last_battery_test_result = status.battery_test_result
                unit.last_battery_test_result_at = now
            # Prefer the less frequent deep test when both become due.
            if unit.deep_test_enabled and self._due(unit.last_deep_test_at, now, 30):
                command = "test.battery.start.deep"
            elif unit.quick_test_enabled and self._due(unit.last_quick_test_at, now, 7):
                command = "test.battery.start.quick"
            await session.commit()
        if command is not None:
            try:
                supported = {item.name for item in await self.ups_manager.commands(ups_id)}
                if command not in supported:
                    logger.warning("UPS %s does not support scheduled command %s", ups_id, command)
                    await self.record_started(ups_id, command)
                    return
                await self.ups_manager.execute(ups_id, command, False)
                await self.record_started(ups_id, command)
            except Exception:
                logger.exception("Scheduled battery test failed for UPS %s", ups_id)

    async def get(self, ups_id: int) -> BatteryTestSchedule:
        async with self.sessions() as session:
            unit = await session.get(ManagedUps, ups_id)
            if unit is None:
                raise LookupError("UPS not found")
            return self._schema(unit)

    async def update(
        self, ups_id: int, *, quick_enabled: bool, deep_enabled: bool
    ) -> BatteryTestSchedule:
        async with self.sessions() as session:
            unit = await session.get(ManagedUps, ups_id)
            if unit is None:
                raise LookupError("UPS not found")
            unit.quick_test_enabled = quick_enabled
            unit.deep_test_enabled = deep_enabled
            await session.commit()
            return self._schema(unit)

    async def record_started(self, ups_id: int, command: str) -> None:
        if command not in {"test.battery.start.quick", "test.battery.start.deep"}:
            return
        async with self.sessions() as session:
            unit = await session.get(ManagedUps, ups_id)
            if unit is None:
                return
            if command.endswith("quick"):
                unit.last_quick_test_at = datetime.now(UTC)
            else:
                unit.last_deep_test_at = datetime.now(UTC)
                unit.last_quick_test_at = unit.last_deep_test_at
            await session.commit()

    @staticmethod
    def _due(last_run: datetime | None, now: datetime, days: int) -> bool:
        if last_run is None:
            return False
        if last_run.tzinfo is None:
            last_run = last_run.replace(tzinfo=UTC)
        return now - last_run >= timedelta(days=days)

    @staticmethod
    def _schema(unit: ManagedUps) -> BatteryTestSchedule:
        return BatteryTestSchedule(
            quick_enabled=unit.quick_test_enabled,
            deep_enabled=unit.deep_test_enabled,
            last_quick_test_at=unit.last_quick_test_at,
            last_deep_test_at=unit.last_deep_test_at,
            last_result=unit.last_battery_test_result,
            last_result_at=unit.last_battery_test_result_at,
        )

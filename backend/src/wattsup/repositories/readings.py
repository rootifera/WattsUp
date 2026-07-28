from datetime import datetime

from sqlalchemy import Select, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from wattsup.models.reading import UpsReading
from wattsup.schemas.status import UpsStatus


class ReadingRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self.sessions = sessions

    async def add(self, status: UpsStatus) -> None:
        reading = UpsReading(
            ups_name=status.ups_name,
            recorded_at=status.last_poll_at,
            status=status.status,
            battery_charge=status.battery_charge,
            battery_voltage=status.battery_voltage,
            runtime_seconds=status.runtime_seconds,
            input_voltage=status.input_voltage,
            output_voltage=status.output_voltage,
            load_percent=status.load_percent,
            power_watts=status.power_watts,
            power_source=status.power_source,
        )
        async with self.sessions() as session:
            session.add(reading)
            await session.commit()

    async def list_since(self, ups_name: str, since: datetime, limit: int) -> list[UpsReading]:
        query: Select[tuple[UpsReading]] = (
            select(UpsReading)
            .where(UpsReading.ups_name == ups_name, UpsReading.recorded_at >= since)
            .order_by(desc(UpsReading.recorded_at))
            .limit(limit)
        )
        async with self.sessions() as session:
            result = await session.scalars(query)
            return list(reversed(result.all()))

    async def energy_since(self, ups_name: str, since: datetime, interval_seconds: int) -> float:
        query = select(func.coalesce(func.sum(UpsReading.power_watts), 0.0)).where(
            UpsReading.ups_name == ups_name,
            UpsReading.recorded_at >= since,
            UpsReading.power_watts.is_not(None),
        )
        async with self.sessions() as session:
            watts = float(await session.scalar(query) or 0)
        return watts * interval_seconds / 3_600_000

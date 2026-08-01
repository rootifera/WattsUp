from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import Select, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from wattsup.models.configuration import (
    DailyEnergy,
    ManagedUps,
    NutServer,
    RetentionSettings,
    TariffRate,
)
from wattsup.models.reading import UpsReading
from wattsup.schemas.status import UpsStatus


class ReadingRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession], interval_seconds: int) -> None:
        self.sessions = sessions
        self.interval_seconds = interval_seconds

    async def add(self, status: UpsStatus) -> None:
        async with self.sessions() as session:
            ups_id = int(status.ups_name)
            unit = await session.get(ManagedUps, ups_id)
            if unit is None:
                return
            server = await session.get(NutServer, unit.server_id)
            if server is None:
                return
            tariff = await session.scalar(
                select(TariffRate)
                .where(
                    TariffRate.server_id == server.id,
                    TariffRate.effective_from <= status.last_poll_at,
                )
                .order_by(desc(TariffRate.effective_from))
                .limit(1)
            )
            price = float(tariff.price_per_kwh if tariff else server.price_per_kwh)
            currency = tariff.currency if tariff else server.currency
            energy = (status.power_watts or 0) * self.interval_seconds / 3_600_000
            local_date = status.last_poll_at.astimezone(ZoneInfo(server.timezone)).date()
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
                energy_kwh=energy,
                cost=energy * price,
                currency=currency,
                local_date=local_date,
            )
            session.add(reading)
            daily = await session.scalar(
                select(DailyEnergy).where(
                    DailyEnergy.ups_id == ups_id, DailyEnergy.local_date == local_date
                )
            )
            if daily is None:
                daily = DailyEnergy(
                    ups_id=ups_id,
                    local_date=local_date,
                    energy_kwh=0,
                    cost=0,
                    currency=currency,
                    sample_count=0,
                    max_power_watts=None,
                )
                session.add(daily)
            daily.energy_kwh += energy
            daily.cost += energy * price
            daily.sample_count += 1
            daily.currency = currency
            if status.power_watts is not None:
                daily.max_power_watts = max(daily.max_power_watts or 0, status.power_watts)
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

    async def daily(self, ups_id: int, start: date, end: date) -> list[DailyEnergy]:
        async with self.sessions() as session:
            return list(
                (
                    await session.scalars(
                        select(DailyEnergy)
                        .where(
                            DailyEnergy.ups_id == ups_id,
                            DailyEnergy.local_date >= start,
                            DailyEnergy.local_date <= end,
                        )
                        .order_by(DailyEnergy.local_date)
                    )
                ).all()
            )

    async def day_readings(self, ups_id: int, day: date) -> list[UpsReading]:
        async with self.sessions() as session:
            return list(
                (
                    await session.scalars(
                        select(UpsReading)
                        .where(UpsReading.ups_name == str(ups_id), UpsReading.local_date == day)
                        .order_by(UpsReading.recorded_at)
                    )
                ).all()
            )

    async def retention(self) -> RetentionSettings:
        async with self.sessions() as session:
            value = await session.get(RetentionSettings, 1)
            if value is None:
                value = RetentionSettings(id=1, raw_days=None)
                session.add(value)
                await session.commit()
            session.expunge(value)
            return value

    async def set_retention(self, raw_days: int | None) -> RetentionSettings:
        async with self.sessions() as session:
            value = await session.get(RetentionSettings, 1) or RetentionSettings(id=1)
            session.add(value)
            value.raw_days = raw_days
            await session.commit()
            await session.refresh(value)
            session.expunge(value)
            return value

    async def prune(self) -> int:
        retention = await self.retention()
        if retention.raw_days is None:
            return 0
        async with self.sessions() as session:
            result = await session.execute(
                delete(UpsReading).where(
                    UpsReading.recorded_at < datetime.now(UTC) - timedelta(days=retention.raw_days)
                )
            )
            await session.commit()
            return int(getattr(result, "rowcount", 0) or 0)

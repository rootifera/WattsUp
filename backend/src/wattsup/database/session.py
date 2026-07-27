from collections.abc import AsyncIterator

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from wattsup.core.config import Settings
from wattsup.database.base import Base


class Database:
    def __init__(self, settings: Settings) -> None:
        self.engine: AsyncEngine = create_async_engine(settings.database_url)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_schema(self, default_ups_name: str) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            columns = await connection.run_sync(
                lambda sync: {
                    table: {item["name"] for item in inspect(sync).get_columns(table)}
                    for table in ("ups_readings", "remote_devices")
                }
            )
            for table in ("ups_readings", "remote_devices"):
                if "ups_name" not in columns[table]:
                    await connection.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN ups_name VARCHAR(255)")
                    )
                    await connection.execute(
                        text(f"UPDATE {table} SET ups_name = :ups_name"),
                        {"ups_name": default_ups_name},
                    )
                await connection.execute(
                    text(
                        f"CREATE INDEX IF NOT EXISTS ix_{table}_ups_name " f"ON {table} (ups_name)"
                    )
                )

    async def close(self) -> None:
        await self.engine.dispose()

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.sessions() as session:
            yield session

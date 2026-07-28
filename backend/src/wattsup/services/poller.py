import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable

from wattsup.repositories.readings import ReadingRepository
from wattsup.schemas.status import UpsStatus
from wattsup.services.ups import UpsManager

logger = logging.getLogger(__name__)


class Poller:
    def __init__(
        self,
        ups_manager: UpsManager,
        repository: ReadingRepository,
        interval_seconds: int,
        on_status: Callable[[UpsStatus], Awaitable[None]] | None = None,
    ) -> None:
        self.ups_manager = ups_manager
        self.repository = repository
        self.interval_seconds = interval_seconds
        self.on_status = on_status
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name="ups-poller")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _run(self) -> None:
        while True:
            try:
                await self.ups_manager.discover()
                units = await self.ups_manager.list_units()
                for unit in units:
                    status = await self.ups_manager.status(unit.id)
                    if status.connected:
                        await self.repository.add(status)
                    if self.on_status is not None:
                        await self.on_status(status)
            except Exception:
                logger.exception("UPS polling failed")
            await asyncio.sleep(self.interval_seconds)

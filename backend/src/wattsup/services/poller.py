import asyncio
import contextlib
import logging

from wattsup.repositories.readings import ReadingRepository
from wattsup.services.status import StatusService

logger = logging.getLogger(__name__)


class Poller:
    def __init__(
        self,
        status_service: StatusService,
        repository: ReadingRepository,
        interval_seconds: int,
    ) -> None:
        self.status_service = status_service
        self.repository = repository
        self.interval_seconds = interval_seconds
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
                status = await self.status_service.get_status()
                if status.connected:
                    await self.repository.add(status)
            except Exception:
                logger.exception("UPS polling failed")
            await asyncio.sleep(self.interval_seconds)

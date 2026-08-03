from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from wattsup.api.router import api_router
from wattsup.core.config import get_settings
from wattsup.core.secrets import SecretBox
from wattsup.database.session import Database
from wattsup.models import UpsReading  # noqa: F401
from wattsup.repositories.readings import ReadingRepository
from wattsup.schemas.status import UpsStatus
from wattsup.services.battery_tests import BatteryTestScheduler
from wattsup.services.notifications import NotificationDispatcher
from wattsup.services.poller import Poller
from wattsup.services.shutdown import ShutdownService
from wattsup.services.ups import UpsManager
from wattsup.shutdown.ssh import SshService


def create_app() -> FastAPI:
    settings = get_settings()
    database = Database(settings)
    ssh_service = SshService(settings.ssh_key_path)
    shutdown_service = ShutdownService(database.sessions, ssh_service)
    reading_repository = ReadingRepository(database.sessions, settings.poll_interval_seconds)
    ups_manager = UpsManager(database.sessions, SecretBox(settings.jwt_secret))
    notifier = NotificationDispatcher(database.sessions, SecretBox(settings.jwt_secret))
    battery_test_scheduler = BatteryTestScheduler(database.sessions, ups_manager)

    async def status_observed(value: UpsStatus) -> None:
        await battery_test_scheduler.observe(value)
        await notifier.evaluate(value)
        await shutdown_service.evaluate_status(value)

    poller = Poller(
        ups_manager,
        reading_repository,
        settings.poll_interval_seconds,
        on_status=status_observed,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await database.create_schema(settings.ups_name)
        ssh_service.ensure_key()
        poller.start()
        try:
            yield
        finally:
            await poller.stop()
            await database.close()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url=f"{settings.api_prefix}/docs",
        openapi_url=f"{settings.api_prefix}/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.database = database
    app.state.ups_manager = ups_manager
    app.state.reading_repository = reading_repository
    app.state.shutdown_service = shutdown_service
    app.state.battery_test_scheduler = battery_test_scheduler
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/adduser.sh", response_class=PlainTextResponse, include_in_schema=False)
    async def adduser_script() -> PlainTextResponse:
        return PlainTextResponse(
            ssh_service.setup_script(),
            media_type="text/x-shellscript",
            headers={"Content-Disposition": 'inline; filename="adduser.sh"'},
        )

    frontend_dist = settings.frontend_dist.resolve()
    if frontend_dist.is_dir():
        assets = frontend_dist / "assets"
        if assets.is_dir():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        async def frontend(path: str) -> FileResponse:
            requested = (frontend_dist / path).resolve()
            if requested.is_relative_to(frontend_dist) and requested.is_file():
                return FileResponse(requested)
            return FileResponse(frontend_dist / "index.html")

    return app


app = create_app()

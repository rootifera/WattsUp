from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from wattsup.api.router import api_router
from wattsup.core.config import get_settings
from wattsup.database.session import Database
from wattsup.models import UpsReading  # noqa: F401
from wattsup.nut.protocol import NutClient
from wattsup.repositories.readings import ReadingRepository
from wattsup.services.commands import CommandService
from wattsup.services.poller import Poller
from wattsup.services.shutdown import ShutdownService
from wattsup.services.status import StatusService
from wattsup.shutdown.ssh import SshService


def create_app() -> FastAPI:
    settings = get_settings()
    database = Database(settings)
    client = NutClient(
        settings.nut_host,
        settings.nut_port,
        username=settings.nut_username,
        password=settings.nut_password,
        timeout=settings.nut_timeout_seconds,
    )
    status_service = StatusService(client, settings.ups_name)
    ssh_service = SshService(settings.ssh_key_path)
    shutdown_service = ShutdownService(database.sessions, ssh_service)
    reading_repository = ReadingRepository(database.sessions)
    poller = Poller(
        status_service,
        reading_repository,
        settings.poll_interval_seconds,
        on_status=shutdown_service.evaluate_status,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await database.create_schema()
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
    app.state.status_service = status_service
    app.state.nut_client = client
    app.state.command_service = CommandService(client, settings.ups_name)
    app.state.reading_repository = reading_repository
    app.state.shutdown_service = shutdown_service
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

from fastapi import APIRouter

from wattsup.api.routes import (
    admin,
    auth,
    commands,
    history,
    setup,
    shutdown,
    status,
    system,
    variables,
)

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(setup.router)
api_router.include_router(admin.router)
api_router.include_router(status.router)
api_router.include_router(history.router)
api_router.include_router(commands.router)
api_router.include_router(variables.router)
api_router.include_router(shutdown.router)

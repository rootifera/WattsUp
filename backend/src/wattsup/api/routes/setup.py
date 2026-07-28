import hmac

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func, select

from wattsup.core.auth import hash_password
from wattsup.core.config import get_settings
from wattsup.core.secrets import SecretBox
from wattsup.models.configuration import Administrator, ManagedUps, NutServer
from wattsup.nut.exceptions import NutError
from wattsup.nut.protocol import NutClient
from wattsup.schemas.setup import InitialNutServer, InstallationRequest, SetupStatus

router = APIRouter(prefix="/setup", tags=["Installation"])


@router.get("/status", response_model=SetupStatus)
async def setup_status(request: Request) -> SetupStatus:
    async with request.app.state.database.sessions() as session:
        count = await session.scalar(select(func.count()).select_from(Administrator))
    return SetupStatus(required=not bool(count))


@router.post("", status_code=status.HTTP_201_CREATED)
async def install(body: InstallationRequest, request: Request) -> dict[str, str]:
    settings = get_settings()
    if not hmac.compare_digest(body.setup_token, settings.setup_token):
        raise HTTPException(status_code=403, detail="Invalid setup token")
    secret_box = SecretBox(settings.jwt_secret)
    discovered: list[tuple[InitialNutServer, dict[str, str]]] = []
    for server in body.servers:
        client = NutClient(
            server.host,
            server.port,
            username=server.username,
            password=server.password,
        )
        try:
            units = await client.list_ups()
        except NutError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"{server.name}: {error}",
            ) from error
        discovered.append((server, units))

    async with request.app.state.database.sessions() as session:
        count = await session.scalar(select(func.count()).select_from(Administrator))
        if count:
            raise HTTPException(status_code=409, detail="WattsUp is already installed")
        session.add(
            Administrator(
                username=body.admin_username,
                password_hash=hash_password(body.admin_password),
            )
        )
        for server_input, units in discovered:
            db_server = NutServer(
                name=server_input.name,
                host=server_input.host,
                port=server_input.port,
                username_encrypted=secret_box.encrypt(server_input.username),
                password_encrypted=secret_box.encrypt(server_input.password),
                currency=body.currency.upper(),
                price_per_kwh=body.price_per_kwh,
            )
            session.add(db_server)
            await session.flush()
            session.add_all(
                ManagedUps(
                    server_id=db_server.id,
                    nut_name=nut_name,
                    display_name=description or nut_name,
                    description=description,
                )
                for nut_name, description in units.items()
            )
        await session.commit()
    return {"message": "Installation complete"}

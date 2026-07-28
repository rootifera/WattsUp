import json
from decimal import Decimal
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from wattsup.core.auth import require_authenticated
from wattsup.core.config import get_settings
from wattsup.core.secrets import SecretBox
from wattsup.models.configuration import ManagedUps, NotificationChannel, NutServer
from wattsup.nut.exceptions import NutError
from wattsup.nut.protocol import NutClient
from wattsup.services.notifications import send_notification

router = APIRouter(
    prefix="/admin", tags=["Administration"], dependencies=[Depends(require_authenticated)]
)


class ServerInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=3493, ge=1, le=65535)
    username: str | None = None
    password: str | None = None
    currency: str = Field(default="GBP", min_length=3, max_length=3)
    price_per_kwh: Decimal = Field(default=Decimal("0"), ge=0)


class ServerUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    currency: str = Field(min_length=3, max_length=3)
    price_per_kwh: Decimal = Field(ge=0)


class UpsUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)


class ChannelInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    kind: Literal["smtp", "gotify", "pushover", "webhook"]
    enabled: bool = False
    configuration: dict[str, Any]
    events: list[str] = []


def box() -> SecretBox:
    return SecretBox(get_settings().jwt_secret)


def server_client(server: NutServer) -> NutClient:
    secret_box = box()
    return NutClient(
        server.host,
        server.port,
        username=secret_box.decrypt(server.username_encrypted),
        password=secret_box.decrypt(server.password_encrypted),
        timeout=server.timeout_seconds,
    )


def server_output(server: NutServer) -> dict[str, Any]:
    return {
        "id": server.id,
        "name": server.name,
        "host": server.host,
        "port": server.port,
        "currency": server.currency,
        "price_per_kwh": float(server.price_per_kwh),
        "units": [
            {"id": unit.id, "nut_name": unit.nut_name, "display_name": unit.display_name}
            for unit in server.units
        ],
    }


@router.get("/servers")
async def servers(request: Request) -> list[dict[str, Any]]:
    async with request.app.state.database.sessions() as session:
        values = (
            await session.scalars(
                select(NutServer).options(selectinload(NutServer.units)).order_by(NutServer.name)
            )
        ).all()
        return [server_output(server) for server in values]


@router.post("/servers", status_code=201)
async def add_server(body: ServerInput, request: Request) -> dict[str, Any]:
    client = NutClient(body.host, body.port, username=body.username, password=body.password)
    try:
        units = await client.list_ups()
    except NutError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    secret_box = box()
    async with request.app.state.database.sessions() as session:
        server = NutServer(
            name=body.name,
            host=body.host,
            port=body.port,
            username_encrypted=secret_box.encrypt(body.username),
            password_encrypted=secret_box.encrypt(body.password),
            currency=body.currency.upper(),
            price_per_kwh=body.price_per_kwh,
        )
        session.add(server)
        await session.flush()
        session.add_all(
            ManagedUps(
                server_id=server.id,
                nut_name=name,
                display_name=description or name,
                description=description,
            )
            for name, description in units.items()
        )
        await session.commit()
    return {"message": f"Added {len(units)} UPS units"}


@router.put("/servers/{server_id}")
async def update_server(server_id: int, body: ServerUpdate, request: Request) -> dict[str, str]:
    async with request.app.state.database.sessions() as session:
        server = await session.get(NutServer, server_id)
        if server is None:
            raise HTTPException(status_code=404, detail="NUT server not found")
        server.name = body.name
        server.currency = body.currency.upper()
        server.price_per_kwh = body.price_per_kwh
        await session.commit()
    return {"message": "Server updated"}


@router.put("/ups/{ups_id}")
async def update_ups(ups_id: int, body: UpsUpdate, request: Request) -> dict[str, str]:
    async with request.app.state.database.sessions() as session:
        unit = await session.get(ManagedUps, ups_id)
        if unit is None:
            raise HTTPException(status_code=404, detail="UPS not found")
        unit.display_name = body.display_name
        await session.commit()
    return {"message": "UPS renamed"}


@router.get("/notifications")
async def channels(request: Request) -> list[dict[str, Any]]:
    async with request.app.state.database.sessions() as session:
        values = (await session.scalars(select(NotificationChannel))).all()
    return [
        {
            "id": channel.id,
            "name": channel.name,
            "kind": channel.kind,
            "enabled": channel.enabled,
            "configuration": {},
            "events": channel.events.split(",") if channel.events else [],
        }
        for channel in values
    ]


@router.post("/notifications", status_code=status.HTTP_201_CREATED)
async def add_channel(body: ChannelInput, request: Request) -> dict[str, int]:
    channel = NotificationChannel(
        name=body.name,
        kind=body.kind,
        enabled=body.enabled,
        configuration_encrypted=box().encrypt(json.dumps(body.configuration)) or "",
        events=",".join(body.events),
    )
    async with request.app.state.database.sessions() as session:
        session.add(channel)
        await session.commit()
        await session.refresh(channel)
    return {"id": channel.id}


@router.post("/notifications/{channel_id}/test")
async def test_channel(channel_id: int, request: Request) -> dict[str, str]:
    async with request.app.state.database.sessions() as session:
        channel = await session.get(NotificationChannel, channel_id)
        if channel is None:
            raise HTTPException(status_code=404, detail="Notification channel not found")
    configuration = json.loads(box().decrypt(channel.configuration_encrypted) or "{}")
    try:
        await send_notification(
            channel.kind, configuration, "WattsUp test", "Your notification channel is working."
        )
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return {"message": "Test notification sent"}

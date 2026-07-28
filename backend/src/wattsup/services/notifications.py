import asyncio
import json
import smtplib
import urllib.parse
import urllib.request
from email.message import EmailMessage
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from wattsup.core.secrets import SecretBox
from wattsup.models.configuration import NotificationChannel
from wattsup.schemas.status import UpsStatus


async def send_notification(kind: str, config: dict[str, Any], title: str, message: str) -> None:
    await asyncio.to_thread(_send, kind, config, title, message)


def _send(kind: str, config: dict[str, Any], title: str, message: str) -> None:
    if kind == "smtp":
        email = EmailMessage()
        email["Subject"] = title
        email["From"] = config["from"]
        email["To"] = config["to"]
        email.set_content(message)
        with smtplib.SMTP(config["host"], int(config.get("port", 587)), timeout=10) as client:
            if config.get("starttls", True):
                client.starttls()
            if config.get("username"):
                client.login(config["username"], config.get("password", ""))
            client.send_message(email)
        return
    if kind == "gotify":
        url = config["url"].rstrip("/") + "/message?token=" + config["token"]
        payload = {"title": title, "message": message, "priority": config.get("priority", 5)}
    elif kind == "pushover":
        url = "https://api.pushover.net/1/messages.json"
        payload = {
            "token": config["token"],
            "user": config["user"],
            "title": title,
            "message": message,
        }
    elif kind == "webhook":
        url = config["url"]
        payload = {"title": title, "message": message, "event": "test"}
    else:
        raise ValueError("Unsupported notification channel")
    if kind == "pushover":
        data = urllib.parse.urlencode(payload).encode()
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
    else:
        data = json.dumps(payload).encode()
        headers = {"Content-Type": "application/json"}
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=10):
        pass


class NotificationDispatcher:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        secret_box: SecretBox,
    ) -> None:
        self.sessions = sessions
        self.secret_box = secret_box
        self.previous: dict[str, tuple[bool, set[str]]] = {}

    async def evaluate(self, value: UpsStatus) -> None:
        codes = set((value.status or "").split())
        previous = self.previous.get(value.ups_name)
        self.previous[value.ups_name] = (value.connected, codes)
        if previous is None:
            return
        was_connected, old_codes = previous
        events: list[tuple[str, str]] = []
        if was_connected and not value.connected:
            events.append(("unreachable", "NUT server or UPS became unreachable."))
        if not was_connected and value.connected:
            events.append(("reconnected", "Connection to the UPS was restored."))
        if "OB" in codes and "OB" not in old_codes:
            events.append(("on_battery", "The UPS is running on battery."))
        if "OB" in old_codes and "OB" not in codes:
            events.append(("power_restored", "Mains power has been restored."))
        if "LB" in codes and "LB" not in old_codes:
            events.append(("low_battery", "The UPS battery is critically low."))
        for event, message in events:
            await self.dispatch(event, f"WattsUp · UPS {value.ups_name}", message)

    async def dispatch(self, event: str, title: str, message: str) -> None:
        async with self.sessions() as session:
            channels = (
                await session.scalars(
                    select(NotificationChannel).where(NotificationChannel.enabled.is_(True))
                )
            ).all()
        for channel in channels:
            if event not in channel.events.split(","):
                continue
            config = json.loads(self.secret_box.decrypt(channel.configuration_encrypted) or "{}")
            try:
                await send_notification(channel.kind, config, title, message)
            except Exception:
                # A failed notification must never interrupt UPS monitoring.
                continue

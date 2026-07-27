from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from wattsup.database.base import Base


class RemoteDevice(Base):
    __tablename__ = "remote_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ups_name: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(100))
    host: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer, default=22)
    username: Mapped[str] = mapped_column(String(100))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    use_sudo: Mapped[bool] = mapped_column(Boolean, default=True)
    mains_state: Mapped[str] = mapped_column(String(20), default="on_battery")
    battery_state: Mapped[str] = mapped_column(String(20), default="discharging")
    battery_threshold: Mapped[int] = mapped_column(Integer, default=30)
    custom_command: Mapped[str | None] = mapped_column(Text)
    trusted_host_key: Mapped[str | None] = mapped_column(Text)
    host_key_fingerprint: Mapped[str | None] = mapped_column(String(255))
    last_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_result: Mapped[str | None] = mapped_column(Text)


class AutomationConfig(Base):
    __tablename__ = "automation_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True)

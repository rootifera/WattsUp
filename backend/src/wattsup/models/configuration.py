from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wattsup.database.base import Base


class Administrator(Base):
    __tablename__ = "administrators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class NutServer(Base):
    __tablename__ = "nut_servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    host: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer, default=3493)
    username_encrypted: Mapped[str | None] = mapped_column(Text)
    password_encrypted: Mapped[str | None] = mapped_column(Text)
    timeout_seconds: Mapped[float] = mapped_column(Float, default=5.0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    currency: Mapped[str] = mapped_column(String(3), default="GBP")
    price_per_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal("0"))
    units: Mapped[list["ManagedUps"]] = relationship(
        back_populates="server", cascade="all, delete-orphan"
    )


class ManagedUps(Base):
    __tablename__ = "managed_ups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("nut_servers.id", ondelete="CASCADE"))
    nut_name: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    server: Mapped[NutServer] = relationship(back_populates="units")


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    kind: Mapped[str] = mapped_column(String(20))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    configuration_encrypted: Mapped[str] = mapped_column(Text)
    events: Mapped[str] = mapped_column(
        Text,
        default="on_battery,power_restored,low_battery,unreachable,reconnected,"
        "test_result,shutdown_result",
    )

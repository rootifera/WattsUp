from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
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
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
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
    quick_test_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    deep_test_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_quick_test_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    last_deep_test_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    last_battery_test_result: Mapped[str | None] = mapped_column(Text)
    last_battery_test_result_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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


class TariffRate(Base):
    __tablename__ = "tariff_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(
        ForeignKey("nut_servers.id", ondelete="CASCADE"), index=True
    )
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    currency: Mapped[str] = mapped_column(String(3))
    price_per_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 6))


class DailyEnergy(Base):
    __tablename__ = "daily_energy"
    __table_args__ = (UniqueConstraint("ups_id", "local_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ups_id: Mapped[int] = mapped_column(
        ForeignKey("managed_ups.id", ondelete="CASCADE"), index=True
    )
    local_date: Mapped[date] = mapped_column(Date, index=True)
    energy_kwh: Mapped[float] = mapped_column(Float, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(3))
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    max_power_watts: Mapped[float | None] = mapped_column(Float)


class RetentionSettings(Base):
    __tablename__ = "retention_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    raw_days: Mapped[int | None] = mapped_column(Integer)

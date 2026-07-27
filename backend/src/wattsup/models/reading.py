from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from wattsup.database.base import Base


class UpsReading(Base):
    __tablename__ = "ups_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ups_name: Mapped[str] = mapped_column(String(255), index=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    status: Mapped[str | None] = mapped_column(String(64))
    battery_charge: Mapped[float | None] = mapped_column(Float)
    battery_voltage: Mapped[float | None] = mapped_column(Float)
    runtime_seconds: Mapped[float | None] = mapped_column(Float)
    input_voltage: Mapped[float | None] = mapped_column(Float)
    output_voltage: Mapped[float | None] = mapped_column(Float)
    load_percent: Mapped[float | None] = mapped_column(Float)

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HistoryReading(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recorded_at: datetime
    status: str | None
    battery_charge: float | None
    battery_voltage: float | None
    runtime_seconds: float | None
    input_voltage: float | None
    output_voltage: float | None
    load_percent: float | None

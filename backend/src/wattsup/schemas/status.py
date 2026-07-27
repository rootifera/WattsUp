from datetime import datetime

from pydantic import BaseModel, Field


class HiddenMetrics(BaseModel):
    output_voltage: bool = False
    input_frequency: bool = False


class UpsStatus(BaseModel):
    connected: bool
    ups_name: str
    last_poll_at: datetime
    error: str | None = None
    status: str | None = None
    battery_charge: float | None = None
    battery_voltage: float | None = None
    runtime_seconds: float | None = None
    load_percent: float | None = None
    input_voltage: float | None = None
    output_voltage: float | None = None
    input_frequency: float | None = None
    battery_date: str | None = None
    battery_test_result: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    driver: str | None = None
    power_restored: bool = False
    hidden_metrics: HiddenMetrics = Field(default_factory=HiddenMetrics)

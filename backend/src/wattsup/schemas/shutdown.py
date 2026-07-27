from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MainsState = Literal["online", "on_battery", "any"]
BatteryState = Literal["charging", "discharging", "full", "any"]


class DeviceInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=22, ge=1, le=65535)
    username: str = Field(min_length=1, max_length=100)
    enabled: bool = False
    use_sudo: bool = True
    mains_state: MainsState = "on_battery"
    battery_state: BatteryState = "discharging"
    battery_threshold: int = Field(default=30, ge=0, le=100)
    custom_command: str | None = None


class DeviceOutput(DeviceInput):
    model_config = ConfigDict(from_attributes=True)

    id: int
    host_key_fingerprint: str | None
    last_test_at: datetime | None
    last_result: str | None


class HostKeyInfo(BaseModel):
    algorithm: str
    fingerprint: str
    public_key: str
    trusted: bool


class AutomationSettings(BaseModel):
    enabled: bool
    dry_run: bool


class TestResult(BaseModel):
    success: bool
    message: str


class SimulationRequest(BaseModel):
    mains_state: Literal["online", "on_battery"]
    battery_state: Literal["charging", "discharging", "full"]
    battery_percentage: int = Field(ge=0, le=100)


class SimulationResult(BaseModel):
    device_id: int
    name: str
    matches: bool
    reason: str

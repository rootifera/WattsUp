from datetime import datetime

from pydantic import BaseModel


class CommandInfo(BaseModel):
    name: str
    category: str
    dangerous: bool
    description: str | None


class ExecuteCommandRequest(BaseModel):
    confirmed: bool = False


class CommandResult(BaseModel):
    accepted: bool = True


class BatteryTestSchedule(BaseModel):
    quick_enabled: bool
    deep_enabled: bool
    last_quick_test_at: datetime | None = None
    last_deep_test_at: datetime | None = None
    last_result: str | None = None
    last_result_at: datetime | None = None


class BatteryTestScheduleUpdate(BaseModel):
    quick_enabled: bool
    deep_enabled: bool

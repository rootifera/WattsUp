from decimal import Decimal

from pydantic import BaseModel, Field


class SetupStatus(BaseModel):
    required: bool


class InitialNutServer(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=3493, ge=1, le=65535)
    username: str | None = None
    password: str | None = None


class InstallationRequest(BaseModel):
    setup_token: str
    admin_username: str = Field(min_length=1, max_length=100)
    admin_password: str = Field(min_length=12)
    currency: str = Field(default="GBP", min_length=3, max_length=3)
    price_per_kwh: Decimal = Field(default=Decimal("0"), ge=0)
    servers: list[InitialNutServer] = Field(min_length=1)

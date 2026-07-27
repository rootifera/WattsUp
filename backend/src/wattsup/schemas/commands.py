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

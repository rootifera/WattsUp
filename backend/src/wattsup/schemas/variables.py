from pydantic import BaseModel


class UpsVariable(BaseModel):
    name: str
    value: str
    group: str

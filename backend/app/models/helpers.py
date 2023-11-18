from pydantic import BaseModel


class SimpleActionResult(BaseModel):
    result: str
    message: str | None


class DbIdMixin(BaseModel):
    id: str

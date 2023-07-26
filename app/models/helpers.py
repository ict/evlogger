from pydantic import BaseModel


class SimpleActionResult(BaseModel):
    result: str
    message: str | None

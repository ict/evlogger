from pydantic import BaseModel

from app.models.helpers import DbIdMixin


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    is_admin: bool = False


class UserWithPasswordHash(User):
    password_hash: str


class UserInDb(UserWithPasswordHash, DbIdMixin):
    pass


class UserRegister(BaseModel):
    username: str
    password: str
    email: str | None = None
    full_name: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None

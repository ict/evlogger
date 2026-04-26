from datetime import datetime

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


class ApiTokenCreate(BaseModel):
    name: str
    expires_at: datetime | None = None


class ApiToken(BaseModel):
    name: str
    owner_id: str
    token_hash: str
    preview: str
    created_at: datetime
    last_used_at: datetime | None = None
    expires_at: datetime | None = None


class ApiTokenInDb(ApiToken, DbIdMixin):
    pass


class ApiTokenPublic(DbIdMixin):
    name: str
    preview: str
    created_at: datetime
    last_used_at: datetime | None = None
    expires_at: datetime | None = None


class ApiTokenCreated(ApiTokenPublic):
    token: str

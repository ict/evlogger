import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette import status

from app.core import config
from app.core.db import AsyncIOMotorClient, get_database
from app.models.users import TokenData, User, UserInDb
from app.operations.users import ApiTokenCrudOp, UserCrudOp

SECRET_KEY = config.API_SECRET_KEY
ALGORITHM = config.API_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = config.API_ACCESS_TOKEN_EXPIRE_MINUTES
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='users/token')
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(user: UserInDb, password: str) -> bool:
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return True


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_api_token() -> tuple[str, str, str]:
    """Return (raw_token, token_hash, preview) for a new long-lived API token."""
    raw = config.API_TOKEN_PREFIX + secrets.token_urlsafe(32)
    return raw, hash_api_token(raw), raw[:10] + '…' + raw[-4:]


def hash_api_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


async def _resolve_api_token(token: str, db: AsyncIOMotorClient) -> User | None:
    api_token = await ApiTokenCrudOp.get_by_property(db, 'token_hash', hash_api_token(token))
    if api_token is None:
        return None
    if api_token.expires_at is not None and api_token.expires_at < datetime.now(UTC):
        return None
    user = await UserCrudOp.get_by_id(db, api_token.owner_id)
    if user is None:
        return None
    await ApiTokenCrudOp.touch_last_used(db, api_token.id, datetime.now(UTC))
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: AsyncIOMotorClient = Depends(get_database)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    if token.startswith(config.API_TOKEN_PREFIX):
        user = await _resolve_api_token(token, db)
        if user is None:
            raise credentials_exception
        return user
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await UserCrudOp.get_by_property(db, 'username', token_data.username)

    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail='Inactive user')
    return current_user


async def get_current_admin_user(current_user: Annotated[User, Depends(get_current_active_user)]):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin access required')
    return current_user

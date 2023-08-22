from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from app.core import config
from app.core.db import AsyncIOMotorClient, get_database
from app.models.users import User, UserInDb, UserRegister, Token, UserWithPasswordHash
from app.operations.users import UserCrudOp
from app.util.auth import get_current_user, authenticate_user, create_access_token, get_password_hash

router = APIRouter()

DBDepends = Depends(get_database)


@router.get("/users/me", tags=['Users'])
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


@router.post("/users/token", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: AsyncIOMotorClient = DBDepends):
    user: UserInDb = await UserCrudOp.get_by_property(db, 'username', form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not authenticate_user(user, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.API_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post('/users/register', response_model=User)
async def register(user_data: UserRegister, db: AsyncIOMotorClient = DBDepends) -> User:
    exists_exception = HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Username or email address already in use")
    first_user = await UserCrudOp.list(db, limit=1)
    if not first_user:
        is_admin = True
    else:
        is_admin = False
    existing = await UserCrudOp.get_by_property(db, 'username', user_data.username)
    if existing:
        raise exists_exception
    existing = await UserCrudOp.get_by_property(db, 'email', user_data.email)
    if existing and user_data.email is not None:
        raise exists_exception

    new_user = UserWithPasswordHash(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        disabled=False,
        is_admin=is_admin,
        password_hash=get_password_hash(user_data.password),
    )
    user = await UserCrudOp.create(db, new_user)
    return user

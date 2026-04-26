from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from app.core import config
from app.core.db import AsyncIOMotorClient, get_database
from app.models.users import (
    ApiToken,
    ApiTokenCreate,
    ApiTokenCreated,
    ApiTokenPublic,
    Token,
    User,
    UserInDb,
    UserRegister,
    UserWithPasswordHash,
)
from app.operations.users import ApiTokenCrudOp, UserCrudOp
from app.util.auth import (
    authenticate_user,
    create_access_token,
    generate_api_token,
    get_current_user,
    get_password_hash,
)

router = APIRouter()

DBDepends = Depends(get_database)


@router.get('/users/me', tags=['Users'])
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


@router.post('/users/token', response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: AsyncIOMotorClient = DBDepends):
    user: UserInDb = await UserCrudOp.get_by_property(db, 'username', form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail='Incorrect username or password')
    if not authenticate_user(user, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token_expires = timedelta(minutes=config.API_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={'sub': user.username}, expires_delta=access_token_expires)
    return {'access_token': access_token, 'token_type': 'bearer'}


@router.post('/users/register', response_model=User)
async def register(user_data: UserRegister, db: AsyncIOMotorClient = DBDepends) -> User:
    exists_exception = HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, 'Username or email address already in use')
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


@router.post('/users/api-tokens', response_model=ApiTokenCreated, tags=['Users'])
async def create_api_token(
    body: ApiTokenCreate,
    current_user: Annotated[UserInDb, Depends(get_current_user)],
    db: AsyncIOMotorClient = DBDepends,
) -> ApiTokenCreated:
    raw, token_hash, preview = generate_api_token()
    new_token = ApiToken(
        name=body.name,
        owner_id=current_user.id,
        token_hash=token_hash,
        preview=preview,
        created_at=datetime.now(UTC),
        expires_at=body.expires_at,
    )
    created = await ApiTokenCrudOp.create(db, new_token)
    return ApiTokenCreated(
        id=created.id,
        name=created.name,
        preview=created.preview,
        created_at=created.created_at,
        last_used_at=created.last_used_at,
        expires_at=created.expires_at,
        token=raw,
    )


@router.get('/users/api-tokens', response_model=list[ApiTokenPublic], tags=['Users'])
async def list_api_tokens(
    current_user: Annotated[UserInDb, Depends(get_current_user)],
    db: AsyncIOMotorClient = DBDepends,
) -> list[ApiTokenPublic]:
    tokens = await ApiTokenCrudOp.list(db, limit=100, owner_id=current_user.id)
    return [
        ApiTokenPublic(
            id=t.id,
            name=t.name,
            preview=t.preview,
            created_at=t.created_at,
            last_used_at=t.last_used_at,
            expires_at=t.expires_at,
        )
        for t in tokens
    ]


@router.delete('/users/api-tokens/{token_id}', tags=['Users'])
async def delete_api_token(
    token_id: str,
    current_user: Annotated[UserInDb, Depends(get_current_user)],
    db: AsyncIOMotorClient = DBDepends,
):
    deleted = await ApiTokenCrudOp.delete_by_id(db, token_id, owner_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='API token not found')
    return {'result': 'ok'}

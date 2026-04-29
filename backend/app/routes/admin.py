import asyncio
from typing import Annotated

import bson
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status

from app.core.config import (
    COLLECTION_API_TOKENS,
    COLLECTION_CARS,
    COLLECTION_CHARGES,
    COLLECTION_CPOS,
    COLLECTION_USERS,
)
from app.core.db import AsyncIOMotorClient, get_database
from app.models.charging import CarInDb, ChargeInDb, CPOInDb
from app.models.site_settings import SiteSettings
from app.models.users import User
from app.operations.charging import ChargeCrudOp
from app.operations.crud_base import CarCRUD, CPOCrud, get_collection
from app.operations.site_settings import get_site_settings, update_site_settings
from app.operations.users import UserCrudOp
from app.util.auth import get_current_admin_user

router = APIRouter(prefix='/admin', tags=['Admin'])

DBDepends = Depends(get_database)


@router.get('/settings', response_model=SiteSettings)
async def read_admin_settings(
    _: Annotated[User, Depends(get_current_admin_user)],
    db: AsyncIOMotorClient = DBDepends,
) -> SiteSettings:
    return await get_site_settings(db)


@router.put('/settings', response_model=SiteSettings)
async def write_admin_settings(
    body: SiteSettings,
    _: Annotated[User, Depends(get_current_admin_user)],
    db: AsyncIOMotorClient = DBDepends,
) -> SiteSettings:
    return await update_site_settings(db, body)


class UserListItem(User):
    id: str
    cars_count: int = 0
    cpos_count: int = 0
    charges_count: int = 0


class UserDetail(User):
    id: str
    cars: list[CarInDb]
    cpos: list[CPOInDb]
    charges: list[ChargeInDb]


class ToggleAdminResponse(BaseModel):
    result: str
    is_admin: bool


class OkResponse(BaseModel):
    result: str


@router.get('/users', response_model=list[UserListItem])
async def list_users(
    _: Annotated[User, Depends(get_current_admin_user)],
    db: AsyncIOMotorClient = DBDepends,
) -> list[UserListItem]:
    """List all users with their resource counts (admin only)."""
    users = await UserCrudOp.list(db, limit=100)
    cars_col = get_collection(db, COLLECTION_CARS)
    cpos_col = get_collection(db, COLLECTION_CPOS)
    charges_col = get_collection(db, COLLECTION_CHARGES)

    async def counts_for(uid: str) -> tuple[int, int, int]:
        return await asyncio.gather(
            cars_col.count_documents({'owner_id': uid}),
            cpos_col.count_documents({'owner_id': uid}),
            charges_col.count_documents({'owner_id': uid}),
        )

    all_counts = await asyncio.gather(*(counts_for(u.id) for u in users))
    return [
        UserListItem(
            id=u.id,
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            disabled=u.disabled,
            is_admin=u.is_admin,
            cars_count=cars_count,
            cpos_count=cpos_count,
            charges_count=charges_count,
        )
        for u, (cars_count, cpos_count, charges_count) in zip(users, all_counts, strict=True)
    ]


@router.get('/users/{user_id}', response_model=UserDetail)
async def get_user_detail(
    user_id: str,
    _: Annotated[User, Depends(get_current_admin_user)],
    db: AsyncIOMotorClient = DBDepends,
) -> UserDetail:
    """Get a user's details including their cars, CPOs, and charges (admin only)."""
    user = await UserCrudOp.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    cars, cpos, charges = await asyncio.gather(
        CarCRUD.list(db, limit=500, owner_id=user_id),
        CPOCrud.list(db, limit=500, owner_id=user_id),
        ChargeCrudOp.list(db, limit=10, owner_id=user_id),
    )
    return UserDetail(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        disabled=user.disabled,
        is_admin=user.is_admin,
        cars=cars,
        cpos=cpos,
        charges=charges,
    )


@router.post('/users/{user_id}/toggle-admin', response_model=ToggleAdminResponse)
async def toggle_user_admin(
    user_id: str,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: AsyncIOMotorClient = DBDepends,
) -> ToggleAdminResponse:
    """Toggle a user's admin status (admin only)."""
    user = await UserCrudOp.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    if user.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot change your own admin status')
    new_is_admin = not user.is_admin
    if not new_is_admin:
        # Prevent removing the last admin
        admin_count = await get_collection(db, COLLECTION_USERS).count_documents({'is_admin': True})
        if admin_count <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot remove the last admin')
    await get_collection(db, COLLECTION_USERS).update_one(
        {'_id': bson.ObjectId(user_id)}, {'$set': {'is_admin': new_is_admin}}
    )
    return ToggleAdminResponse(result='ok', is_admin=new_is_admin)


@router.delete('/users/{user_id}', response_model=OkResponse)
async def delete_user(
    user_id: str,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: AsyncIOMotorClient = DBDepends,
) -> OkResponse:
    """Delete a user and all their resources (admin only)."""
    user = await UserCrudOp.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    if user.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot delete yourself')
    if user.is_admin:
        admin_count = await get_collection(db, COLLECTION_USERS).count_documents({'is_admin': True})
        if admin_count <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot delete the last admin')
    await asyncio.gather(
        get_collection(db, COLLECTION_CHARGES).delete_many({'owner_id': user_id}),
        get_collection(db, COLLECTION_CARS).delete_many({'owner_id': user_id}),
        get_collection(db, COLLECTION_CPOS).delete_many({'owner_id': user_id}),
        get_collection(db, COLLECTION_API_TOKENS).delete_many({'owner_id': user_id}),
    )
    await UserCrudOp.delete_by_id(db, user_id)
    return OkResponse(result='ok')

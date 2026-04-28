from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.db import AsyncIOMotorClient, get_database
from app.models.site_settings import SiteSettings
from app.models.users import User
from app.operations.site_settings import get_site_settings, update_site_settings
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

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_204_NO_CONTENT

from app.core.db import AsyncIOMotorClient, get_database
from app.models.charging import CPO, CPOInDb
from app.models.users import UserInDb
from app.operations.charging import delete_or_archive_cpo
from app.operations.crud_base import CPOCrud
from app.util.auth import get_current_active_user

router = APIRouter()

DBDepend = Depends(get_database)
UserDepends = Depends(get_current_active_user)


@router.get('/')
async def list_cpos(
    limit: int = 20,
    offset: int = 0,
    include_archived: bool = False,
    db: AsyncIOMotorClient = DBDepend,
    user: UserInDb = UserDepends,
) -> list[CPOInDb]:
    extra_filter = None if include_archived else {'archived': {'$ne': True}}
    return await CPOCrud.list(db, limit, offset, user.id, extra_filter)


@router.post('/', status_code=201)
async def create_cpo(cpo: CPO, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends) -> CPOInDb:
    return await CPOCrud.create(db, cpo, user.id)


@router.get('/{id}')
async def get_cpo_by_id(id: str, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends) -> CPOInDb:
    car = await CPOCrud.get_by_id(db, id, user.id)
    if not car:
        raise HTTPException(404, 'Not found')
    return car


@router.delete('/{id}', status_code=HTTP_204_NO_CONTENT)
async def delete_cpo_by_id(id: str, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends):
    # CPOs referenced by charges are archived instead of deleted, so old charges stay intact
    success = await delete_or_archive_cpo(db, id, user.id)
    if not success:
        raise HTTPException(404, 'Not found')


@router.put('/{id}')
async def update_cpo_by_id(
    id: str, cpo: CPO, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends
) -> CPOInDb:
    new_car = await CPOCrud.update_by_id(db, id, cpo, user.id)
    if not new_car:
        raise HTTPException(404, 'Not found')
    return new_car

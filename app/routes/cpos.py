from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_204_NO_CONTENT

from app.core.db import AsyncIOMotorClient, get_database
from app.models.charging import CPO, CPOInDb
from app.models.users import UserInDb
from app.operations.crud_base import CPOCrud
from app.util.auth import get_current_active_user

router = APIRouter()

DBDepend = Depends(get_database)
UserDepends = Depends(get_current_active_user)


@router.get('/')
async def list_cpos(
    limit: int = 20, offset: int = 0, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends
) -> list[CPOInDb]:
    cars = await CPOCrud.list(db, limit, offset, user.id)
    return cars


@router.post('/', status_code=201)
async def create_cpo(cpo: CPO, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends) -> CPOInDb:
    return await CPOCrud.create(db, cpo, user.id)


@router.get('/{id}')
async def get_cpo_by_id(id: str, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends) -> CPOInDb:
    car = await CPOCrud.get_by_id(db, id, user.id)
    if not car:
        raise HTTPException(404, "Not found")
    return car


@router.delete('/{id}', status_code=HTTP_204_NO_CONTENT)
async def delete_cpo_by_id(id: str, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends):
    success = await CPOCrud.delete_by_id(db, id, user.id)
    if not success:
        raise HTTPException(404, "Not found")
    return None


@router.put('/{id}')
async def update_cpo_by_id(
    id: str, cpo: CPO, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends
) -> CPOInDb:
    new_car = await CPOCrud.update_by_id(db, id, cpo, user.id)
    if not new_car:
        raise HTTPException(404, "Not found")
    return new_car

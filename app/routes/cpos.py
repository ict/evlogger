from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_204_NO_CONTENT

from app.core.db import AsyncIOMotorClient, get_database
from app.models.charging import CPO, CPOInDb
from app.operations.crud_base import CPOCrud

router = APIRouter()

DBDepend = Depends(get_database)


@router.get('/cpo', tags=['CPOs'])
async def list_cpos(limit: int = 20, offset: int = 0, db: AsyncIOMotorClient = DBDepend) -> list[
    CPOInDb]:
    cars = await CPOCrud.list(db, limit, offset)
    return cars


@router.post('/cpo', tags=['CPOs'])
async def create_cpo(cpo: CPO, db: AsyncIOMotorClient = DBDepend) -> CPOInDb:
    return await CPOCrud.create(db, cpo)


@router.get('/cpo/{id}', tags=['CPOs'])
async def get_cpo_by_id(id: str, db: AsyncIOMotorClient = DBDepend) -> CPOInDb:
    car = await CPOCrud.get_by_id(db, id)
    if not car:
        raise HTTPException(404, "Not found")
    return car


@router.delete('/cpo/{id}', status_code=HTTP_204_NO_CONTENT, tags=['CPOs'])
async def delete_cpo_by_id(id: str, db: AsyncIOMotorClient = DBDepend):
    success = await CPOCrud.delete_by_id(db, id)
    if not success:
        raise HTTPException(404, "Not found")
    return None


@router.put('/cpo/{id}', tags=['CPOs'])
async def update_cpo_by_id(id: str, cpo: CPO, db: AsyncIOMotorClient = DBDepend) -> CPOInDb:
    new_car = await CPOCrud.update_by_id(db, id, cpo)
    if not new_car:
        raise HTTPException(404, "Not found")
    return new_car

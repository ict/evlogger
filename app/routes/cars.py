from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_204_NO_CONTENT

import app.core.config
from app.core.db import AsyncIOMotorClient, get_database
from app.models.charging import CarInDb, Car
from app.operations.crud_base import CRUDBase

router = APIRouter()

DBDepend = Depends(get_database)
CarCRUD = CRUDBase[Car, CarInDb](app.core.config.COLLECTION_CARS, Car, CarInDb)


@router.get('/car', tags=['Cars'])
async def list_cars(limit: int = 20, offset: int = 0, db: AsyncIOMotorClient = DBDepend) -> list[
    CarInDb]:
    cars = await CarCRUD.list(db, limit, offset)
    return cars


@router.post('/car', tags=['Cars'])
async def create_car(car: Car, db: AsyncIOMotorClient = DBDepend) -> CarInDb:
    return await CarCRUD.create(db, car)


@router.get('/car/{id}', tags=['Cars'])
async def get_car_by_id(id: str, db: AsyncIOMotorClient = DBDepend) -> CarInDb:
    car = await CarCRUD.get_by_id(db, id)
    if not car:
        raise HTTPException(404, "Not found")
    return car


@router.delete('/car/{id}', status_code=HTTP_204_NO_CONTENT, tags=['Cars'])
async def delete_car_by_id(id: str, db: AsyncIOMotorClient = DBDepend):
    success = await CarCRUD.delete_by_id(db, id)
    if not success:
        raise HTTPException(404, "Not found")
    return None


@router.put('/car/{id}', tags=['Cars'])
async def update_car_by_id(id: str, car: Car, db: AsyncIOMotorClient = DBDepend) -> CarInDb:
    new_car = await CarCRUD.update_by_id(db, id, car)
    if not new_car:
        raise HTTPException(404, "Not found")
    return new_car

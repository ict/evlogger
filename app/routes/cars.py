from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_204_NO_CONTENT

from app.core.db import AsyncIOMotorClient, get_database
from app.models.charging import CarInDb, Car
from app.models.users import UserInDb
from app.operations.crud_base import CarCRUD
from app.util.auth import get_current_active_user

router = APIRouter()

DBDepend = Depends(get_database)
UserDepends = Depends(get_current_active_user)


@router.get('/car', tags=['Cars'])
async def list_cars(
    limit: int = 20, offset: int = 0, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends
) -> list[CarInDb]:
    cars = await CarCRUD.list(db, limit, offset, str(user.id))
    return cars


@router.post('/car', tags=['Cars'])
async def create_car(car: Car, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends) -> CarInDb:
    return await CarCRUD.create(db, car, str(user.id))


@router.get('/car/{id}', tags=['Cars'])
async def get_car_by_id(id: str, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends) -> CarInDb:
    car = await CarCRUD.get_by_id(db, id, str(user.id))
    if not car:
        raise HTTPException(404, "Not found")
    return car


@router.delete('/car/{id}', status_code=HTTP_204_NO_CONTENT, tags=['Cars'])
async def delete_car_by_id(id: str, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends):
    success = await CarCRUD.delete_by_id(db, id, str(user.id))
    if not success:
        raise HTTPException(404, "Not found")
    return None


@router.put('/car/{id}', tags=['Cars'])
async def update_car_by_id(id: str, car: Car, db: AsyncIOMotorClient = DBDepend) -> CarInDb:
    new_car = await CarCRUD.update_by_id(db, id, car)
    if not new_car:
        raise HTTPException(404, "Not found")
    return new_car

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from app.core.db import AsyncIOMotorClient, get_database
from app.models.charging import Car, CarInDb
from app.models.users import UserInDb
from app.operations.cars import CarCRUD
from app.util.auth import get_current_active_user

router = APIRouter()

DBDepend = Depends(get_database)
UserDepends = Depends(get_current_active_user)


@router.get('/')
async def list_cars(
    limit: int = 20, offset: int = 0, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends
) -> list[CarInDb]:
    cars = await CarCRUD.list(db, limit, offset, str(user.id))
    return cars


@router.post('/', status_code=HTTP_201_CREATED)
async def create_car(car: Car, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends) -> CarInDb:
    try:
        return await CarCRUD.create(db, car, str(user.id))
    except ValueError as err:
        raise HTTPException(HTTP_400_BAD_REQUEST, str(err)) from None


@router.get('/{id}')
async def get_car_by_id(id: str, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends) -> CarInDb:
    car = await CarCRUD.get_by_id(db, id, str(user.id))
    if not car:
        raise HTTPException(404, 'Not found')
    return car


@router.delete('/{id}', status_code=HTTP_204_NO_CONTENT)
async def delete_car_by_id(id: str, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends):
    success = await CarCRUD.delete_by_id(db, id, str(user.id))
    if not success:
        raise HTTPException(404, 'Not found')


@router.put('/{id}')
async def update_car_by_id(
    id: str, car: Car, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends
) -> CarInDb:
    try:
        new_car = await CarCRUD.update_by_id(db, id, car, user.id)
    except ValueError as err:
        raise HTTPException(HTTP_400_BAD_REQUEST, str(err)) from None
    if not new_car:
        raise HTTPException(404, 'Not found')
    return new_car

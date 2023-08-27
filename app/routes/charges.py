from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile
from fastapi.exceptions import HTTPException
from starlette.status import (
    HTTP_204_NO_CONTENT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_406_NOT_ACCEPTABLE,
    HTTP_201_CREATED,
)

from app.core.db import AsyncIOMotorClient, get_database
from app.models.charging import Charge, ChargeInDb, CarInDb
from app.models.helpers import SimpleActionResult
from app.models.users import UserInDb
from app.operations.charging import ChargeCrudOp
from app.operations.crud_base import CarCRUD
from app.util.auth import get_current_active_user

router = APIRouter()

DBDepend = Depends(get_database)
UserDepends = Depends(get_current_active_user)


@router.get('/')
async def list_charges(
    limit: int = 20,
    offset: int = 0,
    timespan: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: AsyncIOMotorClient = DBDepend,
    user: UserInDb = UserDepends,
) -> list[ChargeInDb]:
    try:
        charges = await ChargeCrudOp.list(db, limit, offset, user.id, timespan, from_date, to_date)
    except ValueError as err:
        raise HTTPException(HTTP_406_NOT_ACCEPTABLE, str(err))
    return charges


@router.post('/', status_code=HTTP_201_CREATED)
async def create_charge(charge: Charge, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends) -> ChargeInDb:
    try:
        return await ChargeCrudOp.create(db, charge, user.id)
    except ValueError as err:
        raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, str(err))


@router.get('/{id}')
async def get_charge_by_id(id: str, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends) -> ChargeInDb:
    charge = await ChargeCrudOp.get_by_id(db, id, user.id)
    if not charge:
        raise HTTPException(404, "Not found")
    return charge


@router.delete('/{id}', status_code=HTTP_204_NO_CONTENT)
async def delete_charge_by_id(id: str, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends):
    success = await ChargeCrudOp.delete_by_id(db, id, user.id)
    if not success:
        raise HTTPException(404, "Not found")
    return None


@router.put('/{id}')
async def update_charge_by_id(
    id: str, charge: Charge, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends
) -> ChargeInDb:
    try:
        new_charge = await ChargeCrudOp.update_by_id(db, id, charge, user.id)
    except ValueError as err:
        raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, str(err))
    if not new_charge:
        raise HTTPException(404, "Not found")
    return new_charge


async def car_from_id(car_id: str, db: AsyncIOMotorClient = DBDepend) -> CarInDb:
    car = await CarCRUD.get_by_id(db, car_id)
    if not car:
        raise HTTPException(404, "Car not found")
    return car


@router.post('/csv_import')
async def csv_import(
    csv_file: UploadFile,
    car: CarInDb = Depends(car_from_id),
    delimimiter: str = ',',
    db: AsyncIOMotorClient = DBDepend,
    user: UserInDb = UserDepends,
) -> SimpleActionResult:
    status, msg = await ChargeCrudOp.csv_import(db, car, user.id, csv_file.file, delim=delimimiter)
    return SimpleActionResult(result=status, message=msg)

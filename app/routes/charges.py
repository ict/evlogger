from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_204_NO_CONTENT, HTTP_422_UNPROCESSABLE_ENTITY, HTTP_406_NOT_ACCEPTABLE

from app.core.db import AsyncIOMotorClient, get_database
from app.models.charging import Charge, ChargeInDb, CarInDb
from app.models.helpers import SimpleActionResult
from app.operations.charging import ChargeCrudOp
from app.operations.crud_base import CarCRUD

router = APIRouter()

DBDepend = Depends(get_database)


@router.get('/charge', tags=['Charging'])
async def list_charges(limit: int = 20, offset: int = 0, timespan: str | None = None, from_date: datetime | None = None,
                       to_date: datetime | None = None, db: AsyncIOMotorClient = DBDepend) -> list[ChargeInDb]:
    try:
        charges = await ChargeCrudOp.list(db, limit, offset, timespan, from_date, to_date)
    except ValueError as err:
        raise HTTPException(HTTP_406_NOT_ACCEPTABLE, str(err))
    return charges


@router.post('/charge', tags=['Charging'])
async def create_charge(charge: Charge, db: AsyncIOMotorClient = DBDepend) -> ChargeInDb:
    try:
        return await ChargeCrudOp.create(db, charge)
    except ValueError as err:
        raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, str(err))


@router.get('/charge/{id}', tags=['Charging'])
async def get_charge_by_id(id: str, db: AsyncIOMotorClient = DBDepend) -> ChargeInDb:
    charge = await ChargeCrudOp.get_by_id(db, id)
    if not charge:
        raise HTTPException(404, "Not found")
    return charge


@router.delete('/charge/{id}', status_code=HTTP_204_NO_CONTENT, tags=['Charging'])
async def delete_charge_by_id(id: str, db: AsyncIOMotorClient = DBDepend):
    success = await ChargeCrudOp.delete_by_id(db, id)
    if not success:
        raise HTTPException(404, "Not found")
    return None


@router.put('/charge/{id}', tags=['Charging'])
async def update_charge_by_id(id: str, charge: Charge, db: AsyncIOMotorClient = DBDepend) -> ChargeInDb:
    try:
        new_charge = await ChargeCrudOp.update_by_id(db, id, charge)
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


@router.post('/charge/csv_import', tags=['Charging'])
async def csv_import(csv_file: UploadFile, car: CarInDb = Depends(car_from_id), delimimiter: str = ',',
                     db: AsyncIOMotorClient = DBDepend) -> SimpleActionResult:
    status, msg = await ChargeCrudOp.csv_import(db, car, csv_file.file, delim=delimimiter)
    return SimpleActionResult(result=status, message=msg)

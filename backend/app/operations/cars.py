import datetime

import bson
from bson.errors import InvalidId

import app.core
from app.core.config import COLLECTION_CHARGES, COLLECTION_EXPENSES
from app.core.db import AsyncIOMotorClient
from app.models.charging import Car, CarInDb
from app.operations.crud_base import CRUDBase, dump_for_db, get_collection


async def get_owned_car(
    db: AsyncIOMotorClient, car_id: str, owner_id: str, entry_date: datetime.date | None = None
) -> dict:
    """
    Look up a car by id and make sure it belongs to the owner. Returns the raw car document.
    If entry_date is given, entries after the car's sale date are rejected (retired cars are frozen).
    """
    try:
        object_id = bson.ObjectId(car_id)
    except (TypeError, InvalidId):
        msg = f"car_id '{car_id}' invalid"
        raise ValueError(msg) from None
    car = await get_collection(db, app.core.config.COLLECTION_CARS).find_one({'_id': object_id})
    if not car or car.get('owner_id', None) != owner_id:
        msg = f"car_id '{car_id}' is invalid"
        raise ValueError(msg) from None

    sale_date = car.get('sale_date')
    if entry_date is not None and sale_date:
        if isinstance(entry_date, datetime.datetime):
            entry_date = entry_date.date()
        sale_date = datetime.date.fromisoformat(sale_date) if isinstance(sale_date, str) else sale_date
        if entry_date > sale_date:
            msg = f'car was retired on {sale_date.isoformat()}'
            raise ValueError(msg)
    return car


class CarCrud(CRUDBase[Car, CarInDb]):
    def __init__(self):
        super().__init__(app.core.config.COLLECTION_CARS, Car, CarInDb)

    async def _validate_retirement(self, db: AsyncIOMotorClient, car: Car, car_id: str | None) -> None:
        """Validate (and fill defaults of) the sale fields. car_id is None for cars that do not exist yet."""
        if car.sale_date is None:
            if car.sale_price is not None or car.sale_odometer is not None:
                msg = 'sale_date required when sale_price or sale_odometer is set'
                raise ValueError(msg)
            return
        if car.purchase_date is not None and car.sale_date < car.purchase_date:
            msg = 'sale_date must not be before purchase_date'
            raise ValueError(msg)
        if car.sale_odometer is None:
            car.sale_odometer = car.odometer
        if car_id is not None:
            newest = await get_collection(db, COLLECTION_CHARGES).find_one(
                {'car_id': car_id}, sort=[('car_odometer', -1)], projection=['car_odometer']
            )
            if newest and car.sale_odometer < newest['car_odometer']:
                msg = f'sale_odometer must not be lower than the latest charge ({newest["car_odometer"]})'
                raise ValueError(msg)
        if car.sale_price is None:
            car.sale_price = 0

    async def create(self, db: AsyncIOMotorClient, new_item: Car, owner_id: str | None = None) -> CarInDb:
        await self._validate_retirement(db, new_item, None)
        return await super().create(db, new_item, owner_id)

    async def update_by_id(
        self, db: AsyncIOMotorClient, by_id: str, new_item: Car, owner_id: str | None = None
    ) -> CarInDb | None:
        old_item = await self.get_by_id(db, by_id)
        if not old_item or (owner_id and old_item.owner_id != owner_id):
            return None
        # Validate the car as it will look after the update, then store the filled-in result
        merged = Car(**{**dump_for_db(old_item), **new_item.model_dump(exclude_unset=True)})
        await self._validate_retirement(db, merged, by_id)
        return await super().update_by_id(db, by_id, merged, owner_id)

    async def delete_by_id(self, db: AsyncIOMotorClient, by_id: str, owner_id: str | None = None) -> bool:
        deleted = await super().delete_by_id(db, by_id, owner_id)
        if deleted and owner_id is not None:
            # Remove everything that belongs to this car
            for collection in (COLLECTION_CHARGES, COLLECTION_EXPENSES):
                await get_collection(db, collection).delete_many({'car_id': by_id, 'owner_id': owner_id})
        return deleted


CarCRUD = CarCrud()

from datetime import datetime, timedelta
from typing import BinaryIO

import bson

from app.core.config import COLLECTION_CARS, COLLECTION_CPOS
from app.core.db import AsyncIOMotorClient
from app.models.charging import Charge, ChargeInDb, CarInDb
from app.operations.crud_base import CRUDBase, get_collection
from app.util.timeparse import timeparse


async def _check_references(db: AsyncIOMotorClient, item: Charge) -> None:
    """
    Checks the "foreign keys" of the entity and fills optional (denormalized) fields
    """
    try:
        car_id = bson.ObjectId(item.car_id)
    except:
        raise ValueError(f"car_id '{item.car_id}' does not exist")
    car = await get_collection(db, COLLECTION_CARS).find_one({'_id': car_id})
    if not car:
        raise ValueError(f"car_id '{item.car_id}' does not exist")
    item.car_name = car.get('name', '')

    try:
        cpo_id = bson.ObjectId(item.cpo_id)
    except:
        raise ValueError(f"cpo_id '{item.cpo_id}' does not exist")
    cpo = await get_collection(db, COLLECTION_CPOS).find_one({'_id': cpo_id})
    if not cpo:
        raise ValueError(f"cpo_id '{item.cpo_id}' does not exist")
    item.cpo_name = cpo.get('name', '')

    if item.price_total is None:
        item.price_total = int(round((item.kwh_charged / 100) * cpo.get('default_price', 0)))


class ChargeCrud(CRUDBase[Charge, ChargeInDb]):

    def __init__(self, collection_name: str):
        super().__init__(collection_name, Charge, ChargeInDb)

    async def create(self, db: AsyncIOMotorClient, item: Charge) -> ChargeInDb:
        await _check_references(db, item)  # raises on errors
        return await super().create(db, item)

    async def list(self, db: AsyncIOMotorClient, limit: int = 20, offset: int = 0, timespan: str = None,
                   from_date: datetime = None, to_date: datetime = None) -> list[ChargeInDb]:
        filters = {}
        if timespan:
            filters["date"] = {}
            if to_date or from_date:
                raise ValueError("to_date and from_date cannot be used alongside timespan")
            timespan_seconds = timeparse(timespan)
            if not timespan_seconds:
                raise ValueError(f"Cannot parse timespan value '{timespan}'")
            date_start = datetime.now() - timedelta(seconds=timespan_seconds)
            filters["date"]["$gte"] = date_start
        if from_date:
            if filters.get("date", None) is None:
                filters["date"] = {}
            filters["date"]["$gte"] = from_date
        if to_date:
            if filters.get("date", None) is None:
                filters["date"] = {}
            filters["date"]["$lte"] = to_date
        sort = [('date', -1)]
        entries = get_collection(db, self.collection).find(filters, limit=limit, skip=offset, sort=sort)
        results: list[ChargeInDb] = []
        async for entry in entries:
            entry['id'] = str(entry['_id'])
            results.append(ChargeInDb(**entry))
        return results

    async def update_by_id(self, db: AsyncIOMotorClient, by_id: str, new_item: Charge) -> ChargeInDb | None:
        update_data = new_item.model_dump()
        old_item = await self.get_by_id(db, by_id)
        if not old_item:
            return None
        item_data = old_item.model_dump()
        item_data.update(update_data)
        check_item = Charge(**item_data)
        await _check_references(db, check_item)
        await get_collection(db, self.collection).update_one({'_id': bson.ObjectId(by_id)},
                                                             {'$set': check_item.model_dump()})
        return await self.get_by_id(db, by_id)

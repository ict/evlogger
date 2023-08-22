import codecs
import csv
import re
from datetime import datetime, timedelta
from typing import BinaryIO

import bson
import chardet
import dateparser
from pydantic import ValidationError

import app.core
from app.core.config import COLLECTION_CARS, COLLECTION_CPOS
from app.core.db import AsyncIOMotorClient
from app.models.charging import Charge, ChargeInDb, CarInDb, CPO
from app.operations.crud_base import CRUDBase, get_collection, CPOCrud
from app.util.timeparse import timeparse


async def _check_references(db: AsyncIOMotorClient, item: Charge) -> None:
    """
    Checks the "foreign keys" of the entity and fills optional (denormalized) fields
    """
    try:
        car_id = bson.ObjectId(item.car_id)
    except:
        raise ValueError(f"car_id '{item.car_id}' invalid")
    car = await get_collection(db, COLLECTION_CARS).find_one({'_id': car_id})
    if not car:
        raise ValueError(f"car_id '{item.car_id}' does not exist")
    item.car_name = car.get('name', '')

    try:
        cpo_id = bson.ObjectId(item.cpo_id)
    except:
        raise ValueError(f"cpo_id '{item.cpo_id}' invalid")
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

    async def list(
        self,
        db: AsyncIOMotorClient,
        limit: int = 20,
        offset: int = 0,
        timespan: str = None,
        from_date: datetime = None,
        to_date: datetime = None,
    ) -> list[ChargeInDb]:
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
        await get_collection(db, self.collection).update_one(
            {'_id': bson.ObjectId(by_id)}, {'$set': check_item.model_dump()}
        )
        return await self.get_by_id(db, by_id)

    async def csv_import(
        self, db: AsyncIOMotorClient, car: CarInDb, csv_handle: BinaryIO, delim: str
    ) -> tuple[str, str]:
        charset = chardet.detect(csv_handle.read(100))
        dateparser_opts = {'DATE_ORDER': 'DMY'}
        csv_handle.seek(0)
        reader = csv.DictReader(codecs.iterdecode(csv_handle, charset['encoding']), delimiter=delim)
        fieldnames = reader.fieldnames
        for req_field in ('date', 'kwh_charged', 'charge_type'):
            if req_field not in fieldnames:
                return "format-error", f"Required field missing: {req_field}"
        if not any(field in fieldnames for field in ('cpo_name', 'cpo_id')):
            return "format-error", "One of cpo_name, cpo_id is required"
        entry_no = 0
        seen_dates = set()
        logs = []
        errors = False
        line: dict
        no_number = re.compile(r'[^\d.]')

        for line in reader:
            entry_no += 1
            try:
                charged = float(no_number.sub("", line.get('kwh_charged')))
            except ValueError as err:
                logs.append(f"Line {entry_no}: invalid kwh_charged value: {charged}")
                errors = True
                continue
            if charged < 100:
                # Assume number is in kWh with decimal places
                charged = int(round(charged * 100, 2))
            else:
                charged = int(round(charged, 2))
            line['kwh_charged'] = charged

            price_str = line.get('price_total')
            if price_str is not None:
                try:
                    price = float(no_number.sub("", price_str))
                except ValueError as err:
                    logs.append(f"Line {entry_no}: invalid price_total value: {price_str}")
                    errors = True
                    continue
                if price < 100:
                    # Assume number is not yet in cents
                    price = int(round(price * 100, 2))
                else:
                    price = int(round(price, 2))
            else:
                price = None
            line['price_total'] = price

            if "cpo_id" not in line:
                # For CSV import, we also allow just the name and infer the CPO, creating a new one if it does not exist
                cpo_name = line.get('cpo_name')
                if not cpo_name:
                    logs.append(f"Line {entry_no}: \"{cpo_name}\": invalid cpo name")
                    errors = True
                    continue
                cpo = await CPOCrud.get_by_property(db, "name", cpo_name)
                if not cpo:
                    logs.append(f"Line {entry_no}: Creating new CPO for \"{cpo_name}\"")
                    # infer default price from entry
                    if price is not None:
                        default_price = int(round(price / (charged / 100)))
                    else:
                        default_price = 0
                    cpo_obj = CPO(name=cpo_name, default_price=default_price)
                    cpo = await CPOCrud.create(db, cpo_obj)
                line['cpo_id'] = cpo.id

            date_str = line['date']
            date_parsed: datetime = dateparser.parse(date_str, settings=dateparser_opts)
            while date_parsed.timestamp() in seen_dates:
                # If we have identical dates, add a second until it is unique
                # This way, we keep the charges in the order from the CSV file
                date_parsed = date_parsed + timedelta(seconds=1)
            seen_dates.add(date_parsed.timestamp())
            line['date'] = date_parsed

            line['car_id'] = car.id
            try:
                charge_obj = Charge(**line)
            except ValidationError as err:
                errors = True
                logs.append(f"Line {entry_no}: {str(err)}")
                continue
            try:
                charge = await ChargeCrudOp.create(db, charge_obj)
                logs.append(f"Line {entry_no}: Created Charge {charge.id}")
            except ValueError as err:
                errors = True
                logs.append(f"Line {entry_no}: {str(err)}")
                continue

        status = "completed (errors)" if errors else "completed"
        return status, "\n".join(logs)


ChargeCrudOp = ChargeCrud(app.core.config.COLLECTION_CHARGES)

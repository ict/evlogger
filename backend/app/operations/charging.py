import codecs
import csv
import re
from datetime import UTC, datetime, timedelta
from typing import BinaryIO

import bson
import chardet
import dateparser
from pydantic import ValidationError

import app.core
from app.core.config import COLLECTION_CARS, COLLECTION_CHARGES, COLLECTION_CPOS
from app.core.db import AsyncIOMotorClient
from app.models.charging import (
    CPO,
    CarChargeStats,
    CarInDb,
    ChargeInDb,
    ChargeStats,
    ChargeStatsBucket,
    ChargeSubmission,
)
from app.operations.cars import get_owned_car
from app.operations.crud_base import CPOCrud, CRUDBase, get_collection
from app.util.timeparse import timeparse


async def _check_plausible(
    db: AsyncIOMotorClient, item: ChargeSubmission, owner_id: str, *, is_new: bool = True, item_id: str | None = None
) -> None:
    """
    Check the "foreign keys" of the entity and fills optional (denormalized) fields
    """
    car = await get_owned_car(db, item.car_id, owner_id, entry_date=item.date)
    car_id = car['_id']
    item.car_name = car.get('name', '')

    try:
        cpo_id = bson.ObjectId(item.cpo_id)
    except TypeError:
        msg = f"cpo_id '{item.cpo_id}' invalid"
        raise ValueError(msg) from None
    cpo = await get_collection(db, COLLECTION_CPOS).find_one({'_id': cpo_id})
    if not cpo:
        msg = f"cpo_id '{item.cpo_id}' is invalid"
        raise ValueError(msg) from None
    if cpo.get('owner_id', None) != owner_id:
        msg = f"cpo_id '{item.cpo_id}' is invalid"
        raise ValueError(msg) from None
    item.cpo_name = cpo.get('name', '')

    if is_new:
        if item.price_total is None:
            item.price_total = int(round((item.kwh_charged / 100) * cpo.get('default_price', 0)))
        if item.car_odometer is None:
            item.car_odometer = car.get('odometer', 0) + item.car_km_driven

    # Check if the odometer value and price is plausible when editing a charge
    else:
        if not item.car_odometer:
            msg = 'car_odometer is required when editing a charge'
            raise ValueError(msg)
        if item.price_total is None:
            msg = 'price_total is required when editing a charge'
            raise ValueError(msg)

    # Find the previous charge before this one and the next one, if they exist.
    # Exclude the charge being edited (item_id) so a date submitted with lower
    # sub-second precision than what's stored in MongoDB doesn't cause the charge
    # to match itself as its own neighbour.
    id_exclusion = {'_id': {'$ne': bson.ObjectId(item_id)}} if item_id else {}
    prev_charge = await get_collection(db, COLLECTION_CHARGES).find_one(
        {'car_id': item.car_id, 'date': {'$lt': item.date}, **id_exclusion}, sort=[('date', -1)], limit=1
    )
    next_charge = await get_collection(db, COLLECTION_CHARGES).find_one(
        {'car_id': item.car_id, 'date': {'$gt': item.date}, **id_exclusion}, sort=[('date', 1)], limit=1
    )
    if prev_charge:
        prev_odo = prev_charge.get('car_odometer', 0)
        if prev_odo > item.car_odometer:
            msg = f'car_odometer must be greater than the previous charge ({prev_odo})'
            raise ValueError(msg)

    if next_charge:
        next_odo = next_charge.get('car_odometer', 1_000_000)
        if next_odo < item.car_odometer:
            msg = f'car_odometer must be less than the next charge ({next_odo})'
            raise ValueError(msg)

    else:
        # This is the newest charge, update the car's global odometer
        await get_collection(db, COLLECTION_CARS).update_one({'_id': car_id}, {'$set': {'odometer': item.car_odometer}})


class ChargeCrud(CRUDBase[ChargeSubmission, ChargeInDb]):
    def __init__(self, collection_name: str):
        super().__init__(collection_name, ChargeSubmission, ChargeInDb)

    async def create(self, db: AsyncIOMotorClient, item: ChargeSubmission, owner_id: str) -> ChargeInDb:
        await _check_plausible(db, item, owner_id)  # raises on errors
        return await super().create(db, item, owner_id)

    async def list(
        self,
        db: AsyncIOMotorClient,
        limit: int = 100,
        offset: int = 0,
        owner_id: str | None = None,
        timespan: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        car_id: str | None = None,
    ) -> list[ChargeInDb]:
        filters = {}
        if car_id is not None:
            filters['car_id'] = car_id
        if owner_id is not None:
            filters['owner_id'] = owner_id
        if timespan:
            filters['date'] = {}
            if to_date or from_date:
                msg = 'to_date and from_date cannot be used alongside timespan'
                raise ValueError(msg)
            timespan_seconds = timeparse(timespan)
            if not timespan_seconds:
                msg = f"Cannot parse timespan value '{timespan}'"
                raise ValueError(msg)
            date_start = datetime.now(UTC) - timedelta(seconds=timespan_seconds)
            filters['date']['$gte'] = date_start
        if from_date:
            if filters.get('date') is None:
                filters['date'] = {}
            filters['date']['$gte'] = from_date
        if to_date:
            if filters.get('date') is None:
                filters['date'] = {}
            filters['date']['$lte'] = to_date
        sort = [('date', -1)]
        entries = get_collection(db, self.collection).find(filters, limit=limit, skip=offset, sort=sort)
        results: list[ChargeInDb] = []
        async for entry in entries:
            entry['id'] = str(entry['_id'])
            results.append(ChargeInDb(**entry))
        return results

    async def stats(
        self,
        db: AsyncIOMotorClient,
        owner_id: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        car_id: str | None = None,
    ) -> ChargeStats:
        """
        Aggregate charge count, energy and cost per car (and in total) inside MongoDB.
        Date bounds are inclusive on both ends, like in `list`. A missing price_total counts as 0 cost
        (same as the frontend, see frontend/src/costs.js) and is reported in `charges_without_price`.
        """
        match: dict = {'owner_id': owner_id}
        if car_id is not None:
            match['car_id'] = car_id
        if from_date or to_date:
            match['date'] = {}
            if from_date:
                match['date']['$gte'] = from_date
            if to_date:
                match['date']['$lte'] = to_date
        pipeline = [
            {'$match': match},
            {'$sort': {'date': 1}},
            {
                '$group': {
                    '_id': '$car_id',
                    'car_name': {'$last': '$car_name'},
                    'count': {'$sum': 1},
                    'kwh_charged': {'$sum': '$kwh_charged'},
                    'price_total': {'$sum': {'$ifNull': ['$price_total', 0]}},
                    'charges_without_price': {
                        '$sum': {'$cond': [{'$eq': [{'$ifNull': ['$price_total', None]}, None]}, 1, 0]}
                    },
                }
            },
            {'$sort': {'car_name': 1, '_id': 1}},
        ]
        per_car: list[CarChargeStats] = []
        async for row in get_collection(db, self.collection).aggregate(pipeline):
            per_car.append(
                CarChargeStats(
                    car_id=row['_id'],
                    car_name=row.get('car_name'),
                    count=int(row['count']),
                    kwh_charged=int(row['kwh_charged']),
                    price_total=int(row['price_total']),
                    charges_without_price=int(row['charges_without_price']),
                )
            )
        total = ChargeStatsBucket(
            count=sum(c.count for c in per_car),
            kwh_charged=sum(c.kwh_charged for c in per_car),
            price_total=sum(c.price_total for c in per_car),
            charges_without_price=sum(c.charges_without_price for c in per_car),
        )
        return ChargeStats(from_date=from_date, to_date=to_date, total=total, per_car=per_car)

    async def update_by_id(
        self, db: AsyncIOMotorClient, by_id: str, new_item: ChargeSubmission, owner_id: str | None = None
    ) -> ChargeInDb | None:
        update_data = new_item.model_dump()
        old_item = await self.get_by_id(db, by_id)
        if not old_item:
            return None
        if not owner_id or old_item.owner_id != owner_id:
            return None
        item_data = old_item.model_dump()
        item_data.update(update_data)
        check_item = ChargeSubmission(**item_data)
        await _check_plausible(db, check_item, owner_id, is_new=False, item_id=by_id)
        await get_collection(db, self.collection).update_one(
            {'_id': bson.ObjectId(by_id)}, {'$set': check_item.model_dump()}
        )
        return await self.get_by_id(db, by_id)

    async def csv_import(
        self, db: AsyncIOMotorClient, car: CarInDb, owner_id: str, csv_handle: BinaryIO, delim: str
    ) -> tuple[str, str]:
        logs = []
        charset = chardet.detect(csv_handle.read(1024 * 1024))
        logs.append(f'Charset detected: {charset}')
        dateparser_opts = {'DATE_ORDER': 'DMY', 'TIMEZONE': 'UTC', 'RETURN_AS_TIMEZONE_AWARE': True}
        csv_handle.seek(0)
        reader = csv.DictReader(codecs.iterdecode(csv_handle, charset['encoding'] or 'utf-8'), delimiter=delim)
        fieldnames = list(reader.fieldnames or [])
        for req_field in ('date', 'kwh_charged', 'charge_type'):
            if req_field not in fieldnames:
                return 'format-error', f'Required field missing: {req_field}'
        if not any(field in fieldnames for field in ('cpo_name', 'cpo_id')):
            return 'format-error', 'One of cpo_name, cpo_id is required'
        entry_no = 0
        seen_dates = set()
        errors = False
        line: dict
        no_number = re.compile(r'[^\d.]')

        for line in reader:
            entry_no += 1
            charged_str = line.get('kwh_charged', '')
            if ',' in charged_str:
                # Replace comma with dot for decimal numbers on best efforts
                if charged_str.count('.') != 0 or charged_str.count(',') != 1:
                    logs.append(f'Line {entry_no}: kwh_charged contains dot and comma: {charged_str}')
                    errors = True
                    continue
                charged_str = charged_str.replace(',', '.')
            try:
                charged = float(no_number.sub('', charged_str))
            except ValueError:
                logs.append(f'Line {entry_no}: invalid kwh_charged value: {charged_str}')
                errors = True
                continue
            if charged < 100:
                # Assume number is in kWh with decimal places
                charged = int(round(charged * 100, 2))
            else:
                charged = int(round(charged, 2))
            line['kwh_charged'] = charged

            price_str = line.get('price_total')
            if price_str and ',' in price_str:
                # Replace comma with dot for decimal numbers on best efforts
                if price_str.count('.') != 0 or price_str.count(',') != 1:
                    logs.append(f'Line {entry_no}: price_total contains dot and comma: {price_str}')
                    errors = True
                    continue
                price_str = price_str.replace(',', '.')
            if price_str is not None:
                try:
                    price = float(no_number.sub('', price_str))
                except ValueError:
                    logs.append(f'Line {entry_no}: invalid price_total value: {price_str}')
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

            if 'cpo_id' not in line:
                # For CSV import, we also allow just the name and infer the CPO, creating a new one if it does not exist
                cpo_name = line.get('cpo_name')
                if not cpo_name:
                    logs.append(f'Line {entry_no}: "{cpo_name}": invalid cpo name')
                    errors = True
                    continue
                cpo = await CPOCrud.get_by_property(db, 'name', cpo_name, owner_id)
                if not cpo:
                    logs.append(f'Line {entry_no}: Creating new CPO for "{cpo_name}"')
                    # infer default price from entry
                    default_price = int(round(price / (charged / 100))) if price is not None else 0
                    cpo_obj = CPO(name=cpo_name, default_price=default_price)
                    cpo = await CPOCrud.create(db, cpo_obj, owner_id)
                line['cpo_id'] = cpo.id

            date_str = line['date']
            date_parsed = dateparser.parse(date_str, settings=dateparser_opts)
            if not date_parsed:
                logs.append(f'Line {entry_no}: invalid date: {date_str}')
                errors = True
                continue
            while date_parsed.timestamp() in seen_dates:
                # If we have identical dates, add a second until it is unique
                # This way, we keep the charges in the order from the CSV file
                date_parsed = date_parsed + timedelta(seconds=1)
            seen_dates.add(date_parsed.timestamp())
            line['date'] = date_parsed

            line['car_id'] = car.id
            try:
                charge_obj = ChargeSubmission(**line)
            except ValidationError as err:
                errors = True
                logs.append(f'Line {entry_no}: {err!s}')
                continue
            try:
                charge = await ChargeCrudOp.create(db, charge_obj, owner_id)
                logs.append(f'Line {entry_no}: Created Charge {charge.id}')
            except ValueError as err:
                errors = True
                logs.append(f'Line {entry_no}: {err!s}')
                continue

        status = 'completed (errors)' if errors else 'completed'
        return status, '\n'.join(logs)


ChargeCrudOp = ChargeCrud(app.core.config.COLLECTION_CHARGES)

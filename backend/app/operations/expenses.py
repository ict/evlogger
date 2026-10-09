from datetime import datetime

import bson

import app.core
from app.core.db import AsyncIOMotorClient
from app.models.expenses import Expense, ExpenseCategory, ExpenseInDb, ExpenseKind
from app.operations.cars import get_owned_car
from app.operations.crud_base import CRUDBase, dump_for_db, get_collection


async def _check_plausible(db: AsyncIOMotorClient, item: Expense, owner_id: str) -> None:
    """
    Check the "foreign keys" of the entity and fills optional (denormalized) fields
    """
    car = await get_owned_car(db, item.car_id, owner_id, entry_date=item.date)
    item.car_name = car.get('name', '')


class ExpenseCrud(CRUDBase[Expense, ExpenseInDb]):
    def __init__(self, collection_name: str):
        super().__init__(collection_name, Expense, ExpenseInDb)

    async def create(self, db: AsyncIOMotorClient, item: Expense, owner_id: str | None = None) -> ExpenseInDb:
        await _check_plausible(db, item, owner_id)  # raises on errors
        return await super().create(db, item, owner_id)

    async def list(
        self,
        db: AsyncIOMotorClient,
        limit: int = 100,
        offset: int = 0,
        owner_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        car_id: str | None = None,
        category: ExpenseCategory | None = None,
        kind: ExpenseKind | None = None,
    ) -> list[ExpenseInDb]:
        filters: dict = {}
        if car_id is not None:
            filters['car_id'] = car_id
        if owner_id is not None:
            filters['owner_id'] = owner_id
        if category is not None:
            filters['category'] = category.value
        if kind == ExpenseKind.expense:
            # entries stored before `kind` existed have no field and count as expenses
            filters['kind'] = {'$ne': ExpenseKind.income.value}
        elif kind is not None:
            filters['kind'] = kind.value
        if from_date:
            filters.setdefault('date', {})['$gte'] = from_date
        if to_date:
            filters.setdefault('date', {})['$lte'] = to_date
        entries = get_collection(db, self.collection).find(filters, limit=limit, skip=offset, sort=[('date', -1)])
        results: list[ExpenseInDb] = []
        async for entry in entries:
            entry['id'] = str(entry['_id'])
            results.append(ExpenseInDb(**entry))
        return results

    async def update_by_id(
        self, db: AsyncIOMotorClient, by_id: str, new_item: Expense, owner_id: str | None = None
    ) -> ExpenseInDb | None:
        old_item = await self.get_by_id(db, by_id)
        if not old_item or not owner_id or old_item.owner_id != owner_id:
            return None
        check_item = Expense(**{**dump_for_db(old_item), **new_item.model_dump(exclude_unset=True)})
        await _check_plausible(db, check_item, owner_id)
        await get_collection(db, self.collection).update_one(
            {'_id': bson.ObjectId(by_id)}, {'$set': dump_for_db(check_item)}
        )
        return await self.get_by_id(db, by_id)


ExpenseCrudOp = ExpenseCrud(app.core.config.COLLECTION_EXPENSES)

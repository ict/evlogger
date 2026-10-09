from decimal import Decimal
from typing import Generic, TypeVar

import bson
from bson.codec_options import CodecOptions, TypeCodec, TypeRegistry
from pydantic import BaseModel

import app.core
from app.core import config
from app.core.db import AsyncIOMotorClient
from app.models.charging import CPO, CarInDb, CPOInDb

InCls = TypeVar('InCls')
DbCls = TypeVar('DbCls')


class DecimalCodec(TypeCodec):
    python_type = Decimal  # the Python type acted upon by this type codec
    bson_type = bson.Decimal128  # the BSON type acted upon by this type codec

    def transform_python(self, value):
        """Function that transforms a custom type value into a type
        that BSON can encode."""
        return bson.Decimal128(value)

    def transform_bson(self, value):
        """Function that transforms a vanilla BSON type value into our
        custom type."""
        return value.to_decimal()


def get_collection(db: AsyncIOMotorClient, collection_name: str):
    def fallback_encoder(value):
        # BSON has no date-only type: datetime.date is stored as an ISO string (YYYY-MM-DD),
        # which pydantic parses back into a date when loading
        return str(value)

    decimal_codec = DecimalCodec()
    type_registry = TypeRegistry([decimal_codec], fallback_encoder=fallback_encoder)
    codec_options = CodecOptions(type_registry=type_registry, tz_aware=True)
    return db[config.DATABASE_NAME].get_collection(collection_name, codec_options=codec_options)


def dump_for_db(item: BaseModel) -> dict:
    """Dump a model for storage, leaving out computed fields (they are derived on read)"""
    return item.model_dump(exclude=set(type(item).model_computed_fields))


class CRUDBase(Generic[InCls, DbCls]):
    def __init__(self, collection: str, incls, dbcls):
        self.collection = collection
        self.incls = incls
        self.dbcls = dbcls

    async def get_by_id(self, db: AsyncIOMotorClient, by_id: str, owner_id: str | None = None) -> DbCls | None:
        try:
            object_id = bson.ObjectId(by_id)
        except TypeError:
            return None
        if owner_id is not None:
            res = await get_collection(db, self.collection).find_one({'_id': object_id, 'owner_id': owner_id})
        else:
            res = await get_collection(db, self.collection).find_one({'_id': object_id})
        if res:
            res['id'] = str(res['_id'])
            return self.dbcls(**res)
        return None

    async def get_by_property(
        self, db: AsyncIOMotorClient, property_name: str, property_value: str, owner_id: str | None = None
    ) -> DbCls | None:
        find_filter = {property_name: property_value}
        if owner_id is not None:
            find_filter['owner_id'] = owner_id
        res = await get_collection(db, self.collection).find_one(find_filter)
        if res:
            res['id'] = str(res['_id'])
            return self.dbcls(**res)
        return None

    async def list(
        self, db: AsyncIOMotorClient, limit: int = 20, offset: int = 0, owner_id: str | None = None
    ) -> list[DbCls]:
        result: list[CarInDb] = []
        if not owner_id:
            items = get_collection(db, self.collection).find(limit=limit, skip=offset)
        else:
            items = get_collection(db, self.collection).find({'owner_id': owner_id}, limit=limit, skip=offset)
        async for item in items:
            item['id'] = str(item['_id'])
            result.append(self.dbcls(**item))
        return result

    async def create(self, db: AsyncIOMotorClient, new_item: InCls, owner_id: str | None = None) -> DbCls:
        doc = dump_for_db(new_item)
        if owner_id:
            doc['owner_id'] = owner_id
        collection = get_collection(db, self.collection)
        result = await collection.insert_one(doc)
        return await self.get_by_id(db, result.inserted_id)

    async def delete_by_id(self, db: AsyncIOMotorClient, by_id: str, owner_id: str | None = None) -> bool:
        if owner_id is not None:
            res = await get_collection(db, self.collection).delete_one(
                {'_id': bson.ObjectId(by_id), 'owner_id': owner_id}
            )
        else:
            res = await get_collection(db, self.collection).delete_one({'_id': bson.ObjectId(by_id)})
        return res.deleted_count > 0

    async def update_by_id(
        self, db: AsyncIOMotorClient, by_id: str, new_item: InCls, owner_id: str | None = None
    ) -> DbCls | None:
        # Only touch fields the client actually sent; an explicit null clears the field
        update_data = new_item.model_dump(exclude_unset=True, exclude=set(type(new_item).model_computed_fields))
        old_item = await self.get_by_id(db, by_id)
        if not old_item or (owner_id and old_item.owner_id != owner_id):
            return None
        item_data = dump_for_db(old_item)
        item_data.update(update_data)
        await get_collection(db, self.collection).update_one({'_id': bson.ObjectId(by_id)}, {'$set': item_data})
        return await self.get_by_id(db, by_id)


CPOCrud = CRUDBase[CPO, CPOInDb](app.core.config.COLLECTION_CPOS, CPO, CPOInDb)

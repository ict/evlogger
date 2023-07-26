from decimal import Decimal
from typing import TypeVar, Generic

import bson
from bson.codec_options import CodecOptions, TypeRegistry, TypeCodec

import app.core
from app.core import config
from app.core.db import AsyncIOMotorClient
from app.models.charging import CarInDb, Car, CPO, CPOInDb

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
        return str(value)

    decimal_codec = DecimalCodec()
    type_registry = TypeRegistry([decimal_codec], fallback_encoder=fallback_encoder)
    codec_options = CodecOptions(type_registry=type_registry)
    coll = db[config.DATABASE_NAME].get_collection(collection_name,
                                                   codec_options=codec_options)
    return coll


class CRUDBase(Generic[InCls, DbCls]):
    def __init__(self, collection: str, incls, dbcls):
        self.collection = collection
        self.incls = incls
        self.dbcls = dbcls

    async def get_by_id(self, db: AsyncIOMotorClient, by_id: str) -> DbCls | None:
        try:
            object_id = bson.ObjectId(by_id)
        except:
            return None
        res = await get_collection(db, self.collection).find_one({'_id': object_id})
        if res:
            res['id'] = str(res['_id'])
            return self.dbcls(**res)
        return None

    async def list(self, db: AsyncIOMotorClient, limit: int = 20, offset: int = 0) -> list[DbCls]:
        result: list[CarInDb] = []
        items = get_collection(db, self.collection).find(limit=limit, skip=offset)
        async for item in items:
            item['id'] = str(item['_id'])
            result.append(self.dbcls(**item))
        return result

    async def create(self, db: AsyncIOMotorClient, new_item: InCls) -> DbCls:
        doc = new_item.model_dump()
        collection = get_collection(db, self.collection)
        result = await collection.insert_one(doc)
        return await self.get_by_id(db, result.inserted_id)

    async def delete_by_id(self, db: AsyncIOMotorClient, by_id: str) -> bool:
        res = await get_collection(db, self.collection).delete_one({'_id': by_id})
        return res.deleted_count > 0

    async def update_by_id(self, db: AsyncIOMotorClient, by_id: str, new_item: InCls) -> DbCls | None:
        update_data = new_item.model_dump(exclude_defaults=True, exclude_unset=True)
        old_item = await self.get_by_id(db, by_id)
        if not old_item:
            return None
        item_data = old_item.model_dump()
        item_data.update(update_data)
        await get_collection(db, self.collection).update_one({'_id': bson.ObjectId(by_id)}, {'$set': item_data})
        return await self.get_by_id(db, by_id)


CarCRUD = CRUDBase[Car, CarInDb](app.core.config.COLLECTION_CARS, Car, CarInDb)
CPOCrud = CRUDBase[CPO, CPOInDb](app.core.config.COLLECTION_CPOS, CPO, CPOInDb)

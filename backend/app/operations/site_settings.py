from pymongo import ReturnDocument

from app.core.config import COLLECTION_SITE_SETTINGS, DATABASE_NAME
from app.core.db import AsyncIOMotorClient
from app.models.site_settings import SiteSettings


def _col(db: AsyncIOMotorClient):
    return db[DATABASE_NAME][COLLECTION_SITE_SETTINGS]


async def get_site_settings(db: AsyncIOMotorClient) -> SiteSettings:
    doc = await _col(db).find_one({'_key': 'singleton'})
    if doc is None:
        return SiteSettings()
    return SiteSettings(**{k: v for k, v in doc.items() if k in SiteSettings.model_fields})


async def update_site_settings(db: AsyncIOMotorClient, settings: SiteSettings) -> SiteSettings:
    doc = await _col(db).find_one_and_update(
        {'_key': 'singleton'},
        {'$set': {'_key': 'singleton', **settings.model_dump()}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return SiteSettings(**{k: v for k, v in doc.items() if k in SiteSettings.model_fields})

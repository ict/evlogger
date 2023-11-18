from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from ..core.config import MONGODB_URL


class MongoDatabase:
    client: AsyncIOMotorClient = None


db = MongoDatabase()


async def get_database() -> AsyncIOMotorClient:
    return db.client


async def connect_to_mongo():
    logger.info('Connecting to MongoDB...')
    db.client = AsyncIOMotorClient(str(MONGODB_URL))
    logger.info('Connected to MongoDB')


async def close_mongo_connection():
    logger.info('Closing MongoDB connection...')
    db.client.close()
    logger.info('MongoDB connection closed')

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from ..core import config


class MongoDatabase:
    client: AsyncIOMotorClient = None


db = MongoDatabase()


async def get_database() -> AsyncIOMotorClient:
    return db.client


async def connect_to_mongo():
    logger.info(f'Connecting to MongoDB at {config.MONGODB_URL!s}')
    db.client = AsyncIOMotorClient(str(config.MONGODB_URL))
    logger.info('Connected to MongoDB')


async def close_mongo_connection():
    logger.info('Closing MongoDB connection...')
    db.client.close()
    logger.info('MongoDB connection closed')

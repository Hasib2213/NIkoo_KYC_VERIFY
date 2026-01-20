# app/database/mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client = None
    db = None

    @classmethod
    async def connect_db(cls):
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL, tls=True)
            cls.db = cls.client[settings.DATABASE_NAME]
            # Test connection
            await cls.client.admin.command("ping")
            logger.info("MongoDB connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect MongoDB: {str(e)}")
            raise

    @classmethod
    async def close_db(cls):
        if cls.client:
            cls.client.close()
            logger.info("MongoDB disconnected")

    @classmethod
    def get_collection(cls, collection_name: str):
        if cls.db is None:
            raise RuntimeError("Database connection is not established.")
        return cls.db[collection_name]
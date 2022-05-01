from datetime import datetime
import logging

logger = logging.getLogger("ai4mat")
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import Config
from db.mongodb import db


async def connect_to_mongo():
    logger.info("Connecting to MongoDB..")

    db.client = AsyncIOMotorClient(
        str(Config.mongo_uri), maxPoolSize=Config.max_conn, minPoolSize=Config.min_conn
    )
    logger.info(
        f"Connection succesfully established at {datetime.now().strftime('%Y-%B-%d %H:%M:%S')}."
    )


async def close_mongo_connection():
    logger.info("Closing connection to MongoDB...")
    db.client.close()
    logger.info("Connection succesfully closed！")

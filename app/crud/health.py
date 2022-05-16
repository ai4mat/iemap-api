import logging
from db.mongodb import AsyncIOMotorClient
from core.config import Config

logger = logging.getLogger("ai4mat")

database_name, collection_name = (Config.mongo_db, Config.mongo_coll)


async def checkDB(conn: AsyncIOMotorClient):

    # doc = await conn[database_name][collection_name].find_one({}, {"_id": 0})
    try:
        info = await conn.server_info()
        return info
    except Exception as e:
        logger.error(f"Checking DB result in error: {e}")
        return e

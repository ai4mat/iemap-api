from db.mongodb import AsyncIOMotorClient
from core.config import Config


database_name, collection_name = (Config.mongo_db, Config.mongo_coll)


async def checkDB(conn: AsyncIOMotorClient):

    doc = await conn[database_name][collection_name].find_one({}, {"_id": 0})

    return doc

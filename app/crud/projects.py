from db.mongodb import AsyncIOMotorClient
from core.config import Config
from models.iemap import Project as IEMAPModel

database_name, ai4mat_collection_name = (Config.mongo_db, Config.mongo_coll)


async def add_project(conn: AsyncIOMotorClient, project: IEMAPModel):
    # result is of type InsertOneResult
    result = await conn[database_name][ai4mat_collection_name].insert_one(
        project.dict()
    )
    return result.inserted_id

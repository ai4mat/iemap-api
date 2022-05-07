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


async def list_projects(conn: AsyncIOMotorClient, project: IEMAPModel, limit, skip):

    """Function returns `page_size` number of documents after last_id
    and the new last_id.
    """
    coll = conn[database_name][ai4mat_collection_name]
    list_projects = []
    projects_docs = coll.find({}, {"_id": 0}, limit=limit, skip=skip)
    async for row in projects_docs:
        list_projects.append(row)
    return list_projects

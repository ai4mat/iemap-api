import json
from pickle import FALSE
from db.mongodb import AsyncIOMotorClient
from bson.objectid import ObjectId
from core.config import Config
from core.utils import JSONEncoder
from models.iemap import ObjectIdStr, Project as IEMAPModel
from crud.pipelines import get_properties_files

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
    projects_docs = await coll.find({}, {"_id": 0}, limit=limit, skip=skip)
    async for row in projects_docs:
        list_projects.append(row)
    return list_projects


async def list_project_properties_files(
    conn: AsyncIOMotorClient, affiliation: str, useremail: str
):

    """Function returns `page_size` number of documents after last_id
    and the new last_id.
    """
    coll = conn[database_name][ai4mat_collection_name]
    list_docs = []
    pipeline = get_properties_files(affiliation, useremail)
    result = await coll.aggregate(pipeline).to_list(length=None)
    # async for doc in file_list_docs:
    #     list_docs.append(doc)
    return result


async def add_property_file(
    conn: AsyncIOMotorClient,
    id: str,
    fileHash: str,
    strFileSize: str,
    strFileExt: str,
    elementName: str,
    elementType: str,
):
    """Function to add file hash to a property file.
    The document to update is identified by the document's id, and the property file's name.
    """
    #  {"_id":ObjectId("62752dd88856514dab27dd8e")},
    # {$set:{"process.properties.$[elem].hash":"hash-2"}},{arrayFilters:[{$and:[{"elem.name":"H2o"},{"elem.type":"2D"}]}]}

    coll = conn[database_name][ai4mat_collection_name]

    result_update = await coll.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "process.properties.$[elem].file.hash": fileHash,
                "process.properties.$[elem].file.size": strFileSize,
                "process.properties.$[elem].file.extention": strFileExt,
            }
        },
        upsert=False,
        array_filters=[
            {"$and": [{"elem.name": elementName}, {"elem.type": elementType}]}
        ],
    )
    return result_update.modified_count


async def add_project_file(
    conn: AsyncIOMotorClient,
    id: str,
    fileHash: str,
    fileSize: str,
    fileExt: str,
    fileName: str,
):
    """Function to add file hash to PROJECT
    The document to update is identified by the document's id, and file's name and extention.
    """
    #  {"_id":ObjectId("62752dd88856514dab27dd8e")},
    # {$set:{"process.properties.$[elem].hash":"hash-2"}},{arrayFilters:[{$and:[{"elem.name":"H2o"},{"elem.type":"2D"}]}]}

    coll = conn[database_name][ai4mat_collection_name]

    result_update = await coll.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "files.$[elem].hash": fileHash,
                "files.$[elem].size": fileSize,
                "files.$[elem].extention": fileExt,
            }
        },
        upsert=False,
        array_filters=[
            {"$and": [{"elem.name": fileName}, {"elem.extention": fileExt}]}
        ],
    )
    return result_update.modified_count


# https://medium.com/@madhuri.pednekar/handling-mongodb-objectid-in-python-fastapi-4dd1c7ad67cd
# https://www.tutorialsteacher.com/mongodb/update-arrays
# https://www.mongodb.com/docs/manual/reference/operator/update/positional-filtered/#mongodb-update-up.---identifier--

from models.iemap import FileProject, Property

from db.mongodb import AsyncIOMotorClient
from bson.objectid import ObjectId
from core.config import Config

from models.iemap import Project as IEMAPModel
from crud.pipelines import get_properties_files

database_name, ai4mat_collection_name = (Config.mongo_db, Config.mongo_coll)


async def add_project(conn: AsyncIOMotorClient, project: IEMAPModel):
    # result is of type InsertOneResult
    result = await conn[database_name][ai4mat_collection_name].insert_one(
        project.dict()
    )
    return result.inserted_id


async def list_projects(conn: AsyncIOMotorClient, limit, skip):
    """Function to list all projects in DB

    Args:
        conn (AsyncIOMotorClient): Motor MongoDB client connection
        limit (int): number of documents to return
        skip (int): number of documents to skip

    Returns:
        List[Any]: list of documents as result of the query (find({}))
    """

    coll = conn[database_name][ai4mat_collection_name]
    list_projects = await coll.find({}, {"_id": 0}, limit=limit, skip=skip).to_list(
        None
    )
    # async for row in projects_docs:
    #     list_projects.append(row)
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
    """# Function to add file to PROJECT
    (using filne name hash and original extention)
    The document to update is identified by the mdocuent's id, and file's name and extention.

    Parameters:
    -----------
        conn: AsyncIOMotorClient - Motor MongoDB client connection
        id: str - MongoDB document's id (ObjectId) to update
        fileHash: str - file hash
        fileSize: str - file size
        fileExt: str - file extention
        fileName: str - file name

    Returns:
    --------
        modified_count, matched_cound: (int,int) - number of modified documents, number of matched documents

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
    # if a document already exists, number_matched_documents will be 1
    num_docs_updated, number_doc_matched = (
        result_update.modified_count,
        result_update.matched_count,
    )

    return num_docs_updated, number_doc_matched


async def find_project_file_by_hash(conn: AsyncIOMotorClient, file_hash: str, id: str):
    """Function to check if file hash already exists in the database."""
    coll = conn[database_name][ai4mat_collection_name]
    # db.data.find({_id:ObjectId("62761c48856da47202945e05")},{"files":{$filter:{input:"$files",cond:{$eq:["$$this.name","File esperimento 1"]}}}})
    result = await coll.find_one(
        {"_id": ObjectId(id)},
        {
            "files": {
                "$filter": {
                    input: "$files",
                    "cond": {"$eq": ["$$this.hash", file_hash]},
                }
            }
        },
    )
    return result


async def count_projects(conn: AsyncIOMotorClient) -> int:
    coll = conn[database_name][ai4mat_collection_name]
    result = await coll.count_documents({})
    return result


async def add_project_file_and_data(
    conn: AsyncIOMotorClient, id: str, file_data: FileProject
):
    """Function to add file hash to PROJECT
    The document to update is identified by the document's id, and file's name and extention.
    """
    #  {"_id":ObjectId("62752dd88856514dab27dd8e")},
    # {$set:{"process.properties.$[elem].hash":"hash-2"}},{arrayFilters:[{$and:[{"elem.name":"H2o"},{"elem.type":"2D"}]}]}

    coll = conn[database_name][ai4mat_collection_name]
    try:
        result_update = await coll.update_one(
            {"_id": ObjectId(id)},
            {
                "$addToSet": {
                    "files": file_data.dict(),
                }
            },
        )
    # result_update = await coll.update_one(
    #     {"_id": ObjectId(id)},
    #     {
    #         "$set": {
    #             "files.$[elem]": file_data.dict(),
    #         }
    #     },
    #     upsert=True,
    #     array_filters=[{"$and": [{"elem.hash": file_data.hash}]}],
    # )
    except Exception as WriteError:
        result_update = await coll.update_one(
            {"_id": ObjectId(id)},
            {
                "$addToSet": {
                    "files": file_data.dict(),
                }
            },
        )

    return result_update.modified_count, result_update.matched_count


async def add_property(conn: AsyncIOMotorClient, id: str, property: Property):
    """Function to add file hash to a property file.
    The document to update is identified by the document's id, and the property file's name.
    """
    #  {"_id":ObjectId("62752dd88856514dab27dd8e")},
    # {$set:{"process.properties.$[elem].hash":"hash-2"}},{arrayFilters:[{$and:[{"elem.name":"H2o"},{"elem.type":"2D"}]}]}

    coll = conn[database_name][ai4mat_collection_name]
    update_query = {
        "$addToSet": {"process.properties": {**property.dict()}}
        # "$set": {
        #     "process.properties.$[elem].name": property.name
        #     #  {
        #     #     **property.dict(),
        #     # }
        # }
    }
    print(update_query)
    result_update = await coll.update_one(
        {"_id": ObjectId(id)},
        update_query,
        # upsert=True,
        # array_filters=[
        #     {"$and": [{"elem.name": property.name}, {"elem.type": property.type}]}
        # ],
    )

    return result_update.modified_count, result_update.upserted_id


def generate_pagination_query(query, sort=None, next_key=None):
    sort_field = None if sort is None else sort[0]

    def next_key_fn(items):
        if len(items) == 0:
            return None
        item = items[-1]
        if sort_field is None:
            return {"_id": item["_id"]}
        else:
            return {"_id": item["_id"], sort_field: item[sort_field]}

    if next_key is None:
        return query, next_key_fn

    paginated_query = query.copy()

    if sort is None:
        paginated_query["_id"] = {"$gt": next_key["_id"]}
        return paginated_query, next_key_fn

    sort_operator = "$gt" if sort[1] == 1 else "$lt"

    pagination_query = [
        {sort_field: {sort_operator: next_key[sort_field]}},
        {
            "$and": [
                {sort_field: next_key[sort_field]},
                {"_id": {sort_operator: next_key["_id"]}},
            ]
        },
    ]

    if "$or" not in paginated_query:
        paginated_query["$or"] = pagination_query
    else:
        paginated_query = {"$and": [query, {"$or": pagination_query}]}

    return paginated_query, next_key_fn


async def find_all_project_paginated(
    conn: AsyncIOMotorClient, query={}, limit=10, sort=["_id", -1], next_key=None
):
    coll = conn[database_name][ai4mat_collection_name]
    paginated_query, next_key_fn = generate_pagination_query(query, sort, next_key)
    result = await coll.find(paginated_query).limit(limit).sort([sort]).to_list(None)
    next_key = next_key_fn(result)
    return result, next_key


# https://medium.com/@madhuri.pednekar/handling-mongodb-objectid-in-python-fastapi-4dd1c7ad67cd
# https://www.tutorialsteacher.com/mongodb/update-arrays
# https://www.mongodb.com/docs/manual/reference/operator/update/positional-filtered/#mongodb-update-up.---identifier--

from typing import List

from core.utils import get_value_float_or_str
from models.iemap import FileProject, Property, queryModel

from db.mongodb import AsyncIOMotorClient
from bson.objectid import ObjectId
from core.config import Config

from models.iemap import Project as IEMAPModel
from models.iemap import ProjectQueryResult
from crud.pipelines import get_properties_files, get_user_projects_base_info

from dateutil.parser import parse

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
    fp: FileProject,
    elementName: str,
):
    """Function to add file hash to a property file.
    The document to update is identified by the document's id, and the property file's name.
    """
    #  {"_id":ObjectId("62752dd88856514dab27dd8e")},
    # {$set:{"process.properties.$[elem].hash":"hash-2"}},{arrayFilters:[{$and:[{"elem.name":"H2o"},{"elem.type":"2D"}]}]}

    coll = conn[database_name][ai4mat_collection_name]

    result_update_property = await coll.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "properties.$[elem].file": fp.hash + "." + fp.extention,
            }
        },
        upsert=False,
        array_filters=[{"$and": [{"elem.name": elementName}]}],
    )
    if result_update_property.modified_count == 1:
        result_update = await coll.update_one(
            {"_id": ObjectId(id)}, {"$push": {"files": fp.dict()}}
        )

    return result_update_property.modified_count, result_update_property.matched_count


async def add_project_file(conn: AsyncIOMotorClient, id: str, fp: FileProject):
    """# Function to add file to PROJECT
    (using filne name hash and original extention)
    The document to update is identified by the mdocuent's id, and file's name and extention.

    Parameters:
    -----------
        conn: AsyncIOMotorClient - Motor MongoDB client connection
        id: str - MongoDB document's id (ObjectId) to update
        fp: FileProject

    Returns:
    --------
        modified_count, matched_cound: (int,int) - number of modified documents, number of matched documents

    """
    #  {"_id":ObjectId("62752dd88856514dab27dd8e")},
    # {$set:{"process.properties.$[elem].hash":"hash-2"}},{arrayFilters:[{$and:[{"elem.name":"H2o"},{"elem.type":"2D"}]}]}

    coll = conn[database_name][ai4mat_collection_name]

    # first check if field exist and is not null
    # if exist than Add element to array, otherwise create array field with one element
    # filesExists = await coll.find_one({"_id": ObjectId(id), "files": {"$ne": None}})
    # result_update = None
    # if filesExists:
    #     result_update = await coll.update_one(
    #         {"_id": ObjectId(id)},
    #         {
    #             "$set": {
    #                 "files.$[elem].hash": fp.hash,
    #                 "files.$[elem].size": fp.size,
    #                 "files.$[elem].extention": fp.extention,
    #             }
    #         },
    #         upsert=False,
    #         array_filters=[
    #             {"$and": [{"elem.name": fp.name}, {"elem.extention": fp.extention}]}
    #         ],
    #     )
    # if a document already exists, number_matched_documents will be 1

    # if not filesExists:
    result_update = await coll.update_one(
        {"_id": ObjectId(id)}, {"$push": {"files": fp.dict()}}
    )

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


async def exec_query(conn: AsyncIOMotorClient, qp: queryModel):

    get_affiliation = lambda x: x.affiliation.split(",") if x.affiliation else None
    get_dates = (
        lambda x: {"$gte": parse(x[0]), "$lte": parse(x[1])}
        if len(x) > 1
        else {"$gte": parse(x[0])}
    )

    get_list_elements = lambda x: list(x.split(",")) if x else None

    query = {
        "_id" if qp.id else None: ObjectId(qp.id),
        "provenance.affiliation"
        if qp.affiliation
        else None: {"$in": get_affiliation(qp)},
        "project.name" if qp.project_name else None: qp.project_name,
        "provenance.email" if qp.provenance_email else None: qp.provenance_email,
        "material.formula" if qp.material_formula else None: qp.material_formula,
        "iemap_id" if qp.iemap_id else None: qp.iemap_id,
        "process.isExperiment" if qp.isExperiment != None else None: qp.isExperiment,
        # simulationCode translate into the 2 following fields ~~~~~~~~~~~~~~~~~~~
        "process.isExperiment" if qp.simulationCode else None: False,
        "process.agent.name" if qp.simulationCode else None: qp.simulationCode,
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # experimentInstrument translate into the 2 following fields ~~~~~~~~~~~~~~~~~~~
        "process.isExperiment" if qp.experimentInstrument else None: True,
        "process.agent.name"
        if qp.experimentInstrument
        else None: qp.experimentInstrument,
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # simulationMethod translate into the 2 following fields ~~~~~~~~~~~~~~~~~~~
        "process.isExperiment" if qp.simulationMethod else None: False,
        "process.method" if qp.simulationMethod else None: qp.simulationMethod,
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # simulationMethod translate into the 2 following fields ~~~~~~~~~~~~~~~~~~~
        "process.isExperiment" if qp.experimentMethod else None: True,
        "process.method" if qp.experimentMethod else None: qp.experimentMethod,
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        "parameters"
        if qp.parameterName and not qp.parameterValue
        else None: {"$elemMatch": {"name": qp.parameterName}},
        "parameters"
        if qp.parameterValue and qp.parameterValue
        else None: {
            "$elemMatch": {
                "name": qp.parameterName,
                "value": get_value_float_or_str(qp.parameterValue),
            }
        },
        "properties"
        if qp.propertyName and not qp.propertyValue
        else None: {"$elemMatch": {"name": qp.propertyName}},
        "properties"
        if qp.propertyName and qp.propertyValue
        else None: {
            "$elemMatch": {
                "name": qp.propertyName,
                "value": get_value_float_or_str(qp.propertyValue),
            }
        },
        "provenance.createdAt"
        if qp.publication_dates
        else None: get_dates(qp.publication_dates)
        if qp.publication_dates
        else None,
        "material.elements"
        if qp.material_all_elements
        else None: {"$all": get_list_elements(qp.material_all_elements)},
        "material.elements"
        if qp.material_any_element
        else None: get_list_elements(qp.material_any_element),
    }
    del query[None]  # removes single None:None introduced from above dict definition
    # print(query)

    projection = {}
    if qp.fields:
        projection = {i: 1 for i in qp.fields.split(",")}
    # print(projection)
    coll = conn[database_name][ai4mat_collection_name]
    if len(projection) > 0:
        result_query = await coll.find(query, projection).to_list(None)
    else:
        result_query = await coll.find(query).to_list(None)
    response = []
    # {"_id": ObjectId("6333075e1fd43266d2a6196a")}
    for doc in result_query:
        # convert to dict and exclude none
        response.append(ProjectQueryResult(**doc).dict(exclude_none=True))
        # if "_id" in doc.keys():
        #     doc.pop("_id")
    return response


async def get_user_projects(
    conn: AsyncIOMotorClient, user_email: str, affiliation: str
) -> dict:
    coll = conn[database_name][ai4mat_collection_name]
    pipeline = get_user_projects_base_info(user_email, affiliation)
    result = await coll.aggregate(pipeline).to_list(None)
    return result


# https://medium.com/@madhuri.pednekar/handling-mongodb-objectid-in-python-fastapi-4dd1c7ad67cd
# https://www.tutorialsteacher.com/mongodb/update-arrays
# https://www.mongodb.com/docs/manual/reference/operator/update/positional-filtered/#mongodb-update-up.---identifier--

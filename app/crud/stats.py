from typing import List

from core.utils import get_value_float_or_str
from models.iemap import FileProject, Property, queryModel

from db.mongodb import AsyncIOMotorClient
from bson.objectid import ObjectId
from core.config import Config

from models.iemap import Project as IEMAPModel
from models.iemap import ProjectQueryResult
from crud.pipelines import (
    get_iemap_formulas_and_elements,
    get_proj_stats,
    get_proj_stats_by_user,
)

from dateutil.parser import parse

# retrieve DB name and collection name from config
database_name, ai4mat_collection_name, auth_collection = (
    Config.mongo_db,
    Config.mongo_coll,
    Config.mongo_coll_users,
)

# get statitics about all projects
async def project_stat(conn: AsyncIOMotorClient) -> dict:
    # get Motor Client
    coll = conn[database_name][ai4mat_collection_name]
    # execute aggregation pipeline
    pipeline = get_proj_stats()
    # result[0] to return a dictionary
    result = await coll.aggregate(pipeline).to_list(length=None)
    # get number of users by quering the auth collection
    coll_users = conn[database_name][auth_collection]
    num_users = await coll_users.count_documents({"is_verified": True})
    # add number of users to the result array
    result[0]["totalUsersRegistered"] = num_users
    return result[0]


# get statitics about a SPECIFIC user's projects
async def project_stat_user(conn: AsyncIOMotorClient, email: str) -> dict:
    # get Motor Client
    coll = conn[database_name][ai4mat_collection_name]
    # execute aggregation pipeline
    pipeline = get_proj_stats_by_user(email=email)
    # result[0] to return a dictionary
    result = await coll.aggregate(pipeline).to_list(length=None)
    return result[0]


# get distinct formulas and elements (with their count)
async def iemap_formulas_elements(conn: AsyncIOMotorClient) -> dict:
    # get Motor Client
    coll = conn[database_name][ai4mat_collection_name]
    # execute aggregation pipeline
    pipeline = get_iemap_formulas_and_elements()
    # result[0] to return a dictionary
    result_arr = await coll.aggregate(pipeline).to_list(length=None)
    number_of_formulas = len(result_arr[0]["formulas"])
    number_of_elements = len(result_arr[0]["unique_elements"])
    result: dict = result_arr[0]
    data = {
        **result,
        "n_formulas": number_of_formulas,
        "n_elements": number_of_elements,
    }
    return data

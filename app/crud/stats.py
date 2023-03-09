from typing import List

from core.utils import get_value_float_or_str
from models.iemap import FileProject, Property, queryModel

from db.mongodb import AsyncIOMotorClient
from bson.objectid import ObjectId
from core.config import Config

from models.iemap import Project as IEMAPModel
from models.iemap import ProjectQueryResult
from crud.pipelines import get_proj_stats, get_proj_stats_by_user

from dateutil.parser import parse

# retrieve DB name and collection name from config
database_name, ai4mat_collection_name = (Config.mongo_db, Config.mongo_coll)

# get statitics about all projects
async def project_stat(conn: AsyncIOMotorClient) -> dict:
    # get Motor Client
    coll = conn[database_name][ai4mat_collection_name]
    # execute aggregation pipeline
    pipeline = get_proj_stats()
    # result[0] to return a dictionary
    result = await coll.aggregate(pipeline).to_list(length=None)
    return result[0]

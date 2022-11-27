import logging
from bson.objectid import ObjectId as BsonObjectId
from fastapi import APIRouter, Depends, status

from fastapi.responses import JSONResponse
from db.mongodb import AsyncIOMotorClient, get_database

# NECESSARY TO HANDLE FASTAPI_USERS
from db.mongodb_utils import UserAuth
from models.users import fastapi_users
from crud.projects import get_user_projects
from models.iemap import userProjectsResponse
from core.config import Config
from typing import List

logger = logging.getLogger("ai4mat")
router = APIRouter()
upload_dir = Config.files_dir

# Get the current user (active or not)
current_user = fastapi_users.current_user(verified=True)

# http://0.0.0.0:8001/api/v1/user/projects/info
@router.get("/user/projects/info", tags=["users"], status_code=status.HTTP_200_OK)
async def user_project_info(
    db: AsyncIOMotorClient = Depends(get_database),
    # COMMENT user:...below TO REMOVE AUTHORIZATION ~~~~~~~~~~~~~~~
    # IF USER ACCOUNT IS NOT VERIFIED IT RETURNS FORBIDDEN ~~~~~~~~~~~~~~~~
    # Options defined in current_user RULE how authentication works, see below
    # https://fastapi-users.github.io/fastapi-users/10.1/usage/current-user/?h=verified#get-the-current-active-and-verified-user
    user: UserAuth = Depends(current_user),
) -> List[userProjectsResponse]:
    """Retrieve user's projects base info ()

    Args:
        db (AsyncIOMotorClient, optional): Motor client connection to MongoDB.
        Defaults to Depends(get_database).


    Returns:
        dict: {"inserted_id": ObjectID} where ObjectID is the document ID inserted in DB
            (use this ID as path parameter to add files to project)
    """

    # RETRIEVE USER DATA FROM JWT
    user, affiliation = user.email, user.affiliation
    # retrieve user projects base info
    docs = await get_user_projects(db, user, affiliation)

    return [userProjectsResponse(**d) for d in docs]

from typing import Dict
from fastapi import APIRouter, Depends, Response, status, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from db.mongodb_utils import UserAuth

# from models.users import (
#     current_active_user,
# )

# from core.jwt import get_current_user_authorizer
from core.auth import JWTBearer, signJWT  # , decodeJWT
from models.user import UserBase, User
from crud.stats import project_stat, project_stat_user, iemap_formulas_elements
from db.mongodb import AsyncIOMotorClient, get_database

# Use fastapi_users instance as Dependence Injection into routes
# to protect as show in
# https://fastapi-users.github.io/fastapi-users/10.1/usage/current-user/

from models.users import (
    fastapi_users,
)

router = APIRouter()

# Get the current user (active or not)¶
current_user = fastapi_users.current_user()


# http://0.0.0.0:8001/api/v1/stats
# GET STATS ABOUT ALL PROJECTS in DB
@router.get(
    "/stats",
    tags=["stats"],
    status_code=status.HTTP_200_OK,
    summary="General Statistics on IEMAP Project",
    description="This route gets general statistics on IEMAP project",
)
async def stats_project(
    db: AsyncIOMotorClient = Depends(get_database),
    response: Response = Response(status_code=status.HTTP_200_OK),
):

    # dictionary result aggreation pipeline
    result = await project_stat(db)
    if type(result) is dict:
        return {"data": result}

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Something went wrong!!",
    )


# http://0.0.0.0:8001/api/v1/stats_user/
# GET STATS ABOUT PROJECTS for the current logged in user
@router.get(
    "/stats_user",
    tags=["stats"],
    status_code=status.HTTP_200_OK,
    summary="Statistics on IEMAP User Project",
    description="This route gets projects statistics for the specified user",
)
async def stats_project(
    db: AsyncIOMotorClient = Depends(get_database),
    response: Response = Response(status_code=status.HTTP_200_OK),
    # COMMENT user:...below TO REMOVE AUTHORIZATION ~~~~~~~~~~~~~~~
    # IF USER ACCOUNT IS NOT VERIFIED IT RETURNS FORBIDDEN ~~~~~~~~~~~~~~~~
    # Options defined in current_user RULE how authentication works, see below
    # https://fastapi-users.github.io/fastapi-users/10.1/usage/current-user/?h=verified#get-the-current-active-and-verified-user
    user: UserAuth = Depends(current_user),
):

    # dictionary result aggreation pipeline
    result = await project_stat_user(db, user.id)
    # iemap_formulas_elements(db)
    if type(result) is dict:
        return {"data": result}
    # return a JSON response as
    #     {
    #     "data": {
    #         "total": 45, # total number of projects in DB
    #         "totalByUser": 42, # total number of projects for the current l user
    #         "totalByUserWithFile": 24, # total number of projects for the current user with at least one file
    #         "totalByUserCountFiles": 74 # total number of files for the current user
    #     }
    # }

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Something went wrong!!",
    )


# http://0.0.0.0:8001/api/v1/stats_iemap
# GET DISTICNT FORMULAS AND ELEMENTS in IEMAP DB (as whole)
# with their counts
@router.get(
    "/stats_iemap",
    tags=["stats"],
    status_code=status.HTTP_200_OK,
    summary="Distinc Materials and Elements ind IEMAP DB (with counts)",
    description="This route gets all distinct materials' formulas and elements in IEMAP DB (with counts)",
)
async def stats_project(
    db: AsyncIOMotorClient = Depends(get_database),
    response: Response = Response(status_code=status.HTTP_200_OK),
):

    # dictionary result aggreation pipeline
    result = await iemap_formulas_elements(db)
    if type(result) is dict:
        return {"data": result}
    # return a JSON response as
    #         {
    #     "data": {
    #         "formulas": [
    #             "C6H12",
    #             "GAZ2058",
    #             "Mn6Na12Ni6O24",
    #             "C6H12O6",
    #             "CONO2"
    #         ],
    #         "unique_elements": [
    #             "C",
    #             "H",
    #             "Mn",
    #             "N",
    #             "Na",
    #             "Ni",
    #             "O"
    #         ],
    #         "n_formulas": 5,
    #         "n_elements": 7
    #     }
    # }

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Something went wrong!!",
    )

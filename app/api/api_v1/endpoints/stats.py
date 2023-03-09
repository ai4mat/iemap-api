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
from crud.stats import project_stat
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

# UserAuth is the Beanie Model for storing user credentials
# @router.get(
#     "/health/on-premise-auth",
#     tags=["health"],
#     status_code=status.HTTP_200_OK,
#     summary="Check if the on-premise auth service is up and running",
#     description="Pass a JWT using Beared in Header or using an HTTPonly Cookie",
# )
# # IF NO TOKEN IS PROVIDED IN HEADER AS BEARER OR TOKEN NOT VALID
# # THEN RETURNS
# # {
# #     "detail": "Unauthorized"
# # }
# async def check_on_premise_auth(user: UserAuth = Depends(current_user)):
#     return {"message": f"{user.email} ({user.affiliation}) you are welcome!"}


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

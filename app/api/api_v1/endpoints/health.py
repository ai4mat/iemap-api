from fastapi import APIRouter, Depends, Response, status, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


# from core.jwt import get_current_user_authorizer
from core.auth import JWTBearer, signJWT, decodeJWT
from models.user import UserBase, User
from crud.health import checkDB
from db.mongodb import AsyncIOMotorClient, get_database

router = APIRouter()

# http://0.0.0.0:8001/api/v1/health
# CHECK DB CONNECTION
@router.get(
    "/health",
    tags=["health"],
    status_code=status.HTTP_200_OK,
    summary="Check DB connection",
    description="This route checks DB connection",
)
async def check_health(
    db: AsyncIOMotorClient = Depends(get_database),
    response: Response = Response(status_code=status.HTTP_200_OK),
):

    # dictionary Motor Client Info
    result = await checkDB(db)
    if type(result) is dict:
        return {
            "status": "Server's health is fine!",
        }

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Something went wrong!!",
    )


condition = True

# http://0.0.0.0:8001/api/v1/health/checkauth
# CHECK AUTHENTICATION by providing JWT in header as Bearer token
@router.get(
    "/health/checkauth",
    # dependencies=[Depends(JWTBearer())],
    tags=["JWT"],
    summary="Check JWT Authentication",
    description="This route checks JWT Authentication by passing a valid JWT in header as Bearer token",
)
async def check_auth(dep=Depends(JWTBearer())) -> dict:
    token, payload = dep
    # get current user from JWT paylaod using Request state
    # payload = request.state.payload

    return {"status": "You are authenticated!", "user": payload["user_id"]}


# http://0.0.0.0:8001/api/v1/health/jwt
# POST credentails to get JWT
@router.post(
    "/health/jwt",
    tags=["JWT"],
    status_code=status.HTTP_200_OK,
    summary="Get JWT",
    description="This route gets JWT if valid credentials are POSTed",
)
async def get_jwt(user: UserBase) -> User:
    if user.email == "ai4mat@enea.it":
        return signJWT(user.email)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": "Unauthorized user!!"},
    )


# https://github.com/tiangolo/fastapi/discussions/4161
# https://stackoverflow.com/questions/68827065/how-to-get-return-values-form-fastapi-global-dependencies

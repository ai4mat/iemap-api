from fastapi import APIRouter, Depends, Response, status, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


# from core.jwt import get_current_user_authorizer
from core.auth import JWTBearer, signJWT
from models.user import UserBase, User
from crud.health import checkDB
from db.mongodb import AsyncIOMotorClient, get_database

router = APIRouter()

# http://0.0.0.0:8001/api/v1/health
@router.get("/health", tags=["health"], status_code=status.HTTP_200_OK)
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


# http://0.0.0.0:8001/api/v1/health/checkauth
@router.get(
    "/health/checkauth",
    dependencies=[Depends(JWTBearer())],
    tags=["JWT"],
)
async def check_auth(request: Request) -> dict:
    # get current user from JWT paylaod using Request state
    payload = request.state.payload
    return {"status": "You are authenticated!", "user": payload["user_id"]}


# http://0.0.0.0:8001/api/v1/health/jwt
@router.post("/health/jwt", tags=["JWT"], status_code=status.HTTP_200_OK)
async def get_jwt(user: UserBase) -> User:
    if user.email == "ai4mat@enea.it":
        return signJWT(user.email)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": "Unauthorized user!!"},
    )


# https://stackoverflow.com/questions/68827065/how-to-get-return-values-form-fastapi-global-dependencies

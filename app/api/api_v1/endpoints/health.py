from fastapi import APIRouter, Depends, Response, status
from starlette.exceptions import HTTPException


from core.jwt import get_current_user_authorizer
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

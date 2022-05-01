from typing import Optional

from fastapi import APIRouter, Depends, Path
from starlette.exceptions import HTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from core.jwt import get_current_user_authorizer
from crud.health import checkDB
from db.mongodb import AsyncIOMotorClient, get_database


router = APIRouter()

# http://0.0.0.0:8001/api/v1/health
@router.get("/health", tags=["health"])
async def check_health(
    db: AsyncIOMotorClient = Depends(get_database),
):
    status = await checkDB(db)
    if type(status) is dict:
        return {
            "status": "Server's health is fine!",
        }
    else:
        return {
            "status": "Something went wrong!",
        }

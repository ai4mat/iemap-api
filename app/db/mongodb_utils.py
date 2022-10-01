from zlib import DEF_BUF_SIZE
from beanie import init_beanie
from beanie import PydanticObjectId

from fastapi_users.db import BeanieBaseUser, BeanieUserDatabase

from datetime import datetime
import logging

logger = logging.getLogger("ai4mat")
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import Config
from db.mongodb import db
from typing import Optional, Annotated
from pydantic import Field

# originally User (this is the name of the collection in MongoDB)
class UserAuth(BeanieBaseUser[PydanticObjectId]):
    # ADD ANY ADDITIONAL FIELD AS DEFINED in app/models/schemas.py
    affiliation: Optional[str] = None
    createdAt: Optional[datetime] = datetime.now().utcnow()
    last_login: Optional[datetime] = None
    # pass


async def get_user_db():
    yield BeanieUserDatabase(UserAuth)


async def connect_to_mongo():
    logger.info("Connecting to MongoDB..")

    db.client = AsyncIOMotorClient(
        str(Config.mongo_uri), maxPoolSize=Config.max_conn, minPoolSize=Config.min_conn
    )
    logger.info(
        f"Connection succesfully established at {datetime.now().strftime('%Y-%B-%d %H:%M:%S')}."
    )
    if Config.enable_onpremise_auth:
        db_users = db.client[Config.mongo_db]
        await init_beanie(
            database=db_users,
            document_models=[
                UserAuth,
            ],
        )
        logger.info(
            f"Succesfully initialize On-Premise AUTH using collection User and db {db_users.name}."
        )


async def close_mongo_connection():
    logger.info("Closing connection to MongoDB...")
    db.client.close()
    logger.info("Connection succesfully closed！")

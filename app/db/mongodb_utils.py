from beanie import init_beanie
from beanie import PydanticObjectId

from fastapi_users.db import BeanieBaseUser, BeanieUserDatabase

from datetime import datetime
import logging

logger = logging.getLogger("ai4mat")
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import Config
from db.mongodb import db


class User(BeanieBaseUser[PydanticObjectId]):
    pass


async def get_user_db():
    yield BeanieUserDatabase(User)


async def connect_to_mongo():
    logger.info("Connecting to MongoDB..")

    db.client = AsyncIOMotorClient(
        str(Config.mongo_uri), maxPoolSize=Config.max_conn, minPoolSize=Config.min_conn
    )
    logger.info(
        f"Connection succesfully established at {datetime.now().strftime('%Y-%B-%d %H:%M:%S')}."
    )
    if Config.enable_onpremise_auth:
        collection_users = "user_db_jwt"
        await init_beanie(
            database=db.client[collection_users],
            document_models=[
                User,
            ],
        )
        logger.info(
            f"Succesfully initialize On-Premise AUTH using collection {collection_users}."
        )


async def close_mongo_connection():
    logger.info("Closing connection to MongoDB...")
    db.client.close()
    logger.info("Connection succesfully closed！")

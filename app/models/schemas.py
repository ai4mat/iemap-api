from token import OP
from beanie import PydanticObjectId
from fastapi_users import schemas
from typing import Optional, Annotated
from datetime import datetime
from pydantic import Field, validator


# ANY ADDITIONAL FIELD TO BE PERSISTED IN THE UserAuth COLLECTION in MongoDB
# NEEDS TO BE DEFINED HERE ASS WELL AS IN THE USERAUTH MODEL in mongodb_utils.py
class UserRead(schemas.BaseUser[PydanticObjectId]):
    # added to support affiliation info
    affiliation: Optional[str] = None
    # added to support user activity tracking
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    # pass


class UserCreate(schemas.BaseUserCreate):
    # added to support affiliation info
    affiliation: Optional[str] = None
    # added to support user activity tracking
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    # pass


class UserUpdate(schemas.BaseUserUpdate):
    # added to support affiliation info
    affiliation: Optional[str] = None
    # added to support user activity tracking
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    # pass

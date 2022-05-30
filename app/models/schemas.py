from beanie import PydanticObjectId
from fastapi_users import schemas
from typing import Optional


# ANY ADDITIONAL FIELD TO BE PERSISTED IN THE UserAuth COLLECTION in MongoDB
# NEEDS TO BE DEFINED HERE ASS WELL AS IN THE USERAUTH MODEL in mongodb_utils.py
class UserRead(schemas.BaseUser[PydanticObjectId]):
    # added to support affiliation info
    affiliation: Optional[str] = None
    pass


class UserCreate(schemas.BaseUserCreate):
    # added to support affiliation info
    affiliation: Optional[str] = None
    pass


class UserUpdate(schemas.BaseUserUpdate):
    # added to support affiliation info
    affiliation: Optional[str] = None
    pass

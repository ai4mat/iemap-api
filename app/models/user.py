from typing import Optional

from pydantic import EmailStr, AnyUrl, Field


from models.dbmodel import DBModelMixin
from models.rwmodel import RWModel
from core.security import generate_salt, get_password_hash, verify_password


class UserBase(RWModel):
    fullname: str = Field(...)
    email: EmailStr
    affiliation: Optional[str] = ""


class UserInDB(DBModelMixin, UserBase):
    salt: str = ""
    hashed_password: str = ""

    def check_password(self, password: str):
        return verify_password(self.salt + password, self.hashed_password)

    def change_password(self, password: str):
        self.salt = generate_salt()
        self.hashed_password = get_password_hash(self.salt + password)


class User(UserBase):
    token: str


class UserInResponse(RWModel):
    user: User


class UserInLogin(RWModel):
    email: EmailStr
    password: str


class UserInCreate(UserInLogin):
    username: str


class UserInUpdate(RWModel):

    email: Optional[EmailStr] = None
    password: Optional[str] = None

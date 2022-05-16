from typing import Optional

from pydantic import AnyUrl

from models.rwmodel import RWModel


class Profile(RWModel):
    username: str
    bio: Optional[str] = ""
    image: Optional[AnyUrl] = None
    following: bool = False


class ProfileInResponse(RWModel):
    profile: Profile

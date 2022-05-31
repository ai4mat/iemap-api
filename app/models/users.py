from typing import Optional

from beanie import PydanticObjectId
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
    CookieTransport,
)
from fastapi_users.db import BeanieUserDatabase, ObjectIDIDMixin

from db.mongodb_utils import UserAuth, get_user_db

SECRET = "2cc29249a2602c779e08c0b9cac8ecf8694159decbc0698b"


class UserManager(ObjectIDIDMixin, BaseUserManager[UserAuth, PydanticObjectId]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(
        self, user: UserAuth, request: Optional[Request] = None
    ):
        # await user.update({"$set": {"is_active": False}})
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: UserAuth, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: UserAuth, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db: BeanieUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
cookie_transport = CookieTransport(cookie_httponly=True, cookie_secure=False)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

auth_backend_cookie = AuthenticationBackend(
    name="cookie", transport=cookie_transport, get_strategy=get_jwt_strategy
)

fastapi_users = FastAPIUsers[UserAuth, PydanticObjectId](
    get_user_manager, [auth_backend, auth_backend_cookie]
)

current_active_user = fastapi_users.current_user(active=True)

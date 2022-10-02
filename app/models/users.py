from typing import Optional
from beanie import PydanticObjectId
from fastapi import Depends, Request
from starlette.datastructures import URL
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
    CookieTransport,
)
from fastapi_users.db import BeanieUserDatabase, ObjectIDIDMixin
from db.mongodb_utils import UserAuth, get_user_db
from core.smtp_email import readVerifyMailTemplate, send_mail_async
from core.config import Config

from fastapi_users.manager import BaseUserManager
from fastapi_users import exceptions
from fastapi_users.jwt import generate_jwt
from pathlib import Path


SECRET = Config.secrete_on_premise_auth


class UserManager(ObjectIDIDMixin, BaseUserManager[UserAuth, PydanticObjectId]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(
        self,
        user: UserAuth,
        request: Optional[Request] = None,
    ):
        # CHECK IF USER IS ACTIVE AND NOT ALREADY VERIFIED
        # THEN GENERATE TEMPORARY TOKEN AND EMIT on_after_request_verify
        if not user.is_active:
            raise exceptions.UserInactive()
        if user.is_verified:
            raise exceptions.UserAlreadyVerified()

        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "aud": self.verification_token_audience,
        }
        token = generate_jwt(
            token_data,
            self.verification_token_secret,
            self.verification_token_lifetime_seconds,
        )

        # retrieve requested url to use for link to embend in email sent to user
        strBaseRequest = str(request.url).split("auth/register")[0]
        strEndpointVerifyByEmail = "auth/verify-email/"
        strLinkVerifyEmail = strBaseRequest + strEndpointVerifyByEmail + token

        # send email to user to verify his/her email
        # eventually add other email to list to notify an administrator
        pathVerifyEmail = (
            "./app/templates/mail_template.html"
            if not "app" in str(Path.cwd()).split("/")
            else "./templates/mail_template.html"
        )
        textMail = await readVerifyMailTemplate(pathVerifyEmail, strLinkVerifyEmail)
        await send_mail_async(
            [user.email], "Finish registration to IEMAP REST API service", textMail
        )

    async def on_after_forgot_password(
        self, user: UserAuth, token: str, request: Optional[Request] = None
    ):

        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: UserAuth, token: str, request: Optional[Request] = None
    ):
        # retrieve requested url to use for link to embend in email sent to user
        strBaseRequest = str(request.url).split("auth/request-verify-token")[0]
        strEndpointVerifyByEmail = "auth/verify-email/"
        strLinkVerifyEmail = strBaseRequest + strEndpointVerifyByEmail + token
        pathVerifyEmail = (
            "./app/templates/mail_template.html"
            if not "app" in str(Path.cwd()).split("/")
            else "./templates/mail_template.html"
        )
        textMail = await readVerifyMailTemplate(pathVerifyEmail, strLinkVerifyEmail)
        await send_mail_async(
            [user.email], "Finish registration to IEMAP REST API service", textMail
        )


async def get_user_manager(user_db: BeanieUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


# TRASPORT TO USE FOR AUTHENTICATION
# bearer is for token in header as Bearer (useful for REST API service)
# cookie is for token in cookie (useful for web app)
# https://fastapi-users.github.io/fastapi-users/10.0/configuration/authentication/transports/cookie/
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
cookie_transport = CookieTransport(cookie_httponly=True, cookie_secure=False)

# DEFINE JWT STRATEGY
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=Config.jwt_lifetime)


# DEFINE TWO AUTHENTICATION BACKEND
# using same strategy for both backend
# one use JWT in header, the other use JWT in cookie (HTTPONLY)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

auth_backend_cookie = AuthenticationBackend(
    name="cookie", transport=cookie_transport, get_strategy=get_jwt_strategy
)

# ADD AUTHENTICATION BACKEND TO FASTAPI USERS
fastapi_users = FastAPIUsers[UserAuth, PydanticObjectId](
    get_user_manager, [auth_backend, auth_backend_cookie]
)

current_active_user = fastapi_users.current_user(active=True)

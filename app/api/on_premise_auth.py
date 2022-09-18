from typing import Type
from webbrowser import get
from fastapi import APIRouter, Depends, status
import fastapi_users
from db.mongodb_utils import UserAuth
from models.schemas import UserCreate, UserRead, UserUpdate

# ADDED
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi_users.manager import BaseUserManager, UserManagerDependency
from fastapi_users import exceptions, models, schemas
from pydantic import EmailStr
from fastapi_users import schemas
from fastapi_users.router.common import ErrorCode, ErrorModel


# import FASTAPIUsers authentication backends
from models.users import (
    auth_backend,
    auth_backend_cookie,
    # current_active_user,
    fastapi_users,
)

router = APIRouter()

# A route for EACH auth_backend is required ******************

# route for JWT backend in Bearer
# register two POST routes: /login and /logout
# http://localhost:8000/auth/jwt/login
# http://localhost:8000/auth/jwt/logout
# requires to form fields: username and password
router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)

# route for JWT backend in Cookie
# register two POST routes: /login and /logout
# http://localhost:8000/auth/jwt/login
# http://localhost:8000/auth/jwt/logout
# requires to form fields: username and password
router.include_router(
    fastapi_users.get_auth_router(auth_backend_cookie),
    prefix="/auth/cookie",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate, requires_verification=True),
    prefix="/users",
    tags=["users"],
)


# https://github.com/fastapi-users/fastapi-users/discussions/800

# CREATE ADDITIONAL CUSTOM ROUTE TO VERIFY USER BY EMAIL
# /verify-email/{token}
# Works as follow:
# 1. decode token
# 2. retrieve user_id and email from token
# 3. if not already verified set _is_verified to True
def get_verify_email_router(
    get_user_manager: UserManagerDependency[models.UP, models.ID],
    user_schema: Type[schemas.U],
):
    router = APIRouter()

    @router.get(
        "/verify-email/{token}",
        # response_model=user_schema,
        name="verify:verify",
        responses={
            status.HTTP_400_BAD_REQUEST: {
                "model": ErrorModel,
                "content": {
                    "application/json": {
                        "examples": {
                            ErrorCode.VERIFY_USER_BAD_TOKEN: {
                                "summary": "Bad token, not existing user or"
                                "not the e-mail currently set for the user.",
                                "value": {"detail": ErrorCode.VERIFY_USER_BAD_TOKEN},
                            },
                            ErrorCode.VERIFY_USER_ALREADY_VERIFIED: {
                                "summary": "The user is already verified.",
                                "value": {
                                    "detail": ErrorCode.VERIFY_USER_ALREADY_VERIFIED
                                },
                            },
                        }
                    }
                },
            }
        },
    )
    async def verifyEmail(
        request: Request,
        token: str,
        user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
    ):
        try:
            # return UserAuth
            user = await user_manager.verify(token, request)
            return {"verified": user.is_verified}
        except (exceptions.InvalidVerifyToken, exceptions.UserNotExists):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.VERIFY_USER_BAD_TOKEN,
            )
        except exceptions.UserAlreadyVerified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.VERIFY_USER_ALREADY_VERIFIED,
            )

    return router


# ADDED CUSTOM
# GET ENDPOINT TO VERIFY USER
router.include_router(
    get_verify_email_router(fastapi_users.get_user_manager, Type[schemas.U]),
    prefix="/auth",
    tags=["auth"],
)

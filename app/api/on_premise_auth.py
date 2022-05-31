from fastapi import APIRouter, Depends
import fastapi_users
from db.mongodb_utils import UserAuth
from models.schemas import UserCreate, UserRead, UserUpdate
from models.users import (
    auth_backend,
    auth_backend_cookie,
    # current_active_user,
    fastapi_users,
)

router = APIRouter()

# A route for EACH auth_backend is required ******************

# route for JWT backend in Bearer
router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
# route for JWT backend in Cookie
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

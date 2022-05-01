from fastapi import APIRouter

from .endpoints.authentication import router as auth_router
from .endpoints.health import router as health_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(health_router)

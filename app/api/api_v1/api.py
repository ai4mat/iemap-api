from fastapi import APIRouter

from api.api_v1.endpoints.authentication import router as auth_router
from api.api_v1.endpoints.health import router as health_router
from api.api_v1.endpoints.fileshandling import router as files_router
from api.api_v1.endpoints.project import router as projects_router
from api.api_v1.endpoints.user_projects import router as user_proj_info_router
from api.api_v1.endpoints.stats import router as stats

router = APIRouter()
router.include_router(auth_router)
router.include_router(health_router)
router.include_router(files_router)
router.include_router(projects_router)
router.include_router(user_proj_info_router)
router.include_router(stats)

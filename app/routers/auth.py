from fastapi import APIRouter

from app.auth.users import auth_backend, fastapi_users
from app.schemas.business import BusinessCreate, BusinessRead, BusinessUpdate

router = APIRouter()

router.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/jwt")
router.include_router(fastapi_users.get_register_router(BusinessRead, BusinessCreate))
router.include_router(
    fastapi_users.get_users_router(BusinessRead, BusinessUpdate), prefix="/users"
)

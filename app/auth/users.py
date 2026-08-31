import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session
from app.models.business import Business


async def get_user_db(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    yield SQLAlchemyUserDatabase(session, Business)


class BusinessManager(UUIDIDMixin, BaseUserManager[Business, uuid.UUID]):
    reset_password_token_secret = get_settings().jwt_secret
    verification_token_secret = get_settings().jwt_secret


async def get_business_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
) -> AsyncGenerator[BusinessManager, None]:
    yield BusinessManager(user_db)


bearer_transport = BearerTransport(tokenUrl="api/v1/auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=get_settings().jwt_secret, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[Business, uuid.UUID](get_business_manager, [auth_backend])

current_active_business = fastapi_users.current_user(active=True)

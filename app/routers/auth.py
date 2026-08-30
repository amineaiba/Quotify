from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.refresh import create_refresh_token, revoke_refresh_token, rotate_refresh_token
from app.auth.users import BusinessManager, fastapi_users, get_business_manager, get_jwt_strategy
from app.core.exceptions import InvalidRefreshToken
from app.db.session import get_session
from app.schemas.auth import RefreshRequest, TokenPair
from app.schemas.business import BusinessCreate, BusinessRead, BusinessUpdate

router = APIRouter()

router.include_router(fastapi_users.get_register_router(BusinessRead, BusinessCreate))
router.include_router(
    fastapi_users.get_users_router(BusinessRead, BusinessUpdate), prefix="/users"
)


@router.post("/jwt/login", response_model=TokenPair)
async def login(
    credentials: OAuth2PasswordRequestForm = Depends(),
    business_manager: BusinessManager = Depends(get_business_manager),
    session: AsyncSession = Depends(get_session),
) -> TokenPair:
    business = await business_manager.authenticate(credentials)
    if business is None or not business.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="LOGIN_BAD_CREDENTIALS"
        )

    access_token = await get_jwt_strategy().write_token(business)
    refresh_token = await create_refresh_token(session, business.id)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/jwt/refresh", response_model=TokenPair)
async def refresh(
    body: RefreshRequest, session: AsyncSession = Depends(get_session)
) -> TokenPair:
    try:
        business, new_refresh_token = await rotate_refresh_token(session, body.refresh_token)
    except InvalidRefreshToken as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_REFRESH_TOKEN"
        ) from err

    access_token = await get_jwt_strategy().write_token(business)
    return TokenPair(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/jwt/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, session: AsyncSession = Depends(get_session)) -> None:
    await revoke_refresh_token(session, body.refresh_token)

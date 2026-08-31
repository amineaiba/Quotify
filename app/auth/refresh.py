import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidRefreshToken
from app.models.business import Business
from app.models.refresh_token import RefreshToken

REFRESH_TOKEN_TTL = timedelta(days=30)


def _hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def create_refresh_token(session: AsyncSession, business_id: uuid.UUID) -> str:
    raw_token = secrets.token_urlsafe(32)
    session.add(
        RefreshToken(
            business_id=business_id,
            token_hash=_hash(raw_token),
            expires_at=datetime.now(UTC) + REFRESH_TOKEN_TTL,
        )
    )
    await session.commit()
    return raw_token


async def rotate_refresh_token(session: AsyncSession, raw_token: str) -> tuple[Business, str]:
    token = (
        await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == _hash(raw_token))
        )
    ).scalar_one_or_none()

    if token is None or token.revoked_at is not None or token.expires_at < datetime.now(UTC):
        raise InvalidRefreshToken()

    business = await session.get(Business, token.business_id)
    token.revoked_at = datetime.now(UTC)
    new_raw_token = await create_refresh_token(session, token.business_id)

    return business, new_raw_token


async def revoke_refresh_token(session: AsyncSession, raw_token: str) -> None:
    token = (
        await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == _hash(raw_token))
        )
    ).scalar_one_or_none()

    if token is not None:
        token.revoked_at = datetime.now(UTC)
        await session.commit()

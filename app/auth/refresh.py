import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
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
    # Single atomic UPDATE, not a SELECT then a later write: two concurrent
    # calls with the same token could otherwise both read revoked_at as NULL
    # before either commits. The WHERE clause makes "still unused" and "mark
    # used" one step, so at most one concurrent caller ever gets a row back.
    business_id = (
        await session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == _hash(raw_token),
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at >= datetime.now(UTC),
            )
            .values(revoked_at=datetime.now(UTC))
            .returning(RefreshToken.business_id)
        )
    ).scalar_one_or_none()

    if business_id is None:
        raise InvalidRefreshToken()

    business = await session.get(Business, business_id)
    new_raw_token = await create_refresh_token(session, business_id)

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

import pytest
from sqlalchemy import select

from app.auth.refresh import create_refresh_token, revoke_refresh_token, rotate_refresh_token
from app.core.exceptions import InvalidRefreshToken
from app.models.business import Business
from app.models.refresh_token import RefreshToken


async def _make_business(session) -> Business:
    business = Business(
        name="Atelier Print",
        email="owner@atelier.dz",
        hashed_password="hashed",
        is_active=True,
        is_verified=False,
        is_superuser=False,
    )
    session.add(business)
    await session.commit()
    return business


async def test_create_refresh_token_stores_hash_not_raw(session):
    business = await _make_business(session)

    raw_token = await create_refresh_token(session, business.id)

    row = (await session.execute(select(RefreshToken))).scalar_one()
    assert row.token_hash != raw_token
    assert row.business_id == business.id
    assert row.revoked_at is None


async def test_rotate_refresh_token_returns_new_token_and_revokes_old(session):
    business = await _make_business(session)
    raw_token = await create_refresh_token(session, business.id)

    rotated_business, new_raw_token = await rotate_refresh_token(session, raw_token)

    assert rotated_business.id == business.id
    assert new_raw_token != raw_token

    with pytest.raises(InvalidRefreshToken):
        await rotate_refresh_token(session, raw_token)  # old token is now revoked


async def test_rotate_refresh_token_rejects_unknown_token(session):
    with pytest.raises(InvalidRefreshToken):
        await rotate_refresh_token(session, "not-a-real-token")


async def test_revoke_refresh_token_marks_revoked(session):
    business = await _make_business(session)
    raw_token = await create_refresh_token(session, business.id)

    await revoke_refresh_token(session, raw_token)

    with pytest.raises(InvalidRefreshToken):
        await rotate_refresh_token(session, raw_token)


async def test_revoke_refresh_token_on_unknown_token_is_a_no_op(session):
    await revoke_refresh_token(session, "not-a-real-token")  # must not raise

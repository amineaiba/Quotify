import pytest
from sqlalchemy.exc import IntegrityError

from app.models.business import Business, Client


async def test_create_business_and_client(session):
    business = Business(
        name="Atelier Print",
        email="owner@atelierprint.dz",
        hashed_password="hashed",
        api_key="key-123",
    )
    client = Client(phone_number="+213555000000", name="Yacine")
    business.clients.append(client)
    session.add(business)
    await session.commit()

    assert client.id is not None
    assert client.business_id == business.id
    assert business.clients == [client]


async def test_business_email_must_be_unique(session):
    session.add(Business(name="A", email="dup@x.com", hashed_password="h", api_key="k1"))
    await session.commit()

    session.add(Business(name="B", email="dup@x.com", hashed_password="h", api_key="k2"))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_client_phone_unique_per_business(session):
    business = Business(name="A", email="a@x.com", hashed_password="h", api_key="k1")
    session.add(business)
    await session.flush()

    session.add(Client(business_id=business.id, phone_number="+213555000000"))
    await session.commit()

    session.add(Client(business_id=business.id, phone_number="+213555000000"))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_client_phone_can_repeat_across_businesses(session):
    business_a = Business(name="A", email="a2@x.com", hashed_password="h", api_key="k2")
    business_b = Business(name="B", email="b2@x.com", hashed_password="h", api_key="k3")
    session.add_all([business_a, business_b])
    await session.flush()

    session.add(Client(business_id=business_a.id, phone_number="+213555000000"))
    session.add(Client(business_id=business_b.id, phone_number="+213555000000"))
    await session.commit()  # must not raise

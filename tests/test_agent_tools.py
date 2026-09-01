import uuid

from app.agent.tools import dispatch
from tests.conftest import FLYER_ID, seed_flyer


async def test_dispatch_calc_price_success(session):
    await seed_flyer(session)

    result = await dispatch(session, "calc_price", {"item_id": str(FLYER_ID), "quantity": 500})

    assert result["total"] == 9500
    assert result["unit_price"] == 19


async def test_dispatch_calc_price_below_minimum_returns_error(session):
    await seed_flyer(session)

    result = await dispatch(session, "calc_price", {"item_id": str(FLYER_ID), "quantity": 50})

    assert result == {"error": "BelowMinimumQuantity", "min_qty": 100}


async def test_dispatch_calc_price_unknown_item_returns_error(session):
    unknown_id = str(uuid.uuid4())

    result = await dispatch(session, "calc_price", {"item_id": unknown_id, "quantity": 500})

    assert result == {"error": "ItemNotFound", "item_id": unknown_id}


async def test_dispatch_unknown_tool_returns_error(session):
    result = await dispatch(session, "not_a_real_tool", {})

    assert result == {"error": "UnknownTool", "name": "not_a_real_tool"}

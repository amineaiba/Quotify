from app.agent.tools import dispatch
from tests.conftest import seed_flyer


async def test_dispatch_calc_price_success(session):
    await seed_flyer(session)

    result = await dispatch(session, "calc_price", {"item_id": 1, "quantity": 500})

    assert result["total"] == 9500
    assert result["unit_price"] == 19


async def test_dispatch_calc_price_below_minimum_returns_error(session):
    await seed_flyer(session)

    result = await dispatch(session, "calc_price", {"item_id": 1, "quantity": 50})

    assert result == {"error": "BelowMinimumQuantity", "min_qty": 100}


async def test_dispatch_calc_price_unknown_item_returns_error(session):
    result = await dispatch(session, "calc_price", {"item_id": 999, "quantity": 500})

    assert result == {"error": "ItemNotFound", "item_id": 999}


async def test_dispatch_unknown_tool_returns_error(session):
    result = await dispatch(session, "not_a_real_tool", {})

    assert result == {"error": "UnknownTool", "name": "not_a_real_tool"}

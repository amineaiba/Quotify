import uuid

from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BelowMinimumQuantity,
    ItemNotFound,
    NoConfirmableQuote,
    OrderAlreadyExists,
)
from app.schemas.catalog import CatalogItemOut
from app.services.catalog import search_catalog
from app.services.orders import confirm_order
from app.services.pricing import calc_price

#describing the tools :
TOOLS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="search_catalog",
            description="Find catalog items closest in meaning to a client's message.",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "k": {"type": "integer"},
                },
                "required": ["message"],
            },
        ),
        types.FunctionDeclaration(
            name="calc_price",
            description="Price a specific catalog item at a given quantity.",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "format": "uuid"},
                    "quantity": {"type": "integer"},
                },
                "required": ["item_id", "quantity"],
            },
        ),
        types.FunctionDeclaration(
            name="confirm_order",
            description=(
                "Create an order from the conversation's most recently sent quote. "
                "Call this only when the client has clearly confirmed they want to go "
                "ahead with that quote — not for a new request."
            ),
            parameters_json_schema={"type": "object", "properties": {}},
        ),
    ]
)


async def dispatch(
    session: AsyncSession,
    name: str,
    args: dict,
    conversation_id: uuid.UUID | None = None,
    business_id: uuid.UUID | None = None,
) -> dict:
    try:
        if name == "search_catalog":
            items = await search_catalog(session, business_id, **args)
            return {
                "items": [
                    CatalogItemOut.model_validate(i).model_dump(mode="json") for i in items
                ]
            }
        if name == "calc_price":
            # item_id arrives as a string — the LLM only speaks JSON.
            try:
                item_id = uuid.UUID(args["item_id"])
            except ValueError:
                return {"error": "ItemNotFound", "item_id": args["item_id"]}
            return (
                await calc_price(session, business_id, item_id, args["quantity"])
            ).model_dump(mode="json")
        if name == "confirm_order":
            if conversation_id is None:
                return {"error": "NoConfirmableQuote"}
            order = await confirm_order(session, conversation_id)
            return {"order_id": str(order.id), "status": order.status.value}
        return {"error": "UnknownTool", "name": name}
    except ItemNotFound as e:
        return {"error": "ItemNotFound", "item_id": str(e.item_id)}
    except BelowMinimumQuantity as e:
        return {"error": "BelowMinimumQuantity", "min_qty": e.min_qty}
    except NoConfirmableQuote:
        return {"error": "NoConfirmableQuote"}
    except OrderAlreadyExists:
        return {"error": "AlreadyConfirmed"}

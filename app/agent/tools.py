import uuid

from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BelowMinimumQuantity, ItemNotFound
from app.schemas.catalog import CatalogItemOut
from app.services.catalog import search_catalog
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
    ]
)


async def dispatch(session: AsyncSession, name: str, args: dict) -> dict:
    try:
        if name == "search_catalog":
            items = await search_catalog(session, **args)
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
            return (await calc_price(session, item_id, args["quantity"])).model_dump(
                mode="json"
            )
        return {"error": "UnknownTool", "name": name}
    except ItemNotFound as e:
        return {"error": "ItemNotFound", "item_id": str(e.item_id)}
    except BelowMinimumQuantity as e:
        return {"error": "BelowMinimumQuantity", "min_qty": e.min_qty}

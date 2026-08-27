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
                    "item_id": {"type": "integer"},
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
                "items": [CatalogItemOut.model_validate(i).model_dump() for i in items]
            }
        if name == "calc_price":
            return (await calc_price(session, **args)).model_dump()
        return {"error": "UnknownTool", "name": name}
    except (ItemNotFound, BelowMinimumQuantity) as e:
        return {"error": type(e).__name__, **vars(e)}

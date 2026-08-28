from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.routers.agent import router as agent_router
from app.routers.catalog import router as catalog_router

app = FastAPI(title="Quotify")

app.include_router(catalog_router, prefix="/api/v1/catalog", tags=["catalog"])
app.include_router(agent_router, prefix="/api/v1/agent", tags=["agent"])


@app.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict:
    try:
        await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    return {"status": "ok", "db": db_status}

import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session
from app.routers.agent import router as agent_router
from app.routers.auth import router as auth_router
from app.routers.catalog import router as catalog_router
from app.routers.conversations import router as conversations_router
from app.routers.webhooks.whatsapp import router as whatsapp_webhook_router

logging.basicConfig(
    level=get_settings().log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logging.getLogger("app").setLevel(logging.DEBUG)

app = FastAPI(title="Quotify")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog_router, prefix="/api/v1/catalog", tags=["catalog"])
app.include_router(conversations_router, prefix="/api/v1/conversations", tags=["conversations"])
app.include_router(agent_router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(whatsapp_webhook_router, prefix="/api/v1/webhooks/whatsapp", tags=["webhooks"])


@app.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict:
    try:
        await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    return {"status": "ok", "db": db_status}

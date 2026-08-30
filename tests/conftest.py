from dataclasses import dataclass, field

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_session
from app.llm.embeddings import EMBED_DIM
from app.main import app
from app.models.business import Business, Client  # noqa: F401 — registers tables for create_all
from app.models.catalog import CatalogItem, CatalogItemTier
from app.models.conversation import (  # noqa: F401 — registers tables for create_all
    Channel,
    Conversation,
    Message,
    Sender,
)
from app.models.refresh_token import RefreshToken  # noqa: F401 — registers table for create_all

# Kept as URL objects, not str(url) — that masks the password with "***".
_app_url = make_url(get_settings().database_url)
ADMIN_DATABASE_URL = _app_url.set(database="postgres")
TEST_DATABASE_URL = _app_url.set(database="quotify_test")


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _ensure_test_database() -> None:
    admin_engine = create_async_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        exists = await conn.exec_driver_sql(
            "SELECT 1 FROM pg_database WHERE datname = 'quotify_test'"
        )
        if not exists.first():
            await conn.exec_driver_sql("CREATE DATABASE quotify_test")
    await admin_engine.dispose()


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        # Extensions are per-database — quotify_test needs its own.
        await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncClient:
    app.dependency_overrides[get_session] = lambda: session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# --- test doubles for the Gemini client -------------------------------
# run_agent only ever touches response.candidates[0].content,
# response.function_calls, and response.text — these fakes provide
# exactly that, nothing more.


@dataclass
class FakeCall:
    name: str
    args: dict


@dataclass
class FakeCandidate:
    content: object = None


@dataclass
class FakeResponse:
    function_calls: list
    text: str = ""
    candidates: list = field(default_factory=lambda: [FakeCandidate()])


class FakeModels:
    def __init__(self, responses):
        self._responses = iter(responses)

    def generate_content(self, **kwargs):
        return next(self._responses)


class FakeClient:
    def __init__(self, responses):
        self.models = FakeModels(responses)


async def seed_flyer(session: AsyncSession) -> None:
    session.add(
        CatalogItem(
            id=1,
            name="Flyer A5 quadri recto-verso",
            unit="flyer",
            tiers=[
                CatalogItemTier(min_qty=100, unit_price=30),
                CatalogItemTier(min_qty=500, unit_price=19),
            ],
            embedding=[0.0] * EMBED_DIM,
        )
    )
    await session.commit()

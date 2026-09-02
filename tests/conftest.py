import uuid
from dataclasses import dataclass, field

import pytest_asyncio
from google.genai import types
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


# --- test doubles for the LangGraph agent (app/agent/graph.py) ------------
# call_model only reads response.candidates[0].content, and run_tools/
# has_tool_calls read function calls out of content.parts (see
# app.agent.graph._function_calls) — so these doubles build real
# google.genai Content/Part objects, unlike FakeResponse above which
# leaves content as None and exposes function_calls as a flat list
# instead (matching the hand-written loop.py's reads).


def graph_tool_call_content(name: str, args: dict) -> types.Content:
    return types.Content(
        role="model",
        parts=[types.Part(function_call=types.FunctionCall(name=name, args=args))],
    )


def graph_text_content(text: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part(text=text)])


class _GraphFakeCandidate:
    def __init__(self, content: types.Content) -> None:
        self.content = content


class _GraphFakeResponse:
    def __init__(self, content: types.Content) -> None:
        self.candidates = [_GraphFakeCandidate(content)]


class _GraphFakeModels:
    def __init__(self, responses: list[types.Content]) -> None:
        self._responses = iter(responses)

    def generate_content(self, **kwargs):
        return _GraphFakeResponse(next(self._responses))


class GraphFakeClient:
    def __init__(self, responses: list[types.Content]) -> None:
        self.models = _GraphFakeModels(responses)


async def make_business(session: AsyncSession, **overrides) -> Business:
    defaults = {
        "name": "Seed Business",
        "email": f"seed-{uuid.uuid4()}@example.com",
        "hashed_password": "hashed",
        "api_key": f"key-{uuid.uuid4()}",
    }
    defaults.update(overrides)
    business = Business(**defaults)
    session.add(business)
    await session.flush()
    return business


async def register_and_login(client: AsyncClient, email: str, name: str = "Test Co") -> str:
    """Registers a business and returns a bearer access token for it."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "s3cret-pw", "name": name},
    )
    login = await client.post(
        "/api/v1/auth/jwt/login", data={"username": email, "password": "s3cret-pw"}
    )
    return login.json()["access_token"]


FLYER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


async def seed_flyer(session: AsyncSession) -> None:
    business = await make_business(session)
    session.add(
        CatalogItem(
            id=FLYER_ID,
            business_id=business.id,
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

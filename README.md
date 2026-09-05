# Quotify

Reads a customer's message and drafts a price quote
for the owner to approve.

For small businesses that write quotes by hand and
lose clients by answering too late.

An AI agent does the work: understands the message,
asks back for what's missing, searches the catalog,
calculates the price.

## Stack

Python, FastAPI, PostgreSQL + pgvector, SQLAlchemy + Alembic, Docker, Gemini

## Run it

```
cp .env.example .env        # fill in GEMINI_API_KEY
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api pytest
```

API is at `http://localhost:8000`, health check at `/health`.

Check retrieval quality: `docker compose exec api python evals/recall_at_k.py`

## Status

Catalog search is live: `POST /api/v1/catalog/search`. Tier pricing is live:
`app/services/pricing.py::calc_price` (no endpoint — the agent will call it
directly, same as `search_catalog`). The agent loop is live:
`app/agent/loop.py::run_agent` — calls both tools via Gemini function
calling, no endpoint yet.

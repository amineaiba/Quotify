# Quotify

AI quoting agent for small print/workshop businesses. Reads a client message
(mixed French/Darja), asks for what's missing, looks up the shop's catalog,
calculates a price, drafts a quote. The owner approves before anything sends.

## How we work

- **Agent loop, tools, retrieval, prompts — build together.** Explain the
  approach, build it in small pieces, let Amine make the calls. Pair
  programming, not autocomplete.
- **Everything else — just build it.** Docker, config, migrations, linting,
  tests, dependencies. No need to check in first.
- Unsure which one something is? Ask.

## Build it right

This is a professional portfolio project. Best practice first, every time —
including not adding a layer nothing needs yet. A repository class over one
query is noise, not professionalism. Build the right thing, at the right size.

Comments and docstrings: light, one line, only when the code doesn't already
say it. Match `services/catalog.py` — not a tutorial in the source file.

## Decisions already made

- **Stack**: FastAPI + PostgreSQL + pgvector, in Docker.
- **API**: Gemini (`google-genai`), free tier — not the Claude API. Function
  calling uses Gemini's shape, not Claude's `tool_use`.
- **Agent loop**: hand-written `while` loop first. A LangGraph rebuild comes
  later as an explicit comparison, not a replacement.
- **Data**: portfolio project — fake catalog, fake client messages only.
  Never put a real client's data through the Gemini key (free tier: Google
  can use it).

These aren't open questions — check with Amine before proposing a different
stack or approach.

## Repo layout

Layer folders under `app/`: `models/`, `schemas/`, `services/`, `routers/`.
One file per feature, same name in every layer — `models/catalog.py`,
`schemas/catalog.py`, `services/catalog.py`, `routers/catalog.py`. Imports
flow one way: `routers` → `services` → `models`. A service never imports a
router.

`app/llm/` is a package, not a layer — it's the only place a Gemini client
gets created. `app/agent/` will be the same when it arrives: `loop.py`,
`tools.py`, `prompts/` — not spread across the layer folders, because a
prompt is not a layer.

`evals/` sits next to `tests/`, not inside it. A test passes or fails. An
eval returns a score (`recall@k`). Evals cost real API calls, so they run by
hand, not in CI.

## Right now

Skeleton done, first task verified. Catalog is in Postgres via pgvector,
served at `POST /api/v1/catalog/search`. `evals/recall_at_k.py` against the
live endpoint: `recall@1 = 0.94` (16/17), `recall@3 = 1.00` (17/17).

`calc_price` is done — `app/services/pricing.py`, `app/schemas/pricing.py`.
Tier lookup, Pydantic-validated `PriceBreakdown` output, no endpoint (the
agent will call it directly, like `search_catalog`). Below-minimum quantity
raises `BelowMinimumQuantity` instead of inventing a price.

Next: `app/agent/` — the hand-written `while` loop, calling `search_catalog`
and `calc_price` as Gemini function-call tools.

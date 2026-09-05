# Architecture

Current-state summary. Distilled from `docs/specs/` after each
phase ships — this file describes what's built, not what's planned (see
`ROADMAP.md`) and not why a past call was made (see `docs/adr/`).

## Stack

FastAPI + PostgreSQL + pgvector. Gemini (`google-genai`, free tier) for
embeddings and function calling. SQLAlchemy + Alembic for the DB layer.
LangGraph for the agent loop.

Locally, only `db` runs in Docker (`pgvector/pgvector:pg17`, host port
`5433`); the API runs with `uv run uvicorn app.main:app --reload` for fast
reload. A full `docker compose up` (API included, `.env.docker`) is for a
prod-like run.

## Repo layout

Layer folders under `app/`: `models/`, `schemas/`, `services/`, `routers/`.
One file per feature, same name in every layer — e.g. `models/catalog.py`,
`schemas/catalog.py`, `services/catalog.py`, `routers/catalog.py`. Imports
flow one way: `routers` → `services` → `models`.

`app/llm/` is a package, not a layer — the only place a Gemini client gets
created. `app/agent/` is the same: `graph.py` (active, LangGraph),
`tools.py`, `prompts/`. `loop.py` is the frozen hand-written version — see
`docs/adr/0001-hand-written-loop-before-langgraph.md`.
`app/auth/` too: `users.py` (fastapi-users manager, JWT backend),
`refresh.py` (refresh token create/rotate/revoke).

`app/meta/` (`signature.py`, HMAC verification) and `app/whatsapp/`
(`schemas.py`, `client.py`) are one package per external integration, same
idea as `app/llm/` — Meta/WhatsApp's payload shapes stay out of
`app/schemas/`, which is only for our own API's request/response models.
`routers/webhooks/whatsapp.py` gets its own subpackage so Messenger/
Instagram get their own files and paths later without conflict.

`evals/` sits next to `tests/`, not inside it — evals score retrieval
quality (`recall@k`) and cost real API calls, so they run by hand.

## Data model

```mermaid
erDiagram
    BUSINESS ||--o{ CLIENT : has
    BUSINESS ||--o{ REFRESH_TOKEN : has
    BUSINESS ||--o{ CONVERSATION : has
    BUSINESS ||--o{ CATALOG_ITEM : has
    CLIENT ||--o{ CONVERSATION : has
    CONVERSATION ||--o{ MESSAGE : has
    CATALOG_ITEM ||--o{ CATALOG_ITEM_TIER : has

    BUSINESS {
        uuid id PK
        string name
        string email
        string hashed_password
        string api_key
        string whatsapp_phone_number_id "unique, nullable"
        bool is_active
        bool is_superuser
        bool is_verified
        datetime created_at
    }
    CLIENT {
        uuid id PK
        uuid business_id FK
        string phone_number
        string name
        datetime created_at
    }
    REFRESH_TOKEN {
        uuid id PK
        uuid business_id FK
        string token_hash
        datetime expires_at
        datetime revoked_at
        datetime created_at
    }
    CONVERSATION {
        uuid id PK
        uuid business_id FK
        uuid client_id FK
        string channel
        datetime created_at
    }
    MESSAGE {
        uuid id PK
        uuid conversation_id FK
        string sender
        string content
        string whatsapp_message_id "unique, nullable — dedups retried webhooks"
        datetime created_at
    }
    CATALOG_ITEM {
        uuid id PK
        uuid business_id FK
        string name
        string unit
        vector embedding
    }
    CATALOG_ITEM_TIER {
        uuid id PK
        uuid catalog_item_id FK
        int min_qty
        int unit_price
    }
```

`(business_id, client_id, channel)` is unique on `CONVERSATION` — one
conversation per client per channel; no separate "closed" state yet. Full
target model (including `Quote`, not built yet) is in
`docs/specs/2026-08-28-data-model-design.md`.

## Request flow (current)

```mermaid
sequenceDiagram
    participant C as Client (curl/Postman)
    participant R as routers/agent.py
    participant L as agent/graph.py (run_agent)
    participant G as Gemini
    participant T as agent/tools.py (dispatch)
    participant DB as Postgres

    C->>R: POST /api/v1/agent/messages {message}
    R->>L: run_agent(session, message)
    loop until no function calls or MAX_TURNS
        L->>G: generate_content(history)
        G-->>L: text or function_call(s)
        L->>T: dispatch(name, args)
        T->>DB: search_catalog / calc_price
        DB-->>T: rows / tiers
        T-->>L: result (or caught domain error)
    end
    L-->>R: AgentReply(status, message, lines)
    R-->>C: 200 AgentReply / 503 on MAX_TURNS
```

Single message in, single reply out — no conversation persistence yet.
`ItemNotFound` and `BelowMinimumQuantity` are caught inside `dispatch` and
fed back to Gemini as text instead of crashing the loop.

## Request flow — WhatsApp webhook

```mermaid
sequenceDiagram
    participant Meta
    participant R as routers/webhooks/whatsapp.py
    participant DB as Postgres
    participant BG as background task
    participant L as agent/graph.py (run_agent)
    participant W as whatsapp/client.py

    Meta->>R: POST /api/v1/webhooks/whatsapp
    R->>R: verify_signature (app/meta/signature.py)
    R->>DB: find Business by whatsapp_phone_number_id
    R->>DB: dedup by whatsapp_message_id
    R->>DB: get_or_create client/conversation, save inbound message (commit)
    R-->>Meta: 200
    R->>BG: schedule reply (own DB session)
    BG->>L: run_agent(session, message)
    L-->>BG: AgentReply
    BG->>DB: save agent reply
    BG->>W: send_message(...)
```

The agent's reply happens after the `200` is returned — Meta doesn't wait
for it. The background task opens its own DB session
(`get_session_factory`, overridable in tests); the request's session is
gone by the time it runs. A failure in the background task is logged, not
retried — see `docs/specs/2026-09-02-whatsapp-webhook-design.md` for the
accepted gap and why (Hardening phase closes it).

## Decisions already made

- **Agent loop**: hand-written `while` loop first (done, frozen). A
  LangGraph rebuild replaces it as the active implementation — see
  `docs/adr/0001-hand-written-loop-before-langgraph.md`.
- **Data**: portfolio project — fake catalog, fake client messages only.
  Never put a real client's data through the Gemini key (free tier: Google
  can use it).

These aren't open questions — check with Amine before proposing a
different stack or approach.

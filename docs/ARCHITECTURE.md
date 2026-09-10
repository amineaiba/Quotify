# Architecture

Current-state summary. Distilled from `docs/specs/` after each
phase ships — this file describes what's built, not what's planned (see
`ROADMAP.md`) and not why a hard-to-reverse decision was made (see
`docs/adr/`).

## Stack

FastAPI + PostgreSQL + pgvector. Gemini (`google-genai`, free tier) for
embeddings and function calling. SQLAlchemy + Alembic for the DB layer.
LangGraph for the agent loop. Redis for the guardrails rate limiter —
fails open (rate limiting stops, replies still send) if unreachable.

Locally, `db` and `redis` run in Docker (`pgvector/pgvector:pg17` on host
port `5433`, `redis:7-alpine` on host port `6380`); the API runs with
`uv run uvicorn app.main:app --reload` for fast reload. A full
`docker compose up` (API included, `.env.docker`) is for a prod-like run.

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
    CONVERSATION ||--o{ QUOTE : has
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
    QUOTE {
        uuid id PK
        uuid conversation_id FK
        string draft_message
        string final_message "nullable — set if staff edits before approving (phase 5)"
        int confidence "nullable — agent's self-reported 0-100 score"
        string status "pending | approved | rejected | auto_sent"
        string hold_reason "nullable — low_confidence | rate_limited"
        json lines "nullable — price breakdown, if any"
        datetime created_at
        datetime reviewed_at "nullable — set in phase 5"
    }
```

`(business_id, client_id, channel)` is unique on `CONVERSATION` — one
conversation per client per channel; no separate "closed" state yet. One
`QUOTE` row is written per agent reply, whether it auto-sent or was held.

## Request flow (current)

```mermaid
sequenceDiagram
    participant C as Client (curl/Postman)
    participant R as routers/agent.py
    participant L as agent/graph.py (run_agent)
    participant G as Gemini
    participant T as agent/tools.py (dispatch)
    participant DB as Postgres

    C->>R: POST /api/v1/agent/messages {message, conversation_id?}
    alt conversation_id given
        R->>DB: save inbound message, load full conversation history
    end
    R->>L: run_agent(session, history)
    loop until no function calls or MAX_TURNS
        L->>G: generate_content(history)
        G-->>L: text or function_call(s)
        L->>T: dispatch(name, args)
        T->>DB: search_catalog / calc_price
        DB-->>T: rows / tiers
        T-->>L: result (or caught domain error)
    end
    L-->>R: AgentReply(status, message, lines)
    alt conversation_id given
        R->>DB: save agent reply
    end
    R-->>C: 200 AgentReply / 404 unknown conversation / 503 on MAX_TURNS
```

`run_agent` takes a ready-made history (`list[types.Content]`), not a bare
string — it doesn't know or care whether that history came from one
throwaway message or a saved conversation. Building that history is the
caller's job: `messages_to_history` (`app/agent/graph.py`) converts saved
`Message` rows into Gemini's format (`client`/`staff` → `"user"`,
`agent` → `"model"`). Without a `conversation_id`, the endpoint behaves as
before — one message in, one reply out, nothing saved.
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
    participant RL as core/rate_limit.py
    participant Redis
    participant W as whatsapp/client.py

    Meta->>R: POST /api/v1/webhooks/whatsapp
    R->>R: verify_signature (app/meta/signature.py)
    R->>DB: find Business by whatsapp_phone_number_id
    R->>DB: dedup by whatsapp_message_id
    R->>DB: get_or_create client/conversation, save inbound message (commit)
    R-->>Meta: 200
    R->>BG: schedule reply (own DB session)
    BG->>DB: load full conversation history
    BG->>L: run_agent(session, history)
    L-->>BG: AgentReply (message, confidence)
    BG->>RL: is_rate_limited(conversation_id)
    RL->>Redis: INCR / EXPIRE
    alt Redis unreachable
        Redis-->>RL: RedisError
        RL-->>BG: False (fails open — see ADR 0002)
    else
        Redis-->>RL: count
        RL-->>BG: bool
    end
    BG->>DB: save_quote (status: auto_sent, or pending + hold_reason)
    alt auto_sent (rate limit ok, confidence ≥ threshold)
        BG->>DB: save agent reply as Message
        BG->>W: send_message(...)
    else pending (rate limited, or low/missing confidence)
        Note over BG: nothing sent — held for staff review (phase 5)
    end
```

The agent's reply happens after the `200` is returned — Meta doesn't wait
for it. The background task opens its own DB session
(`get_session_factory`, overridable in tests); the request's session is
gone by the time it runs. A failure in the background task is logged, not
retried — see `docs/specs/2026-09-02-whatsapp-webhook-design.md` for the
accepted gap and why (Hardening phase closes it).

The rate limit and confidence check (guardrails) are new. Every reply
writes a `Quote` row, whether it sent or was held; there's no
staff-facing way to review a held one yet (phase 5, once the dashboard
exists).

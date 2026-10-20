# Quotify

An AI agent that answers a client's WhatsApp message and drafts a price quote.

Small businesses write quotes by hand and lose clients by answering too late.
Quotify reads the message (French and Darja mixed), asks for what is missing,
finds the item in the catalog, calculates the price, and replies.

A reply is sent on its own only when the agent is confident. If not, it is held
in a review queue and the owner approves or rejects it.

## What it does

- **Agent**: Gemini function calling in a LangGraph loop. Tools: `search_catalog`,
  `calc_price`, `confirm_order`. Handles several items in one message.
- **Catalog**: items with price tiers by quantity. Search uses pgvector embeddings.
- **Guardrails**: the agent reports a confidence score. A low score or a
  rate-limited conversation holds the reply for review. Redis rate limit fails open.
- **WhatsApp**: Meta Cloud API webhook. Signature check, duplicate protection,
  reply in the background, retry on failed sends.
- **Orders**: when a client confirms a quote, it becomes an order.
- **Dashboard**: React app with catalog, inbox, review queue and quote history.

## Stack

Python, FastAPI, PostgreSQL + pgvector, SQLAlchemy 2.0 (async) + Alembic, Redis,
LangGraph, Gemini. Frontend: React, TypeScript, Vite, Tailwind.

## Run it locally

Postgres (with pgvector) and Redis run in Docker. The API and the frontend run on your machine.

```
cp .env.example .env
```

Fill in `GEMINI_API_KEY` and `JWT_SECRET` in `.env`.
Change `DATABASE_URL` to the local port:
`postgresql+asyncpg://quotify:quotify@localhost:5433/quotify`.

```
docker compose up -d db redis
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Frontend, in another terminal:

```
cd frontend
npm install
npm run dev
```

API: `http://localhost:8000` (docs at `/docs`). Dashboard: `http://localhost:5173`.

Sign up in the dashboard, then add catalog items. To test the agent without WhatsApp,
log in and call `POST /api/v1/agent/messages` with your access token.

### Connect WhatsApp

There is no self-serve flow yet. Set the business's number by hand:

```sql
UPDATE businesses SET whatsapp_phone_number_id = '<phone_number_id>' WHERE email = '<email>';
```

Then point the Meta webhook to `/api/v1/webhooks/whatsapp` and fill
`META_APP_SECRET`, `META_VERIFY_TOKEN` and `WHATSAPP_ACCESS_TOKEN` in `.env`.

## Tests and evals

```
uv run pytest
uv run ruff check .
```

Evals call the real Gemini API, so they run by hand:

```
uv run python -m evals.confirm_order_eval
uv run python -m evals.multi_item_eval
uv run python evals/recall_at_k.py --token <access token>
```

## Data rule

Use fake catalog data and fake client messages only. The Gemini key is on the free tier,
and Google can use that data.

## Known gaps

Left out on purpose. This is a portfolio project.

- **Connect WhatsApp from the dashboard** (Meta Embedded Signup). Needs Meta business verification.
- **Email verification and password reset.** Needs real email setup.
- **Background job queue.** A failed reply is retried on send and then logged. It is not queued.
- **Approving a quote** saves it as approved before sending. If the send still fails after retries, the endpoint returns an error and the client gets no message.
- **`confirm_order` always uses the latest quote.** A client who confirms an older quote after a new one is not handled.
- **No cancel flow** for orders, although the `cancelled` status exists.
- **Full conversation history goes to Gemini.** No cap yet.
- **No images, voice notes, FAQ answers, client memory or follow-up nudges.** See `docs/ROADMAP.md`.

## Docs

- `docs/ARCHITECTURE.md`: stack, data model, request flow
- `docs/ROADMAP.md`: what is built and what is next
- `docs/adr/`: why hard-to-reverse decisions were made
- `docs/specs/` and `docs/plans/`: design docs and plans for each phase

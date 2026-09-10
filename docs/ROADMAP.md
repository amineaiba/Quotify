# Roadmap

Two tracks, worked separately but both built together with Amine — see
`CLAUDE.md`. Each phase
gets its own brainstorming session before it's built; see
`docs/specs/` for the design docs that come out of that.

## AI track

- [x] Catalog search via pgvector (`search_catalog`)
- [x] Pricing (`calc_price`, tiers, `BelowMinimumQuantity`)
- [x] Hand-written agent loop (`run_agent`) + endpoint
- [x] LangGraph rebuild of the agent loop — replaces the hand-written
      version as the active implementation (that version stays in the repo,
      frozen, not extended further)
- [x] Multi-turn conversation state for the agent (depends on the software
      track's conversations table)

## Software track

Ordered by dependency — each phase only needs what came before it.

1. [x] **Foundation** — business/tenant model, auth (dashboard
   login/refresh/logout), conversations + messages tables. Webhook
   `api_key` column exists on `Business`; the verification dependency
   itself lands in Channel integration, where it's first used.
2. [x] **Catalog management** — CRUD endpoints for items/tiers, replacing
   `scripts/seed_catalog.py`; wires in embed-on-write
3. [x] **Channel integration** — Meta/WhatsApp webhook: verify signature →
   save inbound message → call agent → send reply back. `Business.
   whatsapp_phone_number_id` is wired by hand (SQL) for now — no self-serve
   way for a business to connect their own WhatsApp number yet, see phase 5.
4. [x] **Guardrails** — the engine only, no staff-facing UI/API yet (that's
   phase 5, once the dashboard exists to use it). Verified with automated
   tests. Sub-phases, in order:
   1. [x] `Quote` model — one row per agent reply (draft/final message,
      confidence, status, hold_reason, price lines, timestamps)
   2. [x] Confidence check — agent self-reports a confidence score;
      below threshold → held instead of auto-sent. Plan for a second
      LLM-judge pass as a later addition, not built now.
   3. [x] Rate limiting — Redis, per-conversation window (new local dev
      service, `docker-compose.yml`); fails open (limiting stops, replies
      still send) if Redis is unreachable — see ADR
   4. [x] Gate `_reply_to_message` — rate limit then confidence check
      before save+send; always writes a `Quote` row either way
5. [ ] **Frontend dashboard** — React (Vite + TS + Tailwind), `frontend/`
   folder, npm, runs locally not in Docker. Sub-phases, in order:
   1. [ ] Scaffold — Vite/React/TS/Tailwind, API client, routing skeleton,
      CORS added to `app/main.py`
   2. [ ] Landing page — static, no backend dependency
   3. [ ] Auth — login/signup wired to real endpoints
   4. [ ] Catalog — table + add/edit/delete, wired to real CRUD endpoints
   5. [ ] Conversations/inbox + thread view, wired to real data (no pricing-
      reasoning panel or PDF download yet — not built on the backend)
   6. [ ] Review endpoints (backend) — `GET /quotes`, `approve`, `reject`.
      Blocked on `Quote` model (Guardrails phase)
   7. [ ] Review queue + quote history screen — wired to the endpoints
      above
   8. [ ] **"Connect WhatsApp" via Meta's Embedded Signup** (business owner
      logs into their own Facebook Business account, picks their number,
      Meta hands us `phone_number_id` + token automatically — replaces
      today's manual DB update)
6. [ ] **Hardening** — background jobs/retries for webhook delivery and
   failed sends, logging, error tracking, basic metrics, email
   verification + password reset (needs real email infra — skipped while
   signups are fake data only)

Update this file's checkboxes as phases ship. Add new phases as they come
up; don't pre-plan past what's reasonably foreseeable.

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
- [ ] Multi-turn conversation state for the agent (depends on the software
      track's conversations table)

## Software track

Ordered by dependency — each phase only needs what came before it.

1. [x] **Foundation** — business/tenant model, auth (dashboard
   login/refresh/logout), conversations + messages tables. Webhook
   `api_key` column exists on `Business`; the verification dependency
   itself lands in Channel integration, where it's first used.
2. [x] **Catalog management** — CRUD endpoints for items/tiers, replacing
   `scripts/seed_catalog.py`; wires in embed-on-write
3. [ ] **Channel integration** — Meta/WhatsApp webhook: verify signature →
   save inbound message → call agent → send reply back
4. [ ] **Guardrails** — confidence checks, hold-for-review queue, rate
   limits in front of auto-send
5. [ ] **Frontend dashboard** — conversations view, catalog management UI,
   quote history
6. [ ] **Hardening** — background jobs/retries for webhook delivery and
   failed sends, logging, error tracking, basic metrics, email
   verification + password reset (needs real email infra — skipped while
   signups are fake data only)

Update this file's checkboxes as phases ship. Add new phases as they come
up; don't pre-plan past what's reasonably foreseeable.

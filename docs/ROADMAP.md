# Roadmap

Two tracks, worked separately by time of day (AI in the morning, software
later) but both built together with Amine — see `CLAUDE.md`. Each phase
gets its own brainstorming session before it's built; see
`docs/specs/` for the design docs that come out of that.

## AI track

- [x] Catalog search via pgvector (`search_catalog`)
- [x] Pricing (`calc_price`, tiers, `BelowMinimumQuantity`)
- [x] Hand-written agent loop (`run_agent`) + endpoint
- [ ] LangGraph rebuild of the agent loop — explicit comparison to the
      hand-written version, not a replacement of it
- [ ] Multi-turn conversation state for the agent (depends on the software
      track's conversations table)

## Software track

Ordered by dependency — each phase only needs what came before it.

1. [ ] **Foundation** — business/tenant model, auth (dashboard login +
   webhook API keys), conversations + messages tables
2. [ ] **Catalog management** — CRUD endpoints for items/tiers, replacing
   `scripts/seed_catalog.py`; wires in embed-on-write
3. [ ] **Channel integration** — Meta/WhatsApp webhook: verify signature →
   save inbound message → call agent → send reply back
4. [ ] **Guardrails** — confidence checks, hold-for-review queue, rate
   limits in front of auto-send
5. [ ] **Frontend dashboard** — conversations view, catalog management UI,
   quote history
6. [ ] **Hardening** — background jobs/retries for webhook delivery and
   failed sends, logging, error tracking, basic metrics

Update this file's checkboxes as phases ship. Add new phases as they come
up; don't pre-plan past what's reasonably foreseeable.

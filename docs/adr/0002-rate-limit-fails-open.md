# 0002. Rate limiter fails open

## Context

Guardrails adds a per-conversation rate limit (Redis `INCR`/`EXPIRE`) in
front of auto-send. Redis is new local infrastructure — a service that can
be down or unreachable, unlike Postgres which is already a hard dependency
for everything.

## Decision

If Redis is unreachable, `is_rate_limited` returns `False` — rate limiting
just stops working for that check, and replies keep sending. The error is
logged as a warning, never raised.

Rate limiting is a safety net, not the core feature. The core feature
(the agent replying to clients) must not be able to break because a
secondary safety net's backing store had a hiccup.

## Consequences

- A prolonged Redis outage means no rate-limit protection until it's back.
  Acceptable at this project's traffic level (see `CLAUDE.md` — fake data,
  portfolio project).
- If Redis becomes load-bearing for something else later (e.g. sessions,
  caching), this tradeoff needs revisiting for that use case separately —
  it does not automatically apply there.

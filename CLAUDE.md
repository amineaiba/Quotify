# Quotify

AI quoting agent for small businesses. Reads a client message (mixed
French/Darja), asks for what's missing, looks up the business's catalog,
calculates a price, drafts a quote. Replies send automatically — needs
automated guardrails.

## How we work

- **Feature work — build together.** Agent loop, retrieval, prompts, CRUD,
  auth, webhooks, frontend — all of it. Explain the approach, build it in
  small pieces, let Amine make the calls. Pair programming, not autocomplete.
- **Routine chores — just build it.** Docker, config, migrations, linting,
  dependencies, boilerplate test setup. No need to check in first.
- Unsure which one something is? Ask.
- **Never commit, ever, unless Amine explicitly confirms in that exact
  moment.** Approving a plan is not approval to commit. Finishing a task is
  not approval to commit. A plan document saying "commit" as one of its
  steps is not approval to commit. Ask, every single time, no exceptions.

## Build it right

This is a professional portfolio project. Best practice first, every time —
including not adding a layer nothing needs yet. A repository class over one
query is noise, not professionalism. Build the right thing, at the right size.

Comments and docstrings: light, one line, only when the code doesn't already
say it. Match `services/catalog.py` — not a tutorial in the source file.

## Local dev

Only the `db` service runs in Docker (`pgvector/pgvector:pg17`, host port
`5433`). The API runs locally with `uv run uvicorn`, not in Docker — faster
reload, no image rebuild per change.

```
docker compose up -d db
uv run uvicorn app.main:app --reload
```

Two env files: `.env` (local — app reads this by default) and `.env.docker`
(used only by `docker-compose.yml`, for a full `docker compose up` when
someone needs the whole stack containerized, e.g. prod-like testing).

## Decisions already made

Never put a real client's data through the Gemini key — free tier, Google
can use it. Portfolio project: fake catalog, fake client messages only.

Everything else — stack, why the agent loop is hand-written before
LangGraph, why any other irreversible call was made — lives in
`docs/ARCHITECTURE.md` and `docs/adr/`. These aren't open questions; check
with Amine before proposing a different stack or approach.

## Repo layout

See `docs/ARCHITECTURE.md` for the current layer structure and where each
kind of code lives.

## Where things are

- `docs/ROADMAP.md` — what's built, what's next, both tracks (AI + software)
- `docs/ARCHITECTURE.md` — current stack, repo layout, data model, request
  flow
- `docs/adr/` — why a hard-to-reverse decision was made, one file each
- `docs/specs/` and `docs/plans/` — the design docs and implementation
  plans that came out of each brainstorming session

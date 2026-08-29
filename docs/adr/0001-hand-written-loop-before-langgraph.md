# 0001. Hand-written agent loop before LangGraph

## Context

The agent needs a loop that calls Gemini, dispatches function calls
(`search_catalog`, `calc_price`), and stops when Gemini has no more tool
calls. LangGraph is the eventual target for this project, but the loop's
mechanics should work and stay debuggable on their own, before any
framework abstraction sits on top of them.

## Decision

Build the agent loop by hand first (`app/agent/loop.py::run_agent`, a plain
`while`/`for` loop with a hard `MAX_TURNS` cap), to learn the mechanics
without a framework in the way. That step is done.

The LangGraph rebuild **replaces** it as the active implementation — all
new agent work (multi-turn state, future tools) goes into the LangGraph
version, not the hand-written one.

The hand-written version isn't deleted: it stays in the repo, frozen and
tested.

## Consequences

- No conversation/graph state management yet — multi-turn memory lands in
  the LangGraph version, not retrofitted onto the hand-written loop (see
  `ROADMAP.md`).
- The hand-written version keeps its existing tests passing but gets no
  new features — it's frozen, not actively maintained.
- Once the LangGraph version exists, it's what the API endpoint calls.
- Adding LangGraph is a new phase, not a fix to this one.

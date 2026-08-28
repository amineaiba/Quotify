# 0001. Hand-written agent loop before LangGraph

## Context

The agent needs a loop that calls Gemini, dispatches function calls
(`search_catalog`, `calc_price`), and stops when Gemini has no more tool
calls. LangGraph is the eventual target for this project (portfolio value:
show the "before" and "after"), but reaching for it first would mean
learning the framework and the agent-loop mechanics at the same time.

## Decision

Build the agent loop by hand first (`app/agent/loop.py::run_agent`, a plain
`while`/`for` loop with a hard `MAX_TURNS` cap). Rebuild it in LangGraph
later as an explicit comparison, not a replacement — both versions stay
comparable in the portfolio.

## Consequences

- No conversation/graph state management yet — multi-turn memory is
  deferred to the LangGraph rebuild (see `ROADMAP.md`).
- The hand-written version must stay working and tested; it's not throwaway
  code, it's half of the comparison.
- Adding LangGraph is a new phase, not a fix to this one.

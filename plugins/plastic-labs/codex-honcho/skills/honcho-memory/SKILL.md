---
name: honcho-memory
description: Persistent cross-session memory via Honcho — recall what you know about the user before working, and save durable insights after.
license: MIT
---

# Honcho memory

You have a persistent memory of this user that survives across sessions, backed by Honcho. The codex-honcho hooks already inject relevant context at the start of each turn, and they record the conversation automatically. This skill is for the times you should reach for memory *actively*.

## When to pull memory

Before non-trivial work, query memory instead of guessing:

- The task touches the user's preferences, conventions, or past decisions
- You're about to make an assumption you could instead verify ("which package manager?", "how is auth done here?")
- The user references something from "before" or "last time"

Use the Honcho MCP tools:

- `search` — semantic lookup over past messages
- `get_peer_context` / `get_representation` — the current model of the user
- `chat` — ask a natural-language question about the user ("what's their testing style?")

## When to save memory

After you learn something durable, persist it with `create_conclusions`:

- A decision with rationale ("chose SQLite over Postgres — embedded, zero-setup")
- A stable preference ("prefers small, focused PRs")
- A non-obvious gotcha or root cause worth remembering
- A convention specific to this codebase

Keep each conclusion to one concise statement with the *why*. Review with `list_conclusions` before adding near-duplicates.

## When not to bother

Skip memory for throwaway or purely mechanical tasks — running a build, answering a general knowledge question, trivial edits. Don't narrate that you checked memory; just use it.

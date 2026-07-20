---
name: agent-deck-session
description: Use at session start in a deck-bound workspace, or when the user asks for the deck status line / which deck is active.
---

# Agent Deck session opener

Once per conversation (or after bind changes):

1. `get_decks`
2. `bind_workspace` with the workspace root and a `deckId` — if `.agent-deck/use.json` exists, use its `deckId`
3. `get_session_binding`
4. Print **exactly one** line from `display_summary` (e.g. `◆ dev · 2 MCP · 0 keys · 1 playbooks`)

Do not repeat the status line every turn unless the user asks or the bind changes.

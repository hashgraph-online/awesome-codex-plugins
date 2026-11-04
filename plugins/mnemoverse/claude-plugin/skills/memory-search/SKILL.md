---
name: memory-search
description: "Searches long-term Mnemoverse memory before answering, so earlier decisions, preferences and project setup are used instead of asked again, then rates which recalled memories helped. Use when the answer may depend on an earlier session or another tool, when the user says \"like last time\", \"do you remember\", or \"check memory\", or before choosing a library, pattern or convention in a project touched before."
---

# Search memory before answering

## Check first

Look for the tools `memory_read` and `memory_feedback`. If they are missing, memory is not connected: say so in one sentence and use the bundled `setup` skill if it is installed, otherwise https://mnemoverse.com/docs/api/install-by-host. Do not guess what memory would have said.

## When to search

Search before answering when the answer could depend on something said in an earlier session or in another connected tool: a decision, a preference, a convention, a person, how the project is set up. General world knowledge does not need a search.

## How to search

1. Call `memory_read` with the user's own words plus the project or repository name.
2. If nothing useful comes back, try one broader query. Then stop and say what was searched, rather than looping.
3. For "what changed lately" questions, use the `memory-catch-up` skill. `order_by: "recency"` only puts the matches of this query newest first, which suits "the latest decision about X".
4. For a shared room (beta), pass the room's address as `domain`. Rooms are separate stores, and a search without that address never covers them.

## How to answer with what came back

- Say what each memory states and, when it is recorded, where it came from and when. Do not present a recalled memory as your own knowledge.
- If two memories disagree, show both with their dates and let the user decide. Do not quietly pick one.
- If a memory looks wrong or out of date, say so. It is corrected by saving a fresh statement with the `memory-save` skill, not by editing the old one.

## Rate what helped

After the answer, call `memory_feedback` with the ids of the memories that were used: outcome `1` if a memory helped, `-1` if it misled, a value between for partly. Tell it a recalled memory helped or misled, and it re-ranks what comes back next; nothing is erased by a low rating. For memories read from a shared room (beta), pass the room's address as `domain`. If `memory_feedback` has no `domain` parameter, or the user is a read-only member of the room, skip rating the room's memories.

Rate only memories that were actually used or actually misleading. Skip the rest.

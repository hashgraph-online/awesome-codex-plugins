---
name: memory-save
description: "Saves a durable decision, preference, correction or lesson to long-term Mnemoverse memory as one self-contained fact, so later sessions and other connected tools can recall it. Use when the user says \"save this to memory\", \"note that we decided\", or \"that was wrong, it is actually\", or when a session settles something worth keeping. Never stores secrets."
---

# Save to memory

## Check first

Look for the tools `memory_write` and `memory_stats`. If they are missing, memory is not connected: say so in one sentence and use the bundled `setup` skill if it is installed, otherwise https://mnemoverse.com/docs/api/install-by-host. Do not pretend the fact was saved.

## What belongs in memory

Durable things: a stated preference, a decision and its reason, a correction, a fact about people, roles or project setup, a lesson from a failure. Chatter that only matters this turn does not belong.

Never store passwords, API keys, tokens, payment data, MFA codes, government IDs or health records. If the input contains any of these, refuse that part in one sentence and save the rest if anything is left.

## How to write it

1. **One fact per memory.** If the user gave several independent facts, save them separately and say how many were saved.
2. **Self-contained.** Write `content` so it still makes sense when recalled months later in another tool: what was decided or observed, why, and where it came from (a file, a meeting, a test run) when that is known. Prefer the user's own words.
3. **The right place.** Personal memory needs no `domain`. To keep a project's facts together, use a domain such as `project:<repository-name>`, and before writing to a named domain call `memory_stats` to reuse its exact spelling: a different case or a stray space opens a separate store. A shared room (beta) is written to only when the user means the room, with its address as `domain`.
4. **Corrections are new memories.** When something saved earlier turned out wrong, save the corrected statement and say in it what it replaces. Nothing is edited in place.

## After writing

The result says whether the memory was stored or refused. A write can be refused when memory already holds a statement too close to this one in the same domain. If the point really is the same, tell the user it is already known and do not reword it to force a duplicate in. If it is a correction or adds something new, write only what is different and lead with it, for example "Correction: staging deploys run on Thursday, not Friday"; if that is refused too, tell the user the correction was not saved.

Confirm with the stored text word for word, so the user sees exactly what future sessions will recall.

---
name: memtomem-search
description: Search indexed memtomem memories by topic. Use for past decisions, notes, findings, or project context that may exist in the memory index.
---

# Search memories

Derive the search query from the current user request.
If the request does not clearly specify the search query, ask before calling a tool — and
in a non-interactive context (a subagent or scripted run with nobody to ask), do not
stall and do not guess: stop and report `insufficient_input` naming the missing search query.
A request that does specify the search query proceeds normally in either context.
Call `mem_search` with the requested topic and use the compact output unless machine-readable details are necessary.

Present the strongest matches concisely with their source path, heading, and relevance score. Explain that memtomem uses BM25 by default and adds dense retrieval only when embeddings are configured. If nothing matches, suggest a broader query or the status workflow; do not write or index anything automatically.

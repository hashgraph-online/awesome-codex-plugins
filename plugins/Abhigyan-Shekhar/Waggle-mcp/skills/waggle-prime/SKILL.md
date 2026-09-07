---
name: waggle-prime
description: Prime a Codex task with the most relevant Waggle project history before starting or resuming substantial work.
---

# Prime project context

1. Determine the stable project scope: prefer the credential-free Git remote identity, otherwise the canonical absolute Git root or workspace path.
2. Call `prime_context` with that `project`, `agent_id: "codex"`, and the current session identifier when available.
3. Summarize only the returned decisions, constraints, failed approaches, open questions, and next steps relevant to the current task.
4. Distinguish remembered history from facts verified in the current working tree. Do not invent context when the result is empty.

This is the Codex skill equivalent of `/waggle-prime`; invoke it as `$waggle-prime`.

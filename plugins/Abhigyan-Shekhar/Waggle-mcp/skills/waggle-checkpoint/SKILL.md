---
name: waggle-checkpoint
description: Checkpoint durable decisions, fixes, constraints, results, and open next steps from the current Codex task into scoped Waggle project memory.
---

# Checkpoint durable outcomes

1. Review the current task and select only durable outcomes: decisions and rationale, verified fixes and causes, stable constraints, failed approaches worth avoiding, measured results, unresolved problems, and concrete next steps.
2. Exclude greetings, raw command logs, speculative thoughts, secrets, duplicate facts, and details easily recovered from the current code unless their historical meaning matters.
3. Determine the stable project scope: prefer the credential-free Git remote identity, otherwise the canonical absolute Git root or workspace path.
4. Draft a compact checkpoint summary. Call `observe_conversation` with the user's checkpoint request as `user_message`, the summary as `assistant_response`, and the stable `project`, `agent_id: "codex"`, and current session identifier when available.
5. Report what categories were checkpointed and any non-fatal extraction errors. If there is nothing durable, say so and skip the write.

This is the Codex skill equivalent of `/waggle-checkpoint`; invoke it as `$waggle-checkpoint`.

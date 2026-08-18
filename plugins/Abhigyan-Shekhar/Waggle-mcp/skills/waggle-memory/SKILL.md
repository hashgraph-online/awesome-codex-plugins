---
name: waggle-memory
description: Use Waggle automatically as portable, local project memory during meaningful coding work; retrieve prior decisions and constraints, then store only durable outcomes.
---

# Waggle project memory

Treat Waggle as memory owned by the project, not as a transcript archive or generic personal chat memory.

## Establish a stable scope

Before the first Waggle call in a task, choose one stable `project` value:

1. Prefer the repository's canonical remote identity without credentials or a trailing `.git`, such as `github.com/acme/api`.
2. If there is no remote, use the canonical absolute Git root path.
3. Outside Git, use the canonical absolute workspace path.

Reuse that value across sessions. Do not use only a directory basename because unrelated repositories can share it. Pass `agent_id: "codex"` and the current task/session identifier when one is available. Never mix remembered context from a different project into the answer.

## Retrieve selectively

- At the beginning of a new task that involves meaningful project work, call `prime_context` once with the narrowest known scope.
- Skip priming for greetings, trivial formatting, or questions fully answerable from the current prompt with no project-history dependency.
- Before answering anything that may depend on earlier decisions, preferences, constraints, failed attempts, bugs, experiments, unresolved questions, or project state, call `query_graph` with the stable project scope. Start with `max_nodes: 10`, `max_depth: 1`, and `retrieval_mode: "hybrid"`.
- Use `get_related` when a returned node ID needs graph context, and `graph_diff` when the user asks what changed.
- Treat retrieved memories as historical evidence, not current repository truth. Verify changeable facts against the working tree. If retrieval is empty or conflicts with current evidence, say so and do not invent history.

## Store durable knowledge only

Use this threshold for every write:

> Store information when forgetting it would likely cause duplicated work, a wrong future decision, or violation of an established constraint. Do not store something merely because it happened.

After a completed turn, call `observe_conversation` only when the turn crosses that threshold and contains durable project knowledge, such as:

- a decision and its rationale;
- a stable requirement, constraint, dependency, or compatibility promise;
- a user correction or durable project preference;
- the diagnosed cause and verified fix for a bug;
- a failed approach worth avoiding and why it failed;
- a benchmark or experiment result with enough context to interpret it;
- an unresolved problem or concrete next step that should survive the session.

Pass the actual completed `user_message`, the final `assistant_response`, and the same project, agent, and session scope used for retrieval.

Do not store greetings, acknowledgements, temporary debugging chatter, command logs, speculative thoughts, duplicate facts, aborted work, secrets, or facts cheaply recoverable from the repository unless their historical significance matters.

Prefer `observe_conversation` for normal completed turns. Use `store_node` only for an explicitly requested single atomic memory, and always include the project scope. Use `store_edge` when an explicit relationship materially improves the record, choosing only supported relationships: `depends_on`, `contradicts`, `updates`, `derived_from`, `part_of`, or `relates_to`. Use `decompose_and_store` only when the user explicitly requests unscoped bulk ingestion; it does not accept project scope.

## Safety

- Waggle writes to the local configured store. Do not claim a cloud upload occurred.
- Ask before destructive tools such as `clear_project`, `clear_session`, or `clear_all`; preview with `dry_run: true` first.
- Do not hide memory writes. If a write materially affects the user's requested outcome, mention it briefly.
- If Waggle tools are unavailable, continue the coding task without fabricating recall or persistence and report the missing integration concisely.

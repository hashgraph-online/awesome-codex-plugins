---
name: graymatter-memory
description: Search, retrieve, save, revise, and forget secure durable GrayMatter memory. Use when a task may depend on prior decisions, preferences, todos, artifacts, or long-lived context, or when the user asks to remember, update, or forget information.
---

# GrayMatter Memory

Use GrayMatter as the durable memory system for information that remains useful beyond the current conversation.

## Workflow

1. Call `memory_search` before asking the user to repeat prior context that may already be known.
2. Use `memory_get` only to hydrate a specific authorized result when its full content is needed.
3. Keep temporary reasoning, transient chat state, and one-off working notes in the conversation rather than durable memory.
4. Call `memory_save` only for useful durable decisions, preferences, todos, artifacts, configuration, or reusable context.
5. Avoid storing passwords, access tokens, private keys, payment data, or highly sensitive personal information unless the product explicitly supports and the user clearly requests that use.
6. Use concise titles, normalized tags, and a stable source or scope. Store the durable fact in `content`; do not embed owner, tenant, ACL, user, or organization identifiers.
7. Call `memory_update` when an existing durable fact changes. Do not create a contradictory duplicate when the existing memory can be revised.
8. Before `memory_forget`, identify the exact memory and obtain explicit user confirmation. Pass `confirm: true` only after that confirmation.

## Authorization boundary

- Never request, infer, or supply tenant, organization, owner, user, role, permission, or ACL overrides.
- Treat `FORBIDDEN` and `NOT_FOUND` as authorization-safe outcomes; do not probe adjacent identifiers.
- Do not use broad search results as a context dump. For task-specific grounding, use the GrayMatter context skill and `context_compile`.


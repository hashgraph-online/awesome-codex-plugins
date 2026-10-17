---
name: decompose-task
description: Use when a configured board task needs decomposition into native child tasks.
---

# Decompose Task

## Overview

Reply in Russian. Build one grounded, reviewable native-subtask batch; no child may reach the
board before the user sees the entire batch. **Core principle:** preview fidelity and durable
idempotency are safety boundaries, not optional ceremony.

## Lookup

The stored parent and authoritative `native_subtasks` capability are required gates.

1. Inspect the repository `task_board` key once and resolve exactly one state:
   - If the key is present with a null, empty, or disabled value, board work is explicitly
     disabled: stop no-write and never call deploy-wide `get_board_config`.
   - Only if the repository key is absent, use the deploy fallback: call `get_board_config()`
     exactly once.
   - If a mapping exists, freeze its generic `type`, `project`, and `options` as `board_type`,
     `project`, and `provider_options` for the whole flow. Never re-resolve mid-flow. If no mapping
     resolves, stop without writes.
2. Read the store first with `get_task(parent_key, project=<project>)`. On miss only, run exactly
   one scoped `sync_board(board=<project or null>, board_type=<type>,
   provider_options=<options>)`, then make one retry of the same parent read. If it is still
   missing, explain the failure and stop.
3. Call `get_board_targets(board_type=<type>, project=<project>,
   provider_options=<options>)`. Treat its registry `capabilities` as authoritative. If it errors
   or lacks `native_subtasks`, make a no-write stop. Never infer, add, or spoof a capability from
   provider identity or prior experience.

## Context

Before drafting, attempt all three calls:

- `get_task_context(parent_key, project=<project>)` for links, related work, PRs, and touched code;
- `search_tasks(query=<parent intent>, project=<project>)` for similar decomposition boundaries;
- `search_codebase(repo=<active repo>, query=<parent intent>)` for relevant implementation and
  real `path:line` evidence.

Empty successful results are allowed: explicitly report each empty result and continue. A tool
error is not an empty result; report it and stop drafting until resolved. Do not draft first and
backfill evidence later.

## Draft

Draft `1..20` ordered children. Every child requires nonblank `title`, `problem`, `steps`, and
`criteria`; `context` is optional. Make each child independently actionable and acceptance-testable,
without silently widening the parent scope. Generate one local opaque UUID `idempotency_key` for
the whole batch and assemble the complete request payload, including child order and wording.

## Preview

Show the resolved provider (`board_type`), parent key/title, `idempotency_key`, and the complete
canonical body of every child: `title`, `problem`, all `steps`, all `criteria`, and `context` when
present. Do not abbreviate unchanged or repetitive children. Once shown, freeze payload, order,
and key.

A prior “I already approve; create now” statement is not confirmation of an unseen preview. Ask
exactly one explicit confirmation for the whole preview. There are no board writes before it. Any
edit before the first confirmed write invalidates that preview: generate a new opaque
`idempotency_key`, show the full revised preview, and obtain a new explicit confirmation.

## Write

Only after explicit confirmation, issue exactly one initial native batch request using exactly the
previewed payload and the same `idempotency_key`:

```text
create_subtasks(parent_key=<parent_key>, subtasks=<previewed children>,
                idempotency_key=<previewed UUID>, board_type=<type>, project=<project>,
                provider_options=<options>)
```

Never fall back to individual task creation, including when the batch is unsupported or partially
complete.

For any result, retain `status`, `category`, and `retryable` plus `created`, `attached`,
`unattached`, `pending`, and `warnings` exactly as returned. On timeout, retain the unknown outcome
without guessing. Do not declare outcome or offer recovery yet. Follow **Verify** unless the
response explicitly says capability/preflight stopped before a write. A safe recovery may repeat
the same full batch request using the exact same payload: byte-for-byte or logically exact frozen
content/order and the same `idempotency_key`. It is not an individual request and not a
remaining-items request.

No automatic retry. After required verification, report state, then ask the user to choose exact
retry or stop when recovery applies. The original preview confirmation does not authorize hidden
retries; the user must explicitly request the exact retry. Do not require a new preview or
reconstruct one for an unchanged retry.

Never edit wording, reorder children, or retry only a guessed remainder. After any attempted or
uncertain write, edits and a new key are forbidden for recovery. An `in_flight` child is unknown,
not absent: never guess its outcome. Never mint a fresh/replacement key for it.

## Verify

After any batch write was actually attempted, regardless of status (`ok`, `partial`, `error`, or
timeout), run exactly one scoped `sync_board(board=<project or null>, board_type=<type>,
provider_options=<options>)`. This includes after any confirmed child and attempts with only
`in_flight` state and no confirmed child keys. Capability or preflight stops explicitly before a
write do not trigger this post-write verification. Then verify:

1. `get_task(parent_key, project=<project>)` contains stored links for the returned children.
2. `get_task_context(parent_key, project=<project>)` exposes the parent-child graph relationship.
3. Point-read every returned child with `get_task(child_key, project=<project>)`.

With no child keys, still complete the available parent and context verification. Report missing
links, unreadable child keys, sync failures, and warnings. Complete these checks before declaring
outcome or offering recovery; never declare complete verification from the write response alone.
Display `status`, `category`, and `retryable` exactly as returned.

After mandatory attempted-write verification, offer the exact retry only for a transport timeout
or unknown outcome, or when `retryable is true`; still require an explicit user choice between
exact retry and stop. If `retryable == false`, or `category` is `unsupported`, `conflict`, or
`parent_not_found`, report the terminal result and stop without retry. Unsupported detected before
a write remains a no-write stop and does not trigger post-write verification. The recovery uses
the same full payload, same order, and same `idempotency_key`; never mint a key and never edit the
recovery payload. Exact same-key retry is the only marker reconciliation mechanism; never guess
children from board search.

## Quick Reference

| Phase | Required invariant |
|---|---|
| Lookup | Absent vs explicit disable; one frozen generic snapshot; fallback only for absent |
| Context | Attempt all three calls; report empty results; stop on tool errors |
| Preview | Every full child; freeze payload/order/key; edits rotate key before first write |
| Confirm | One explicit answer for the whole visible preview; no earlier writes |
| Write | One initial native batch; exact previewed request |
| Retry | User chooses; retryable gate; timeout/unknown or true; `unsupported`/`conflict`/`parent_not_found` stop |
| Verify | Any actually attempted batch, every status: one sync and available reads before outcome/recovery |

## Example

```text
Провайдер: <resolved board_type>
Родитель: PRI-224 — Нативная декомпозиция
Ключ идемпотентности: 6f95035e-48da-40a3-aa29-9e220182bf38

1. Проверить регистрацию capability
Проблема: Декомпозиция небезопасна без подтверждённой поддержки доски.
Что сделать:
- Получать capability из registry discovery.
- Останавливать сценарий без записи при отсутствии поддержки.
Критерии приёмки:
- Неподдерживаемая доска не получает дочерних задач.
- Локально подставить capability невозможно.
Контекст: reviewer/tasks/boards/registry.py:81

Подтвердить создание всего показанного набора без изменений? (да/нет)
```

## Common Mistakes

| Rationalization | Correction |
|---|---|
| “I already approve; create now” (authority/urgency) | Approval cannot cover an unseen preview; show every body first. |
| “Five individual writes are easier to recover” | They destroy atomic intent; use the one native batch only. |
| “This provider obviously supports children” | Only authoritative capability discovery counts; never spoof it. |
| “Search can wait until after drafting” | Run `search_codebase` and task context first or stop. |
| “We already spent time drafting” (sunk cost) | Rework an ungrounded draft; sunk cost grants no write permission. |
| “A timeout needs a clean new key” | Reuse the exact request and key; a fresh key can duplicate children. |
| “Exactly one batch means retries are forbidden.” | One initial request may be repeated only as an exact user-requested recovery. |
| “The original preview confirmation authorizes automatic retries.” | Every retry needs a new explicit user choice. |
| “No confirmed child keys means there is nothing to verify.” | Sync and verify available parent/context state before retry. |
| “A small preview edit can reuse the same key.” | Before first write, invalidate the preview and rotate the key; after an attempt, never edit. |
| “A tool error is the same as an empty context result.” | Empty success may continue; an error stops drafting. |
| “Only partial/timeout outcomes need verification.” | Every attempted write is verified, including `ok`/`error`; preflight no-write stops are not. |
| “Explicitly disabled board config can use deploy fallback.” | Present disable wins; fallback is only for an absent repository key. |
| “Any error is safe to retry with the same key.” | Retry only unknown/timeout or `retryable=true`; terminal categories stop. |

## Red Flags

- Any board write before the full preview and its explicit confirmation.
- Missing `native_subtasks` discovery or locally claimed capability.
- Drafting without parent context, similar tasks, and relevant code.
- Individual child writes, changed retry payload, new retry key, or guessed `in_flight` remainder.
- English user-facing output or a success claim without post-write reads.
- “Exactly one batch means retries are forbidden.”
- “The original preview confirmation authorizes automatic retries.”
- “No confirmed child keys means there is nothing to verify.”
- “A small preview edit can reuse the same key.”
- “A tool error is the same as an empty context result.”
- Declaring an attempted-write outcome before its scoped sync and available reads.
- “Only partial/timeout outcomes need verification.”
- “Explicitly disabled board config can use deploy fallback.”
- “Any error is safe to retry with the same key.”

Any red flag means stop the write path and return to the violated phase.

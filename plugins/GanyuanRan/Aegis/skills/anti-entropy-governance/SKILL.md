---
name: anti-entropy-governance
description: Use when retiring old logic, collapsing duplicate owners, removing fallbacks, or touching schema, persistence, or source-of-truth boundaries while deciding whether to delete old paths, retain compatibility, or stop for confirmation.
---

# Anti-Entropy

## Overview

Use this skill when the task is not merely "change code" but "remove old paths
safely without growing entropy".

This skill chooses between:

- `delete-first` for internal code retirement
- `compat-exception` for proven external dependency boundaries
- `confirmation-first` for persistent-state or irreversible object deletion

It does not replace `brainstorming`, `writing-plans`,
`systematic-debugging`, or `verification-before-completion`. It is a narrow
governance owner for retirement, fallback collapse, duplicate-owner cleanup,
and deletion safety.

## When to Use

Use when any of these are true:

- old logic, duplicate owners, or stale fallbacks should be retired
- a candidate fix is "delete old path" vs "add another fallback"
- internal keyword / phrase / trigger logic is being replaced by structured logic
- a new canonical owner exists and the old owner may still carry real behavior
- a cleanup, migration, or deprecation task touches schema, persistence,
  source-of-truth, or external compatibility boundaries
- the task risks confusing code retirement with live data deletion

Do not use for:

- pure additive feature work with no retirement decision
- tiny wording edits
- simple status or read-only Q&A
- normal bug fixes that do not involve owner collapse, fallback cleanup, or
  deletion choice

## Auto-Compose Boundary

This skill should be composed by other owners. It should not become a new
global hot-path entry.

Prefer composition from:

- `brainstorming` for approach selection involving retirement or persistence risk
- `writing-plans` for plans that delete old paths or touch schema / migration /
  persistence
- `systematic-debugging` when the tempting fix is fallback growth or
  delete-vs-retain
- `verification-before-completion` for cleanup / retirement / compatibility /
  migration closeout

Do not load this directly from `using-aegis` unless explicitly requested.

## Core Principle

Default to reducing internal entropy, not preserving internal history.

Use this rule:

- internal code retirement -> `delete-first`
- external compatibility boundary -> `compat-exception` only with active
  dependency evidence
- persistent-state or irreversible source-of-truth object ->
  `confirmation-first`

Unknown dependency is not active dependency evidence.

Mentioning, loading, or discussing destructive-action rules never authorizes
destructive execution. Without explicit scoped user confirmation:

- no irreversible deletion is executed
- no destructive tool call is made
- no runnable destructive command is emitted as the next action
- no broad assent is reinterpreted as deletion approval

## Deletion Classes

Classify the deletion target first:

- `code-retirement`
  - source code
  - internal triggers
  - duplicate owners
  - stale fallback branches
  - compat-only carriers
  - dead tests/config tied to removed internal behavior

- `contract-carrying code`
  - schema definition files
  - migration files
  - public API contract code
  - host install/discovery code
  - persistence read/write logic

- `live-state mutation surface`
  - code or commands that would mutate live databases, object stores, queues,
    or other persistent state

- `derived-state`
  - rebuildable caches
  - generated indexes
  - temporary exports
  - recomputable artifacts

- `persistent-state`
  - live database tables / columns / rows
  - source-of-truth object storage files
  - user records
  - permission / identity / membership records
  - audit / billing / irreversible business records
  - non-rebuildable queue or event contents

## Default Path By Class

- `code-retirement` -> `delete-first`
- `contract-carrying code` -> `delete-first` with high-risk verification
- `live-state mutation surface` -> inspect and classify; destructive execution
  still requires confirmation when it reaches persistent-state
- `derived-state` -> verify rebuildability first, then decide
- `persistent-state` -> `confirmation-first`

## Hard Stops

If the target is `persistent-state` or another irreversible source-of-truth
object:

- do not execute deletion automatically
- do not emit a runnable destructive command as the next action
- do not call a destructive tool
- do not interpret generic agreement as confirmation
- ask for explicit scoped user confirmation
- request backup / rollback / migration note when relevant

Examples that require confirmation:

- `DROP TABLE`
- `DROP COLUMN`
- `TRUNCATE`
- bulk delete of real business data
- deleting source-of-truth uploaded files
- deleting permission, identity, audit, billing, or membership records
- purging non-rebuildable queues or event streams

## Data Destruction Guard

When `confirmation-first` is required, stop normal retirement flow and emit:

```text
Data Destruction Guard:
- Target Class:
- Exact Target(s):
- Environment:
- Why Irreversible:
- Backup / Rollback Note:
- Allowed Read-Only Next Steps:
- Blocked Destructive Steps:
- Confirmation Required: yes
- Status: awaiting scoped confirmation
```

Only explicit scoped confirmation can continue. Broad assent such as "OK",
"continue", or "sounds good" is insufficient. If scope changes at all, previous
confirmation is invalid and fresh confirmation is required.

## Anti-Entropy Declaration

Before deletion, state:

```text
Anti-Entropy Declaration:
- Deletion Class:
- Old Path/Object:
- New Canonical Owner:
- Expected Preserved Behavior:
- Expected Retired Behavior:
- External Boundary Touched: no | yes
- Source-of-Truth Data Risk: none | possible | confirmed
- User Confirmation Required: no | yes
```

If `User Confirmation Required: yes`, stop normal delete-first flow and enter
`Data Destruction Guard`.

## Retirement Decision

Choose one path only:

```text
Retirement Decision:
- Path: delete-first | compat-exception | confirmation-first
- Why:
- Non-edits:
```

Rules:

- choose `delete-first` for internal retirement unless a stronger boundary blocks it
- choose `compat-exception` only when external dependency is proven
- choose `confirmation-first` for persistent-state or irreversible targets

If `Path = confirmation-first`, no destructive execution may happen until
scoped confirmation is received.

## Verification Plan

Do not verify only by "tests are green". Verify that the old logic actually
died and the new owner actually carries the behavior.

```text
Verification Plan:
- Main-path check:
- Lingering-reference check:
- Negative check:
- Boundary check:
```

Meaning:

- `Main-path check`: new canonical owner still satisfies intended behavior
- `Lingering-reference check`: old path is no longer referenced on the main path
- `Negative check`: retired trigger/path really stopped working
- `Boundary check`: host/API/schema/persistence boundary was not accidentally broken

## Gap Taxonomy

If a gap appears after deletion, classify it before repairing:

- `expected-retirement`
- `missing-owner-logic`
- `stale-internal-consumer`
- `baseline-gap`
- `external-compat`
- `persistent-state-risk`

`persistent-state-risk` is a stop condition, not a normal repair branch.

## Gap Closure

Repair order:

- `expected-retirement`
  - update tests, docs, or caller expectations
- `missing-owner-logic`
  - fix the new canonical owner
- `stale-internal-consumer`
  - migrate the internal consumer
- `baseline-gap`
  - correct requirement / spec / baseline first
- `external-compat`
  - allow compat only if active external dependency evidence exists
- `persistent-state-risk`
  - stop and ask for user confirmation

Use this contract:

```text
Gap Closure:
- Gap Found:
- Gap Type:
- Repair Action:
- Reintroduced Compat: no | yes
- If yes, External Dependency Evidence:
- Retirement Trigger:
```

If `Gap Type = persistent-state-risk`, stop and return to the confirmation
gate. Do not improvise destructive repair.

## Compat Exception Gate

Retention is allowed only if all are true:

- an external boundary is touched
- current active dependency evidence exists
- deletion would break a published or documented contract
- the current slice cannot complete owner repair or consumer migration
- an observation metric exists
- a retirement trigger exists

Without these, do not retain compat.

## Completion Semantics

Completion claims must reflect the real outcome:

- internal retirement with old compat preserved -> `bounded mitigation` or
  `deferred debt`, not clean retirement
- external compat retained with full evidence -> `bounded compatibility exception`
- persistent-state deletion without scoped confirmation -> not complete

## Common Mistakes

Do not:

- treat unknown dependency as proof of dependency
- keep both owners active "for safety"
- add a fallback before checking whether the gap belongs in the new owner
- confuse migration-file deletion with live database deletion
- treat source-of-truth data cleanup as ordinary code retirement
- call a task "cleaned up" when old logic still carries main-path behavior
- treat a warning or guard card as destructive authorization

## Minimal Reporting Shape

This shape is the anti-entropy workflow's decision surface, not a separate
final completion report. When anti-entropy materially shapes a completed task,
its preserved/retired behavior, deletion class, retained boundary, verification
plan, and residual risk should flow into `verification-before-completion`'s
unified Aegis impact/safety receipt.

```text
Aegis Visibility:
Anti-Entropy Declaration:
Retirement Decision:
Verification Plan:
Gap Closure:
```

Use the compact shape by default. Expand only when task risk requires it.

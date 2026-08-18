---
name: memory-load
description: Use when Wingman memory is already known enabled in the current repository and starting non-trivial coding, debugging, planning, review, API integration, or business-logic work, or when the user explicitly asks to load or read Wingman memory.
---

# Wingman Memory Load

`memory-load` is read-only. It loads current truth by default and history only when the task needs explanation or past-change context.

## Memory State

Use `.wingman/memory/` as the repository-local memory root.

Repository memory is enabled only when both core entry files exist:

```text
.wingman/memory/brief.md
.wingman/memory/context.md
```

If `.wingman/memory/` is missing, continue without memory unless the user explicitly asked about memory. If the directory exists but a core entry file is missing, report partial memory only when the user asked about memory or the task depends on memory consistency.

## Authority

Use this authority order when memory files disagree:

```text
brief.md current Project Decisions
> domains/ current truths
> context.md hot working state
> history/ past events and evidence
```

History explains why something changed. It is not current truth unless a current entry in `brief.md` or `domains/` links to it as evidence.

Only `Status: current` current-truth entries are binding. `candidate`, `deprecated`, and `superseded` entries are background only.

Relations:

- `updates <id>` replaces the referenced entry for overlapping scope.
- `extends <id>` keeps both entries valid when compatible.
- `derived_from <id-or-path>` records evidence lineage, not authority.

If two current entries with the same `Subject` conflict and no relation resolves them, stop and ask which rule is valid.

## When To Load

Skip memory for trivial isolated work: typo-only edits, formatting, isolated style tweaks, throwaway experiments, or local changes with no business, state, data, contract, reuse, or existing-behavior impact.

Load memory before non-trivial coding, debugging, planning, review, refactor, API integration, reusable implementation work, or changes touching business logic, state flow, permissions, quotas, billing, field mappings, contracts, or existing behavior.

Also load memory when the user mentions previous work, consistency, "之前", "上次", "沿用", "保持一致", "不要破坏", or asks to use memory.

## Load Protocol

1. Check memory state.
2. If memory is disabled or not needed, continue without reading memory files.
3. Read `.wingman/memory/brief.md`.
4. Use the Domain Registry to choose relevant current domain truth.
5. Read relevant `domains/` files.
6. Read `.wingman/memory/context.md` only for hot task state and direct pointers.
7. Read history projections only when Historical-Risk Signals are present.
8. Read at most 0-3 selected history event bodies by default.

For folder domains, read the folder `index.md` first, then only the relevant subfiles named by that index. Do not read every domain subfile by default.

## Domain Registry

The Domain Registry in `brief.md` is a routing table:

```md
| Domain | Read When | Current File | History Domain Index | History Topics | Aliases | Related Domains | Status |
```

- `Current File` points to current truth.
- `History Domain Index` and `History Topics` point to historical lookup indexes.
- `Related Domains` are hints, not automatic expansion.
- Deprecated or superseded registry rows are not authoritative unless the replacement points there.

Read a current domain when the task matches `Domain`, `Read When`, or `Aliases`. Read related domains only when the task also touches that related area or the current domain file points to a specific related rule.

## Context

`context.md` is a hot cache. Read it for:

- active unfinished work;
- pending follow-up;
- blocker or debugging state needed soon;
- direct pointer to current truth or history for the active task.

Treat context pointers as routing hints. If a pointer names a current truth, read that truth. If it names a history event, read the event only when Historical-Risk Signals are present or the pointer is directly needed for the task.

## Historical-Risk Signals

Read history projections only when at least one signal is present:

- the user asks about previous work, "before", "last time", "why", "what changed", "之前", or "上次";
- the task changes or depends on rule semantics, field meanings, state flows, API contracts, business meaning, or agent behavior;
- current truth links to a history event and the reason matters for the task;
- a context pointer directly names a relevant history event;
- history is needed to avoid repeated debugging or repeated wrong interpretation.

When history is needed, prefer sources in this order:

1. Direct event links from current truth or context pointers.
2. `history/topics/<topic>.md`.
3. `history/domains/<domain>.md`.
4. `history/months/YYYY-MM.md` for date questions.
5. `history/index.md` when projection routing is unclear or the user asks broadly.

Choose only the strongest 0-3 event bodies for the current task unless the user asks for deeper history.

Do not scan `history/events/` directly by default.

## Internal Checklist

Before editing code, internally confirm:

- active task and relevant files;
- memory files read;
- relevant current truth IDs and subjects;
- any candidate, deprecated, or superseded entries;
- any relation targets needed to understand the current rule;
- history projections or event bodies read, if any;
- exact fields, symbols, contracts, or rules that are binding;
- whether the requested change conflicts with memory.

Do not show the checklist by default. Surface it only when there is a conflict, missing context, or the user asks.

## Memory Pressure Signals

`memory-load` may notice memory pressure but must not clean, compact, summarize, promote, or delete memory.

Mention cleanup only when a concrete candidate affects the task:

- `context.md` contains durable rule bodies instead of pointers;
- context repeats bodies already owned by `brief.md`, `domains/`, or `history/events/`;
- two current truths conflict;
- a replaced rule is still marked current;
- history projections copy event bodies instead of linking them;
- relevant history exists but no topic or domain projection helps lookup.

Suggest explicit `memory-clean` later. If a conflict blocks correct work, ask the user which rule is valid.

## Binding Rules

- Never substitute one business field for a semantically different field for convenience.
- If memory specifies a canonical field or contract, follow it unless the user changes the rule.
- Treat existing `// @invariant:` comments as local binding context when present.
- `memory-load` is read-only; new comments or memory updates belong to the relevant coding task or `memory-sync`.
- Existing capability and reuse lookup belongs to `project-map-find`; do not read project-map files during `memory-load` unless the user explicitly asks for project-map context.

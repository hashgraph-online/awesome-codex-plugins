---
name: memory-sync
description: Use when Wingman memory is already known enabled in the current repository and progress, decisions, business logic, API contracts, state flow, field mappings, or durable project knowledge should be recorded, or when the user explicitly asks to sync Wingman memory.
---

# Wingman Memory Sync

`memory-sync` writes the smallest useful memory update after meaningful work. It chooses the owning body for each memory item before writing.

## Storage Roles

```text
brief.md / domains/ = current projection, current binding truth bodies
history/events/     = event log, historical event bodies
history indexes     = projection indexes for historical lookup
context.md          = hot cache, active work state and short pointers
```

Authority order:

```text
brief.md current Project Decisions
> domains/ current truths
> context.md hot working state
> history/ past events and evidence
```

Current truth says what future agents must obey now. History explains what changed and why. Context carries only active work state and short pointers.

## Gate

Apply these gates before reading or writing memory:

1. If the user opts out of memory for this work, stop without reading or writing memory.
2. If `.wingman/memory/` is missing, ordinary completion does not use `memory-sync`. If sync was explicitly requested, report that repository memory is disabled and `memory-setup` is the explicit enable path.
3. If `.wingman/memory/` exists but `.wingman/memory/brief.md` or `.wingman/memory/context.md` is missing, stop before writing, report the missing core entry files, and suggest `memory-setup`. Do not repair from `memory-sync`.
4. Continue only when both `brief.md` and `context.md` exist.

Before reporting meaningful coding, documentation, configuration, product, or operational work as complete in a repository where memory is enabled, run the routing checks below. If a write route qualifies, sync memory before saying the work is done unless the user opted out.

## Ownership Routing

Classify each memory item into one of these routes:

| Route | Owner | Qualifies When |
| --- | --- | --- |
| `IGNORE` | none | The change has no reusable future value. |
| `CURRENT_TRUTH` | `brief.md` or `domains/` | Future agents must obey the rule, contract, field meaning, state flow, policy, invariant, or recurring debugging conclusion. |
| `HISTORY_EVENT` | `history/events/` | The change explains durable rule evolution, old-to-new meaning, important correction, migration, incident, important regression fix, or user-requested historical memory. |
| `CONTEXT_POINTER` | `context.md` | Active unfinished work, pending follow-up, blocker, debugging state, or an immediate continuation pointer is needed. |

Use `IGNORE` for typo-only edits, formatting-only edits, rename-only cleanup, isolated visual tweaks, obvious local implementation details, and failed attempts with no reusable lesson.

A task may write more than one route, but each route needs its own reason. When current truth and history are both written, current truth owns the binding rule and history owns the change narrative.

## Single Owner Body

Each durable memory item has one owning body:

- current binding rule body: `brief.md` or `domains/`;
- historical event body: `history/events/`;
- historical lookup entry: `history/index.md`, `history/domains/`, `history/topics/`, or `history/months/`;
- hot working state or pointer: `context.md`.

Short summaries and pointers are valid. Full duplicated rule bodies, event narratives, evidence, reasoning, or debugging paths are not valid.

## Write Flow

1. Apply the Gate.
2. Route each memory item with Ownership Routing.
3. If every item is `IGNORE`, write nothing and report the threshold that blocked writing.
4. Write `CURRENT_TRUTH` before `HISTORY_EVENT` when both are needed.
5. Write `HISTORY_EVENT` only when the event has durable trace value beyond the current rule.
6. Write `CONTEXT_POINTER` only for hot state or immediate continuation.
7. Update history projections only for new or changed history events.
8. Report changed memory files or the route that blocked writing.

## Current Truth

Write current truth when future agents must obey the result or would otherwise need old logs to avoid a semantic mistake.

Use `brief.md` for project-wide decisions: global conventions, cross-domain rules, architecture choices, repository policies, memory policy, and project-wide agent behavior.

Use `domains/` for one-domain rules: business rules, API contracts, canonical fields, field meanings, state flow, enum mapping, permissions, routing, money, quotas, lifecycle, product invariants, operational procedures, or recurring debugging conclusions.

Before writing current truth:

1. Read `brief.md`.
2. Use the Domain Registry to choose `brief.md` or a domain file.
3. Inspect same-subject current entries when practical.
4. Verify evidence from user direction, existing memory, docs, schema, tests, accepted specs, or intentional implementation behavior.
5. If two current entries conflict and no `updates` or `extends` relation resolves them, stop and ask which rule is valid.

Use stable identity:

- `ID`: `mem:<domain>:<subject-slug>`.
- `Subject`: stable dotted subject such as `order.status.meaning`.
- `Status`: `current | superseded | deprecated | candidate`.
- `Relation`: `updates <id> | extends <id> | derived_from <id-or-path> | None`.
- `Confidence`: `confirmed | implementation-backed | inferred`.

Only `Status: current` entries are binding. Inferred entries start as `candidate` unless confirmed by user, spec, schema, test, or intentional implementation contract.

When replacing a rule, mark the old entry `superseded` or `deprecated` and point to the replacement. When extending a compatible rule, keep both current and link with `extends`.

Read `references/templates.md` before using the default current truth template.

## History Event

Write history when a completed change has durable trace value beyond hot context, especially when:

- a current truth was added, changed, deprecated, or superseded and the reason matters;
- a rule, field meaning, workflow interpretation, data contract, or agent behavior changed;
- the event explains why a current rule exists;
- a recurring confusion, debugging path, or wrong interpretation was resolved;
- a migration, incident, important regression fix, or user-requested historical record needs later lookup.

History is not mandatory for every current truth. Skip history when the reason is obvious from the current rule or the change is trivial.

When writing history:

1. Read `references/history-events.md`.
2. Write one event body under `.wingman/memory/history/events/YYYY/MM/YYYY-MM-DD-<event-slug>.md`.
3. Update only the needed projections: `history/index.md`, `history/domains/<domain>.md`, `history/topics/<topic>.md`, and `history/months/YYYY-MM.md`.
4. Link `Promoted Truths` to current truth IDs or use `None`.
5. Keep projection indexes short and link-only.

Use generic topic names such as `order-status`, `checkout-flow`, `payment-selection`, `upload-retry`, or `quota-display`.

## Context Pointer

Write `context.md` only for active working state:

- unfinished work;
- pending follow-up;
- blocker or debugging state needed in the next few sessions;
- immediate continuation pointer to a current truth or history event.

If current truth or history owns the durable detail, context receives only a short pointer. If no hot follow-up exists, write no context entry.

Use the `## Short Pointers` section when present. If an older memory file lacks that section, add it near current work rather than creating a new log section.

Read `references/templates.md` before using the default context pointer shape.

## Domain Registry

Update the Domain Registry only when creating, renaming, deprecating, or superseding a domain route.

Registry rows use:

```md
| Domain | Read When | Current File | History Domain Index | History Topics | Aliases | Related Domains | Status |
```

`History Domain Index` and `History Topics` are routing hints for historical lookup. They do not make history current truth.

## Language And Completion

Memory language follows `brief.md` Memory Settings when set; otherwise follow existing memory language, then the user's language, then English. Keep code symbols, paths, API names, config names, and field names unchanged.

Finish by reporting changed memory files. If nothing was written, name the blocking gate or route.

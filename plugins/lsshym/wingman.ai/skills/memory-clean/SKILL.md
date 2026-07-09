---
name: memory-clean
description: "Use when the user explicitly asks to clean, compact, prune, trim, deduplicate, optimize, or reduce Wingman memory, or asks to resolve stale or conflicting memory rules."
---

# Wingman Memory Clean

Clean Wingman memory only when the user explicitly asks. Preserve the ownership model while reducing default-read noise and conflicts.

## Ownership Model

```text
brief.md / domains/ = current projection, current binding truth bodies
history/events/     = event log, historical event bodies
history indexes     = projection indexes for historical lookup
context.md          = hot cache, active work state and short pointers
```

Cleanups should move memory toward one owning body per durable item:

- current rule body lives in `brief.md` or `domains/`;
- historical event body lives in `history/events/`;
- historical lookup entry lives in projection indexes;
- hot state or short pointer lives in `context.md`.

## Repository Gate

1. Check `.wingman/memory/`.
2. Check `.wingman/memory/brief.md` and `.wingman/memory/context.md`.
3. If core files are missing, stop and report repository memory state.
4. Read `brief.md` and `context.md` first.
5. Read domain or history files only when the requested cleanup scope points to them.

Never scan all memory files by default.

## Scope Selection

Use the smallest scope that matches the request:

| Scope | Read | Use When |
| --- | --- | --- |
| `context` | `context.md`, relevant current truth/history if linked | Context contains stale hot state, verbose old logs, or duplicate bodies. |
| `current-truth` | `brief.md`, relevant domains | Current rules are duplicated, stale, conflicting, missing identity, or missing relations. |
| `history-index` | relevant projections | History projections are bloated, missing useful routing, or copying event bodies. |
| `history-event` | named event bodies only | User explicitly asks to inspect or edit specific history events. |
| `migration` | target old context logs plus needed destinations | Old context logs need conversion into current truth, history, or pointers. |
| `delete-proposal` | target files only | User asks to delete logs or remove noise. |

If unclear, choose `context` unless the user mentions current rules, domains, Project Decisions, or history.

## Candidate Types

Clean only when at least one concrete candidate exists:

- `COMPACT_TO_POINTER`: context has details already owned by current truth or history.
- `PROMOTE_CURRENT_TRUTH`: context contains a durable rule future agents must obey.
- `PROMOTE_HISTORY`: context contains a durable change narrative or reasoning event.
- `PROMOTE_BOTH`: context contains both current rule and historical explanation.
- `SUPERSEDE`: an old current rule was replaced and should become `superseded` or `deprecated`.
- `REPAIR_RELATION`: same-subject entries need `updates`, `extends`, or conflict resolution.
- `REPAIR_INDEX`: history projection should be link-only or needs a domain/topic route.
- `DELETE_CANDIDATE`: duplicate, obsolete, sensitive, or safely represented elsewhere.
- `NO_ACTION`: cleanup cost or ambiguity exceeds benefit.

File size and line count are diagnostics only. They are not cleanup triggers by themselves.

## Retention Review

Before changing a candidate, decide what would be lost:

- Is it current truth, hot state, or history?
- Is it still valid, replaced, or obsolete?
- Is it the only evidence explaining a current rule?
- Is a future task likely to need the rule, reason, failure mode, or pointer?
- Can the same meaning be recovered from a current truth ID or history event link?

If uncertain, prefer `NO_ACTION` or a deletion proposal over irreversible cleanup.

## Valid Actions

### Compact Context

Replace verbose context with a short pointer only after the durable meaning is preserved elsewhere.

Valid pointer shape:

```md
- <one-line state>; current truth: `<id/path or None>`; event: `<path or None>`; next: <immediate action/blocker or None>.
```

Preserve pending tasks, active blockers, and unresolved current work.

### Promote Current Truth

Write durable rules to `brief.md` or relevant `domains/` when future agents must obey them. Include stable `ID`, `Subject`, `Status`, `Rule`, `Applies When`, `Evidence`, `Confidence`, `Relation`, `Since`, and `History`.

### Promote History

Write historical events under `history/events/YYYY/MM/` when the old context contains durable rule evolution, old-to-new meaning, important correction, migration, incident, regression fix, or user-requested historical memory. Update only needed projections.

### Repair Current Rules

For A -> B requirement changes, make B the only `current` rule for overlapping scope, mark A as `superseded` or `deprecated`, and link with `updates <old-id>`.

If both rules remain valid, link with `extends`. If they conflict and evidence does not settle the winner, stop and ask.

### Repair History Projections

Projection indexes should contain short summaries and links only. Remove copied event bodies from indexes only when the event body remains linked.

### Delete

Never delete without explicit user confirmation after showing a proposal with exact IDs, paths, reasons, preserved locations, and risks.

Do not delete:

- pending tasks;
- current work;
- unresolved bugs;
- current Project Decisions;
- current domain truths;
- user-protected notes;
- the only evidence explaining a current rule;
- history event bodies, unless the user explicitly asked to delete those specific records.

## Optional Resources

- Run `scripts/memory-stats.sh` when heading layout, file size, or candidate discovery is unclear. The script is read-only.
- Read `examples/lossless-compaction.md` when compaction safety is unclear.
- Read `examples/deletion-proposals.md` when preparing a deletion proposal.

Do not read examples or run scripts by default.

## Workflow

1. Apply Repository Gate.
2. Select the smallest cleanup scope.
3. Identify concrete candidates.
4. Run Retention Review.
5. Classify candidates.
6. Apply safe `COMPACT_TO_POINTER`, `PROMOTE_CURRENT_TRUTH`, `PROMOTE_HISTORY`, `PROMOTE_BOTH`, `SUPERSEDE`, `REPAIR_RELATION`, and `REPAIR_INDEX` changes.
7. For `DELETE_CANDIDATE`, present a proposal and wait for explicit confirmation.
8. Report files read, files changed, compactions, promotions, superseded rules, repaired indexes, and proposed or confirmed deletions.

Do not say memory was cleaned if no file changed. If only a deletion proposal was produced, say cleanup is pending confirmation.

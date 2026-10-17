# Memory Sync Templates

Use these templates only when the existing memory file has no stronger local format.

## Current Truth Template

Use in `brief.md` Project Decisions or relevant `domains/` files.

```markdown
- **ID**: `mem:<domain>:<subject-slug>`
- **Subject**: `<stable.dotted.subject>`
- **Status**: `current | superseded | deprecated | candidate`
- **Rule**: <the current binding rule future agents must obey>
- **Applies When**: <scope and trigger>
- **Evidence**: <user statement | existing memory | docs/schema/tests/spec | implementation contract | history event>
- **Confidence**: `confirmed | implementation-backed | inferred`
- **Relation**: `updates <id> | extends <id> | derived_from <id-or-path> | None`
- **Since**: YYYY-MM-DD
- **History**: `history/events/YYYY/MM/YYYY-MM-DD-<event-slug>.md` or `None`
```

Current truth answers what is true now, when it applies, what evidence supports it, and what it updates, extends, or derives from.

## History Event Template

Use under `history/events/YYYY/MM/YYYY-MM-DD-<event-slug>.md`.

```markdown
# <Event Title>

- **Date**: YYYY-MM-DD
- **Summary**: <one-sentence event summary>
- **Before**: <previous rule, assumption, or state; use None when not relevant>
- **After**: <short summary of the new state; link to current truth for the full rule>
- **Reason**: <why the change happened or what mistake it prevents>
- **Evidence**: <user/spec/schema/test/implementation links>
- **Promoted Truths**: <current truth IDs or None>
- **Domains**: <domain list>
- **Topics**: <topic list>
```

History events answer what changed, when, why, what old state was corrected, and which current truths resulted.

## History Projection Entry

Use in `history/index.md`, `history/domains/<domain>.md`, `history/topics/<topic>.md`, and `history/months/YYYY-MM.md`.

```markdown
- YYYY-MM-DD `<event-slug>`: <brief summary>; current truth `<id or None>`; event `history/events/YYYY/MM/YYYY-MM-DD-<event-slug>.md`.
```

Projection entries are lookup indexes. Keep them to one line where possible.

## Context Pointer Template

Use in `context.md` only for hot working state or immediate continuation.

```markdown
- <one-line state>; current truth: `<id/path or None>`; event: `<path or None>`; next: <immediate action/blocker or None>.
```

Use `current truth` for the binding rule pointer and `event` for the historical evidence pointer. If there is no active follow-up, do not write a context pointer.

## Topic Naming Guidance

Use stable, generic feature, workflow, or problem-cluster names:

- `checkout-flow`
- `payment-selection`
- `order-status`
- `product-detail`
- `upload-retry`
- `quota-display`

Avoid customer names, project code names, one-off business campaign names, and temporary implementation labels as topic names.

# History Events And Projections

Use this reference only after `SKILL.md` says the History Event Threshold passed.

## Model

History uses one event body plus projection indexes:

- Event body is the source of truth under `history/events/YYYY/MM/`: `history/events/YYYY/MM/YYYY-MM-DD-<event-slug>.md`.
- `history/index.md` is the top-level entry point, not an ever-growing full event list.
- `history/domains/<domain>.md` is the domain history projection.
- `history/topics/<topic>.md` is the topic history projection for feature, workflow, or recurring problem lookup.
- `history/months/YYYY-MM.md` is the month history projection.

Projection indexes contain links and short summaries only. Do not copy event bodies into indexes.

## Write Procedure

1. Create `.wingman/memory/history/`, `history/events/YYYY/MM/`, `history/domains/`, `history/topics/`, and `history/months/` if needed.
2. Create or update `history/index.md` as the top-level projection entry. Keep it small: list projection files and only recent high-signal events.
3. Write one event body under `history/events/YYYY/MM/` named `YYYY-MM-DD-<event-slug>.md`.
4. Update `history/domains/<primary-domain>.md`.
5. Update each related `history/domains/<related-domain>.md` when the event genuinely touches that domain.
6. Update each relevant `history/topics/<topic>.md`.
7. Update `history/months/YYYY-MM.md`.
8. Include `Promoted Truths` links when domain truth or project ADR was written. Use `None` when no current truth was promoted.
9. Do not rewrite event bodies just because a projection index changes.

## Event Body Template

Use this shape when no stronger local format exists:

```markdown
# Short Event Title

- **Date**: YYYY-MM-DD
- **Primary Domain**: `<domain or none>`
- **Related Domains**: `<domain list or None>`
- **Topics**: `<topic list or None>`
- **Type**: `feature | bugfix | refactor | debugging | contract | decision | docs | operations`
- **Files**:
  - `path/to/file`: what changed
- **Outcome**: what happened
- **Promoted Truths**:
  - `domains/<domain>.md#current-truths` or `brief.md#architecture-decisions-adr---global-rules` or `None`
- **Notes**: historical details only
```

## Top-Level Index Template

Use this shape when no stronger local format exists:

```markdown
# History Index

## Domain Indexes
- `domains/<domain>.md`: <short description>

## Topic Indexes
- `topics/<topic>.md`: <short description>

## Month Indexes
- `months/YYYY-MM.md`: <short description>

## Recent High-Signal Events
- `events/YYYY/MM/YYYY-MM-DD-<event-slug>.md`: <one-line summary>
```

## Domain Projection Template

Use this shape when no stronger local format exists:

```markdown
# <Domain> History Index

## Events
- `../events/YYYY/MM/YYYY-MM-DD-<event-slug>.md`: <summary>; related `<domain list>`; promoted `<truth link or None>`
```

## Topic Projection Template

Use this shape when no stronger local format exists:

```markdown
# <Topic> History Index

## Read When
- <task signals>

## Events
- `../events/YYYY/MM/YYYY-MM-DD-<event-slug>.md`: <summary>; primary `<domain>`; promoted `<truth link or None>`
```

## Month Projection Template

Use this shape when no stronger local format exists:

```markdown
# YYYY-MM History Index

## Events
- `../events/YYYY/MM/YYYY-MM-DD-<event-slug>.md`: <summary>; primary `<domain>`
```

## Growth Rules

- Keep `history/index.md` small. It lists projection entry points and only recent high-signal events.
- If a domain projection grows too large, split the projection index, not the event body, for example `history/domains/<domain>/<topic>.md`.
- If a topic projection grows too large, split the projection index, not the event body, for example `history/topics/<topic>-<subtopic>.md`.
- If a month projection grows too large, split the projection index, not the event body, for example `history/months/YYYY-MM-wNN.md`.
- Event bodies remain under `history/events/YYYY/MM/` and are not copied into domain, topic, or month directories.

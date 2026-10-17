# History Events And Projections

Use this reference only after `memory-sync` has routed an item to `HISTORY_EVENT`.

## Model

History is episodic memory:

- event bodies live under `history/events/YYYY/MM/`;
- projection indexes route lookup by domain, topic, month, or broad index;
- projection indexes contain short summaries and links only;
- history explains past changes and evidence, but is not current truth.

## Event Body

Path:

```text
.wingman/memory/history/events/YYYY/MM/YYYY-MM-DD-<event-slug>.md
```

Default shape:

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

`After` may summarize the result, but the full binding rule belongs in `brief.md` or `domains/`.

## Projection Indexes

Create projection directories on demand:

```text
history/index.md
history/domains/<domain>.md
history/topics/<topic>.md
history/months/YYYY-MM.md
```

Use one-line entries:

```markdown
- YYYY-MM-DD `<event-slug>`: <brief summary>; current truth `<id or None>`; event `history/events/YYYY/MM/YYYY-MM-DD-<event-slug>.md`.
```

`history/index.md` should list projection entry points and only recent high-signal events. Domain, topic, and month projections are the main routing surface.

## Write Procedure

1. Create `.wingman/memory/history/` and the needed child directories if absent.
2. Write the event body once under `history/events/YYYY/MM/`.
3. Update `history/domains/<primary-domain>.md`.
4. Update related domain projections only when the event genuinely touches those domains.
5. Update relevant topic projections with generic topic names.
6. Update `history/months/YYYY-MM.md`.
7. Update `history/index.md` with projection entry points and recent high-signal entries.
8. Do not rewrite event bodies just because a projection changes.

## Growth Rules

If a projection grows too large, split the projection index, not the event body:

- `history/domains/<domain>/<topic>.md`
- `history/topics/<topic>-<subtopic>.md`
- `history/months/YYYY-MM-wNN.md`

Event bodies remain under `history/events/YYYY/MM/` and are not copied into indexes.

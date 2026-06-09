# Domain Corpus — Index

The canonical vocabulary for building software with AI agents in this repo.
Load entries on demand; do not preload the whole corpus.

## Reading order for new agents

1. `entry.md` — what every corpus entry looks like
2. `index-primitive.md` — what an Index is as a concept (this file IS one)
3. `citation.md` — how entries reference each other and how agents claim use
4. `primitive.md` — atomic capabilities (skills, hooks, CLI commands)
5. `slice.md` — vertical work units that cut through multiple primitives
6. `anti-pattern.md` — documented mistakes with the cost when ignored
7. `tracer-bullet.md` — test entry; uses only citations to entries 1-6
8. `context-density-rule.md` — CDLC compression rule for agent context

## Naming note

`INDEX.md` is the catalog file (this file). The vocabulary entry describing
the **Index concept** lives at `index-primitive.md` — separate slug so that
case-insensitive filesystems (macOS APFS default) do not collapse the two.

## Entries

### Structural primitives (the architecture)

| Slug                 | Concept       | Status     | Kind        |
|----------------------|---------------|------------|-------------|
| `entry.md`           | Entry         | tracer     | primitive   |
| `index-primitive.md` | Index         | tracer     | primitive   |
| `citation.md`        | Citation      | tracer     | primitive   |

### Vocabulary nouns (the working units)

| Slug              | Concept      | Status     | Kind         |
|-------------------|--------------|------------|--------------|
| `primitive.md`    | Primitive    | tracer     | primitive    |
| `slice.md`        | Slice        | tracer     | primitive    |
| `anti-pattern.md` | Anti-Pattern | tracer     | primitive    |

### Test / proof entries

| Slug                | Concept       | Status     | Kind     |
|---------------------|---------------|------------|----------|
| `tracer-bullet.md`  | Tracer Bullet | tracer     | concept  |

### Operating discipline concepts

| Slug                      | Concept              | Status     | Kind    |
|---------------------------|----------------------|------------|---------|
| `context-density-rule.md` | Context Density Rule | canonical  | concept |

## Status legend

- `tracer` — part of the initial tracer-bullet shape, not yet canonical
- `draft` — proposed but unreviewed
- `canonical` — operator-approved; safe to cite without caveat
- `deprecated` — kept for traceability; do not cite for new work

## Growth rules

- Adding a new entry: write the file, add a row above, mark status `draft`
- Promoting `draft` → `canonical`: requires operator approval
- Adding a new **structural primitive** (a 7th brick): requires operator
  approval AND a written rationale for why the existing 6 cannot express
  the new concept
- Renaming an entry: leave a deprecated stub at the old slug citing the new one

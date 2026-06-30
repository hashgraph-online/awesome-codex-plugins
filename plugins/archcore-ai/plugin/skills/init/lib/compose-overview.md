# Architecture-overview composer

Assembles the init capstone: one `architecture-overview` `doc` that orients a
reader in two parts — a structural-facts line + a type/topic index of everything
this init run seeded. Composed in ALL modes, **last**, after every other artifact
is planned. This catalog supplies the body template and the relation-wiring plan;
`SKILL.md` performs the `create_document` and `add_relation` calls.

DISTINCT from the large-mode `top-level-map`: that is a domain table
(`detect-domains.md`); this is the index of the seed plus structural facts.

## When to skip

- The overview indexes the *other* seeded docs. If the run created **zero**
  Tier-1/Tier-2 documents (empty-repo gate exited, or every item was deselected
  at `confirm`), skip it — an index of nothing is noise.
- It is never the only document created. Compose it only when ≥ 1 other doc is in
  the confirmed seed.

## Part 1 — structural-facts orientation line

One line, extracted from signals already collected in the Detect sub-phase. NEVER
prose about what the code "does" — only countable / named facts.

| Token | Source | Format |
|---|---|---|
| modules | `detect-modules.md` module count | `N modules` |
| domains | `detect-domains.md` domain count | `across M domains` (omit if M ≤ 1) |
| language | `detect-stack.md` language line | `TypeScript` (polyglot: ≤ 2, ` + `-joined) |
| framework | `detect-stack.md` Frameworks allowlist | `Next.js` |
| persistence | `detect-stack.md` Persistence + `detect-data-model.md` | `Prisma/PostgreSQL` (ORM/store) |
| test runner | `detect-stack.md` Testing | `vitest` |

Join present tokens with `; `, in row order. Drop any token with no signal —
never pad. Examples:

- `42 modules across 4 domains; TypeScript; Next.js; Prisma/PostgreSQL; vitest`
- `9 modules; Python; FastAPI; SQLAlchemy/PostgreSQL; pytest`
- `7 modules; Go` (no framework/ORM/runner detected — still useful)

Edge cases:

- **Polyglot:** list ≤ 2 languages by source-file majority (`TypeScript + Go`).
- **Monorepo:** counts are the combined workspace totals; the framework token
  names the one in the most `package.json` files, `+N more` if several distinct.
- **Multiple frameworks (single app):** name the primary, `+N more`.

## Part 2 — type/topic index table

One row per artifact actually in the confirmed seed. Keyed by **area + document
type + what it covers** — area/type/topic words ONLY, never a filename or path.

| Seeded artifact | Area | Type | Covers |
|---|---|---|---|
| stack rule | Stack | rule | language, framework, persistence, test runner |
| run guide | Running locally | guide | install / dev / test |
| entry-point inventory | Entry points | doc | HTTP / CLI / worker / cron surfaces |
| public-surface doc | Public surface | doc | routes / exports / commands / skills |
| top-level map (large) | Domains | doc | domain boundaries & sizes |
| data-model doc | Data model | doc | entities & relations |
| integrations doc | Integrations | doc | external services |
| config/env doc | Configuration | doc | env-var names & purpose |
| each hotspot spec | Hotspot: `<module>` | spec | `<module>` contract |
| each imported rule | `<imported topic>` | rule | imported convention |

Emit only rows whose artifact is in the seed. Order: facts (stack, run guide),
structure (entry points, domains), data (data-model, integrations, config), then
hotspots, then imports.

## Rule-5 compliance (precision-rules.md Rule 5)

- The body MUST NOT enumerate `.archcore/` file paths and MUST NOT contain a
  `## Related Documents` / `## References` section. Cross-document links live
  ONLY in the relation graph (Relation wiring below).
- The index therefore names **areas/types/topics**, not paths; `Covers` is a
  topic phrase, not a link.

## Output

- Type `doc`, `directory='architecture'`, `filename='architecture-overview'`,
  `title='Architecture overview'`, `status='accepted'`,
  `tags=['architecture-overview', 'architecture']`.
- **OUTPUT cap: ≤ 150 lines** (realistically 30–50: one fact line + the index).
- `SKILL.md` wires the create:
  `mcp__archcore__create_document(type='doc', filename='architecture-overview', directory='architecture', title='Architecture overview', status='accepted', tags=['architecture-overview', 'architecture'], content=<body>)`.

### Body template

```
{structural-facts orientation line}

| Area | Type | Covers |
|---|---|---|
| Stack | rule | language, framework, persistence, test runner |
| Running locally | guide | install / dev / test |
| Entry points | doc | HTTP / CLI / worker / cron |
| Public surface | doc | routes / exports / commands / skills |
| Data model | doc | entities & relations |
| Integrations | doc | external services |
| Configuration | doc | env-var names & purpose |
| Hotspot: <module> | spec | <module> contract |
```

## Relation wiring

After the overview is created, `SKILL.md` adds these edges with
`mcp__archcore__add_relation`. Edge types are drawn from
`{related, implements, extends, depends_on}`; the init seed is associative, so
every planned edge is `related` (the other three are reserved for synthesis the
SKILL wires elsewhere).

| From | Edge | To | Condition |
|---|---|---|---|
| architecture-overview | related | every other seeded doc (stack rule, run guide, entry-points, public-surface, top-level-map, data-model, integrations, config, each hotspot spec, each cross-cutting rule, each imported doc) | always |
| data-model doc | related | integrations doc | both seeded |
| each hotspot spec | related | top-level-map | top-level-map present (large mode) |
| each hotspot spec | related | entry-points doc | entry-points present (medium / large) |
| each hotspot spec | related | public-surface doc | public-surface present |
| imported rule doc | related | project-stack rule | import yielded a `rule` |

Skip any row whose endpoints were not both created. Roll forward on individual
`add_relation` failure — surface the error, keep the successful edges.

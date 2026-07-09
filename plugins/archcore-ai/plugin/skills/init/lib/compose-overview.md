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
| data-model doc (repo-wide, or one row per per-domain doc in large mode) | Data model[: `<domain>`] | doc | entities & relations |
| integrations doc | Integrations | doc | external services |
| config/env doc | Configuration | doc | env-var names & purpose |
| each hotspot spec (a decomposed flagship's sub-specs each get their own row) | Hotspot: `<module>`[ (`<sub-surface>`)] | spec | `<module>`[ `<sub-surface>`] contract |
| each cross-cutting rule | `<concern>` | rule | cross-cutting convention |
| each imported rule | `<imported topic>` | rule | imported convention |

Emit only rows whose artifact is in the seed. Order: facts (stack, run guide),
structure (entry points, domains), data (data-model, integrations, config), then
hotspots, then cross-cutting rules, then imports.

**Row-collapse (keeps Part 1+2+3 ≤ 150 lines on any repo size).** Large-mode's
per-domain-scaled spec cap (`detect-hotspots.md` "Top-N by mode") and its
every-schema-domain data-model breadth (`detect-data-model.md`) can each produce
dozens of rows on a big repo — the old flat caps could not. For ANY artifact category
that would emit **more than 10 rows** in one confirmed seed (hotspot specs at large
`standard`/`deep`, per-domain data-models when many domains carry a schema, or a
large batch of imported modular-rule docs): list the first 10 by rank/name
(deterministic — highest-ranked hotspot first, alphabetical for data-models/imports),
then collapse the remainder into ONE summary row: `<Category>: +<N> more` — same
`Type`, `Covers` = `<N> additional <unit>`. This is the same "index, not directory"
discipline Part 3 already applies to its register, extended to Part 2 so a 24-domain
`deep` run cannot itself blow the cap it exists to guard.

## Part 3 — hotspot register (ranked but not specced)

The hotspot ranking (`detect-hotspots.md`) surfaces more load-bearing modules than
the per-mode spec cap synthesizes. List the remainder here — a compact register so
the full map of where logic concentrates is visible on day one at ~0 token cost, and
the user knows exactly what to `/archcore:capture` next.

- One line per ranked hotspot **beyond** the spec cap, **capped at 12 rows**
  (highest-ranked first): source module (area + short name) + its qualifying signal +
  `→ /archcore:capture <path>`. If the remainder exceeds 12, list the top 12 and close
  with one summary line — `+<N> more ranked candidates — /archcore:capture on demand or
  re-run at a higher --depth.` Never enumerate an unbounded remainder: Part 1 + 2 + 3
  combined MUST stay inside the ≤ 150-line OUTPUT cap regardless of repo size.
- Names **source** modules and paths, not `.archcore/` documents — pointing at code
  the user can act on, never enumerating other seeded docs.
- Omit the section entirely when every ranked hotspot got a full spec.

## Rule-5 compliance (precision-rules.md Rule 5)

- The body MUST NOT enumerate `.archcore/` file paths and MUST NOT contain a
  `## Related Documents` / `## References` section. Cross-document links live
  ONLY in the relation graph (Relation wiring below).
- The index therefore names **areas/types/topics**, not paths; `Covers` is a
  topic phrase, not a link.
- Part 3's hotspot register points at **source** modules/paths and
  `/archcore:capture` targets — it lists code to act on, not `.archcore/` docs, so
  it stays within Rule 5.

## Output

- Type `doc`, `directory='architecture'`, `filename='architecture-overview'`,
  `title='Architecture overview'`, `status='accepted'`,
  `tags=['architecture-overview', 'architecture']`.
- **OUTPUT cap: ≤ 150 lines** (realistically 30–50 on small/medium; up to ~90 on a
  large `deep` run with the row-collapse rule above applied — never uncapped).
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
| <concern> | rule | cross-cutting convention |

Ranked hotspots not yet specced (run /archcore:capture to document):
- <area>: <module> — <signal> → /archcore:capture <path>
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
| a decomposed flagship's sub-specs | related | each other (pairwise) | flagship split into ≥ 2 sub-specs (`detect-hotspots.md` "Flagship specs") |
| each hotspot spec | related | the convention rule(s) it must honor + sibling specs in its tree | **`deep` depth only** (enriched relations) |

Skip any row whose endpoints were not both created. Roll forward on individual
`add_relation` failure — surface the error, keep the successful edges.

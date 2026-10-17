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
| each document converted from authored sources | `<topic>` | its type | `<topic>` |

Emit only rows whose artifact is in the seed. Order: facts (stack, run guide),
structure (entry points, domains), data (data-model, integrations, config), then
hotspots, then cross-cutting rules, then documents converted from authored sources.

**Row-collapse (keeps Part 1+2+3 ≤ 150 lines on any repo size).** The pool-scaled spec
budget (`detect-hotspots.md` "Spec budget by coverage rate") and large mode's
every-schema-domain data-model breadth (`detect-data-model.md`) can each produce
dozens of rows on a big repo — the superseded flat caps could not. For ANY artifact category
that would emit **more than 10 rows** in one confirmed seed (hotspot specs at large
`standard`/`deep`, per-domain data-models when many domains carry a schema, or a
large batch of documents converted from authored sources): list the first 10 by rank/name
(deterministic — highest-ranked hotspot first, alphabetical for data-models and converted documents),
then collapse the remainder into ONE summary row: `<Category>: +<N> more` — same
`Type`, `Covers` = `<N> additional <unit>`. This is the same "index, not directory"
discipline Part 3 already applies to its register, extended to Part 2 so a 24-domain
`deep` run cannot itself blow the cap it exists to guard.

## Part 3 — hotspot register (ranked but not specced)

The hotspot ranking (`detect-hotspots.md`) surfaces more load-bearing modules than the
depth's spec budget synthesizes. List the remainder here — a compact register so
the full map of where logic concentrates is visible on day one at ~0 token cost, and
the user knows exactly what to `/archcore:document` next.

- One line per ranked hotspot **beyond** the spec budget, **capped at 12 rows**
  (highest-ranked first): source module (area + short name) + its qualifying signal +
  `→ /archcore:document <path>`. If the remainder exceeds 12, list the top 12 and close
  with one summary line — `+<N> more ranked candidates — /archcore:document on demand or
  re-run and toggle a higher depth.` Never enumerate an unbounded remainder: Part 1 + 2 + 3
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
  `/archcore:document` targets — it lists code to act on, not `.archcore/` docs, so
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

Ranked hotspots not yet specced (run /archcore:document to document):
- <area>: <module> — <signal> → /archcore:document <path>
```

## Relation wiring

Use these rows to find candidates. Apply `skills/_shared/relation-authoring.md`
before `mcp__archcore__add_relation`. The table proposes navigation links;
when the endpoint claims establish a more specific type, use that type without
an extra `related` for the same purpose. Preview structural candidates before
confirm; resolve their claims from composed bodies before writing each edge.

| From | Edge | To | Condition |
|---|---|---|---|
| architecture-overview | related | each seeded document indexed by its area/type/topic row | index navigation, including documents covered by a collapsed row |
| data-model doc | related | integrations doc | the integration exchanges an entity described by the data model |
| each hotspot spec | related | top-level-map | the map locates the module whose contract the spec owns |
| each hotspot spec | related | entry-points doc | a named entry point invokes the specified module |
| each hotspot spec | related | public-surface doc | the inventory describes the boundary owned by this spec |
| converted `rule` | related | project-stack rule | the converted rule constrains a named stack choice |
| a decomposed flagship's sub-spec | related | another sub-spec | their shared boundary requires joint reading; splitting alone creates no edge |
| each hotspot spec | related | an applicable convention or another spec | **`deep` depth only**; a named constraint or shared contract justifies the link |

Skip any row whose endpoints were not both created or whose claim is unsupported.
Do not build a clique from the confirmed seed. Roll forward on individual
`add_relation` failure — surface the error, keep the successful edges.

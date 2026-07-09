# Data-model detection catalog

Reference data for `/archcore:init` detect sub-phase. SKILL.md wires the `create_document` call; this file supplies detection logic plus the `## Output` template.

## What it detects

A DATA MODEL = the persistent entities the system stores and the relations declared between them — regardless of language, domain, or storage tech. The declaration mechanism is whatever the repo actually uses: an ORM/ODM, class annotations, attributes, macros, a schema DSL, GraphQL SDL, migration DDL, or an in-house data layer. Capture entity NAMES and their relation kinds only — never columns, types, defaults, indexes, or row/seed data.

## How to find it (any codebase)

1. From one manifest pass (shared with `detect-stack` / `detect-config`), read the most-depended direct dependencies and the entry file's imports to learn which persistence mechanism is actually in use — do not assume one from training priors.
2. Glob the repo for that mechanism's entity declarations: schema files, model/entity classes, annotated/attributed types, schema-DSL blocks, GraphQL SDL types, or `CREATE TABLE` in migrations. Schemas are routinely split across many files — union across all matches.
3. For each declaration, extract the entity/table NAME and its relation kind to other named entities (`1:N`, `N:1`, `N:M`, `1:1`); a field name appears only when it is the PK/FK that names a relation.
4. Disambiguate shared markers by manifest/language. The `@Entity` annotation is not TypeORM-only: TypeScript + a `typeorm` dep → TypeORM; Java/Kotlin + `jakarta.persistence`/Hibernate → JPA/Hibernate; Android + `androidx.room` → Room. Do not treat a gRPC `*.proto` wire contract as the persistence model when storage lives elsewhere, and do not match every `class X(Base)`.
5. Set the orientation line to the mechanism you actually observed (e.g. "EF Core schema", "Mongoose schema", "JPA/Hibernate schema"). A bare ORM dependency with NO declaration present is not a match — there is no model surface to extract.
6. Cap at ~15 entities, most-connected first (most relations), ties broken alphabetically — deterministic across runs. If more exist, append a final row `| +N more |  |` and stop; do not paginate.
7. Emit a signal only on positive evidence; when no candidate is unambiguous, prefer omission over a guess — never invent.

## Common signals (non-exhaustive examples)

These are non-exhaustive examples to orient pattern-matching — absence from this list is NOT absence of signal; fall back to the method above for anything not shown.

| Declaration marker | Mechanism | Entity name from | Relation markers |
|---|---|---|---|
| `model <Name> {` in `schema.prisma` | Prisma | `model <Name>` | list `Other[]` = 1:N; scalar `Other` + `@relation` = N:1; both-side list = N:M |
| `pgTable(`/`sqliteTable(`/`mysqlTable(` | Drizzle | `pgTable("<table>")` const | `references(() => other.id)`; `relations()` `many()`/`one()` |
| `@Entity` class (disambiguate by manifest) | TypeORM / JPA-Hibernate / Room | annotated class | `@OneToMany`/`@ManyToOne`/`@ManyToMany`/`@OneToOne` |
| `<Model>.init(` / `sequelize.define(` | Sequelize | `define("<Name>")` / `class X extends Model` | `hasMany`/`belongsTo`/`belongsToMany`/`hasOne` |
| `declarative_base(` / `class X(Base)` / `Mapped[` | SQLAlchemy | `__tablename__` / `Base` subclass | `relationship(...)` + `ForeignKey("other.id")` |
| `class X(models.Model)` | Django ORM | the class | `ForeignKey`=N:1; `ManyToManyField`=N:M; `OneToOneField`=1:1 |
| `use Ecto.Schema` + `schema "<table>" do` | Ecto | `schema "<table>"` | `has_many`/`belongs_to`/`many_to_many`/`has_one` |
| `db/schema.rb` `create_table` + `app/models/*.rb` | ActiveRecord | `create_table "<name>"` / model class | `has_many`/`belongs_to`/`has_and_belongs_to_many`/`has_one` |
| Go struct fields tagged `` gorm:"..." `` | GORM | struct type name | slice/embedded field + `` gorm:"foreignKey:…" `` |
| `CREATE TABLE` in `*.sql` under `migrations/` | raw SQL DDL | `CREATE TABLE <name>` | `REFERENCES <other>` / `FOREIGN KEY` = N:1 |
| `message <Name> {` in `*.proto` | Protobuf (only if it is the storage model) | `message <Name>` | nested/`repeated <Other>` = 1:N composition |

**NAMES ONLY.** MUST NOT dump full column lists, types, defaults, indexes, or any row/seed data.

## Output

- Type `doc`, directory `architecture`, filename `data-model`, title `Data model`, status `accepted`, tags `['data-model','architecture']`.
- **Body cap: ≤ 40 lines.** Orientation line + entity table + one relations line. No prose paragraphs.

```
{ORM/format} schema · {N} entities.

| Entity | Key relations |
|--------|---------------|
| User   | 1:N Post; N:M Role |
| Post   | N:1 User; 1:N Comment |
| Role   | N:M User |
| +12 more |  |

Relations: User↔Role many-to-many via `user_roles`; Post and Comment belong to User.
```

Drop the relations line when no cross-entity relation is detected (a flat `*.proto` or single-table schema). Never pad it.

## When to skip

No declaration resolves to at least one named entity → produce nothing. Do NOT emit a placeholder/empty data-model doc. Surface once in the init closing message:

> No data model detected (no ORM schema, SQL migrations, `.proto`, or equivalent declaration). Run `/archcore:capture` on the data layer when one exists.

## Edge cases

- **Multiple mechanisms in one repo** (e.g. Prisma + raw SQL, or TypeORM beside Drizzle) → one combined doc. Add a `Source` column and name both in the orientation line (`Prisma + Drizzle schema · {N} entities.`). Never create two data-model docs.
- **Schema split across files** → union entities across all matched files, dedupe by name, count once.
- **Monorepo / per-app schemas** → small/medium: union into one doc, prefix ambiguous entity rows with the app slug. **Large mode: emit one data-model doc per domain that owns a schema — for EVERY domain with a detectable schema, not only the domains selected in `SKILL.md` Step A.0.** Data-model breadth is decoupled from the domain-selection dialog: that dialog focuses which domains get hotspot-*spec* priority (`detect-hotspots.md`'s per-domain floor); a data-model doc is names-only and cheap enough that it costs nothing to seed for every schema-bearing domain regardless of selection. Directory `architecture/<domain-slug>`, filename `<domain-slug>-data-model` (the slug prefix keeps per-domain docs from colliding; init dedupes these by filename, not the repo-wide `data-model` tag, so a newly-selected domain still gets its doc). A domain with NO detectable schema gets no data-model doc but still appears as a row in the `top-level-map` (`detect-domains.md`) — the map is never filtered by data-model presence, so an unseeded domain stays visible rather than silently dropped.

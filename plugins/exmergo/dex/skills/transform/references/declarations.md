# Declarations: what a model means

A declaration is a structured statement of what a model means: what one row is,
which rows are in, what each column is, and what was assumed. It travels in the
same payload as the edits, beside them, and works on `transform plan` and on
`semantic define|update|plan`. What you must and must not do is in `SKILL.md`;
this file is the payload's shape and what each field becomes.

## The payload

```json
{"edits": [...],
 "declarations": [
   {"model": "fct_orders",
    "description": "One row per order placed through the web store.",
    "grain": ["order_id"],
    "population": {
      "rule": "Completed and shipped orders; cancelled and returned orders are excluded.",
      "filters": [{"column": "status", "excludes": ["cancelled", "returned"]}]
    },
    "columns": {
      "order_id":    {"role": "key", "description": "..."},
      "customer_id": {"role": "foreign_key", "references": "dim_customers.customer_id", "null_rule": "never"},
      "ordered_at":  {"role": "time", "description": "..."},
      "order_total": {"role": "measure", "aggregation": "sum", "additivity": "additive", "unit": "currency:USD"},
      "share_of_day":{"role": "measure", "aggregation": "sum", "additivity": "non_additive", "unit": "fraction"}
    },
    "assumptions": [
      {"decision": "Which order statuses count as revenue",
       "chosen": "completed and shipped",
       "evidence": "precedent",
       "detail": "every model reading stg_orders.status excludes cancelled and returned"}
    ]}
 ]}
```

`edits` may be left out when the payload only declares models that already
exist.

## Fields

| Field | Values |
|---|---|
| `role` | `key`, `foreign_key`, `dimension`, `time`, `measure`, `attribute` |
| `additivity` | `additive`; `semi_additive` (does not add across time: a balance, a running or season-to-date total); `non_additive` (a ratio, a share, a distinct count) |
| `unit` | `currency:<ISO code>`, `fraction` (0 to 1), `percent` (0 to 100), `count`, or a plain unit such as `days` |
| `null_rule` | `never`, or a sentence saying what NULL means in this column |
| `references` | `<model>.<column>`, a model, seed or snapshot the project has, or one an installed package has (a package's staging model, say) where the project defines none of that name |
| `population.parent` | `{"model": <model, seed or snapshot, the project's or an installed package's>, "key": {<output column>: <parent column>, ...}}`: the entity the model holds one row per. Use it when every parent should be in the model (a parent with no children included), so verification counts the parents missing from it, and the plan warns when the SQL is driven from a relation unrelated to it (`check: population_parent`). A population that only has a `rule` is `prose` under `population_contract`: nothing can run it |
| `evidence` | `request` (what the request settles), `contract` (what the project's declared columns, tests or metric filters settle), `precedent` (how sibling models decide the same thing), `data` (what profiling showed about the data, never the intended population or NULL policy), `default` (the conventional analytics-engineering choice, including a reasonable choice where wording leaves the question open). Name `request` or `contract` only when that source settles the choice: "per account" alone does not say whether accounts without events belong, so that choice is a `default` |

| `assumptions[].column` | optional: the output or source column the decision governs. `data.identifier_conversions` reads it: a conversion that drops, merges or respells identifiers of a column an assumption names is `declared` rather than `undeclared` (#861). Use it when a repair excludes identifiers of a second scheme or merges `7` and `007` on purpose, with the evidence that settles it. Join coverage reads it too: on an INNER join used as a filter, an assumption naming the driving key column (or a `population.filters` entry on it) says the unmatched rows are meant to be dropped, so the join is `satisfied` rather than `join_orphans` (#1162) |

A field Dex does not know is refused by name, so a typo cannot silently drop
part of a declaration.

## What it renders into

The declaration is written into the model's **existing** YAML entry, wherever in
the project it lives. A model with no entry gets one beside its SQL, named for
it, which is where the scaffold puts one. Dex never writes a second entry for a
model, which dbt refuses.

One model has no entry to write into: a project override of a package model the
package documents (`prerequisite-repairs.md`). dbt gives the package's entry to
the override, so any project entry is a second one. The declaration is refused,
naming the package's file and the project's, and the override owes none: declare
the models that read it.

| Declared | Written as |
|---|---|
| `description` (model or column) | dbt's own `description` |
| a single-column `grain` | `data_tests: [unique, not_null]` on that column |
| `null_rule: never` | `not_null` on that column |
| `foreign_key` with `references` | a `relationships` test (`arguments: {to, field}`) |
| `grain`, `population`, `assumptions` | model `config.meta.dex` |
| `role`, `null_rule`, `aggregation`, `additivity`, `unit`, `references` | column `config.meta.dex` |

A test the column already lists is kept as written, under the key it already
uses. Declaring again merges: a key the new declaration states replaces the old
one, and a key it leaves out is kept. `population` merges one level further, so
adding a `parent` keeps the `rule` and `filters` declared earlier. Every byte outside the keys above, comments
included, stays where it was.

### A versioned model

A model with native dbt versions has one YAML entry with a `versions:` list.
Name one version by its label, `"model": "dim_teams.v2"`. The declaration then
renders into that item of `versions:`:

- the description and model facts go to the version's `description` and
  `config.meta.dex`;
- the column facts go to the version's own column entries.

The bare `"model": "dim_teams"` renders into the shared top-level entry, which
every version inherits. A version's file stem (`dim_teams_v2`) is refused,
naming the label, because a declaration under that name would add a second,
plain entry.

Two dbt rules decide what the version holds:

- **Lists concatenate.** dbt merges a version's `config` into the shared one,
  concatenating lists and merging mappings. A model-level fact (`grain`,
  `population`, `assumptions`, `history`) stated at both levels would be read
  back as neither, so one stated at the other level is refused, naming the move.
- **An inherited column is replaced, not merged.** A version's own column entry
  replaces the inherited one wholesale. A fact about an inherited column is
  therefore written as an override: the column joins the version's `exclude`
  list, and the version gets its own entry, carrying the inherited description
  and tests forward. A plan warning names each one. A fact the inherited entry
  already states changes nothing.

A `references` to `dim_teams.v2.team_id` renders `to: ref('dim_teams', v=2)`.
Every reader below reads a version as dbt builds it, under its label. The
workflow is in `model-versions.md`.

## A parent from an installed package

Most marts read a package's staging models (Fivetran's, the dbt-labs
packages'), and the entity a mart holds one row per is usually one of them.
`population.parent` and `references` name it by its model name, as `ref()` does,
and the declaration lives on the project's own model: nothing under the packages
directory is written.

- **The project wins.** The project's models, seeds and snapshots are looked up
  first, so a project override of a package model is the parent, as it is for
  `ref()` and for `transform references`.
- **Columns.** The parent column is checked against the package model's SQL,
  then against the compiled SQL in the project's manifest. A staging model that
  lists its columns through a macro, with no compiled manifest yet, cannot be
  read: the column is a warning naming the package, not a refusal, and
  `transform build --verify` reads the built relation. A column the package
  model provably lacks is refused, naming the package and its file.
- **The plan-time driver check** (`check: population_parent`) walks the
  package's own `ref()` lineage, so a mart driven from the package's parts table
  under a declared package conversations parent is `contradicted`. Column-only
  macros (`fill_staging_columns`, `dbt_utils.star`, the cross-database type and
  date macros) do not hide a relation; any other macro in the lineage, such as a
  `union_data` that reads relations itself, makes the check `unchecked`.
- **At build time** the parent population is measured on the package model's
  relation. A package that sets `+schema` builds into `<dev schema>_<name>`, and
  `--verify` reads those namespaces too, since the dev target wrote them.

## What is checked

Refused, with the fix named:

- a model the project and the plan do not have;
- a declared column or grain column the model's SELECT list does not produce
  (skipped, with a warning, when the SELECT list cannot be read statically);
- a `references` target that is not `<model>.<column>`, names nothing, or names
  a column the target does not produce;
- an unknown `role`, `additivity` or `evidence`, or an unknown field;
- a population filter listing values on a column that looks like personal data;
- a `population.parent` naming no model, seed or snapshot of the project or an
  installed package, naming the model itself, mapping an output column the
  model does not produce, or a parent column the parent does not produce. A
  source is not a parent: name the staging model that selects from it (the
  refusal says so where the name is a source table);
- a `population.parent` or `references` naming a package model the project's
  `dbt_project.yml` disables with no project model of that name;
- a declaration on a project override of a package model the package documents,
  naming both files. A hand-written `schema_yml` entry for that model is refused
  the same way, before dbt parses.

Warned, never refused: a `population.parent` key that is not the declared
grain, a missing description, grain, population, assumptions or
column role (one warning per missing field), a measure without its aggregation,
additivity or unit, an assumption missing its decision, chosen value or evidence,
and a model the plan writes SQL for with no declaration at all (except an
override of a package-documented model, which can take none). Where the SQL
already implies the decision, the warning names it: `fct_orders declares no
population rule; its SQL filters on status`.

A plan carrying declarations or `schema_yml` edits is parsed by dbt against a
throwaway copy of the post-change project before it is stored, and degrades to a
named warning where dbt is not installed.

## `data.declarations`: drafted, declared, missing

For every model a plan creates, edits or declares, the plan envelope carries
`data.declarations.<model>` with three parts. It is computed from the `.dex/`
cache and the post-change repository only, so it scans nothing and costs nothing
on any connector.

```json
{"drafted": {
   "grain": {"value": ["order_id"],
             "evidence": "order_id is a proven unique key of raw_orders, carried through unchanged"},
   "columns": {
     "customer_id": {"from": "raw_orders.customer_id",
                     "role": {"value": "foreign_key", "evidence": "the join ... was verified, no orphans"},
                     "references": {"value": "customers.customer_id", "evidence": "..."},
                     "nullable": {"value": false, "evidence": "..."}},
     "region": {"from": "customers.region",
                "nullable": {"value": true, "evidence": "it comes from the outer side of the left join ..."}},
     "discount_rate": {"from": "raw_orders.discount_rate",
                       "unit": {"value": "fraction", "evidence": "... a hypothesis about the unit, not a certified one"}}},
   "domains": [{"column": "raw_orders.status", "used_in": ["where"],
                "values": ["shipped", "cancelled"], "elided": 0, "complete": true}],
   "precedent": [{"column": "raw_orders.status",
                  "this_model": [{"usage": "where", "expression": "status <> 'cancelled'"}],
                  "readers": 5,
                  "groups": [{"usage": "where", "expression": "NOT status IN ('cancelled', 'returned')",
                              "count": 4, "models": ["fct_revenue", "..."], "elided_models": 0},
                             {"usage": "none", "count": 1, "models": ["fct_gross_orders"], "elided_models": 0}],
                  "elided_groups": 0, "completeness": "complete", "limits": []}],
   "inputs": [{"relation": "raw_orders", "profiled": true, "identifier": "shop.main.raw_orders"}],
   "incomplete": []},
 "declared": {"description": "...", "grain": ["order_id"], "population": {...}, "columns": {...}},
 "missing": ["assumptions", "columns.amount.unit"]}
```

`transform plan` never writes `drafted` into the project; only `transform declare`
does, and only the subset described under "Declaring models that already exist".
Each fact carries the `evidence` it rests on, and a fact the cache cannot support is left out rather than guessed:

| Drafted | When |
|---|---|
| `grain` | the `GROUP BY` keys when the model aggregates; otherwise a key the driving relation's profile *proved* unique, selected unchanged, with every join an equality on a key proven unique on its joined side. Any other join, a right or full join, a set operation or an `UNNEST` gives `{"value": null, "withheld": "<why>"}` |
| `columns.<c>.from` | the upstream `relation.column` a column passes through from unchanged, followed through CTEs |
| `columns.<c>.role` | `key` for a single-column drafted grain; `foreign_key`, with `references`, for a column carrying a join `explore relationships --verify` measured with no orphans. A join measured with orphans would fail the `relationships` test a `references` renders, so it is `references: {"value": null, "withheld": "<the orphan rate>"}` instead. Where the column joins cleanly to several relations (the raw table, its staging model, a dimension), a parent whose column is not unique and the model itself are passed over, a model of this project wins over a seed or snapshot and those over a raw table, and the model nearest this one in the project tree breaks a tie; `evidence` names the other clean parents. A warehouse that reports `STG_CUSTOMERS` resolves to the project's `stg_customers`. The joins read are the input column's; where those reach only raw tables (a staging model over a source, on a warehouse whose build lives in another schema) and the model is already built and profiled, the built relation's own clean joins are read instead, so `stg_orders.customer_id` references `stg_customers` |
| `columns.<c>.pii` | the upstream column's PII flag, category and confidence |
| `columns.<c>.nullable` | `true` on the outer side of a left, right or full join whatever the upstream NULL rate; otherwise from the upstream NULL fraction |
| `columns.<c>.additivity` | `semi_additive` where `explore profile --check-cumulative` found the upstream column never decreasing |
| `columns.<c>.unit` | `fraction` for a non-integer column profiled entirely in 0 to 1; `percent` for one named like a percentage profiled in 0 to 100. A hypothesis, never a certified unit |
| `domains` | the cached value domain of each column the SQL filters (`where`, `having`, `qualify`) or branches on (`case`), capped by `profile_value_domain_cap` with the rest counted in `elided`. A PII-flagged column's values are never drafted: `values` is null and `withheld` says why |
| `precedent` | for each upstream column the SQL filters, branches on or aggregates, what the project's other models reading the same relation do with it: `this_model` (this model's own uses), then `groups`, one per filter conjunct (`where`, `having`, `qualify`), `CASE` condition (`case`) or aggregation (`aggregation`), with `count` and `models`, and `usage: none` for readers that keep every value. See below |
| `inputs` | every relation the SQL reads; one the cache has not profiled is `profiled: false` with the `command` that would profile it |
| `population_parent` | for a model that declares no `population.parent`, the entity dex drafts it is about (#1228), with `evidence`, `supported_by`, `detail`, `alternatives`, `driving_relation` and `drives_from_parent`; `{"value": null, "withheld": "<why>"}` where nothing qualifies. See "A drafted parent" below |
| `incomplete` | why part of the SQL was not read: a macro or jinja block, a set operation, an unqualified column in a multi-relation select |

`declared` is what the model's YAML entry says once the plan lands: this
payload's declaration merged over whatever the entry already carried. `missing`
names each intent field nobody has supplied (`description`, `grain`,
`population`, `assumptions`, `columns.<c>.role`, and a measure's `aggregation`,
`additivity` and `unit`), and each is also a warning. Where the drafted grain and
the declared one disagree, a warning says so. An override of a package model the
package documents owes nothing: its `missing` is empty, and `package_documented`
names the `package` and its `package_entry`, the YAML file that documents it.

### Precedent

Precedent is evidence, not a rule. Every group is listed, conflicting ones
included, and none is called the majority: four models excluding cancelled orders
and one keeping them is the case worth reading before writing a sixth. Decide,
then record the decision in the declaration with `evidence: precedent`, naming the
models you followed.

- A column is the same column only where the SQL resolves to it through its
  aliases and CTEs. `status` on another relation is not precedent.
- Readers are the models that `ref()` or `source()` the relation directly. A
  model reading a downstream model built from it is not counted.
- Groups are by sqlglot's rendering of each fragment, not by logical
  equivalence: `status not in ('a', 'b')` and `status <> 'a' and status <> 'b'`
  are two groups.
- `completeness` uses the `transform references` vocabulary. It is `incomplete`
  when a reader could not be read statically (a macro, a jinja block), when a
  `ref()` could not be resolved, or when a use of the column could not be traced;
  each reason is in `limits`, and such a reader is never counted as one that
  keeps every value.
- Capped at 10 groups and 5 model names per group, with the rest counted in
  `elided_groups` and `elided_models`.
  `transform references <model.column> --usage --full` returns the same answer
  uncapped, before any SQL is written.

### Literals the column never holds

Where the SQL compares a column directly to literals (`=`, `<>`, `IN`, `NOT IN`)
and the cache holds that column's complete value domain, a literal the domain does
not contain is a warning, naming any value that matches it ignoring case and
whitespace ("compares stg_orders.status to 'Cancelled', which none of its 3
profiled values is; 'cancelled' matches it ignoring case and whitespace"). It is
silent when the domain was capped (`elided` above 0), when the column carries a
PII flag at any confidence, when the comparison wraps the column in a function,
and when the literal's type differs from the column's values. Never a refusal: a
filter on a value that does not exist yet is sometimes the intent.

### Contradictions

On a model that already exists, `data.declarations.<model>.contradictions` lists
each declared rule this plan's SQL and the post-change declaration disagree on.
Each entry is also a warning. A new model has no prior to compare, so only
`population_parent` applies to it and it carries the key only when that rule
reports something; an empty list means nothing was contradicted.

```json
{"check": "population", "status": "contradicted",
 "rule": "population.filters status excludes ['cancelled']", "column": "status",
 "stale": "sql", "prior": "status <> 'cancelled'", "preexisting": false,
 "row_delta": 2}
```

| `check` | Fires when |
|---|---|
| `population` | the predicate implementing a declared `population.filters` entry is removed or changes the values it keeps. `excludes` is met by `<>`/`NOT IN` on exactly those values, or by an `IN` list that leaves them out; `includes` by `=`/`IN` on exactly those values |
| `population_parent` | the model declares `population.parent` and the relation driving it has no `ref()` lineage to that parent, in either direction. Fires on a new model too. A RIGHT, FULL or CROSS join that keeps the parent's rows is silent. `authored` names the driver and `parent` the parent. A package parent or driver is read through the package's own `ref()` lineage. A driver or lineage dex cannot read (a macro that may read a relation, `{% if %}`, a set operation, a literal name, packages not installed) is `unchecked` |
| `grain` | the drafted grain (the `GROUP BY` keys, or a carried key) differs from the declared grain, or a declared grain column leaves the SELECT list |
| `columns` | a column whose declaration states a role, unit, additivity or another `config.meta.dex` field leaves the SELECT list. It names what the column was declared as, beside the plain `schema.yml` divergence warning |
| `additivity` | the model takes `SUM` of an upstream column its own model declares `semi_additive` or `non_additive`, or `AVG` of one declared `non_additive` with a `fraction` or `percent` unit. `declared_on` names that upstream model. A running total the cumulative check found and nothing declares fires too, without `declared_on`; a column declared `additive` never does |

Three states are compared: the prior SQL and declaration, the authored SQL and
the post-change declaration, and what this plan changed between them.

| What the plan did | `stale` |
|---|---|
| changed the SQL, left the declaration, and they now disagree | `sql` |
| changed the declaration, left the SQL, and they now disagree | `declaration` (or the plan is half done) |
| changed both, and they still disagree | `either` |
| changed both, and they agree | nothing reported |
| touched neither side of a rule that already disagreed | nothing reported |

`preexisting: true` marks a rule that already disagreed before this plan and
that this edit touches. `status: unchecked` (with `reason`, and no `stale`) is a
rule the plan touched that Dex could not read the SQL for: a macro or jinja
predicate, a function around the column (`lower(status) <> 'x'`), a subquery, a
set operation, or a grain no key proves. It never claims the rule was removed.
Comparison is on sqlglot's reading of the SQL, so a reformat, an alias rename,
`!=` for `<>`, and `NOT IN ('a', 'b')` for `<> 'a' AND <> 'b'` are silent.

A contradicted population is paired with row attribution's report of the same
predicate. Where attribution measured it (DuckDB, or `--attribute-rows` with the
cost handshake on a billed connector), `row_delta` is its delta and the warning
cites it; where it did not, the warning carries attribution's reason. Nothing
here runs a query of its own, refuses a plan, or blocks apply.

### A drafted parent

Most models declare no `population.parent`, so the population checks above
would never run on them. For each such model the plan drafts one (#1228), keyed
by the model's grain (the declared grain, else a uniqueness test on the model,
else the grain the SQL proves; a `GROUP BY` proves one with no cache), from four
kinds of evidence, strongest first:

| `evidence` | The candidate |
|---|---|
| `unique_key` | a model, seed or snapshot of the project or an installed package whose `unique` or combination test, declared grain, or profiled key is the grain, column for column |
| `relationship` | the parent a `relationships` test, a declared `references` or a verified orphan-free join names for each grain column, on this model or on the column the grain is carried from |
| `description` | the noun after "one row per" in the description names the candidate, which carries the grain columns |
| `driving` | the relation that drives the SQL, when the grain is carried from it unchanged and the model does not aggregate it |

A source is never a candidate (it is the raw table under a staging model), nor
is the model itself, anything downstream of it, or a time spine or model
generated in SQL (#988). The best tier wins, then the most tiers agreeing, then
an ancestor of the model, then the candidate the others descend from;
`alternatives` lists the runners-up. A declared `population.parent` always wins
and is never drafted over.

```json
"population_parent": {
  "value": {"model": "stg_conversations", "key": {"conversation_id": "conversation_id"}},
  "evidence": "unique_key", "supported_by": ["unique_key", "relationship"],
  "detail": "conversation_id is unique on stg_conversations (a unique test); ...",
  "drafted": true, "driving_relation": "stg_parts", "drives_from_parent": false}
```

A warning names the draft. `drives_from_parent: false` means the rows come from
a relation outside the parent's lineage (the child table), so the model holds
whatever keys that table holds. The draft is never written into the project.
`transform build --verify` measures the built model against it; see
"Measured against a drafted parent" below.

### Change scope

`data.change_scope` (#1115) is what an edit to an existing model changes beside
its request, read from both versions with no query: whether the row population
moves, and which outputs are removed, retyped, re-aggregated or re-NULLed. It is
held to the assumptions above, not to a new field: a change is `declared` where
an assumption's `column` names a column it governs, and `undeclared` (a warning)
otherwise. So the scope of a repair is stated with what already exists:

- a broad filter: an assumption naming the filter column on each model it
  changes, and a population `rule` (or `filters` on a column the model carries)
  on a roster it deliberately keeps or drops. `data.change_scope.population`
  lists the models whose population changed and the ones kept;
- a coverage repair (missing days or accounts): the spine or parent it joins
  is a population change (`join_added`, often `group_by_changed`), settled by an
  assumption naming the grain column (`visit_date`: every day in the range).
  `count(*)` over a left join counts one on an empty row, so moving to
  `count(<child key>)` is an `aggregate_changed` to record on the count column
  (an empty window counts zero, as before), and a `coalesce` added to an average
  is a `null_handling_changed` that changes what NULL meant;
- an inferred default stays `default`: retaining parents without children,
  keeping a roster whole when the request names only metrics. The assumption's
  `detail` says why in one line and travels in `data.decisions`;
- re-driving a model (#1228): the relations its rows come from change, or its
  declared `population.parent` is removed or replaced. That is a `redriven`
  population change (`reason: redriven`), judged against the applied model or,
  for a model only an earlier unapplied plan wrote, that plan (`against:
  earlier_plan`). It is `declared` only by an assumption on the model at
  `request` or `contract` tier; a `precedent`, `data` or `default` one leaves it
  `undeclared`, since which entity a model is about is never settled by
  observed counts. NULL aggregates on a parent-driven model point at the join
  key, not at a new driving relation.

The full record is in `commands.md` under `transform plan`.

## Declaring models that already exist: `transform declare`

A plan declares the models it creates or edits. Models written before
declarations existed have none, and dex never adds them unasked. To adopt them,
select some and let one plan propose what dex already measured:

```bash
dex transform declare stg_orders,stg_customers fct_orders
dex transform declare --edits-file intent.json   # every model, with intent
```

The selector is the one `maintain verify` takes: model names, repeatable and
comma-separated, case-insensitive, and none for every model. It is read from the
repository, so nothing is compiled. A versioned model is selected by version:
`dim_teams.v2` (or its file stem `dim_teams_v2`) selects one, and the bare
`dim_teams` selects every version. Each is proposed into its own `versions:` item.

**What is proposed.** Per model, only the fields its YAML does not already state:

| Drafted fact | Written as | Only when |
| --- | --- | --- |
| `grain` | `config.meta.dex.grain`, plus `unique` and `not_null` on a single column | no grain is declared |
| `role: key` | the column's `role` | the column has no role |
| `role: foreign_key` | the column's `role` | the column has no role |
| `references` | `references` and a `relationships` test | the column's role is absent or `foreign_key`, and the parent is a model, seed or snapshot of this project or of an installed package (a join verified to a raw table stays in `drafted`) |
| `additivity: semi_additive` | the column's `additivity` | no additivity is declared |

The unit shape, NULL facts, PII flags and value domains are evidence, not
declarations. They stay in `data.declarations.<model>.drafted` and are never
written. Intent (`description`, `population`, `assumptions`) is never drafted.

**Supplied intent.** The payload is the `transform plan` payload with
`declarations` only (`edits` are refused; SQL changes go through `transform plan`).
A supplied declaration wins over the draft field by field, and its model is
considered first. A supplied model the selector does not select is refused, and
so is a malformed one, exactly as in `transform plan`.

**Each model is accounted for.** `data.proposed` lists each model in the plan with
`fields` (every drafted fact written, with its evidence) and `supplied` (the
paths the payload stated). `data.skipped` lists every other selected model:

| `reason` | Meaning |
| --- | --- |
| `not_a_model` | no `.sql` model of that name under the model paths |
| `python_model` | a Python model; dex drafts from SQL only |
| `sql_unreadable` | the SQL could not be read statically (`detail` says why) |
| `unprofiled_inputs` | the cache has not profiled what it reads; `commands` holds an `explore profile` call that can reach each one: `explore profile <dev namespace>.<model> --target dev` for a project model whose dev namespace the source allowlist does not reach, and none (the reason says why) for a name that matches several profiled relations, which no profile run settles. Nothing is scanned |
| `nothing_drafted` | the cache proves no key, verified join or running total for it |
| `complete` | it already declares every fact dex can draft |
| `not_writable` | its YAML cannot be spliced predictably (a flow-style entry), or a drafted fact does not fit the SELECT list; the rest of the batch still plans |
| `package_documented` | it overrides a package model the package documents; dbt gives the package's entry to the override and allows it none of its own (`detail` names the file), so it takes no declaration |

Where present, `missing` lists the intent a skipped model still owes; a
`package_documented` model owes none and carries it empty.

**The cap.** At most 25 models are proposed per plan; `--limit N` narrows that and
never widens it. Skipped models do not count. The models left over are counted in
`data.elided_count` and in `notes`. Apply the plan and run the same command again:
the models just declared are now `complete`, so the next batch is proposed.

**Nothing to propose** returns `ok` with `plan_id: null`, no diff, and a note.

Otherwise the declarations go through the same path as a `transform plan`
declaration: rendered into the existing entry (shared files included, every
other byte kept), gated by dbt's parse, and drafted, with `data.declarations`,
`data.decisions` and, for a declared mart, `data.semantic_proposal`. Free on
every connector: it reads the repository and the cache and opens no connection.

## Checked against the built relation

`transform build --verify` and `maintain verify` hold each declaration to the
relation dbt built, with aggregate-only statements (no row leaves the
warehouse):

| Declared | Finding | Severity |
|---|---|---|
| `grain` | `grain_broken`, `data.source: declaration`, with the duplicate count | high (low below `maintain.grain_min_rows`) |
| `unit: fraction` with a value outside 0 to 1 | `unit_out_of_range`, with the observed `min` and `max` | medium |
| `unit: percent` with every value within 0 to 1 | `unit_out_of_range`; a question rather than proof, since small percentages land here too | medium |
| `additivity: additive` on a running total | `additivity_contradicted`, with the entity, the ordering column and the decrease fraction | medium |
| `population.filters` value still present | `population_contradicted`, with the count of contradicting rows, never the rows | high |
| `population.parent`, eligible parent keys absent from the model | `parent_population_missing`, distinct-key counts, `excluded_by_filters` for parents a declared filter rules out | high (medium when a declared filter's column is not on the parent) |
| `population.parent`, model keys the parent does not have | `parent_population_unexpected`; these keys are never the population | high |
| `history`, a measure disagreeing with the declared policy | `temporal_transition_count_mismatch`, `temporal_latest_transition_mismatch`, `temporal_first_attainment_mismatch`; entity counts, never values | high |
| `history`, entities differing from its `population` | `temporal_population_missing`, `temporal_population_unexpected` | high |
| `history.time.provenance` its column and the snapshot's strategy cannot satisfy | `temporal_provenance_contradicted` | medium |

`null_rule: never` needs no check of its own: it renders as a `not_null` test,
which the build runs. A single-column `grain` renders as a `unique` test, so the
build path leaves it to that test; `maintain verify` ranks the declared grain
first among its grain sources, so one model's grain is checked once.

The additivity probe orders the column by the declaration's own entity and time
columns: a composite grain naming both, else the `foreign_key` (or `key`) and
`time` roles, else the relation's first id-shaped and temporal columns. Declare
the roles where that guess would be wrong.

Each declared parent also gets a record under `data.parent_population`: the
declaration, the counts and a `status` (`satisfied`, `contradicted`,
`not_applicable` when the parent and the model are both empty, or `unchecked`
with a `reason_code`). A column a join supplies is judged by its `null_rule`
too (`join_field_all_null`), with the join's coverage beside it; see the
maintain skill's `axes.md`, "Join contract".

A model derived from a dbt snapshot's status history declares its temporal
contract in `history`; see "Temporal contracts: `history`" below.

### Measured against a drafted parent

`transform build --verify` also measures each built model that declares no
parent against the one drafted for it (#1228), with the declared-parent
statement plus one count. With `--for-plan` only the plan's models are drafted,
and one no parent could be drafted for gets an `unchecked` record
(`no_parent_drafted`); without a plan, up to 25 built models are, the rest
counted in a note. `maintain verify` measures declared parents only. Each gets
a record under `data.verification.population_delta`:

| Count | Meaning |
|---|---|
| `orphan_keys` | the model's distinct keys the drafted parent does not have |
| `missing_parents` | the parent's keys (after any declared `population.filters` the parent can evaluate) with no row in the model |
| `empty_rows`, `empty_columns`, `empty_share` | rows whose child columns (the aggregates, else the columns from a join's outer side) are all NULL or zero: a signal of parents kept with no children to investigate, not proof, since children whose amounts sum to zero read the same |

`status` is `satisfied` (no orphans, no missing parent, `empty_share` at most
0.05), `needs_decision`, `settled`, `not_applicable` (both sides empty) or
`unchecked` with a `reason_code`. `needs_decision` raises a `population_delta`
finding (`high` with orphans, `medium` with missing parents, `low` for empty
rows alone) and is listed under `data.completion.obligations.needs_decision`.
It asks which rows the model is for; dex never picks. Answer it with
`population.parent` (then the declared check governs), or with an assumption
naming the key `column` at `request`, `contract` or `precedent` tier, which
makes the record `settled` with `settled_by`. Every key an orphan says the join
or the parent is suspect, not that the model should be driven from the child
table. Counts and key column names only: no key value is reported. A drafted
parent never appears under `parent_population` or `suppressed`.

A check that could not run is named in `data.suppressed` (`unit`, `additivity`,
`population`, `parent_population`, `temporal`, and `grain` on the build path) with the reason: nothing in scope
declares it, the relation is empty, the column is all NULL, the column was
aggregated away (a rollup cannot carry its population rule's column, so the rule
is checked upstream or not at all), too few observations, or the scan is offered.
A population filter's values are compared as text when the declared values and
the column's type disagree. A unit's range is withheld for a column that looks
like personal data.

### Temporal contracts: `history`

A snapshot can build and hold the right rows while a model over it disagrees
about what the history means. Its own tests adopt its own conventions, so they
cannot settle that. A `history` block states the conventions, and verification
derives each entity's expected values from the snapshot's versions and that policy
alone, without reading the model's SQL:

```json
"history": {
  "snapshot": "hosts_snapshot",
  "entity": {"host_id": "host_id"},
  "status": {"column": "is_superhost", "target": true},
  "initial_observation": "baseline",
  "null_status": "ignore",
  "population": "ever_target",
  "time": {"column": "dbt_valid_from", "provenance": "capture"},
  "measures": {"transition_count": "status_change_count",
               "latest_target_transition_at": "last_status_change_at",
               "first_target_at": "first_superhost_at"}
}
```

| Field | Values | Meaning |
|---|---|---|
| `snapshot` | a snapshot of this project | where the versions come from; a SQL block or a YAML-defined snapshot |
| `entity` | `{<output column>: <snapshot column>}` | the key the model holds one row per |
| `status` | `{column, target}` | the status column of the snapshot, and the value of interest. The target is committed to git, so a column that looks like personal data is refused |
| `initial_observation` | `baseline` | the first observation establishes a starting point and is not a transition |
| | `transition` | a first observation at the target counts as one. This assumes a prior non-target state, so select it only when that is the intent |
| `null_status` | `ignore` | a NULL version is not an observation: true, NULL, true is no change |
| | `state` | NULL is a state: true, NULL, true is two changes |
| `population` | `ever_target`, `all_observed` | the entities the model holds |
| `time` | `{column, provenance}` | the snapshot column the time fields read. `provenance` is `business` (the source recorded it) or `capture` (the snapshot observed it) |
| `measures` | `transition_count`, `latest_target_transition_at`, `first_target_at` | the output columns each expected value is compared with |

`snapshot`, `entity` and `status` are required. A status change is the status
value differing between consecutive versions, ordered by the snapshot's own
validity column, so an edit to another attribute is never a transition. A policy
left out is a plan warning, and whatever rests on it is reported as
`policy_missing`: Dex assumes none. `first_target_at` rests only on `time`.
A `transition_count` needs `initial_observation` and `null_status`, and
`latest_target_transition_at` needs those and `time`.

Under the `timestamp` strategy dbt copies the source's `updated_at` into its
validity column, so that column is source time. Under `check` it is the time the
snapshot ran. `temporal_provenance_contradicted` reports a declaration that says
otherwise, and a column dbt does not write declared as `capture`.

`transform plan` also warns when a model refs a snapshot and walks its versions
(`lag`, `lead`, `row_number`, `dbt_valid_from`, `dbt_updated_at`) with no `history`
declared. It is a text heuristic, and only ever a warning.

Each contract gets one record under `data.temporal_contracts`
(`data.verification.temporal_contracts` on a build), keeping three things apart:

- `snapshot_execution`: dbt's status for the snapshot and its strategy. A snapshot
  that built establishes nothing about what a model made of its versions.
- `assertions`: per measure, `population` and `time_provenance`, each with its own
  status and, for a measure, `compared` and `mismatched_entities`.
- `unchecked`: what was not established, with a count of the entities it covers.

| `status` | Means |
|---|---|
| `satisfied` | every assertion held, and at least one entity made a transition |
| `contradicted` | a finding to fix |
| `not_applicable` | `no_history_observed` (the columns agree, and no entity made a transition, so transitions were not exercised), or `empty_input` |
| `unchecked` | not clean; `reason_code` says why |

| `reason_code` | Why it is unchecked |
|---|---|
| `policy_missing` | the declaration leaves out a policy this assertion rests on |
| `business_order_conflict` | a declared business timestamp runs backwards across a status change, so business and capture order give different sequences. Those entities are excluded from every comparison and counted, never guessed |
| `business_timestamp_unreliable` | a declared business timestamp is NULL or stands still at a status change. Those entities' time fields are not compared; their counts are, since capture order is intact |
| `ambiguous_version_order` | an entity's versions share one validity timestamp |
| `hard_delete_records` | the snapshot uses `hard_deletes: new_record`, whose records are versions that do not observe the status |
| `snapshot_not_ancestor` | the manifest does not show the model descending from the declared snapshot, directly or through other models, so nothing was compared. `reason` names the snapshot and any other snapshot the model descends from. Correct `history.snapshot`, or read the snapshot through `ref()`: the manifest cannot see a hard-coded relation. This is reachability, not column lineage: a snapshot reached only through an unrelated join passes it |
| `lineage_unavailable` | the manifest cannot say whether the model descends from the snapshot (no recorded dependencies, or a parent it does not hold), so nothing was compared |
| `snapshot_not_built` | the snapshot failed or was skipped in the last run |
| `malformed_declaration` | a hand-written block does not parse |
| `column_missing`, `relation_not_found`, `probe_refused`, `scan_offered`, `no_entity_comparable`, `nothing_to_compare` | the check could not reach or compare what it needs |

**Limits.** One snapshot, one status column, one output row per entity. Not a
general SCD verifier: history built on anything but a dbt snapshot, a model holding
one row per period, and any policy not listed here are out of scope, and no policy
is inferred. Nothing here repairs a snapshot or a model. A source timestamp that
merely equals a creation timestamp is not evidence either way, so it is not flagged;
only a failure observed at a status change is. `semantic ossie|slayer|cube` refuse
it, and a derived semantic definition lists it under `not_carried`.

The statements are aggregate-only, priced with `(declared facts)`, and go through
the same handshake and session ceiling. They return counts, never a row or a value.

## Read back by `explore --use-project`

`explore profile` and `explore map` with `--use-project` return each declared
model's declaration as `declaration` on the relation it builds: grain (with
`grain_status` comparing it with the measured keys), population (a declared
`parent` as `model`, `columns` and `parent_columns`), history (under
`--values-free` or on PII-flagged status columns, `status.target` is withheld
and named in `withheld_fields`), and each column's role, unit, additivity and
`references`. A `references` is also a declared join,
`declared_by: declaration <model>.<column>`. It is read from the YAML on every
run and never cached, so a later session reads the rule the project records
rather than one remembered from the conversation that wrote it.

A native layer is read back the same way, so `semantic ossie|slayer|cube plan`
with `declarations` reaches `explore --use-project` with no dbt project present.
The grain comes from the layer's own `primary_key`, and the rest from the `dex`
metadata below. A definition with a primary key and no metadata still reports
`declaration`, with its grain. A document annotated by an earlier release stored
no `role` or `references`, so it reports neither until it is annotated again.
Where a dbt model and a layer declare one relation, the dbt declaration is
reported whole, since the layer's was derived from it, and `notes` says so.

## Derived semantic model: `data.semantic_proposal`

When `transform plan`, `transform declare` or `semantic define|update|plan` creates,
edits or declares a model under `transform.marts_paths` (`.dex/config.yml`, default
`[models/marts]`, relative to the dbt project, subfolders included) and the model's
post-change YAML carries a declaration, the engine derives the semantic definition
the declaration already states, **in whichever semantic layer the repository
reads** (`semantic.vendor`). Every vendor sits behind one hook
(`SemanticDerivationSource`), so the envelope has one shape with a `vendor` field:

| `semantic.vendor` | What a declared mart gets |
| --- | --- |
| `dbt` (default) | a MetricFlow semantic model, spliced into the dbt plan |
| `slayer` | a SLayer model file, stored as a plan of its own beside the dbt plan |
| `cube` | a Cube model file, stored as a plan of its own beside the dbt plan |
| `ossie` | an Ossie dataset, appended to the configured document holding its parents and stored as a plan of its own beside the dbt plan |

Three rules hold for every vendor. Metrics are never derived: a measure is what a
column holds, a metric is a business definition, and it stays the author's. Nothing
is guessed or renamed: an aggregation with no equivalent, a composite grain a layer
cannot key on, a name already declared are each named. And **a population is
metadata, never a filter**: the derived definition sits on the mart, whose SQL
already enforces the population, so a filter would apply the rule twice and diverge
silently the day the two disagree. It is carried structured under the vendor's
metadata key `dex`, and as one sentence at the end of the description
(`Population: <rule>; status is one of 'paid' or 'shipped'.`), where an agent
reading the catalog meets it.

Per model, `carried` lists every declared field that reached the definition
(`grain`, `population`, `columns.amount.unit`) and `not_carried` names every one
that did not, with why. A declared field never disappears without a word.

### MetricFlow (`semantic.vendor: dbt`)

| Declaration | Semantic model |
| --- | --- |
| a single-column `grain` | the primary entity (`order_id` becomes entity `order`) |
| a composite `grain`, or none | no primary entity, and none guessed: MetricFlow needs one for any dimension or measure, so the derivation is `failed` with the limitation named. Add `primary_entity:` and pass it to `semantic plan` yourself |
| `foreign_key` | a foreign entity. With `references`, it takes the entity name the referenced model's semantic model already gives that column, so the join resolves; otherwise the column's name less `_id`, with a note |
| `dimension` | a categorical dimension |
| `time` | a time dimension: `day` for a date, `day` for a timestamp (noted, since finer is the author's choice), the truncated grain where the SQL truncates (`date_trunc('month', ...)`), `day` with a note where the type cannot be read. A column whose type is known not to be temporal is left out. The first time column is `defaults.agg_time_dimension`, and a note names the others |
| `measure` with `aggregation` | a measure: `sum`, `count`, `count_distinct`, `min`, `max`, `average` (`avg`, `mean`), `median`, `sum_boolean`. Anything else (`percentile` needs parameters a declaration does not carry), a missing aggregation, or `non_additive` with a summing aggregation is left out and named. A model with no time column carries no measure, since MetricFlow aggregates over one |
| `semi_additive` | `non_additive_dimension: {name: <default time dimension>, window_choice: max}`: each period reports its last value, which suits a balance or a season-to-date total. MetricFlow's own default is `min`; the note asks you to confirm |
| `non_additive` | `config.meta.dex.additivity: non_additive` on the measure, since MetricFlow reads any measure as one it may add up |
| `description` | carried onto the semantic model, dimensions and measures (MetricFlow's schema has no entity description, and `not_carried` says so) |
| `population`, `assumptions` | the semantic model's `config.meta.dex`, and the population sentence in its description |
| `unit`, `null_rule` | the entity's, dimension's or measure's `config.meta.dex` |

What happens to the derivation depends on the project:

- **With a dbt semantic layer** (a semantic model is declared and a time spine
  is present), a derivation that passes every check is added to the same plan,
  spliced into the project's one semantic-model file (or
  `<mart folder>/<model>_semantic.yml` where there is none, or several) with
  every other byte untouched. `mode` is `included`, and a warning names the file.
- **Without one**, nothing is added. `mode` is `proposed`, `time_spine` says
  whether a spine exists, and `definitions` holds each derivation ready to pass:
  save the whole `data.semantic_proposal` object as a file and run
  `semantic plan --definitions-file <file>`. Adopting MetricFlow and a time spine
  is the project owner's decision, so the engine never bootstraps either.

Before a derivation is offered or included it passes MetricFlow's schemas, the
metric-input check, and dbt's parse of a throwaway copy of the project. In a
project with no time spine, that copy alone gets a temporary spine so dbt can
parse it at all; the project never sees it. The parse runs for a derivation even
under `semantic plan --no-parse`, which still applies to the rest of the plan,
because a semantic YAML dbt cannot parse breaks every dbt command in the project.

```json
"semantic_proposal": {
  "vendor": "dbt",
  "mode": "proposed",
  "time_spine": "missing",
  "definitions": [{"kind": "semantic_model", "path": "models/marts/fct_orders_semantic.yml", "content": "name: fct_orders\n..."}],
  "models": {
    "fct_orders": {
      "status": "proposed",
      "semantic_model": "fct_orders",
      "path": "models/marts/fct_orders_semantic.yml",
      "content": "name: fct_orders\n...",
      "validation": {"schema": {"result": "passed"}, "references": {"result": "passed"}, "parse": {"result": "passed", "detail": "parsed with a throwaway time spine in the copy only; the project has none"}},
      "notes": ["..."],
      "limitations": [],
      "carried": ["description", "grain", "population", "columns.order_total.unit"],
      "not_carried": {}
    }
  },
  "next": "save this object as a file and pass it to `semantic plan --definitions-file <file>` ...",
  "notes": ["the project has no dbt semantic layer and no MetricFlow time spine ..."]
}
```

### SLayer (`semantic.vendor: slayer`)

One model file per mart, `models/<data_source>/<mart>.yaml` under
`semantic.slayer.base_dir`:

| Declaration | SLayer model |
| --- | --- |
| `grain` | `primary_key: true` on each grain column, a composite grain included |
| any role | a column, typed from the SQL's casts or the cache's profile (`INT`, `DOUBLE`, `BOOLEAN`, `DATE`, `TIMESTAMP`, `TEXT`); a summed measure of unknown type is `DOUBLE`, with a note. A list type (`VARCHAR[]`, `text[]`, `ARRAY<STRING>`, Snowflake `ARRAY`) is `type: ARRAY` with the `element_type` its element names, `UNKNOWN` for a list of lists or structs or a semi-structured `ARRAY` |
| the first `time` column | `default_time_dimension` (only where its type is known to be a date or a timestamp) |
| `foreign_key` with `references` | a `many_to_one` join to the SLayer model already sitting on the parent's table; where none does, no join and a note |
| `measure` with `aggregation` | a saved measure named `<column>_<agg>`, formula `<column>:<agg>`: `sum`, `avg` (`average`, `mean`), `min`, `max`, `count`, `count_distinct`, `median`. SLayer keeps columns and measures in one namespace, so a name a column already holds fails the derivation rather than being renamed |
| `semi_additive` | no saved measure, named in `limitations`: SLayer's `last` reports one row's value on the last period, not the total across entities on it, so `<column>:last` is the author's call |
| `description` | the model's and each column's `description` |
| `population`, `assumptions` | the model's `meta.dex`, and the population sentence in its description |
| `unit`, `null_rule`, `additivity`, `role`, `references` | the column's `meta.dex`, beside any native construct a role or a reference also renders |

`data_source` is the one the configured models share; models over more than one
are not guessed between (`failed`). `sql_table` is, in order: the `database.schema`
that the SLayer models on this dbt project's other models already read (so a mart
lands where its siblings do); else the relation the compiled manifest names, with a
note, since that is whatever target last compiled the project (often dev); else the
bare table name, as a limitation, since dex's catalog then claims no relation. A
model already on the mart's table is `skipped`; one holding its name on another
table is `failed`.

Whether it is included depends on the write surface:

- **The path is already listed under `semantic.slayer.models`**: the model is
  validated by exactly the checks `semantic slayer define` runs, read back through
  the SLayer catalog, and stored as **a plan of its own** on the SLayer layer,
  beside the dbt plan, because a plan holds one edit target. `mode` is `included`,
  `plan_id` names that plan, and the hint names both:
  `transform apply <dbt plan>` and `transform apply <plan_id>`. A bare
  `transform apply` takes only the latest, which is the SLayer one.
- **It is not**: `mode` is `proposed`, after the same checks. Listing a file is a
  configuration change with its own confirmation, so `next` names it:
  `dex config set semantic.slayer.models '[..., models/wh/fct_orders.yaml]'`, then
  pass `data.semantic_proposal.definitions` (an edits payload) to
  `semantic slayer define --edits-file`, or re-run the plan to include it.

### Cube (`semantic.vendor: cube`)

One file per mart, `<dir>/<mart>.yml`, where `<dir>` is the one directory the
configured YAML files share (`model/cubes` where they share none):

| Declaration | Cube |
| --- | --- |
| `grain` | `primary_key: true` on each grain dimension, a composite grain included |
| any role but `measure` | a dimension, `sql: "{CUBE}.<column>"`, typed `time`, `number`, `boolean` or `string` from the SQL's casts or the cache's profile; a `time` role is always `time` (with a note where the type could not be read) |
| `measure` with `aggregation` | a measure named after the column, `sql: "{CUBE}.<column>"`: `sum`, `avg` (`average`, `mean`), `min`, `max`, `count`, `count_distinct`. The column is not also a dimension, as MetricFlow does not make it one |
| `median`, `semi_additive` | no measure, named in `limitations` and `not_carried`: Cube has no median type, and no measure that sums across entities but not across time |
| `foreign_key` with `references` | a `many_to_one` join, `{CUBE}.<column> = {<parent>}.<parent column>`, to the cube already on the parent's table; none, or a second key to the same cube, means no join and a note |
| `description` | the cube's and each member's `description` |
| `population`, `assumptions` | the cube's `meta.dex`, and the population sentence in its description; never a measure filter or a segment |
| `unit`, `null_rule`, `additivity`, `role`, `references` | the member's `meta.dex`, beside any native construct a role or a reference also renders |

`sql_table` follows the SLayer order (the siblings' `database.schema`, else the
manifest relation, else the bare name as a limitation), and `data_source` is
written only where `semantic.cube.data_source` is not `default`. A cube already on
the mart's table is `skipped`; a cube or view holding its name is `failed`.
Included and proposed work as for SLayer, against `semantic.cube.files`: listed
paths are stored as a plan of their own (`plan_id`; apply both), others are
proposed with the `dex config set semantic.cube.files '[...]'` that adds them.

### Databricks Metric Views (`semantic.vendor: databricks`)

One file per mart, `<dir>/<mart>.yaml` (the one directory and suffix the
configured files share, `metric_views/` and `.yaml` where they share none). A
Metric View has **no metadata key**: Databricks refuses any key its
specification does not list, so a fact with no native construct is named in
`not_carried` rather than written.

| Declaration | Metric View |
| --- | --- |
| the mart's relation | `source` (the siblings' `catalog.schema`, else the manifest relation, else the bare name as a limitation) |
| any role but `measure` | a field, `expr: <column>`; a date or timestamp column (from the SQL, the cache or a `time` role) gets `format: {type: date, date_format: year_month_day}` or `{type: date_time, date_format: year_month_day, time_format: locale_hour_minute_second}` (Databricks refuses either without its formats), the only way a Metric View marks a field temporal |
| `measure` with `aggregation` | a measure `<column>_<agg>`: `SUM`, `AVG` (`average`, `mean`), `MIN`, `MAX`, `MEDIAN`, `COUNT`, `COUNT(DISTINCT ...)`. Fields and measures share one namespace, so the suffix keeps the measure from shadowing its column |
| `semi_additive` | no measure, named in `limitations`: a window measure (`semiadditive: last`) needs an ordering field and a range, which is the author's call |
| `unit` | `currency:<code>` as `format: {type: currency, currency_code: <code>}`, `fraction` as `format: {type: percentage}` (Databricks displays it multiplied by 100); `percent` and any unit on a count are not carried |
| `foreign_key` with `references` | a `many_to_one` join named after the parent, `on: source.<column> = <parent>.<parent column>`, on the parent's relation; `rely: {at_most_one_match: true}` only where the parent's own declaration states that column as its whole grain |
| `description`, `population` | the view's `comment`, the population as its last sentence; never a `filter`. The catalog withholds that sentence, as every native catalog does |
| a column's `description` | the member's `comment` |
| `grain`, `null_rule`, `additivity`, `assumptions` | not carried: a view declares no key on its own source, and there is no metadata key |

A view already on the mart's table is `skipped`; a file whose stem is the mart's
name on another source is `failed`. Included and proposed work as for SLayer,
against `semantic.databricks.files`. A join's `source` is the source of the view
already on the parent's table where one is configured. A derived join is declared
for exploration and `maintain grain`; a Metric View exposes only its fields, so
add a field that reads it (`<parent>.<column>`) to query through it.

### Snowflake Semantic Views (`semantic.vendor: snowflake`)

One logical table per mart, named after it. A Semantic View has **no free-form
metadata key**, so a fact with no native construct is named in `not_carried`,
never written into `custom_instructions` (Cortex Analyst's prompt).

| Declaration | Semantic View |
| --- | --- |
| the mart's relation | `base_table: {database, schema, table}` (the siblings' `database.schema`, else the manifest relation). A bare name is refused by the reader, so a mart neither names is `failed`: build or compile the project first |
| `grain` | `primary_key: {columns: [...]}`, a composite grain included |
| `time` role | a `time_dimension`, `expr: <column>` |
| any other role but `measure` | a `dimension`, `expr: <column>` |
| `measure` | a `fact` of the same name, the row-level value |
| `measure` with `aggregation` | also a table metric `<column>_<agg>` over the fact (`SUM(<mart>.<column>)`): `SUM`, `AVG` (`average`, `mean`), `MIN`, `MAX`, `MEDIAN`, `COUNT`, `COUNT(DISTINCT ...)`. Members share one namespace per table, so the suffix keeps it from shadowing the fact |
| `semi_additive` | the metric's `non_additive_dimensions` on the table's first time dimension, `sort_direction: ascending` with `null_order: first`, so it reads the rows of the latest date only and is never summed across time (Snowflake reads the last value in the stated order: descending would read the earliest date, and NULLs last an undated row); with no time dimension, no metric and a reason |
| `foreign_key` with `references` | a relationship `<mart>_to_<parent>` to the parent's logical table in the same view, only where that table declares the column as its `primary_key` or a `unique_keys` entry (Snowflake relates a table only to a key) |
| `description`, `population` | the table's `description`, the population as its last sentence; never a filter. The catalog withholds that sentence |
| a column's `description` | the member's (and its metric's) `description` |
| `unit`, `null_rule`, `assumptions`, any other `additivity` | not carried |

Relationships join the tables of one view, so where it goes follows the foreign
keys: the configured file holding the tables they reference, or, with no foreign
key and one configured file, that one. It is spliced in, so every other byte
stays, and stored as a plan of its own (`plan_id`; apply both). Where the parents
span files or none holds them, it is a view of its own, `<dir>/<mart>.yaml` (the
directory and suffix the configured files share, `semantic_views/` and `.yaml`
where they share none), included where that path is configured and `proposed`
otherwise. A table already on the mart's relation is `skipped`; a table or view
of the mart's name is `failed`. Declarations carry no label, so no `synonyms` are
derived.

### Ossie (`semantic.vendor: ossie`)

One dataset per mart, appended as a new list item to a configured document:

| Declaration | Ossie dataset |
| --- | --- |
| each declared column | a field of the same name, `expression: {sql: <column>}` |
| a column's type, where the SQL or the cache knows it | the field's `datatype` (`Integer`, `Decimal`, `Float`, `Boolean`, `Date`, `DateTime`, `DateTimeTz`, `Time`, `String`) |
| `time` role | `dimension: {is_time: true}` |
| `grain` | `primary_key`, every grain field, a composite grain included |
| `foreign_key` with `references` | a relationship `<mart>_to_<parent>` to the dataset in the same document whose field exposes the referenced column; none means no relationship and a note |
| `measure` with `aggregation` | a dataset-scoped metric `<column>_<agg>`: `SUM`, `AVG` (`average`, `mean`), `MIN`, `MAX`, `COUNT`, `COUNT(DISTINCT ...)`. A measure is also a field, since a dataset metric aggregates its dataset's fields |
| `median`, `semi_additive` | no metric, named in `limitations` and `not_carried` |
| `description` | the dataset's and each field's `description` |
| `population`, `assumptions` | the dataset's `ai_context`: the population sentence as `instructions`, and the declaration under a structured `dex` key; the sentence also closes the description. Never a filter, and never `custom_extensions`, whose opaque string a diff cannot review |
| `unit`, `null_rule`, `additivity`, `role`, `references` | the field's `ai_context.dex`, beside any native construct a role or a reference also renders |

A relationship joins datasets of one model, and a model is one document, so where
it goes follows the foreign keys: the configured document holding the datasets
they reference, or, with no foreign key and one configured document, that one. It
is spliced in, so every other byte of the document stays, and stored as a plan of
its own on the Ossie layer (`plan_id`; apply both). Where the parents span
documents or none holds them, it is `proposed` as a document of its own,
`<dir>/<mart>.ossie.yaml`, with the `dex config set semantic.ossie.files '[...]'`
that adopts it. `source` follows the SLayer order (the siblings' `database.schema`,
else the manifest relation, else the bare name as a limitation). A dataset already
on the mart's table is `skipped`; one holding its name in the target document is
`failed`.

### Declarations on `semantic slayer`, `semantic cube`, `semantic ossie`, `semantic databricks` and `semantic snowflake`

`semantic slayer define|update|plan` take the same `declarations` key beside
`edits`. There a declaration **annotates** a SLayer model the payload's edits or
the layer already define (`model` is the SLayer model's name): the declared grain
becomes `primary_key`, descriptions and the population sentence are written, a
`references` adds a `many_to_one` join where none to that model exists, a declared
aggregation adds its `<column>_<agg>` saved measure, and `population`,
`assumptions`, `unit`, `null_rule` and `additivity` land in `meta.dex`. The
declaration wins field by field and nothing else moves; a declaration naming no
defined model is refused. `edits` may be omitted. The result is validated by the
layer's own checks before the plan is stored. `semantic cube` does the same for a
cube (`model` is the cube's name; a view is refused, since it has no table of its
own): grain to `primary_key` on its dimensions, a declared aggregation adds a
measure named after the column, a `references` adds a `many_to_one` join, and
only that cube's entry in its file is rewritten, so every other cube, view and
comment keeps its bytes. `semantic ossie` does the same for a dataset (`model` is
the dataset's name): the grain becomes `primary_key` on the **fields** exposing the
grain columns (a grain column no field exposes is refused by name, since a key
names fields; author the field first), a declared aggregation adds a dataset
metric `<field>_<agg>`, a `references` adds a relationship to the parent dataset's
field in the same document, and the rest lands in `ai_context` as above. Only that
dataset's list item is rewritten, and a relationship is appended, so every other
byte of the document is kept.
`semantic databricks` does the same for a view (`model` is the file's stem): the
description and population sentence become the root `comment`, a column's
description and unit become its member's `comment` and `format`, a declared
aggregation with no member adds a measure `<column>_<agg>`, and a `references`
naming another configured view adds a join on that view's `source` (with no
`rely`, since the native route reads no parent declaration). Only those parts are
spliced, read and written as YAML 1.2, so every other byte, comment and `on:` key
is kept; the grain, NULL rule, additivity and assumptions are named in
`not_carried`.
`semantic snowflake` does the same for a logical table (`model` is `view.table`,
or a table name unique across the layer; one two views share is refused naming
both): the description and population sentence become the table's
`description`, a column's description its member's `description`, a declared
aggregation with no metric adds a metric `<column>_<agg>` (over the member where
one exists, else the base column; with `non_additive_dimensions` for a
`semi_additive` one), and a `references` naming another logical table of the same
view, keyed on that column, adds a relationship. Only those lines are rewritten,
inside the table too, so every other byte and comment is kept. A grain other than
the table's own `primary_key` is not rewritten, an aggregation an authored metric
contradicts is named rather than rewritten, and units, NULL rules, assumptions and
other additivity are named in `not_carried`.

Per model, `status` is one of:

| `status` | Meaning |
| --- | --- |
| `included` | in this plan, or for a native layer in the plan named by `plan_id` |
| `proposed` | passed every check; in `definitions` |
| `failed` | a check failed, the grain is composite (MetricFlow), a name is already declared (renaming is yours, never the engine's), or the data source is ambiguous (SLayer); `reason` or `validation` says which. `content` is kept for you to fix, never offered |
| `unvalidated` | a check could not run (dbt absent, or the plan's own edits do not parse), so it is neither offered nor included |
| `skipped` | an authored definition already sits on the mart (never overwritten), or the declaration names nothing a definition carries |

The key is absent when the plan touches no declared mart. Under a vendor whose
layer does not implement the hook nothing is derived and a warning says so.

## `data.decisions`

The plan, apply and build envelopes carry `data.decisions`: every assumption
declared on the models the command touched, as `{model, decision, chosen,
evidence}`, plus `column` and `detail` where the assumption states them. It is read back from the project's YAML, so the three commands report
the same list. An empty list means the touched models declare no assumption.

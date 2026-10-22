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
| `references` | `<model>.<column>`, a model, seed or snapshot the project has |
| `evidence` | `request` (what the user asked for), `contract` (the project's declared columns, tests or metric filters), `precedent` (how sibling models decide the same thing), `data` (what profiling showed), `default` (the conventional analytics-engineering choice) |

A field dex does not know is refused by name, so a typo cannot silently drop
part of a declaration.

## What it renders into

The declaration is written into the model's **existing** YAML entry, wherever in
the project it lives. A model with no entry gets one beside its SQL, named for
it, which is where the scaffold puts one. dex never writes a second entry for a
model, which dbt refuses.

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
one, and a key it leaves out is kept. Every byte outside the keys above, comments
included, stays where it was.

## What is checked

Refused, with the fix named:

- a model the project and the plan do not have;
- a declared column or grain column the model's SELECT list does not produce
  (skipped, with a warning, when the SELECT list cannot be read statically);
- a `references` target that is not `<model>.<column>`, names nothing, or names
  a column the target does not produce;
- an unknown `role`, `additivity` or `evidence`, or an unknown field;
- a population filter listing values on a column that looks like personal data.

Warned, never refused: a missing description, grain, assumptions or column role,
an assumption missing its decision, chosen value or evidence, and a model the
plan writes SQL for with no declaration at all.

A plan carrying declarations or `schema_yml` edits is parsed by dbt against a
throwaway copy of the post-change project before it is stored, and degrades to a
named warning where dbt is not installed.

## `data.decisions`

The plan, apply and build envelopes carry `data.decisions`: every assumption
declared on the models the command touched, as `{model, decision, chosen,
evidence}`. It is read back from the project's YAML, so the three commands report
the same list. An empty list means the touched models declare no assumption.

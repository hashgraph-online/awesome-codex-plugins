---
name: dataproduct-dbt
description: Build out the transformation layers (`staging/`, `intermediate/`) of a data product and run dbt against them, following project-wide conventions adapted from dbt's best practices (v1.12). Trigger when the user asks to "add a staging model", "build out the staging layer", "create an intermediate model", "refactor this output port into staging + intermediate", "make this model incremental", or "run dbt for this data product".
---

# Build and run dbt transformations for a data product

`dataproduct-implement` generates the ends of the pipeline: input-port sources (from access agreements) and output-port models (from the data contract). This skill fills in the middle, the `staging/` and `intermediate/` layers, and runs dbt against the result. The conventions below are adapted from [dbt's structure and materialization best practices](https://docs.getdbt.com/best-practices?version=1.12), and are meant to be edited by the organization adopting this plugin.

## When to use this vs. other skills

- **No dbt project yet** → run `dataproduct-bootstrap` first.
- **No output-port models or input-port sources yet** → run `dataproduct-implement` first.
- **Auditing or reviewing an existing dbt project** → use `/review` or `/simplify`, not this skill.
- **Authoring or refactoring the middle of the DAG, or running dbt** → this skill.

## Conventions (the editable part)

These rules are the contract between this skill and the rest of the plugin. Organizations forking the plugin should treat this section as the place to encode their own style.

### Layer responsibilities

| Layer | Purpose | Materialization | References | Naming |
|---|---|---|---|---|
| `models/input_ports/<op-id>.source.yaml` | External raw data, one file per active access agreement | n/a (source) | n/a | source `name` = `<provider-dp-id>_<provider-op-id>` |
| `models/staging/stg_<provider-dp-id>__<table>.sql` | One staging model per source table: rename, cast, light cleanup, dedup | `view` | `{{ source(...) }}` only | double underscore separates source from entity |
| `models/intermediate/int_<purpose>.sql` | Joins, aggregations, pivots, surrogate keys, single-purpose | `view` (or `ephemeral` if used once) | `{{ ref(stg_*) }}` and `{{ ref(int_*) }}` only | verb-based filename describing what it does |
| `models/output_ports/v1/<table>.sql` | Published, contract-governed tables | `table` (or `incremental` past the threshold below) | `{{ ref(int_*) }}` or `{{ ref(stg_*) }}` | table name from the ODCS contract's `models:` key |

Deviations from upstream dbt conventions, called out so the lineage stays visible:

- We use `input_ports/` and `output_ports/v1/` instead of dbt's `sources` / `marts`, to match the data-product lifecycle terminology.
- Output-port models are **not** prefixed with `fct_` / `dim_`. The contract dictates the published name, and consumers see that name directly.
- We keep `staging/` and `intermediate/` flat for single-data-product repos. Use subfolders by output port (e.g. `staging/<output-port-id>/`) only if a data product has more than two or three output ports.

### Staging model shape (CTE pattern)

Every staging model uses this three-CTE skeleton so the structure is uniform and a reader knows where to find the rename block.

```sql
-- Staging model for source <provider-dp-id>_<provider-op-id>.<table>
with

source as (
    select * from {{ source('<provider-dp-id>_<provider-op-id>', '<table>') }}
),

renamed as (
    select
        cast(<raw_col> as <warehouse_type>) as <canonical_name>,
        ...
    from source
),

final as (
    select * from renamed
)

select * from final
```

Allowed transformations in `renamed`: column renames, casts, simple `case` rewrites, unit conversions (e.g. cents to dollars), trim/lower. Disallowed: joins, aggregations, any cross-source logic. Those belong in `intermediate/`.

### Intermediate model shape

- One file per purpose. If you find yourself naming it `int_foo_and_bar`, split it.
- All inputs come through `ref()`, never `source()`. A `source()` call in `intermediate/` means a staging model is missing.
- Pick `view` unless the model is referenced once and is cheap, in which case `ephemeral` keeps it out of the warehouse.

### Tests

Tests are declared in the `_models.yml` next to the file.

| Layer | Default tests |
|---|---|
| `input_ports/` (sources) | `freshness:` block when the upstream contract publishes an SLA; otherwise none |
| `staging/` | `not_null` + `unique` on the natural key, `accepted_values` on enum columns |
| `intermediate/` | `relationships` on every join key, `not_null` on any column the next layer depends on |
| `output_ports/v1/` | Derived from the ODCS contract by `dataproduct-implement` |

Custom singular tests live in `tests/<purpose>.sql` and assert cross-model invariants the schema-tests cannot express.

### Materializations

dbt's tiered rule applies: start with `view`, promote to `table` when query latency hurts, promote to `incremental` when the build window hurts.

- Default per layer (set in `dbt_project.yml`): staging → `view`, intermediate → `view`, output_ports → `table`.
- Switch an output port to `incremental` when one of these is true:
  - The model takes longer than 5 minutes to build full-refresh.
  - The source data grows by more than ~10M rows per scheduled run.
  - A CI run cannot rebuild the model within the deploy budget.

When switching to incremental, configure all three keys; defaults vary by warehouse:

```yaml
{{ config(
    materialized='incremental',
    unique_key='<natural_key>',
    on_schema_change='append_new_columns',
    incremental_strategy='merge'   # databricks/snowflake/bigquery; use 'delete+insert' on postgres
) }}
```

Inside the model body, gate new-row logic with `{% if is_incremental() %} where updated_at > (select max(updated_at) from {{ this }}) {% endif %}`.

### Schemas

Each layer lands in its own warehouse schema so consumers see only the published output, not the scaffolding.

| Layer | Schema | Example |
|---|---|---|
| `input_ports/` | n/a (sources read from upstream schemas; not materialized here) | — |
| `staging/` | `internal_<data-product-id>` | `internal_dp_acme_customer_activity` |
| `intermediate/` | `internal_<data-product-id>` (same as staging) | `internal_dp_acme_customer_activity` |
| `output_ports/v<N>/<table>.sql` | `op_<output-port-id>_v<N>` | `op_customer_activity_v1` |

Why this split:

- The output-port schema embeds the **output port version** so v1 and v2 of the same port can coexist while one is being rolled out. Consumers are granted access to `op_<output-port-id>_v<N>` only.
- Staging and intermediate share a single **internal** schema, scoped by data product id so two data products on the same warehouse do not collide. That schema is not granted to consumers.

To wire this up in dbt, the project needs two pieces:

1. **Override `generate_schema_name`** so `+schema:` is taken literally instead of being suffixed onto the target's default schema. Place this in `macros/get_custom_schema.sql`:

   ```sql
   {% macro generate_schema_name(custom_schema_name, node) -%}
       {%- if custom_schema_name is none -%}
           {{ target.schema }}
       {%- else -%}
           {{ custom_schema_name | trim }}
       {%- endif -%}
   {%- endmacro %}
   ```

2. **Per-model schema for output ports** (one schema per port, so a directory-level rule does not work when v<N>/ contains more than one port):

   ```sql
   -- top of models/output_ports/v1/<table>.sql
   {{ config(schema='op_<output_port_id>_v1') }}
   ```

3. **Directory-level schema for internal models** in `dbt_project.yml`:

   ```yaml
   models:
     <data_product_id>:
       staging:
         +schema: internal_<data_product_id>
       intermediate:
         +schema: internal_<data_product_id>
   ```

With these in place, `dbt run` creates exactly `op_<op-id>_v1`, `op_<op-id>_v2`, and `internal_<dp-id>` in the warehouse, no extra prefixes.

### Documentation

- Every model has a `description:` in `_models.yml`. Single sentence: what it represents, not how it is built.
- Every column with a non-obvious meaning has a `description:`. Obvious ones (`customer_id`, `created_at`) can skip it.
- Output-port descriptions come from the contract; do not edit them locally — edit the contract via `datacontract-edit`.

## How to run this skill

> `${PLUGIN_ROOT}` below refers to the root of this plugin (the directory that contains `skills/`). On Claude Code it is set automatically as `${CLAUDE_PLUGIN_ROOT}`; use that. On any other agent it is unset; resolve it as `../..` relative to **this `SKILL.md` file's directory**.

### Plan announcement (before Step 0)

Before running Step 0, print this plan to the user verbatim:

> Running **dataproduct-dbt**. I'll:
> 1. Pre-checks: confirm this is a dbt project with `input_ports/`, `staging/`, `intermediate/`, `output_ports/v1/`.
> 2. Identify which operation you want (build staging, add intermediate, refactor an output port, run dbt, switch to incremental).
> 3. Apply the operation following the conventions in this skill (which you can edit to match your org's style).
> 4. Verify with `dbt parse` and, when you ask, `dbt build --select <scope>`.
> 5. Summarize what changed and what's open.

Then proceed.

### Step 0 — Pre-checks

- Confirm `dbt --version` is on PATH. If not, stop and tell the user to install the adapter for their warehouse.
- Confirm `dbt_project.yml` exists at the working directory root. If not, route to `dataproduct-bootstrap`.
- Confirm the four model directories exist (`input_ports/`, `staging/`, `intermediate/`, `output_ports/v1/`). If any are missing, route to `dataproduct-bootstrap` or `entropy-data-sync` (whichever the user prefers) and stop.

### Step 1 — Identify the operation

Match the user's ask to one of the operations below. If two fit, ask which one. The operations are deliberately small so the skill stays focused; run it again for the next operation.

| If the user says... | Operation |
|---|---|
| "build out staging", "create staging models for input ports" | A |
| "add an intermediate model for X", "join staging models" | B |
| "refactor this output port into staging + intermediate", "this output port has direct source refs" | C |
| "run dbt", "test the models", "compile only", "build the models" | D |
| "make this output port incremental", "switch X to incremental" | E |
| "add tests / descriptions to staging or intermediate" | F |

### Step 2 — Apply the operation

#### A. Generate staging models from input ports

For each `models/input_ports/<provider-op-id>.source.yaml` (skip files the user did not select if they narrowed the scope):

1. Read the source file. Note `sources[0].name` (the `<dp-id>_<op-id>` reference) and each `tables[].name` (from the provider's contract).
2. For each table, write `models/staging/stg_<provider-dp-id>__<table>.sql` using the staging CTE pattern above. Apply column renames only when the raw name violates the project's snake_case convention or the project's column-name policy; otherwise pass them through with explicit casts.
3. Append the model to `models/staging/_models.yml`:
   ```yaml
   models:
     - name: stg_<provider-dp-id>__<table>
       description: Cleaned, renamed, and type-cast columns from <provider-dp-id>.<table>.
       columns:
         - name: <natural_key>
           tests: [not_null, unique]
   ```
4. Do not invent business logic. If a rename or cast is non-obvious, leave a `-- TODO:` comment in the model and surface it in the final report.

#### B. Add an intermediate model

1. Ask the user what the model is for in one sentence (the verb plus the entities). Map to a filename: `int_<verb>_<entity>.sql` (e.g. `int_payments_pivoted_to_orders.sql`).
2. Write `models/intermediate/<filename>.sql`. Use only `{{ ref(...) }}` references to staging or other intermediate models.
3. Append a `_models.yml` entry with a description and tests on join keys (`relationships`, `not_null`).
4. Run `dbt parse` to verify. Do not run the model in the warehouse without the user asking.

#### C. Refactor an output-port model into staging + intermediate

When `models/output_ports/v1/<table>.sql` contains `{{ source(...) }}` calls or pile-up joins:

1. Identify each `source()` call. Generate a staging model for each (operation A).
2. Identify each join, aggregation, pivot, or surrogate-key construction. Move it to one or more intermediate models (operation B).
3. Rewrite the output-port body to be a thin projection over `ref(int_*)` and apply the contract-driven casts and column order.
4. Run `dbt parse`. If the rewrite changes column counts or order, surface a diff and ask before saving.

#### D. Run dbt

Pick the right command based on the user's ask. Always scope with `--select` unless the user explicitly asks for the full project.

| User intent | Command |
|---|---|
| Compile only (no warehouse roundtrip) | `dbt parse` |
| Materialize a model and its upstream | `dbt run --select +<model>` |
| Run tests for a model and its upstream | `dbt test --select +<model>` |
| Materialize + test in DAG order | `dbt build --select +<model>` |
| Rebuild an incremental model from scratch | `dbt build --full-refresh --select <model>` |

Confirm before any `dbt run`, `dbt test`, or `dbt build` on the **whole** project. Those touch the warehouse and can be expensive.

#### E. Switch an output port to incremental

1. Ask the user for the natural key (must be unique per row) and the timestamp column the incremental filter will use.
2. Add the `{{ config(...) }}` block at the top of the model (see the Materializations section above).
3. Add the `{% if is_incremental() %} where <ts> > (select max(<ts>) from {{ this }}) {% endif %}` filter on the deepest CTE that reads from the source.
4. Run `dbt build --full-refresh --select <model>` once with the user's confirmation to seed the table.
5. On the next run, confirm `dbt build --select <model>` only inserts new rows (check `target/run/.../<model>.sql` for the `merge` / `delete+insert` shape).

#### F. Add tests or descriptions

1. Open the relevant `_models.yml`.
2. Add `description:` lines from the user's input or from the contract (for output ports, the contract is the source of truth — do not paraphrase it).
3. Add tests per the Tests table above. Run `dbt parse` to verify YAML.

### Step 3 — Verify

After any operation that wrote SQL or YAML:

- Run `dbt parse` to catch syntax errors and dangling refs.
- If the user authorized it, run `dbt build --select <scope>` to materialize and test the affected models.
- Do not run `dbt run` separately from `dbt test` — `dbt build` orders them correctly and stops on failures.

### Step 4 — Final report

End with this two-part recap. Use the shared `Status` enum: `created`, `updated`, `already present`, `deferred`, `skipped`.

**Part 1 — outcome table.** One row per operation applied.

| Artifact | Status | Details |
|---|---|---|
| Operation | … | A / B / C / D / E / F (one row per operation run) |
| Staging models | … | `<N>` files at `models/staging/stg_<...>.sql` |
| Intermediate models | … | `<N>` files at `models/intermediate/int_<...>.sql` |
| Output-port refactor | … | `<table>.sql` rewritten to ref staging/intermediate / not applicable |
| `_models.yml` entries | … | counts per layer |
| `dbt parse` | … | "passed" / "failed: <reason>" / "skipped" |
| `dbt build --select <scope>` | … | "passed" / "failed: <reason>" / "not run (user did not authorize)" |

**Part 2 — next steps.** Bullet list, include only what applies:

- For each `-- TODO:` left in a generated model, list the model and the open question.
- If staging or intermediate rename decisions were taken without user input, list them so the user can confirm.
- If the user asked for `dbt build` but it was skipped (e.g. missing warehouse creds), the exact env vars they need to set.
- If an output port is approaching the incremental threshold (>5 min, >10M rows/run), suggest operation E.

If there is nothing in Part 2, write a single line: `No further action required.`

## Constraints

- **No business logic in staging.** If a join, aggregation, or `case` involving multiple columns shows up there, push it to `intermediate/`.
- **No `source()` outside staging.** Intermediate and output ports use `ref()` exclusively. If you find a `source()` call elsewhere, surface it and propose operation C.
- **Contract is source of truth for output ports.** Do not edit the column list, types, descriptions, or tests on output-port models from this skill — those come from the ODCS contract. Edits to the contract go through `datacontract-edit`.
- **Idempotent.** Re-running an operation when the target files already match the conventions is a no-op; the skill should report `already present`.
- **Do not push or commit.** Leave VCS state to the user.

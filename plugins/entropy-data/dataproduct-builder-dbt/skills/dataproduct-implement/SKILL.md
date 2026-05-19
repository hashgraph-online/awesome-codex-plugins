---
name: dataproduct-implement
description: Given an Entropy Data data product URL or id, fetch its data contracts (output port ODCS files written next to the SQL under models/output_ports/v<N>/, input port ODCS files cached next to their dbt source under models/input_ports/), translate the schema into dbt models, and ensure the project has the publishing layer (ODPS, OpenLineage, GitHub Actions). Trigger when the user asks to "implement the data product <url>", "build the dbt pipeline for this data product", or "scaffold dbt models from a data contract".
---

# Implement a data product from its data contract

Turn an Entropy Data data product into a working dbt pipeline. The data contract (ODCS) is the source of truth for output schema; this skill reads it and writes the dbt artifacts that produce data matching the contract.

## When to use this vs. other skills

- **Empty directory, no dbt project yet** → run `dataproduct-bootstrap` first, then come back here.
- **Existing dbt project, need ODPS/ODCS/OpenLineage scaffolding only** → use `entropy-data-sync` instead.
- **Existing dbt project, want to derive models from a published data contract** → this skill.

## How to run this skill

> `${PLUGIN_ROOT}` below refers to the root of this plugin — the directory that contains `skills/`. On Claude Code it is set automatically as `${CLAUDE_PLUGIN_ROOT}` — use that. On any other agent (Codex, Copilot CLI, etc.) it is unset; resolve it as `../..` relative to **this `SKILL.md` file's directory** (i.e. the grandparent of `skills/<this-skill>/`).

### Plan announcement (before Step 0)

Before running Step 0, print this plan to the user verbatim:

> Running **dataproduct-implement**. I'll:
> 1. Pre-checks: confirm this is a dbt project, the `dbt` CLI is installed, and the `entropy-data` CLI is connected.
> 2. Resolve the data product by id or URL (`entropy-data dataproducts get`).
> 3. Fetch each selected output port's data contract (`entropy-data datacontracts get`) and save it next to the SQL it governs, under `models/output_ports/v<N>/`.
> 4. Translate the ODCS schema into dbt models under `models/output_ports/v1/` (column list, types, tests).
> 5. Implement the dbt model bodies: declare input ports as dbt sources, cache each upstream contract under `models/input_ports/<provider-op-id>.odcs.yaml` as a trust snapshot, and write the `select` from input ports to output columns (with confirmation; complex joins left as TODOs).
> 6. Stamp the data product on Entropy Data with the `dataProductBuilder` customProperty so the platform knows it is managed by this builder.
> 7. Hand off to `entropy-data-sync` to add any missing publishing artifacts (ODPS, OpenLineage, GitHub Actions).
> 8. Summarize what was generated and the open TODOs.

Then proceed.

### Step 0 — Pre-checks

- Confirm `dbt_project.yml` exists at the working directory root. If not, ask whether to run `dataproduct-bootstrap` first, then stop.
- Confirm `dbt --version` is on PATH. If not, stop and tell the user to install the dbt adapter for their warehouse (e.g. `uv tool install dbt-snowflake`, `uv tool install dbt-databricks`, `uv tool install dbt-bigquery`, `uv tool install dbt-postgres`).
- Confirm `entropy-data --version` is on PATH (install with `uv tool install entropy-data` if not) and `entropy-data connection test` succeeds. If the test fails, stop and tell the user to run `entropy-data connection add <name> --host <host> --api-key <key>`.

### Step 1 — Resolve the data product

Accept either:

- a full URL (e.g. `https://app.entropy-data.com/dataproducts/<id>`) — extract the trailing id, **or**
- a bare data product id.

Run `entropy-data dataproducts get <id> -o yaml`. Remember the response as `DATA_PRODUCT`. Extract:

- `DATA_PRODUCT_ID`, `DATA_PRODUCT_NAME`, owning team, purpose
- the list of output ports — each has an id, a server (catalog/schema/table), and a linked data contract id

If the data product has more than one output port, ask the user which one(s) to implement in this run. Default to all.

If the data product does not exist in Entropy Data, ask the user if they want to create a new one.

### Step 2 — Fetch the data contracts

For each selected output port, run `entropy-data datacontracts get <contract-id> -o yaml` with the contract id from the data product. Remember the response as `CONTRACT`, and write it to `models/output_ports/v<N>/<contract-id>.odcs.yaml` (the version directory matches the output port's version — default `v1` if the data product does not declare one). If the file already exists and differs from the fetched contract, surface the diff and ask before overwriting.

The fields you need from `CONTRACT`:

- `models` (table name → list of fields with `type`, `required`, `unique`, `description`, `classification`)
- `servers` (so the output port's server config is consistent with the contract)
- `terms` and `quality` rules — useful context but not required to materialize the model

### Step 3 — Translate ODCS schema to dbt artifacts

For each contract:

1. Decide a dbt-side table name. Default: the `models` key in the contract. Confirm with the user if it differs from the output-port server's table name.
2. **Identify candidate input ports.** Run `entropy-data access list --consumer-dataproduct <DATA_PRODUCT_ID> -o json` to list the access agreements where this product is the consumer. Each entry's `provider.dataProductId` / `provider.outputPortId` is an input port this product can read. Keep only agreements with `info.active: true` (status `approved`); ignore `pending` / `rejected`. Only fall back to a broader `entropy-data search query` if the user explicitly asks. If `models/input_ports/<provider-output-port-id>.source.yaml` already exists for an agreement, treat it as authoritative and skip recreating it.
3. Generate `models/output_ports/v1/<table>.sql` — a stub `select` that lists the contract columns explicitly with `cast(... as <warehouse-type>) as <column>`. **Leave the `from` clause as a TODO** with a comment listing the candidate input ports from the previous step; do not invent business logic. Prepend a one-line header comment so a reader of the file knows which contract governs the schema:

   ```sql
   -- Governed by <contract-file>.odcs.yaml (ODCS id: <CONTRACT_ID>)
   ```

   The contract file sits in the same directory as the SQL, so the comment names the file without a path prefix.
4. Append the column list to `models/output_ports/v1/_models.yml` under `models:` — name, description (from contract), and tests derived from the contract: `not_null` for `required: true`, `unique` for `unique: true`, `accepted_values` if the contract defines an enum. Add a `config.meta.data_contract` block on the model that points back to the contract — this is the machine-readable counterpart to the SQL header comment, so `dbt list --select config.meta.data_contract.id:<id>`, dbt-docs, and lineage tooling can discover the link:

   ```yaml
   models:
     - name: <table>
       description: <from contract>
       config:
         meta:
           data_contract:
             id: <CONTRACT_ID>
             file: models/output_ports/v<N>/<contract-file>.odcs.yaml
       columns:
         - ...
   ```
5. Map ODCS types to the warehouse dialect:

| ODCS `type` | Databricks | Snowflake | BigQuery | Postgres |
|---|---|---|---|---|
| `string`/`text` | `string` | `varchar` | `string` | `text` |
| `integer`/`long` | `bigint` | `number` | `int64` | `bigint` |
| `decimal`/`numeric` | `decimal(38,9)` | `number(38,9)` | `numeric` | `numeric` |
| `boolean` | `boolean` | `boolean` | `bool` | `boolean` |
| `timestamp` | `timestamp` | `timestamp_ntz` | `timestamp` | `timestamp` |
| `date` | `date` | `date` | `date` | `date` |

Pick the dialect from the contract's `servers[].type` (or, if absent, ask).

### Step 4 — Implement the model bodies

Ask the user: "Want me to wire the output-port models to the input ports, or leave the `from` clauses as TODOs?" Default to wiring them. If the user declines, skip this step and continue with the next one.

For each output port table:

1. **Declare each candidate input port as a dbt source — one file per agreement, plus a trust-snapshot of the upstream contract.** For every agreement from Step 3.2:

   1. Fetch the provider data product (`entropy-data dataproducts get <provider-data-product-id> -o yaml`) to resolve the output port's `server` (catalog/schema/table) and linked contract id.
   2. Fetch the contract (`entropy-data datacontracts get <provider-contract-id> -o yaml`) for columns.
   3. Write the fetched contract to `models/input_ports/<provider-output-port-id>.odcs.yaml`. This is a **cached snapshot of what we trust upstream to produce** — it lets `git log` show when upstream's schema or quality rules changed under us. Do not hand-edit this file; the next run of this skill will refresh it from the platform. If the file already exists and the upstream contract has changed, surface the diff (so the user sees the drift) and ask before overwriting.
   4. Write the dbt source file to `models/input_ports/<provider-output-port-id>.source.yaml`:

      ```yaml
      version: 2
      sources:
        - name: <provider-data-product-id>_<provider-output-port-id>
          database: <output port server.catalog>
          schema: <output port server.schema>
          config:
            meta:
              data_contract:
                id: <provider-contract-id>
                file: models/input_ports/<provider-output-port-id>.odcs.yaml
          tables:
            - name: <table>   # from the contract's `models:` key — one entry per table in the contract
              description: <from contract>
              columns:
                - name: <col>
                  description: <from contract>
                  data_type: <warehouse type from the type map in Step 3>
      ```

   The `sources[].name` combines `<provider-data-product-id>_<provider-output-port-id>` so it stays unique across agreements (two agreements with the same provider data product but different output ports do not collide). Each `tables:` entry comes from the provider contract's `models:` block — a contract can declare multiple tables, and each one becomes a row here. The `meta.data_contract` reference goes on the source element (one contract per output port), not on each table, and points at the local snapshot written in sub-step 3.

   One pair of files (`*.odcs.yaml` + `*.source.yaml`) per agreement. Do not merge multiple agreements into a single file — each access grant should be independently visible in `git log` and easy to remove when revoked. If either file already exists for the same `<provider-output-port-id>`, surface the diff and ask before overwriting.
2. **Match input columns to output columns.** Build a column-by-column map: for each output column in the contract, find the input column with the same name (or an obvious synonym, e.g. `customer_id` ↔ `account_id` only if the input contract's `description` makes it explicit). Don't guess — if no clear match, leave that column as a `null as <col>` placeholder with a `-- TODO: derive from ...` comment.
3. **Write the SQL body.**
   - **Single input source, columns match 1:1** → replace the TODO `from` with `from {{ source('<provider-data-product-id>_<provider-output-port-id>', '<table>') }}` (the first arg matches `sources[].name`, the second matches `tables[].name` — i.e. the contract's model key — from the source file written in step 4.1) and project each output column with `cast(<input_col> as <warehouse_type>) as <output_col>`.
   - **Multiple input sources** → leave the join logic as an inline TODO listing each candidate `{{ source(...) }}` reference and the join keys the user will need to confirm. Do not invent join predicates.
   - **Derived / aggregated columns** (sums, ratios, windows implied by the contract description but not present in any input) → leave as `null as <col>` with a `-- TODO: compute <description from contract>` comment.
4. **Compile to verify.** Run `dbt parse` (cheap, no warehouse roundtrip) to catch syntax errors and unknown source references. If it fails, fix the generated SQL before continuing. Do not run `dbt run` — that touches the warehouse and is the user's call.

### Step 5 — Stamp the data product as builder-managed

Check `DATA_PRODUCT.customProperties` for an entry with `property: "dataProductBuilder"` and `value: "https://github.com/entropy-data/dataproduct-builder-dbt"`. If it is already there, skip this step.

If missing, update the data product on Entropy Data so the platform records that it is managed by this builder. Do **not** rebuild the ODPS from a template — preserve every other field as fetched in Step 1.

1. Save the fetched data product to a temp file as YAML: `entropy-data dataproducts get <DATA_PRODUCT_ID> -o yaml > /tmp/<DATA_PRODUCT_ID>.odps.yaml`.
2. Append to the top-level `customProperties` list (create the list if absent):
   ```yaml
   customProperties:
     - property: "dataProductBuilder"
       value: "https://github.com/entropy-data/dataproduct-builder-dbt"
   ```
3. Push the patched file back: `entropy-data dataproducts put <DATA_PRODUCT_ID> --file /tmp/<DATA_PRODUCT_ID>.odps.yaml`.
4. Delete the temp file.

Forks of this plugin should substitute their own builder URL.

### Step 6 — Hand off to entropy-data-sync

Call the **entropy-data-sync** skill (in this same plugin) so any missing publishing artifacts get created (`<id>.odps.yaml`, `openlineage.yml`, `.github/workflows/data-product.yml`). Pass the parameters you already resolved in Step 1 so the user is not re-asked.

If `<id>.odps.yaml` already exists locally and disagrees with the fetched data product, **do not overwrite** — surface the diff and ask.

### Step 7 — Final report

End with this two-part recap. Use the same `Status` enum the other skills use: `created`, `updated`, `already present`, `deferred`, `skipped`.

**Part 1 — outcome table.** One row per output port implemented.

| Artifact | Status | Details |
|---|---|---|
| Data product | already present | `<DATA_PRODUCT_ID>` — fetched from platform |
| `dataProductBuilder` customProperty | … | "added — pushed to Entropy Data" / "already present" |
| Output-port data contract `<CONTRACT_ID>` | … | written to `models/output_ports/v<N>/<contract_id>.odcs.yaml` |
| Input-port data contracts | … | `models/input_ports/<provider-output-port-id>.odcs.yaml` — `<N>` files written / refreshed (trust snapshots, one per active access agreement) / skipped |
| Input port sources | … | `models/input_ports/<provider-output-port-id>.source.yaml` — `<N>` files written (one per active access agreement) / skipped |
| Model `<table>.sql` | … | `models/output_ports/v1/<table>.sql` — "wired to `<source>`" / "join TODO" / "skipped per user" |
| `_models.yml` entry for `<table>` | … | tests derived from the contract |
| `dbt parse` | … | "passed" / "failed: <reason>" / "skipped" |
| `entropy-data-sync` handoff | … | "ran" / "skipped" — see sync's own report for ODPS/OpenLineage/workflow rows |

**Part 2 — next steps.** Bullet list, include only what applies:

- For each model with a join or derived-column TODO, list the inputs and the missing logic — one bullet per `<table>.sql`.
- Run `dbt run` and `dbt test` locally to verify the generated models compile and pass the contract-derived tests.
- Run the contract test on the output ports against your warehouse: `datacontract test models/output_ports/v<N>/<file>.odcs.yaml` for each contract.
- Any deferred items from the sync skill's report.

If there is nothing in Part 2, write a single line: `No further action required.`

## Constraints

- **Contract is source of truth for schema, not logic.** Generate column names, types, and tests from the contract. When wiring SQL bodies in Step 4, project and cast only — do not invent join predicates, aggregations, or column derivations. Anything not directly mappable from an input column stays a TODO.
- **Don't overwrite existing dbt SQL files**. If `models/output_ports/v1/<table>.sql` already exists, surface the diff and ask before changing.
- **Idempotent**: re-running the skill with the same data product id should be a no-op when contract and local files already agree.
- **Do not commit or push** — leave VCS state to the user.

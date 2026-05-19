---
name: datacontract-test
description: Run the Data Contract CLI (`datacontract test`) against ODCS contracts in the project to verify the live data still conforms — schema, quality rules, and freshness. Handles two kinds of contracts with different semantics: output-port contracts under `models/output_ports/**/*.odcs.yaml` (tested against this project's warehouse — "am I still producing what I promised?") and input-port contracts under `models/input_ports/*.odcs.yaml` (tested against the upstream warehouse — "is upstream still producing what I trusted?"). Trigger when the user asks to "test the data contracts", "verify the data product matches its contract", "are we still contract-conformant", "check upstream drift", or "run the contract tests".
---

# Test ODCS data contracts against the live server

Run the **Data Contract CLI** (`datacontract test`) against contracts in the project to check whether the data currently produced by a warehouse still matches the schema and quality rules declared in the contract.

Two kinds of contracts live in this project and they test against different warehouses:

- **Output-port contracts** at `models/output_ports/v<N>/*.odcs.yaml` — what this data product commits to produce. They test against **this project's** warehouse. A failure means we are no longer producing what we promised.
- **Input-port contracts** at `models/input_ports/*.odcs.yaml` — cached snapshots of what we trust upstream to produce. They test against the **upstream provider's** warehouse, using a server block from upstream's ODCS. A failure means upstream drifted from the contract we trusted; the consequence is that *our* output may break too. Treat input-port failures as an upstream incident, not a local bug.

## When to use this vs. other skills

- **You changed a contract and want to know if the edit breaks consumers** → use `datacontract-edit` (it edits, tests, *and* classifies the failure as breaking-or-not).
- **You want to verify existing contracts against current data, no edits** → this skill.
- **A CI run failed the contract test step** → this skill, to reproduce locally with `--logs`.

## How to run this skill

> `${PLUGIN_ROOT}` below refers to the root of this plugin — the directory that contains `skills/`. On Claude Code it is set automatically as `${CLAUDE_PLUGIN_ROOT}` — use that. On any other agent (Codex, Copilot CLI, etc.) it is unset; resolve it as `../..` relative to **this `SKILL.md` file's directory** (i.e. the grandparent of `skills/<this-skill>/`).

### Plan announcement (before Step 0)

Before running Step 0, print this plan to the user verbatim:

> Running **datacontract-test**. I'll:
> 1. Pre-checks: confirm the `datacontract` CLI is on PATH and the server credentials are available.
> 2. Pick which contract(s) to test — defaults to all `models/output_ports/**/*.odcs.yaml` and `models/input_ports/*.odcs.yaml`.
> 3. Pick the server (defaults to `production` if the contract has one).
> 4. Run `datacontract test` per contract and capture the result.
> 5. Report pass/fail with per-rule detail; flag missing credentials separately from real failures.

Then proceed.

### Step 0 — Pre-checks

- Confirm `datacontract --version` is on PATH. If not, stop and tell the user to install it (e.g. `uv tool install 'datacontract-cli[all]'`).
- Confirm at least one `*.odcs.yaml` exists under `models/output_ports/**/` or `models/input_ports/`. If not, stop and tell the user there's nothing to test.
- For each contract that will run, inspect its `servers` block and list the env vars the chosen server type needs (e.g. `DATACONTRACT_SNOWFLAKE_USERNAME` / `..._PASSWORD`, `DATACONTRACT_DATABRICKS_TOKEN`, `DATACONTRACT_BIGQUERY_ACCOUNT_INFO_JSON`). If any are unset, surface the list to the user and ask whether to continue (the CLI will fail-fast on that server) or stop. Do not try to source credentials yourself.

### Step 1 — Select contracts

- If the user named a specific contract file or data product id, resolve it to one file. Search both `models/output_ports/**/*.odcs.yaml` and `models/input_ports/*.odcs.yaml`.
- If the user said "output contracts" / "input contracts" / "upstream drift", scope to one of those globs.
- If they didn't, default to **all** ODCS files under both globs. List them, grouped by **Output ports** and **Input ports** so the user sees the two roles, then ask before running.
- Remember the resolved list as `CONTRACTS`. For each entry, also remember its role (`output` or `input`) — Step 4 surfaces failures differently.

### Step 2 — Select the server

For each contract in `CONTRACTS`:

- If the contract has exactly one server, use it.
- If it has multiple, default to `production`. If `production` isn't defined, ask the user which one.
- Only pass `--server all` if the user explicitly asks to test every server.

### Step 3 — Run the test

For each contract:

```
datacontract test <path-to-contract>.odcs.yaml --server <server> --logs
```

Where `<path-to-contract>` is the file resolved in Step 1 — typically `models/output_ports/v<N>/<file>.odcs.yaml` for output contracts, or `models/input_ports/<file>.odcs.yaml` for input contracts. The CLI does not care which directory; the role only matters for how Step 4 reports the result.

- `--logs` ensures per-rule failure detail is in stdout — without it the CLI only prints a summary.
- If the user asks for a persisted report (e.g. to attach to a PR), add `--output ./test-results/<contract>.xml --output-format junit`.
- If the user asks to publish results back to Entropy Data (matches the generated CI workflow), add `--publish $API/test-results` where `$API` is the Entropy Data host. Don't publish by default — it writes server-side state.
- Capture stdout and exit code per contract. Non-zero exit means at least one rule failed.

Run sequentially, not in parallel — the warehouse is the bottleneck and parallel runs muddy the log output.

### Step 4 — Report

End with this two-part recap. Use the shared `Status` enum (`created`, `updated`, `already present`, `deferred`, `skipped`); for this skill the relevant statuses are `passed`, `failed`, and `skipped` (missing creds).

**Part 1 — outcome table.** One row per contract tested. Group the rows: output-port contracts first, then input-port contracts under a sub-header (so the reader sees the two roles at a glance).

| Contract | Role | Server | Result | Failures | Details |
|---|---|---|---|---|---|
| `<contract-file>` | `output` / `input` | `<server>` | `passed` / `failed` / `skipped` | count or `—` | one line per failing rule (field + rule), or "missing env var: …" if skipped |

**Part 2 — next steps.** Bullet list, include only what applies. Treat output vs. input failures differently:

- **Output-port failures**: surface the field and the violated check (e.g. `orders.order_id: not_null violated for 17 rows`). The fix is in this project — either the dbt model is wrong, the contract is wrong, or the data is wrong. If the user wants a follow-up SQL to find the offending rows, suggest the shape but don't run it. If failures look like they came from a contract edit (rules tightening), point at `datacontract-edit` to classify breaking-vs-additive.
- **Input-port failures**: this is upstream drift. Name the provider data product and output port (from the contract id and file name). The fix is *not* in this project — the user should contact the upstream owner, and in the meantime expect downstream output-port failures. Suggest re-running `dataproduct-implement` once upstream republishes a corrected contract, so the cached snapshot under `models/input_ports/` refreshes.
- For each `skipped` row, the exact env vars the user needs to set, and where to get them (usually the warehouse admin or `entropy-data connection get`).
- If failures look like a data quality issue (rules unchanged, data drifted), suggest investigating the upstream of the failing model — this skill does not auto-fix data.

If everything passed, write a single line: `All <N> contracts pass against <server>.`

## Authentication examples by server type

The Data Contract CLI reads credentials from environment variables, not from the contract file. Only the connection topology (host, database, schema, etc.) belongs in the `servers` block. The examples below cover the most common warehouses. Other types (Oracle, MySQL, Trino, DuckDB, Kafka, ...) follow the same pattern; see the [Data Contract CLI README](https://github.com/datacontract/datacontract-cli) for the full list.

### Snowflake

ODCS server block:

```yaml
servers:
  production:
    type: snowflake
    account: abcdefg-xn12345
    database: ORDER_DB
    schema: ORDERS_PII_V2
```

Any env var prefixed `DATACONTRACT_SNOWFLAKE_` is forwarded to the Snowflake connector with the prefix stripped and the rest lowercased, so you can pass any Snowflake/Soda parameter this way. Three auth modes:

**Password auth**
```bash
export DATACONTRACT_SNOWFLAKE_USERNAME=...
export DATACONTRACT_SNOWFLAKE_PASSWORD=...
export DATACONTRACT_SNOWFLAKE_WAREHOUSE=COMPUTE_WH
export DATACONTRACT_SNOWFLAKE_ROLE=DATA_CONTRACT_TEST
```

**Private key (JWT) auth** — used for service accounts and CI:
```bash
export DATACONTRACT_SNOWFLAKE_USERNAME=SVC_DATACONTRACT
export DATACONTRACT_SNOWFLAKE_AUTHENTICATOR=SNOWFLAKE_JWT
export DATACONTRACT_SNOWFLAKE_PRIVATE_KEY_PATH=/secrets/snowflake_rsa.p8
# Only if the key is encrypted:
export DATACONTRACT_SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=...
export DATACONTRACT_SNOWFLAKE_WAREHOUSE=COMPUTE_WH
export DATACONTRACT_SNOWFLAKE_ROLE=DATA_CONTRACT_TEST
```

**External browser SSO** — interactive, for local runs against an IdP-backed account:
```bash
export DATACONTRACT_SNOWFLAKE_USERNAME=jane.doe@example.com
export DATACONTRACT_SNOWFLAKE_AUTHENTICATOR=externalbrowser
export DATACONTRACT_SNOWFLAKE_WAREHOUSE=COMPUTE_WH
export DATACONTRACT_SNOWFLAKE_ROLE=DATA_CONTRACT_TEST
```

Not usable in CI — it opens a browser window.

### Databricks

ODCS server block:

```yaml
servers:
  production:
    type: databricks
    host: adb-1234567890.7.azuredatabricks.net   # optional, can also come from env
    catalog: acme_catalog_prod
    schema: orders_latest
```

Env vars:
```bash
export DATACONTRACT_DATABRICKS_TOKEN=dapi...               # required
export DATACONTRACT_DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/abc123def456
export DATACONTRACT_DATABRICKS_SERVER_HOSTNAME=adb-...     # only needed if `host` is not in the server block
```

The token is a Databricks personal access token or service-principal OAuth token. Read access on the catalog + schema is enough.

### Postgres

ODCS server block:

```yaml
servers:
  production:
    type: postgres
    host: db.example.internal
    port: 5432
    database: analytics
    schema: public
```

Env vars:
```bash
export DATACONTRACT_POSTGRES_USERNAME=datacontract_ro
export DATACONTRACT_POSTGRES_PASSWORD=...
```

Both are required. Use a read-only role.

### Amazon Athena

ODCS server block:

```yaml
servers:
  production:
    type: athena
    catalog: awsdatacatalog           # optional, default is awsdatacatalog
    schema: orders_db
    regionName: eu-central-1
    stagingDir: s3://acme-athena-results/datacontract/
```

Env vars:
```bash
export DATACONTRACT_S3_ACCESS_KEY_ID=AKIA...          # required
export DATACONTRACT_S3_SECRET_ACCESS_KEY=...          # required
export DATACONTRACT_S3_REGION=eu-central-1            # optional, overrides regionName
export DATACONTRACT_S3_SESSION_TOKEN=...              # optional, for STS temporary creds
```

The IAM principal needs `athena:*` on the workgroup, `glue:Get*` on the catalog, and read/write on the `stagingDir` bucket prefix.

### BigQuery

ODCS server block:

```yaml
servers:
  production:
    type: bigquery
    project: acme-data-prod
    dataset: orders
```

Two auth modes:

**Service account key file**
```bash
export DATACONTRACT_BIGQUERY_ACCOUNT_INFO_JSON_PATH=/secrets/bq-sa.json
```

**Application Default Credentials (ADC)** — no env vars needed. Used automatically when `DATACONTRACT_BIGQUERY_ACCOUNT_INFO_JSON_PATH` is unset. Works with `gcloud auth application-default login` for local runs and with Workload Identity Federation in CI.

Optional impersonation:
```bash
export DATACONTRACT_BIGQUERY_IMPERSONATION_ACCOUNT=datacontract@acme-data-prod.iam.gserviceaccount.com
```

The principal needs `bigquery.dataViewer` on the dataset and `bigquery.jobUser` on the project.

### Microsoft Fabric (SQL Server protocol)

Fabric Warehouse and Lakehouse SQL endpoints speak the SQL Server wire protocol, so use `type: sqlserver`.

ODCS server block:

```yaml
servers:
  production:
    type: sqlserver
    host: abc123def.datawarehouse.fabric.microsoft.com
    port: 1433
    database: orders_wh
    schema: dbo
    driver: ODBC Driver 18 for SQL Server
```

Fabric only accepts Entra ID (Azure AD) auth, not SQL logins. Pick one of:

**Service principal** — for CI:
```bash
export DATACONTRACT_SQLSERVER_AUTHENTICATION=ActiveDirectoryServicePrincipal
export DATACONTRACT_SQLSERVER_CLIENT_ID=<app-registration-client-id>
export DATACONTRACT_SQLSERVER_CLIENT_SECRET=<client-secret>
```

**User password** — Entra ID username + password (no MFA):
```bash
export DATACONTRACT_SQLSERVER_AUTHENTICATION=ActiveDirectoryPassword
export DATACONTRACT_SQLSERVER_USERNAME=jane.doe@acme.com
export DATACONTRACT_SQLSERVER_PASSWORD=...
```

**Interactive** — opens a browser, for local dev only:
```bash
export DATACONTRACT_SQLSERVER_AUTHENTICATION=ActiveDirectoryInteractive
export DATACONTRACT_SQLSERVER_USERNAME=jane.doe@acme.com
```

The same env vars work for a regular on-prem SQL Server; switch `DATACONTRACT_SQLSERVER_AUTHENTICATION=sql` and supply `DATACONTRACT_SQLSERVER_USERNAME` / `DATACONTRACT_SQLSERVER_PASSWORD`.

Install ODBC Driver 18 locally (`brew install msodbcsql18` on macOS, `apt-get install msodbcsql18` on Debian/Ubuntu) before running.

## Constraints

- **Read-only against the warehouse.** This skill runs `datacontract test` which executes `SELECT` queries; it never writes. Do not invoke `datacontract publish`, `datacontract export`, or `entropy-data datacontracts put` from this skill.
- **No edits to contracts or models.** If a test fails, surface it — do not auto-patch the contract to make it pass. That defeats the purpose.
- **No credential sourcing.** If env vars are missing, tell the user; don't read them from `.env`, `~/.aws`, or anywhere else on the user's behalf.
- **Idempotent**: re-running the skill produces the same report against the same data. Failures from rules that depend on time (freshness, row-count windows) are expected to drift — note that in the failure detail when relevant.

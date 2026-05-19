---
name: entropy-data-sync
description: Audit a dbt project against the Entropy Data reference layout and add anything missing — Open Data Product Specification (ODPS), Open Data Contract Standard (ODCS), OpenLineage transport config, output-port model layout, and the GitHub Actions publish workflow. Trigger when the user asks to integrate a dbt project with Entropy Data, set up Entropy Data publishing, or check whether a dbt project follows the Entropy Data conventions.
---

# Entropy Data integration for dbt projects

Make sure a dbt project is well-integrated with Entropy Data.

## What "well-integrated" means

A dbt project is well-integrated with Entropy Data when it has all of:

| # | Artifact | Path | Purpose |
|---|---|---|---|
| 1 | Open Data Product Specification | `<data-product-id>.odps.yaml` at repo root | Declares the data product, team, output ports |
| 2 | Output-port data contracts | `models/output_ports/v<N>/<contract-id>.odcs.yaml` (one per output port — what this data product **commits** to produce) | Schema + server config the contract test runs against; colocated with the SQL that implements it |
| 3 | Input-port data contracts | `models/input_ports/<provider-output-port-id>.odcs.yaml` (one per active access agreement — what this data product **trusts** upstream to produce) | Cached snapshot of the upstream provider's ODCS; refreshed via `entropy-data datacontracts get`, never hand-edited |
| 4 | OpenLineage transport | `openlineage.yml` at repo root | Makes `dbt-ol run` send lineage to `api.entropy-data.com` |
| 5 | Model layout | `models/{input_ports,staging,intermediate,output_ports/v1}/` | Convention that mirrors the data product's lifecycle |
| 6 | Publish workflow | `.github/workflows/data-product.yml` | CI: dbt run/test → publish ODPS + output ODCS → run contract test |
| 7 | Git connections | One per ODPS + one per output-port ODCS, registered via `entropy-data dataproducts gitconnection put` and `entropy-data datacontracts gitconnection put` | Lets Entropy Data link the published spec back to the YAML in the repo, and enables `pull` / `push` / `push-pr` from the CLI. Input-port ODCS files are *not* registered — they belong to the upstream data product, which owns its own git connection |

## How to run this skill

Work in this exact order. Do not skip the audit.

> `${PLUGIN_ROOT}` below refers to the root of this plugin — the directory that contains `skills/`. On Claude Code it is set automatically as `${CLAUDE_PLUGIN_ROOT}` — use that. On any other agent (Codex, Copilot CLI, etc.) it is unset; resolve it as `../..` relative to **this `SKILL.md` file's directory** (i.e. the grandparent of `skills/<this-skill>/`).

### Plan announcement (before Step 0)

Before running Step 0, print the following plan to the user verbatim so they know what's about to happen:

> Running **entropy-data-sync**. I'll:
> 1. Verify the `entropy-data` CLI is installed and connected.
> 2. Confirm this is a dbt project and pick up its name.
> 3. Audit existing Entropy Data artifacts (ODPS, ODCS, OpenLineage, model layout, publish workflow, git connections).
> 4. Gather any missing parameters from you (one batched question).
> 5. Apply fixes — create missing files, patch incomplete ones, register git connections.
> 6. Summarize what changed and what's deferred.

Then proceed.

### Step 0 — Verify the Entropy Data CLI connection

Confirm `entropy-data --version` is on PATH. If missing, tell the user to run `uv tool install entropy-data` and stop.

Run `entropy-data connection test`. If it fails (no connection, expired key, etc.), stop and tell the user to run `entropy-data connection add <name> --host <host> --api-key <key>` first. Do not prompt for the key yourself.

### Step 1 — Confirm this is a dbt project

Check that `dbt_project.yml` exists at the working directory root. If not, stop and tell the user this skill only works inside a dbt project.

Read `dbt_project.yml` and remember the `name:` value — call it `DBT_PROJECT_NAME`. By convention it is also the dbt profile and the data product id.

### Step 2 — Audit

For each row in the table above, check whether the artifact is present. For row 7 (git connections), call:

- `entropy-data dataproducts gitconnection get <DATA_PRODUCT_ID> -o json`
- `entropy-data datacontracts gitconnection get <CONTRACT_ID> -o json` for each output-port contract under `models/output_ports/**/`

For rows 2 and 3, glob the file system:

- Output contracts: `models/output_ports/**/*.odcs.yaml`
- Input contracts: `models/input_ports/*.odcs.yaml`

Legacy projects may still have contracts at the old `datacontracts/` path. If `datacontracts/` exists and contains `*.odcs.yaml` files, flag those rows as **migration needed** and surface the move target (output contracts → `models/output_ports/v1/`; input contracts, if any, → `models/input_ports/`). Do not move them silently — Step 4 asks the user.

If a `get` returns a 404 (or "not found"), mark that connection as missing. If it returns a connection whose `repository-url` / `repository-path` / `repository-branch` does not match the local repo, mark it as **drifted** and call it out separately — do not silently overwrite. If the underlying data product or contract doesn't exist on the platform yet (the workflow hasn't run for the first time), or if the working directory is not a git repository (`git rev-parse --is-inside-work-tree` errors or returns `false`), mark git connections as **deferred** with a one-line explanation.

For row 1 (ODPS file), also check that the top-level `customProperties` list contains an entry with `property: "dataProductBuilder"` and `value: "https://github.com/entropy-data/dataproduct-builder-dbt"`. If the file exists but the property is missing, mark the ODPS as **incomplete** with a one-line note ("missing dataProductBuilder customProperty"); Step 4 will add it without touching other fields. Forks of this plugin should substitute their own builder URL in the template before publishing.

Produce a short audit report like:

```
Entropy Data integration audit for <DBT_PROJECT_NAME>:
  [✓] ODPS file
  [✗] Output-port contracts (no *.odcs.yaml under models/output_ports/)
  [⏸] Input-port contracts (none — populated by dataproduct-implement from access agreements)
  [✓] openlineage.yml
  [✗] Model layout (no models/output_ports)
  [✗] GitHub Actions publish workflow
  [⏸] Git connections (deferred: data product not yet published — run the workflow first)
```

Show the report. Then list what you intend to create. **Wait for the user to confirm before writing any files.**

### Step 3 — Gather parameters (only ask for what you cannot infer)

Before generating files, fill in these placeholders. Infer from the project where you can; ask the user for the rest in one batched question.

| Placeholder | Default / inference | Notes |
|---|---|---|
| `DATA_PRODUCT_ID` | `DBT_PROJECT_NAME` | Used as `id` in ODPS and as the dbt profile name |
| `DATA_PRODUCT_NAME` | Title-cased `DBT_PROJECT_NAME` | Human-friendly name |
| `OUTPUT_PORT_NAME` | `DBT_PROJECT_NAME` | One output port per ODCS file |
| `CONTRACT_ID` | `<DATA_PRODUCT_ID>-v1` | Stable id used by `entropy-data datacontracts put` |
| `CONTRACT_FILE` | `<contract_id>.odcs.yaml` | File under `models/output_ports/v1/` |
| `CONTRACT_PATH` | `models/output_ports/v1/<CONTRACT_FILE>` | Full repo-relative path; used by `--repository-path`, the CI workflow, and `datacontract test` |
| `TABLE` | last segment of `DBT_PROJECT_NAME` | Output table name |
| `PURPOSE` | — | Ask the user (one sentence) |
| `TEAM_NAME` | — | If `<DATA_PRODUCT_ID>.odps.yaml` already exists with a `team.name`, use that. Otherwise, prefer a team `id` registered in Entropy Data — invoke the **entropy-data-teams** skill (in this same plugin) so the user can pick from the existing teams, and use the returned `id`. Fall back to a free-text answer only if `entropy-data-teams` cannot run (CLI unavailable / not authenticated) |
| `TAG` | — | Ask the user (e.g. a `usecases/...` slug) |
| `PLATFORM` | — | Ask the user: `databricks`, `snowflake`, `bigquery`, `s3`, `postgres` |
| `CATALOG` / `SCHEMA` | — | Ask the user (Databricks: catalog + schema; Snowflake: database + schema; BigQuery: project + dataset) |
| `DBT_PROFILE` | `DBT_PROJECT_NAME` | Used in the workflow's `profiles.yml` block |
| `ODPS_FILE` | `<DATA_PRODUCT_ID>.odps.yaml` | Path passed to `entropy-data dataproducts put` |
| `API_HOST` | `entropy-data connection get -o json` → `host` | Resolve in Step 4, only when writing `openlineage.yml` or the workflow. Uses the same host the CLI is authenticated against, so lineage and CI publish hit the same deployment |
| `GIT_REPOSITORY_URL` | `git remote get-url origin` | Used by `gitconnection put`. If no `origin`, ask the user; if the remote is `git@…` SSH form, convert to the equivalent HTTPS URL the platform expects |
| `GIT_REPOSITORY_BRANCH` | `git rev-parse --abbrev-ref HEAD`, falling back to `main` | Used by `gitconnection put`; if HEAD is detached, ask the user |
| `GIT_CONNECTION_TYPE` | inferred from `GIT_REPOSITORY_URL`: `github.com` → `github`, `gitlab.com` → `gitlab`, `bitbucket.org` → `bitbucket`, `dev.azure.com` / `*.visualstudio.com` → `azuredevops` | Ask the user only if the host doesn't match any of these |
| `GIT_HOST` | the URL host, **only when self-hosted** (i.e. not one of the SaaS hosts above); otherwise omit | Passed as `--host` to `gitconnection put` |
| `GIT_CREDENTIAL_EXTERNAL_ID` | — | Optional. Ask the user; if they don't have one yet, leave the connection unauthenticated (it can still be used for read-only metadata in the UI) |

### Step 4 — Apply the fixes

For each missing artifact, copy the corresponding template from `${PLUGIN_ROOT}/skills/entropy-data-sync/templates/` into the user's project, substituting placeholders. Do **not** overwrite existing files; if a file is present but incomplete, surface the diff and ask before changing.

When (and only when) you're about to write `openlineage.yml` or `.github/workflows/data-product.yml`, resolve `API_HOST` from the active CLI connection:

```
entropy-data connection get -o json
```

Use the `host` field to substitute `{{API_HOST}}` in those templates. Self-hosted deployments are handled via `entropy-data connection add --host <host>`, not a plugin-level setting.

If the ODPS file exists but was flagged as **incomplete — missing dataProductBuilder customProperty** in Step 2, append the entry to the top-level `customProperties` list (do not reorder or touch other entries):

```yaml
customProperties:
  - property: "dataProductBuilder"
    value: "https://github.com/entropy-data/dataproduct-builder-dbt"
```

Surface the diff and ask before saving.

The templates live at:

- `templates/data-product.odps.yaml` → write to `<DATA_PRODUCT_ID>.odps.yaml`
- `templates/models/output_ports/v1/contract.odcs.yaml` → write to `<CONTRACT_PATH>` (i.e. `models/output_ports/v1/<CONTRACT_FILE>`)
- `templates/openlineage.yml` → write to `openlineage.yml`
- `templates/.github/workflows/data-product.yml` → write to `.github/workflows/data-product.yml`

If the audit reported a legacy `datacontracts/` directory, ask the user before moving its contents. The default migration is:

- `datacontracts/<contract>.odcs.yaml` → `models/output_ports/v1/<contract>.odcs.yaml` (if it matches an output port). If multiple output port versions exist, ask which one.
- Update the git connection's `--repository-path` for each moved contract (Step 4b).
- Delete the now-empty `datacontracts/` directory only after the user confirms the move.

This skill does not create input-port ODCS files. They appear only when `dataproduct-implement` resolves an access agreement and writes the cached upstream contract to `models/input_ports/`. If the audit found stale input-port ODCS files (no matching `.source.yaml`), surface them as orphans and let the user decide whether to delete them.

For the model layout, create the directories `models/input_ports/`, `models/staging/`, `models/intermediate/`, `models/output_ports/v1/` if absent, plus `_models.yml` placeholders so dbt does not warn about empty directories. Do not move existing models — only add the empty subfolders the user is missing, and note it in the report.

Also update `dbt_project.yml`'s `models:` block so the materializations match the reference (output port = `table`, staging/intermediate = `view`):

```yaml
models:
  <DBT_PROJECT_NAME>:
    +materialized: table
    staging:
      +materialized: view
    intermediate:
      +materialized: view
```

If the `models:` block already exists, only add missing keys; do not clobber the user's customizations.

#### Step 4b — Configure git connections

Only run this sub-step if the audit (Step 2) flagged at least one git connection as **missing** or the user confirmed re-creating a **drifted** one. Skip entirely if every connection is already correct, if the audit marked them as **deferred**, or if the working directory is not a git repository (check with `git rev-parse --is-inside-work-tree` — if it errors or returns `false`, there's no remote to register; tell the user to run `git init` and add a remote first, then re-run this skill).

For the data product:

```
entropy-data dataproducts gitconnection put <DATA_PRODUCT_ID> \
  --repository-url <GIT_REPOSITORY_URL> \
  --repository-path <ODPS_FILE> \
  --repository-branch <GIT_REPOSITORY_BRANCH> \
  --git-connection-type <GIT_CONNECTION_TYPE> \
  [--host <GIT_HOST>] \
  [--git-credential-external-id <GIT_CREDENTIAL_EXTERNAL_ID>]
```

For each output-port ODCS file (`models/output_ports/**/*.odcs.yaml`):

```
entropy-data datacontracts gitconnection put <CONTRACT_ID> \
  --repository-url <GIT_REPOSITORY_URL> \
  --repository-path <CONTRACT_PATH> \
  --repository-branch <GIT_REPOSITORY_BRANCH> \
  --git-connection-type <GIT_CONNECTION_TYPE> \
  [--host <GIT_HOST>] \
  [--git-credential-external-id <GIT_CREDENTIAL_EXTERNAL_ID>]
```

Do **not** register git connections for input-port ODCS files. They are cached copies of upstream contracts; the upstream data product owns the canonical record.

Notes:

- `--repository-path` is **relative to the repo root**, not the working directory. The ODPS path is just `<DATA_PRODUCT_ID>.odps.yaml`; output-port contract paths look like `models/output_ports/v<N>/<CONTRACT_FILE>`.
- Omit `--host` for SaaS providers (github.com, gitlab.com, bitbucket.org, dev.azure.com); set it only for self-hosted instances.
- These commands fail if the underlying data product / contract does not exist on the platform yet. If you skipped earlier because of "deferred," surface the manual command in Step 5 so the user can run it after the first workflow run. Do not retry-loop.
- If the audit reported drift (existing connection with different URL/branch/path), confirm with the user before overwriting — `put` is upsert.

### Step 5 — Final report

Always end with this exact two-part format so the user gets a consistent recap.

**Part 1 — outcome table.** One row per artifact from the audit. Use the `Status` enum below; `Details` is a short, plain-text note (file path, or "—" if nothing to add).

| Artifact | Status | Details |
|---|---|---|
| ODPS file | … | … |
| Output-port contracts | … | `<N>` file(s) at `models/output_ports/v<N>/<CONTRACT_FILE>` |
| Input-port contracts | … | `<N>` file(s) at `models/input_ports/<provider-output-port-id>.odcs.yaml` (or "—" if no access agreements yet) |
| OpenLineage transport | … | … |
| Model layout | … | … |
| Publish workflow | … | … |
| Git connections | … | … |

`Status` enum (use exactly these words):

- `created` — the skill wrote a new file or registered a new connection.
- `updated` — the skill patched an existing file or fixed a drifted connection.
- `already present` — no change needed.
- `deferred` — skipped intentionally (data product/contract not yet published, or no git repo). The deferred command(s) appear in Part 2.
- `skipped` — the user declined when asked to confirm.

**Part 2 — next steps.** Bullet list, only include the items that apply:

- For each `deferred` git connection, the exact `entropy-data dataproducts gitconnection put …` or `entropy-data datacontracts gitconnection put …` command to run after the first CI publish.
- "Set GitHub repository secrets: `ENTROPY_DATA_API_KEY`, plus platform creds (`DBT_DATABRICKS_HOST`, `DBT_DATABRICKS_HTTP_PATH`, `DBT_DATABRICKS_TOKEN` for Databricks; equivalents for other platforms)."
- "Fill in the data contract schema in `<CONTRACT_PATH>` — the template only seeds `id` and `updated_at`."
- "Run `dbt-ol run` locally once to verify lineage flows to Entropy Data (requires `OPENLINEAGE__TRANSPORT__AUTH__APIKEY`)."

If there is nothing in Part 2, write a single line: `No further action required.`

## Conventions and constraints

- **Platform-aware workflow**: the workflow template assumes Databricks. If the user picks Snowflake/BigQuery/Postgres, swap the `dbt-databricks` install line, the `Create profiles.yml` block, and the `DATACONTRACT_*` env vars to the matching dialect. Do not generate a Databricks workflow for a non-Databricks project.
- **No invented schema**: when generating the ODCS file, do not invent columns. Seed it with `id` + `updated_at` and tell the user to fill in the rest, or — if dbt models already exist for the output port — derive columns from `_models.yml` if available.
- **Idempotent**: running the skill a second time should be a no-op when everything is already present. For git connections that means: if `gitconnection get` returns a record matching the local repo URL / branch / path, do not call `put`.
- **Don't overwrite drifted git connections silently.** If the platform reports a different URL/branch/path than the local repo, surface the diff and ask. The user may have a fork, a renamed default branch, or a deliberate path remap.
- **Don't push secrets**: never write API keys, tokens, or hostnames into committed files. They must come from GitHub secrets in the workflow.
- **Don't create a git repo or commit**: leave VCS state to the user.

---
name: dataproduct-exampledata
description: Extract a small sample of rows from a dbt output port using a non-production profile, scrub anything classified as PII or sensitive in the data contract, and upload the scrubbed sample to Entropy Data via the entropy-data CLI. Trigger when the user asks to "upload example data", "publish sample rows for the data product", or "give consumers a preview of the data".
---

# Upload example data for a data product

Sample rows let prospective consumers evaluate a data product without requesting access. This skill pulls a small sample from a non-production source, scrubs sensitive columns, and uploads the result.

## How to run this skill

> `${PLUGIN_ROOT}` below refers to the root of this plugin — the directory that contains `skills/`. On Claude Code it is set automatically as `${CLAUDE_PLUGIN_ROOT}` — use that. On any other agent (Codex, Copilot CLI, etc.) it is unset; resolve it as `../..` relative to **this `SKILL.md` file's directory** (i.e. the grandparent of `skills/<this-skill>/`).

### Plan announcement (before Step 0)

Before running Step 0, print this plan to the user verbatim:

> Running **dataproduct-exampledata**. I'll:
> 1. Pre-checks: dbt project, ODCS files, `entropy-data` CLI, non-prod dbt target.
> 2. Identify the output port and its contract.
> 3. Build a scrub plan — drop PII/sensitive columns, hash IDs, drop free text. **Wait for your confirmation.**
> 4. Extract ~20 sample rows via `dbt show` against the non-prod target.
> 5. Build the example-data YAML and show the first rows. **Wait for your confirmation.**
> 6. Upload via `entropy-data example-data put`.
> 7. Summarize what was uploaded, what was scrubbed, and cleanup options.

Then proceed.

### Step 0 — Pre-checks

- Confirm `dbt_project.yml` exists at the working directory root.
- Confirm there is at least one output-port ODCS file under `models/output_ports/`.
- Confirm `entropy-data` CLI is on PATH (`entropy-data --version`). If not, surface the install line from the README and stop.
- Confirm a non-production dbt profile/target exists (`test`, `dev`, or similar). Inspect `profiles.yml` if accessible; otherwise ask. **Never use a `prod` target in this skill.**

### Step 1 — Identify the output port

If multiple output ports exist, ask which one. For each candidate, you need:

- `OUTPUT_PORT_ID` (from `<id>.odps.yaml`)
- the matching `models/output_ports/v<N>/<file>.odcs.yaml`
- the table name and server config the contract points at

### Step 2 — Build the scrub plan

Read the contract's field list. For each field, decide what to do with it:

| Contract signal | Action |
|---|---|
| `classification: pii` (or `confidential`, `restricted`) | **Drop the column** from the sample |
| Field name matches obvious PII patterns (`email`, `phone`, `ssn`, `passport`, `dob`, `birth_date`, `iban`, `address`, `name`, `first_name`, `last_name`) and no classification | Treat as PII, drop unless the user explicitly opts in |
| `tags` containing `pii` / `sensitive` / `gdpr` | Drop |
| Numeric ID that could be a customer/user identifier | Hash with a one-way function and prefix `sample_` |
| Free-text `comment`/`note`/`description` columns | Drop unless the user explicitly opts in (free text often leaks PII not declared in the contract) |
| Everything else | Keep |

Show the user the scrub plan as a table — column → action — and **wait for confirmation before extracting any data.**

### Step 3 — Extract the sample

Build the SQL:

```sql
select <kept-and-hashed-columns>
from <contract-server-table>
limit <N>;
```

Default `N = 20`. Use the dbt non-prod target chosen in Step 0. Preferred extraction methods, in order:

1. `dbt show --inline "<sql>" --target <non-prod-target>` — uses the dbt connection, no extra credentials needed.
2. As a fallback, ask the user to run the query themselves and paste the result.

Convert the result rows into a list of objects keyed by **the contract column names** (the names that will be visible to consumers, not the warehouse aliases). Hold the rows in memory as `ROWS` for the next step — do not write a CSV. The `entropy-data example-data put` command takes a YAML/JSON body, not a CSV.

### Step 4 — Build the example-data document and show the sample

Construct the document the CLI expects:

```yaml
id: <DATA_PRODUCT_ID>-<OUTPUT_PORT_ID>
dataProductId: <DATA_PRODUCT_ID>
outputPortId: <OUTPUT_PORT_ID>
dataContractId: <CONTRACT_ID>
schemaName: <model name from the ODCS `models:` block>
data:
  - { <col>: <val>, ... }   # one entry per row from ROWS
  - ...
```

Field semantics confirmed against `entropy-data example-data list -o json`: the ID convention is `<dataProductId>-<outputPortId>`; `schemaName` is the contract's top-level `models:` key (the table name as the contract names it).

Write the document to `examples/<DATA_PRODUCT_ID>-<OUTPUT_PORT_ID>.yaml` (create `examples/` if missing; add `examples/` to `.gitignore` if absent).

Print the first 5 rows of `data:` in a Markdown table. Re-state the dropped columns. **Wait for explicit user confirmation before uploading.**

### Step 5 — Upload via entropy-data CLI

```
entropy-data example-data put <DATA_PRODUCT_ID>-<OUTPUT_PORT_ID> \
  --file examples/<DATA_PRODUCT_ID>-<OUTPUT_PORT_ID>.yaml
```

Notes on the CLI shape (verified against `entropy-data example-data put --help`):

- The example-data ID is a **single positional argument**, not `--data-product` / `--output-port` flags. By convention it is `<dataProductId>-<outputPortId>`; this must also match the `id:` field inside the document.
- `--file` accepts JSON or YAML, or `-` for stdin.
- `put` is upsert — running it again replaces the previous sample for that id.

If the CLI errors, surface the actual error and the relevant `--help` output to the user — do not improvise a different command.

### Step 6 — Final report

End with this two-part recap. Use the same `Status` enum the other skills use: `created`, `updated`, `already present`, `deferred`, `skipped`.

**Part 1 — outcome table.**

| Artifact | Status | Details |
|---|---|---|
| Output port | already present | `<DATA_PRODUCT_ID>/<OUTPUT_PORT_ID>` |
| Scrub plan | … | `<dropped-count>` dropped, `<hashed-count>` hashed, `<kept-count>` kept |
| Sample extraction | … | `<rows>` rows via `dbt show` (target `<non-prod-target>`) |
| Example-data file | … | `examples/<DATA_PRODUCT_ID>-<OUTPUT_PORT_ID>.yaml` |
| Upload to Entropy Data | … | `entropy-data example-data put` succeeded (upsert) |

**Part 2 — next steps.** Bullet list:

- Audit trail: list every column that was dropped or hashed inline so the user has a record of what's now visible to consumers.
- Local cleanup: offer to delete `examples/<DATA_PRODUCT_ID>-<OUTPUT_PORT_ID>.yaml` if it contains anything the user doesn't want left on disk.
- Visibility: the sample is now visible in Entropy Data under this data product (running the skill again upserts the same id and overwrites the previous sample).

If there is nothing additional to surface, write a single line: `No further action required.`

## Constraints

- **Hard guardrail: never upload columns classified as PII/sensitive in the contract, and never upload free-text columns by default.** This rule does not bend for "just this once" — the user can override per-column in Step 2, but the default must be drop.
- **Never use a production dbt profile** to extract the sample. Use `test`/`dev` only. If only a prod profile exists, stop and tell the user to set up a non-prod target first.
- **No silent uploads.** Steps 2 and 4 both require explicit user confirmation before progressing. Skipping either is a bug.
- **Don't commit the YAML body.** `examples/` belongs in `.gitignore`. The uploaded copy is the system of record.
- **Idempotent re-runs are fine** — `entropy-data example-data put` is upsert and will overwrite the previous sample for the same id (`<dataProductId>-<outputPortId>`). Mention this in the final report so the user knows the prior sample is gone.

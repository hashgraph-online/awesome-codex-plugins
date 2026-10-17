# OpenClaw

Read this file **before** any prospecting work when running on an **OpenClaw** gateway.

For shared tool mechanics, filter patterns, and API limits, see [`SKILL.md`](../SKILL.md).

## Install

Once at the **start of each workflow** (not per tool call):

```bash
npm install -g @vibeprospecting/vpai@latest
```

**Always run this install** — even if `which vpai` or `vpai --version` shows an existing global install. Never skip install because the CLI is already on PATH; `@latest` updates frequently and stale globals are common.

Use **`vpai`** for every step in that workflow. Do not use `npx` per tool call.

If global install fails (sandbox, permissions), fall back to `npx @vibeprospecting/vpai@latest` — slower.

## Auth

Authenticate before any vpai tool:

```bash
vpai login
# User opens the printed URL and approves in the browser, then:
vpai login --poll
vpai whoami   # auth status (JSON; no MCP). Exit 0 = ready for tools.
vpai --help   # tool names and descriptions — required every workflow before first tool call
```

**Auth vs discovery:** `whoami` only checks saved credentials. **`vpai --help`** lists available tools; **`vpai <tool> --all-parameters`** prints each tool's input schema before the first real `--args` call (see CLI Workflow below).

Alternatively, set the `VP_API_KEY` environment variable with a tenant API key (no browser flow).

Credentials are stored at `~/.config/vpai/config.json` on the gateway host.

### Sign out / switch account

```bash
vpai logout
# then repeat login flow
```

## CLI hard rules

1. **Install every workflow.** Always run `npm install -g @vibeprospecting/vpai@latest` at workflow start — even if `which vpai` finds a global install. Never skip install.
2. **Wait for `vpai` to exit, then parse stdout once.** No pipes, `2>&1`, or `tail` on the same call.
3. **Sample first, unless skipped.** Default: run the **complete** workflow on exactly **5 entities** before any full run — see Sample Gate below. Never describe those 5 rows as the full dataset. After explicit approval, re-run the same tool(s) at full scale (same session, filters, parameters; raise `--number-of-results` to the user's target). **Exception (this turn only):** if the user invokes `/skip_sample` (or `/vpai:skip_sample`) or explicitly asks to skip the sample (e.g. "fetch all without a sample", "skip the sample, just get everything"), skip Sample Gate and run at full requested scale immediately.
4. **After full scale:** copy the final **`csv_path`** into the working directory with a proper name based on the user's question. Do not ask whether to export first. Chain **`enrich-*`**, **events**, and scoped fetch with **`--session-id`** + **`--csv-path`**.
5. **One session, one agent, sequential steps.** `--session-id` maps to a session run directory (`state.db` holds job checkpoints only; row data lives in CSV files). Never run two agents, parallel shell jobs, or background `vpai` on the same `--session-id`. Never chain the next step until the prior `vpai` command **fully exits**. Concurrent use corrupts CSV output or checkpoint progress.

## CLI Workflow

OpenClaw runs prospecting through the vpai CLI. Run **`vpai`** (after Install above). Treat every tool response as JSON on stdout **after the command exits**.

```
0. Install + Auth — see sections above (`whoami`, then `--help`)
1. vpai --help                         Discover tools (required even if you ran it after login)
2. Before the first real `--args` for each tool: `vpai <tool> --all-parameters` (mandatory per tool, not only when uncertain). Prints the tool **input** schema as JSON. Run again if the planned call diverges from what you already validated.
3. Build `--args` only from fields confirmed by that printed input schema. If a parameter is not confirmed there, do not use it.
4. When the **entire** planned **`fetch-entities`** filter set (and supported flags) matches **`fetch-entities-statistics`** input schema per **`--all-parameters`**: run **`fetch-entities-statistics`**, then Sample Gate (5 entities, full chain)
5. vpai <tool> --args '<json>' --tool-reasoning '<user request>'
6. Chain next step: --session-id <session_id> --csv-path <csv_path> [--businesses-csv-path <path> for prospect fetch from businesses]
7. Need all rows? Read the file at csv_path from stdout JSON (present when row_count > 0). Chaining uses the same csv_path via --csv-path
```

**Every real call:** `--tool-reasoning '<user wording>'` (verbatim). Skip only for `<tool> --all-parameters` with no `--args`.

**Chain IDs:** pass `--session-id` and `--csv-path` from prior JSON only — **never invent `session_id`**. Never paste raw IDs into `--args`. `--csv-path` required for enrich and events when chaining with `--session-id`.

**Session ownership:** one `--session-id` ↔ one agent ↔ one sequential chain. Parallel agents sharing a session overwrite each other's CSV files and checkpoint state. Wait for exit before the next command; use a new `--session-id` if you need parallel workstreams.

**Controlled vocab:** run `autocomplete` before fetch/stats for `linkedin_category`, `naics_category`, `company_tech_stack_tech`, `job_title`, `interests`, `skills`, `business_intent_topics`, `city_region`.

## Sample Gate

The sample is the **complete workflow on 5 entities**, not a fetch preview.

### Skip Sample Gate (this request only)

Skip the 5-entity preview and run at full requested scale **for this user turn only** when:

- The message uses `/skip_sample` or `/vpai:skip_sample`, **or**
- The user explicitly asks to skip the sample (e.g. "fetch all results without showing a sample first", "skip the sample, just get everything", "skip samples and go full scale").

When skipped: do **not** fetch 5 first; do **not** wait for approval before full scale. Still follow install/auth/schema/autocomplete/chaining rules. After full scale, copy **`csv_path`** to the working directory with a proper name based on the user's question. Later messages without an explicit skip return to sample-first mode.

### Default sample path

**Universe vs sample:** The 5 rows are a **small fixed preview** so the user can validate filters and enrichment before spending quota. The underlying match set is typically **much larger** (often thousands or more). Do not equate "we returned 5" with "only 5 exist." Ground volume with **`fetch-entities-statistics`** only when the **entire** planned **`fetch-entities`** filter set is valid for stats; never guess a total.

1. **When the full fetch filter set is supported by statistics**, run **`fetch-entities-statistics`** with the same discovery **`entity_type`**, **`filters`**, and supported scope as the upcoming **`fetch-entities`**. Otherwise skip stats; still tell the user there is **much more** in the index for the same filters (no numeric total, no mention of statistics gaps).
2. Fetch exactly **5** entities (`--number-of-results 5`).
3. Run **every** subsequent step (`match-*`, `enrich-*`, `fetch-*-events`) on those 5.
4. Show the **fully enriched final rows** as a markdown table with all useful columns.
5. Stop. Wait for approval in a new message. Then run at full scale.

NEVER stop after the fetch to ask for approval. Complete the full chain on 5 first.

Example — user says "find 100 Israeli companies, get 30 CEOs, find contact info":
- WRONG: fetch 5 companies → show table → ask "continue?"
- RIGHT: when the **full** **`fetch-entities`** filter set is supported by **`fetch-entities-statistics`**, run stats first (same filters) → fetch 5 companies → fetch CEOs at those 5 → enrich CEOs with contacts → show final table (**5 of [total]** when stats gave a total; otherwise **Sample preview (5 rows)** plus a short line that **much more** matches exist for these filters—no count, no stats apology) → ask "run full 100?"

### Presenting the sample

Always frame the table as a **sample**, not the full population.

Include this blockquote aside once per sample presentation (not mixed into main prose):

> Running in sample-first mode. Preview before full dataset. To skip: `/skip_sample …` or ask to fetch all without a sample.

- **When statistics returned a usable total** (you only called stats because **every** **`fetch-entities`** filter was valid for **`fetch-entities-statistics`**): **Sample preview (5 of [total] matches)** — **[total]** must come from **`fetch-entities-statistics`**, never from counting the 5 rows.
- **When you did not use a numeric total** (no stats, or no usable total): **Sample preview (5 rows)** and one plain sentence that there is **much more** in the index matching these filters—**do not** say how many more, **do not** mention statistics or missing totals, **never** invent **[total]**.

End with an explicit next step, for example: **After you confirm**, I will re-run the same tool(s) at full scale to pull the real batch.

When the preview is a subset of what the user asked for (more rows or fields available at scale):

- With a stats-backed **[total]**: `More data available: Preview shows [n] of [total]. Confirm before I run the full export.`
- Without a numeric **[total]**: say the preview is five rows, **much more** exists in the index for the same filters, and ask to confirm a full export—**do not** give a remaining count or mention why no total was shown.

Do **not** mention export when everything the user asked for is already in chat.

### Before the full export, confirm

- Export size (cap on records).
- Filter narrowing: industry, size, revenue, region, tech.
- For prospects: title variants, dedupe by company.
- For contacts: professional emails only or also personal/phones.

After full scale: copy **`csv_path`** to the working directory with a proper name based on the user's question.

## Stdout vs full data

Every stateful tool JSON includes a compact preview plus a full CSV path when rows exist:

| Field | Meaning |
|-------|---------|
| `row_count` | Total rows stored (e.g. 30) |
| `sample_rows` | **At most 5** preview rows |
| `csv_path` | Full CSV file for every stored row (when `row_count` > 0) |

If `sample_rows.length` is less than `row_count`, that is **normal**. Read the file at **`csv_path`** for all rows.

**Chaining (`enrich-*`, `fetch-*-events`, scoped `fetch-entities`):** pass **`--session-id`** and **`--csv-path`** from the prior step's JSON. The CLI reads entity IDs from that CSV — use the exact **`csv_path`** string from stdout. **Do not manually batch** — pass the full CSV once; the CLI auto-batches IDs internally (`chunk_count` in stdout).

**Editing CSV between steps:** you may read, filter, dedupe, add columns, or rewrite the file at **`csv_path`** before the next tool call. Save the result (overwrite the same file or write a new CSV in the session directory), then pass that path to **`--csv-path`**. **Always keep the entity ID column:** **`business_id`** for business tools, **`prospect_id`** for prospect tools. Every row you want the next step to process must have a non-empty ID. Do not rename or drop those headers — the CLI uses them for ID injection and joins.

- Sample Gate **export approval** governs what you **offer the user** as a deliverable file — not whether you may read **`csv_path`** to build chat tables.

## Fetch (CLI)

- **`--number-of-results` for `fetch-entities`.** CLI flag only — never put `number_of_results` inside `--args` JSON. Default **50**; Sample Gate: **`5`**.
- **No `next_cursor` in CLI output.** The CLI paginates internally until `--number-of-results` is met.

## Match / CSV upload

- **Skip match** if you already ran **`fetch-entities`** — those results include IDs.
- CSV upload via **`--file-path`** and **`--schema`** on `match-business` / `match-prospects`. Maps column headers to API field names:
  - **Business fields:** `name`, `domain`
  - **Prospect fields:** `full_name`, `first_name`, `last_name`, `email`, `phone_number`, `linkedin`, `company_name`, `business_id`
- Output merges original columns with matched IDs. Chain into enrich with returned **`session_id`** and **`csv_path`**.

## Flags

| Flag | Description |
|------|-------------|
| `--help` | List tools and subcommands (`login`, `whoami`, …). Run every workflow before the first tool call. |
| `--all-parameters` | Print `{ name, description, inputSchema }` to stdout (pretty-printed JSON). Run before the first `--args` for each tool in a workflow (and again if the tool or payload changes materially). Routine, not only when uncertain—the **`inputSchema`** field is authoritative. |
| `--args '<json>'` | Tool arguments |
| `--session-id <id>` | Pass **`session_id`** from the previous tool's JSON only — **do not invent one**. Opens the session run directory (`state.db` stores job checkpoints only). |
| `--csv-path <path>` | **Required** with `--session-id` for **`enrich-business`**, **`enrich-prospects`**, **`fetch-businesses-events`**, and **`fetch-prospects-events`** (prior step's **`csv_path`**). Also used by **`fetch-entities`** when reading IDs from a prior CSV. Match CSV upload uses **`--file-path`** + **`--schema`** |
| `--businesses-csv-path <path>` | For `fetch-entities` + `entity_type: prospects`: CSV whose rows supply `business_id` for the filter (with `--session-id`). |
| `--number-of-results <n>` | For `fetch-entities`: total rows across pages (CLI paginates). **Default 50.** **CLI flag only — never put `number_of_results` inside `--args` JSON.** Sample gate: **`5`**. |
| `--file-path <path>` | For `match-business` / `match-prospects`: path to a CSV file to match. Each row becomes one candidate. Requires `--schema`. |
| `--schema '<json>'` | Required with `--file-path`. JSON dict mapping CSV column headers to API field names. Business fields: `name`, `domain`. Prospect fields: `full_name`, `first_name`, `last_name`, `email`, `phone_number`, `linkedin`, `company_name`, `business_id`. |

## Limits

| Tool | Limit |
|------|-------|
| `fetch-entities` | **`--number-of-results`** (internal pagination; default **30**) |

Other per-call limits (`match-*`, `enrich-*`, events) are in [`SKILL.md`](../SKILL.md) Limits.

## Troubleshooting

| Problem | Fix |
|---|---|
| Auth / 401 (OpenClaw) | Run `login`, then `login --poll`. Or set `VP_API_KEY`. Restart gateway if tools still fail after auth change. |
| Check auth before tools | `vpai whoami` — do not read `config.json` directly |
| `Not authenticated` (OpenClaw) | Run `vpai whoami`; if false, follow Auth above |
| Plugin or tools missing | See repo README / OpenClaw install docs (outside this skill) |
| Global install fails | Fall back to `npx @vibeprospecting/vpai@latest` |
| **Source CSV has no rows** / IDs not injected after fetch or match | Prior `vpai` may still be running, or another agent wrote the same `--session-id`. Wait for the prior command to exit; do not parallelize on one session; retry with the same `--session-id` + `--csv-path` |
| Missing **`session_id`** in JSON / CLI refuses to chain | Pass **`--session-id`** with the exact **`session_id`** string from the prior step's JSON |
| Wrong rows used when chaining | Pass **`--csv-path`** matching the prior step's **`csv_path`** |
| **`enrich-*` or `fetch-*-events` with `--session-id` but no `--csv-path`** | **`--csv-path`** is required whenever you pass **`--session-id`** to those tools |
| Edited CSV but next step sees no IDs | Keep column header **`business_id`** or **`prospect_id`**; every kept row needs a non-empty ID value |
| JSON parse error | Wait for exit; parse stdout only — no pipes, `2>&1`, or `tail` |
| `row_count` > `sample_rows.length` | Expected. Read the file at `csv_path` from stdout JSON |
| Sample shown as full dataset | Reframe as **Sample preview (5 rows)** or **5 of [total]**; read `csv_path` if you need every stored row |
| Timeout on `fetch-entities`, `enrich-*`, `fetch-*-events` | **Re-run the exact same command** with the same `--session-id`, `--csv-path`, `--args`. Completed ID batches are skipped. |
| Timeout on `match-*` with `--file-path` | **Re-run the exact same command** with the same `--session-id`, `--file-path`, `--schema`, and `--args`. Completed ID batches are skipped. |
| Timeout without `--session-id` | Re-run the same command; if the prior step returned **`session_id`**, pass that exact value — do not invent a new id |

For empty results and filter mutual exclusions, see [`SKILL.md`](../SKILL.md) Troubleshooting.

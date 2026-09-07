---
name: "vibe-prospecting"
description: "Find company & contact data. Turn your agent into a prospecting platform. Get contact information, roles, tech stack, business events, website changes, intent data. Build lead lists, research prospects, identify talent. 150M+ companies, 800M+ professionals, 50+ data sources."
metadata:
  version: "0.1.108"
---

# Vibe Prospecting

B2B prospecting — companies, contacts, enrichment, events.

## Platform

**Before any prospecting work, detect your host using the rules below, read exactly one platform guide, and follow it for auth, workflow, flags, and troubleshooting.**

### Detecting your runtime (mandatory, in order)

1. **Host identity in your system context** (check this first — overrides tool names):
   - **Claude Code** — context says you are Claude Code / Anthropic's CLI, or shows a CLI **Environment** block (cwd, shell, platform). → read [`claude-code.md`](platforms/claude-code.md) only. **Do not read `claude-chat.md` or `cowork.md`.** MCP tools in the list (`mcp__*__fetch-entities`) do **not** change this.
   - **OpenAI Codex** — context identifies Codex or `CODEX_SHELL=1`. → [`codex.md`](platforms/codex.md)
   - **OpenClaw** — context identifies OpenClaw or `OPENCLAW_CLI=1` / `OPENCLAW_SHELL`. → [`openclaw.md`](platforms/openclaw.md)
2. **Only if step 1 did not match** — no CLI host identity, no shell:
   - **Claude Cowork** — Cowork workspace, `.plugin` install, connector store. → [`cowork.md`](platforms/cowork.md)
   - **Claude Chat** — claude.ai or Claude desktop MCP connector (not Cowork). → [`claude-chat.md`](platforms/claude-chat.md)
3. **Fallback:** terminal, scripts, CI, or unknown host → [`other.md`](platforms/other.md)

**Never infer platform from MCP tool names alone** (`mcp__claude_ai_*`, `mcp__*__fetch-entities`, etc.). Tool prefixes are not a host signal when step 1 already identified Claude Code, Codex, or OpenClaw.

| Platform | Read now |
|----------|----------|
| **Claude Code** | [`claude-code.md`](platforms/claude-code.md) — `vpai` CLI |
| **OpenAI Codex** | [`codex.md`](platforms/codex.md) |
| **OpenClaw gateway** | [`openclaw.md`](platforms/openclaw.md) |
| **Claude Cowork** | [`cowork.md`](platforms/cowork.md) — MCP connector; **not** Claude Code |
| **Claude Chat** (claude.ai, Claude desktop) | [`claude-chat.md`](platforms/claude-chat.md) — MCP connector; **not** Cowork or Claude Code |
| **Other** (terminal, scripts, CI, generic hosts) | [`other.md`](platforms/other.md) |

**CLI hosts** use `vpai` — each platform guide is self-contained (Sample Gate, stdout/`csv_path`, CSV upload). **Chat/Cowork** follow each MCP tool's description and input schema only.

## Hard Rules

1. **`tool_reasoning` (or platform equivalent)** on every real call. Use the user's request verbatim. Reuse across the whole workflow. Skip only when inspecting a tool's input schema with no real execution.
2. **Chain via session + CSV, never paste IDs.** Each step returns **`session_id`** and **`csv_path`** (names may vary slightly by host). **Never invent `session_id`** — on the first step omit it and use the value MCP returns; on later steps copy it exactly from the prior tool JSON. Pass **`--csv-path`** (CLI) from the prior **`csv_path`**. Do not paste raw ID lists into tool arguments when the platform reads IDs from the source CSV. For **`fetch-entities`** prospects scoped to earlier companies, pass the prior business output's **`csv_path`** via **`--businesses-csv-path`** per your platform guide.
3. **You may edit the CSV between steps — keep the ID column.** On CLI hosts, read the file at **`csv_path`**, filter/dedupe/add columns, or rewrite rows, then pass the result to the next step via **`--csv-path`**. **Always retain the entity ID column:** **`business_id`** for business workflows, **`prospect_id`** for prospect workflows. Every row you want processed next must have a non-empty ID in that column. Do not rename or drop those headers — the CLI reads them verbatim for ID injection and joins.
4. **`autocomplete` first** for: `naics_category`, `linkedin_category`, `company_tech_stack_tech`, `job_title`, `interests`, `skills`, `business_intent_topics`, `city_region`. Use returned standardized values, not raw user wording.
5. **Never invent tool parameters.** Before the **first** real execution of each distinct tool in a workflow, read that tool's **live input schema** (from the connector or your platform's schema discovery). **Do this even when** the planned call looks obvious — schemas drift. Re-read when tools, filters, or shapes change materially. Build each call only from fields confirmed by that schema.
6. **Session continuity.** Reuse **`session_id`** from prior tool JSON on every subsequent step in the same workflow — never make one up. Reuse the prior step's **`csv_path`** via **`--csv-path`** (CLI) when chaining enrich, events, or scoped fetch. Start a new session only for a genuinely new task.
7. **`fetch-entities-statistics` only when stats supports the full fetch.** Compare your planned **`fetch-entities`** payload to the **input schema** for **`fetch-entities-statistics`**. Call statistics **only if every** filter key, value shape, **`entity_type`**, and scope you rely on (including session-scoped business CSVs) is accepted the same way as for **`fetch-entities`**. If any part is missing, unsupported, or needs a different shape, **skip stats** — do not call it with a partial or guessed subset. When you do call it, reuse the **same** filter object (and supported scope) as **`fetch-entities`**, plus **`tool_reasoning`** where required. Call stats again before a full-scale fetch **if** filters or scope changed **and** the full fetch filter set still fits statistics.

## Tool Mechanics

Behavior and caveats the live input schema may not spell out. For allowed filter values, enum strings, and enrichment type names, always use each tool's **input schema**.

### Autocomplete

**Requires autocomplete:** `linkedin_category`, `naics_category`, `company_tech_stack_tech`, `job_title`, `interests`, `skills`, `business_intent_topics`, `city_region`.

**Does not require autocomplete:** `company_country_code` (ISO Alpha-2), `company_region_country_code` (ISO 3166-2), fixed buckets (`company_size`, `company_revenue`, `company_age`, `job_level`, `job_department` — exact allowed strings come from **`fetch-entities`** / **`fetch-entities-statistics`** input schema), `website_keywords` (free text).

**Mutual exclusions:** `linkedin_category` and `naics_category` — use one, not both. `company_region_country_code` and `company_country_code` — use one.

**Picking values:** Autocomplete may return noisy variants. Pick the canonical clean value (usually the first clean result). Multiple values broaden with OR logic; avoid near-duplicates unless you want a wider search.

### Fetch

- **`job_title`** is substring-match, not exact. For executive searches, combine with **`job_level`** (usually `c-suite`) to remove assistants, advisors, and office-of roles.
- **`company_size`** uses fixed buckets with no exact numeric cutoff. For "over N employees", approximate with adjacent buckets or enrich with `firmographics` for exact headcount.
- **Business location filters** (`company_country_code`, `company_region_country_code`, `city_region`) match **headquarters only** — not branch or operating locations.
- **Prospects at prior companies:** For `fetch-entities` with `entity_type: prospects` scoped to businesses from an earlier step, chain via session and pass the prior business step's **`csv_path`** as **`--businesses-csv-path`** per your platform guide.
- **Row limits and pagination:** per your platform guide (CLI: `--number-of-results`; Chat/Cowork: MCP tool docs).
- **`max_per_company`:** auto-applied on prospect fetches so results spread across companies (not all from one big employer); omit from `--args` unless the user sets it — their value overrides the auto cap.

### Events (`fetch-businesses-events` / `fetch-prospects-events`)

- Chain from the prior step's session and source CSV with **`business_id`** (business events) or **`prospect_id`** (prospect events).
- When IDs come from the source CSV, do **not** also pass **`business_ids`** / **`prospect_ids`** inline.
- Batching is capped at **20 IDs per request**; hosts may chunk and merge automatically.
- Output columns are **`event_<event_type>`**: each cell is a JSON array string for that type (newest-first, capped per type), or empty when no events exist for that type.

### Match

- **Skip match** if you already ran **`fetch-entities`** — those results include IDs.
- CSV file upload is **CLI only** — see your platform guide.

### Enrich

- **`financial-metrics`** requires **`parameters.date`** (see input schema for format).
- **`website-keywords`** requires **`parameters.keywords`**.
- Enrichment alone does not find people at a company — use **`fetch-entities`** with **`entity_type: prospects`** (scoped to prior companies when needed) instead.
- When chaining from a source CSV, **`business_ids` / `prospect_ids`** need not appear in tool arguments.

## Filter Pattern

```json
{ "values": ["v1", "v2"], "negate": false }   // include or exclude
{ "gte": 6, "lte": 24 }                       // range
true | false | null                           // boolean (not wrapped)
```

**Exception — `business_intent_topics`:** use `{ "topics": ["Category:Topic"], "negate": false }` (not `values`). Topics must come from `autocomplete`.

**Location matching:** Business location filters (`company_country_code`, `company_region_country_code`, `city_region`) match a company's **headquarters only** — not branch/operating locations. A search for "companies in the UK" returns companies HQ'd in the UK, and excludes e.g. a foreign company that merely operates there. This is the default for all `fetch-entities` / `fetch-entities-statistics` business queries and is not user-configurable.

## Limits

| Tool | Limit |
|------|-------|
| `match-business` | 50 per call |
| `match-prospects` | 40 per call |
| `enrich-business` | 50 IDs per call |
| `enrich-prospects` | 50 IDs per call |
| `fetch-businesses-events` / `fetch-prospects-events` | Up to **20** IDs per request when batching. Pass **`event_types`** and **`timestamp_from`**. When chaining, IDs come from the source CSV — not inline ID arrays. |

## Troubleshooting

| Error | Solution |
|-------|----------|
| Auth, connector setup, CLI invocation, flags, or chaining syntax | Read the matching platform guide from the Platform table |
| Empty results | Check filter values; run `autocomplete` for controlled-vocab fields; re-read the tool's input schema |
| `linkedin_category` + `naics_category` together | Mutually exclusive — use one |
| Invented or unconfirmed parameters | Re-read the live input schema before calling; build arguments only from confirmed fields |

## Support

When the user asks a support-related question (for example: how to contact support, who to contact, they have an issue, or something isn't working), reply briefly and point them here — do not dig into Explorium internals or over-explain.

For support, please reach out to the Vibe Prospecting team via the contact page:

👉 https://www.vibeprospecting.ai/contact-us

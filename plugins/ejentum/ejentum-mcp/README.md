# ejentum-mcp

[![npm version](https://img.shields.io/npm/v/ejentum-mcp.svg)](https://www.npmjs.com/package/ejentum-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node](https://img.shields.io/node/v/ejentum-mcp.svg)](https://nodejs.org)
[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-io.github.ejentum%2Fejentum--mcp-blue)](https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.ejentum/ejentum-mcp)
[![Glama score](https://glama.ai/mcp/servers/ejentum/ejentum-mcp/badges/score.svg)](https://glama.ai/mcp/servers/ejentum/ejentum-mcp)
[![Last commit](https://img.shields.io/github/last-commit/ejentum/ejentum-mcp.svg)](https://github.com/ejentum/ejentum-mcp/commits/main)

MCP server that improves LLM reasoning on complex, multi-step, or multi-constraint tasks. Before the agent generates, it calls one of eight tools to retrieve a *cognitive operation*: a structured procedure (numbered steps with the failure pattern to refuse and a falsification test) paired with an executable reasoning topology (a DAG of those steps with decision gates, parallel branches, bounded loops, meta-cognitive exits, and escape paths). The agent reads both layers before producing its response.

Eight tools split into two retrieval modes:

- **Dynamic** (4 tools: `reasoning`, `code`, `anti-deception`, `memory`): the top-1 abstract operation from a library of 679, selected by semantic match on the `query` string. Available on all tiers including the 30-day free trial.
- **Adaptive** (4 tools: `adaptive-reasoning`, `adaptive-code`, `adaptive-anti-deception`, `adaptive-memory`): the same retrieval pool, but an adapter LLM rewrites every step and DAG node in the matched operation with task-specific identifiers (e.g., `extract_duration_estimates` becomes `extract_migration_duration_estimates(DDL_time|backfill_time|trigger_overhead|lock_hold_time)`). Adds ~2-3 s of latency; requires the Go or Super tier.

Two install paths use the same `EJENTUM_API_KEY`:

1. **Stdio** via `npx -y ejentum-mcp` for Claude Desktop, Cursor, Windsurf, Codex CLI, Claude Code, Cline, Continue, and any client that spawns MCP servers as subprocesses.
2. **Hosted Streamable HTTP** at `https://api.ejentum.com/mcp` for n8n MCP Client and any HTTP-MCP client. Send `Authorization: Bearer YOUR_EJENTUM_API_KEY`.

---

## Install

You need:
- An Ejentum API key. 30-day free trial (no card) at [ejentum.com/pricing](https://ejentum.com/pricing).
- Node.js 18+.

### Install from npm

```bash
npm install ejentum-mcp
```

Or skip the install and reference it with `npx -y ejentum-mcp` directly in your client config (shown below).

### Manual install

#### Claude Desktop

Open `claude_desktop_config.json`:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ejentum": {
      "command": "npx",
      "args": ["-y", "ejentum-mcp"],
      "env": { "EJENTUM_API_KEY": "ej_..." }
    }
  }
}
```

Restart Claude Desktop. The eight tools appear in the tool picker.

#### Cursor / Windsurf

Open MCP settings → Add new MCP server → paste the same `ejentum` block as above.

#### Claude Code (CLI)

```bash
claude mcp add ejentum -e EJENTUM_API_KEY=ej_... -- npx -y ejentum-mcp
```

#### n8n MCP Client node

Add an MCP Client node, transport `stdio`, command `npx`, args `["-y", "ejentum-mcp"]`, env `{ "EJENTUM_API_KEY": "ej_..." }`.

---

## Wire contract

The stdio MCP server and the hosted endpoint both proxy to the same upstream:

```
POST https://api.ejentum.com/harness/
Headers:
  Authorization: Bearer <EJENTUM_API_KEY>
  Content-Type: application/json
Body:
  {
    "query": "<string, 1-2 sentences describing the task>",
    "mode":  "reasoning" | "code" | "anti-deception" | "memory"
           | "adaptive-reasoning" | "adaptive-code"
           | "adaptive-anti-deception" | "adaptive-memory"
  }
Response (200):
  [ { "<mode>": "<injection string, ~2-4 KB>" } ]
Response (401): { "error": "Unauthorized; check EJENTUM_API_KEY" }
Response (403): { "error": "Adaptive modes require Go or Super tier" }
Response (429): { "error": "Rate limit exceeded for tier" }
```

The response is an array of length 1 with a single key matching the request `mode`. Use bracket access (`result[0]["anti-deception"]`) for the hyphenated keys; dot access parses the hyphen as subtraction in JavaScript and Python attribute access.

The injection string is plain text containing seven fields. See [Field structure](#field-structure-of-an-injection) below.

---

## Tool inventory

### Dynamic (single retrieval, all tiers including the 30-day trial)

| Tool name | Mode string | Library size |
|---|---|---:|
| `reasoning` | `reasoning` | 311 operations across abstraction, time, causality, simulation, spatial, metacognition |
| `code` | `code` | 128 operations across the software-engineering layer |
| `anti-deception` | `anti-deception` | 139 operations across sycophancy, hallucination, deception, adversarial framing, judgment, executive control |
| `memory` | `memory` | 101 operations in the perception layer (filter-oriented; do not call for fact extraction) |

### Adaptive (top-k retrieval + adapter LLM rewrite; Go or Super tier required)

| Tool name | Mode string | Behavior vs dynamic |
|---|---|---|
| `adaptive-reasoning` | `adaptive-reasoning` | Same retrieval pool, top-5 then picker, then adapter LLM rewrites PROCEDURE and REASONING TOPOLOGY fields with task-specific identifiers. Adds ~2-3 s of latency. |
| `adaptive-code` | `adaptive-code` | Same as above for the code library. |
| `adaptive-anti-deception` | `adaptive-anti-deception` | Same as above for the anti-deception library. |
| `adaptive-memory` | `adaptive-memory` | Same as above for the memory library. |

Each tool takes one argument, `query` (string, 1-2 sentences describing the task). Returns the injection string.

---

## Field structure of an injection

Every retrieved record contains seven labelled blocks plus a cognitive payload. The exact set of labels varies by mode:

The fields appear in this fixed order in every response. Each mode uses its own label for the same slot (e.g., `[PROCEDURE]` in reasoning corresponds to `[ENGINEERING PROCEDURE]` in code):

| Order | Slot | Per-mode labels | Content |
|--:|---|---|---|
| 1 | Procedure | `[PROCEDURE]` (reasoning) · `[ENGINEERING PROCEDURE]` (code) · `[INTEGRITY PROCEDURE]` (anti-deception) · `[SHARPENING PROCEDURE]` (memory) | Numbered steps the model executes. |
| 2 | Topology | `[REASONING TOPOLOGY]` (reasoning) · `[REASONING TOPOLOGY]` (code) · `[DETECTION TOPOLOGY]` (anti-deception) · `[PERCEPTION TOPOLOGY]` (memory) | DAG specification. See [DAG syntax](#dag-syntax). |
| 3 | Cognitive payload | `Amplify:` / `Suppress:` / `Cognitive Style:` / `Elasticity:` (all modes) | Tendency vectors and execution-style hints. |
| 4 | Verification | `[FALSIFICATION TEST]` (reasoning) · `[VERIFICATION]` (code) · `[INTEGRITY CHECK]` (anti-deception) · `[PERCEPTION CHECK]` (memory) | Self-check the model runs after drafting. |
| 5 | Failure pattern | `[NEGATIVE GATE]` (reasoning) · `[CODE FAILURE]` (code) · `[DECEPTION PATTERN]` (anti-deception) · `[PERCEPTION FAILURE]` (memory) | The failure pattern to refuse. |
| 6 | Correct shape | `[TARGET PATTERN]` (reasoning) · `[CORRECT PATTERN]` (code) · `[HONEST BEHAVIOR]` (anti-deception) · `[CLEAR SIGNAL]` (memory) | What a correct response looks like. |

The same six-slot order holds for both dynamic and adaptive variants of every mode. In adaptive responses, the adapter LLM rewrites slots 1 and 2 (procedure and topology) with task-specific identifiers; slots 3-6 are returned verbatim.

### DAG syntax

The topology block uses a flat string notation:

| Token | Meaning |
|---|---|
| `Sn:label` | Step node. Numbered, sequential by default. |
| `Gn{?}` | Decision gate. Branches `--yes->` / `--no->`. |
| `N{...}` | Negative anchor. Active across the whole branch; the labelled failure pattern is refused. |
| `M{...}` | Meta-cognitive node. Model pauses, evaluates the trace, then `RE-ENTER`s at a named step. |
| `FREEFORM{...}` | Escape path. Model exits the prescribed DAG when the plan stops fitting; returns to a step or `OUT`. |
| `FIXED_POINT[...]` | A quantity held stable across the branch. |
| `for_each:` / `LOOP[...]` | Bounded iteration. |
| `C{expr}` | Computed value used downstream. |
| `OUT:label` | Terminal node. |

The DAG is meant to be read by the LLM as a structured outline of the reasoning path, not executed by a host runtime. The labelled-step structure persists across long context windows where prose-only reasoning specifications lose retrieval salience.

---

## Canonical example: dynamic vs adaptive on the same query

Query (used for both calls):

> Evaluate whether a database migration plan that adds a NOT NULL column to a 50M-row table is safe under concurrent writes, given that the backfill strategy uses a trigger-based default.

The picker matched the same operation in both calls ("realistic duration estimation" with the Hofstadter buffer). The `[NEGATIVE GATE]`, `[TARGET PATTERN]`, `[FALSIFICATION TEST]`, and `[COGNITIVE PAYLOAD]` fields are identical between the two responses (the adapter does not rewrite them). The `[PROCEDURE]` and `[REASONING TOPOLOGY]` fields differ: the adaptive response replaces abstract identifiers with task-specific ones.

### Dynamic `reasoning` response (truncated to the differing fields)

```
[PROCEDURE]
Step 1: Extract every duration estimate and identify its basis: historical data,
expert judgment, or optimistic assumption. Step 2: Compare each estimate against
historical base rates or p90 benchmarks for similar tasks. Step 3: Flag estimates
below the historical median as likely optimistic. Step 4: Never accept best-case
estimates as planning targets. Do not anchor to initial optimistic numbers.
Step 5: If an estimate lacks historical basis, simulate impact with a 1.5x-2.0x
buffer. If data exists, compute the variance-adjusted range. Verify the final
timeline accounts for cascading delay propagation across dependent tasks.

[REASONING TOPOLOGY]
S1:extract_duration_estimates -> N{accept_best_case_estimates_planning_targets}
-> S2:identify_basis(historical|expert|assumption)
-> FIXED_POINT[historical_base_rates]
-> S3:compare(estimate_vs_p90_benchmark)
-> G1{below_median?} --yes-> FLAG:likely_optimistic -> S4:apply_buffer(1.5x_to_2x) -> S3[LOOP]
                       --no-> G2{lacks_historical_basis?} --yes-> S4b:simulate_with_buffer -> S3
                                                          --no-> C{adjusted_range = base_rate_estimate +/- sqrt(variance) * z}
                                                              -> S5:apply_adjusted_range
                                                              -> S6:verify_cascade_delay
                                                              -> OUT:realistic_timeline
```

### Adaptive `adaptive-reasoning` response (same query, same picked operation)

```
[PROCEDURE]
Step 1: Extract every duration estimate in the migration plan (DDL execution time
for adding NOT NULL column on 50M rows, backfill duration, trigger overhead per
concurrent write, total migration window) and identify its basis: historical
migration data on similar table sizes, DBA expert judgment, or optimistic
assumption assuming zero contention. Step 2: Compare each estimate against
historical base rates or p90 benchmarks for similar DDL operations on large tables
(e.g., ALTER TABLE duration per million rows, trigger-induced latency under
concurrent write load). Step 3: Flag estimates below the historical median as
likely optimistic, e.g., assuming sub-second column addition without considering
lock escalation on a 50M-row table, or assuming trigger-based backfill adds
negligible overhead under concurrent write traffic. Step 4: Never accept best-case
estimates as planning targets. Do not anchor to initial optimistic numbers such
as "the NOT NULL addition will complete instantly" or "the trigger will not slow
down concurrent writes." Step 5: If an estimate lacks historical basis (e.g., no
prior trigger-based backfill on a table this size), simulate impact with a
1.5x-2.0x buffer for lock duration and write throughput degradation. If data
exists (e.g., past ALTER TABLE timings on this table), compute the
variance-adjusted range. Verify the final timeline accounts for cascading delay
propagation across dependent tasks (e.g., extended lock hold times blocking
application queries, backfill slowdown under write contention propagating to
downstream replication lag).

[REASONING TOPOLOGY]
S1:extract_migration_duration_estimates(DDL_time|backfill_time|trigger_overhead|lock_hold_time)
-> N{accept_best_case_estimates_planning_targets}
-> S2:identify_basis(historical_migration_data|DBA_expert_judgment|optimistic_assumption)
-> FIXED_POINT[historical_base_rates_for_DDL_on_large_tables]
-> S3:compare(estimate_vs_p90_benchmark_for_ALTER_TABLE_and_trigger_overhead)
-> G1{below_median_for_similar_migrations?} --yes-> FLAG:likely_optimistic(e.g.,assumes_zero_lock_contention)
                                                 -> S4:apply_buffer(1.5x_to_2x_for_lock_duration_and_write_throughput)
                                                 -> S3[LOOP]
                                              --no-> G2{lacks_historical_basis_for_trigger_backfill_on_50M_table?}
                                                       --yes-> S4b:simulate_with_buffer_for_concurrent_write_impact_and_lock_escalation
                                                       --no--> C{adjusted_range = base_rate_migration_estimate +/- sqrt(variance) * z}
                                                              -> S5:apply_adjusted_range_for_migration_window
                                                              -> S6:verify_cascade_delay(lock_blocking_app_queries -> replication_lag -> downstream_consumers)
                                                              -> OUT:realistic_migration_timeline
```

### Fields shared by both responses (slots 3-6, unchanged by the adapter)

Returned in the canonical order: cognitive payload, falsification test, negative gate, target pattern.

```
[COGNITIVE PAYLOAD]
Amplify: hofstadter buffer application; p90 baseline comparison; variance
         multiplier scaling
Suppress: best case anchoring; optimism bias
Cognitive Style: realistic duration estimation
Elasticity: coherence=risk adjusted timeline, expansion=conservative

[FALSIFICATION TEST]
If time estimates reflect only the best-case scenario without verifying applying
any buffer multiplier, duration calibration has defaulted to optimism.

[NEGATIVE GATE]
The database migration will take two weeks: that's our best-case estimate and the
team is experienced, so there's no reason to add buffer. We'll hit the deadline
if everything goes according to plan.

[TARGET PATTERN]
Challenge the two-week estimate: what do similar migrations actually take? If past
projects averaged four weeks at p90, the best-case anchor is dangerously optimistic.
Apply a variance multiplier for schema complexity, data volume, and rollback
testing: build buffer from the full distribution, not the happy path.
```

This is the contract: dynamic returns the matched abstract operation; adaptive returns the same operation with `PROCEDURE` and topology nodes rewritten in terms of the caller's task (`DDL execution time`, `lock_blocking_app_queries`, `trigger-based backfill on a table this size`) while preserving the operation's structural identity, the safety language, and the cognitive payload verbatim.

---

## Configuration

| Variable | Required | Purpose |
|---|---|---|
| `EJENTUM_API_KEY` | yes | API key from [ejentum.com/pricing](https://ejentum.com/pricing). |
| `EJENTUM_API_URL` | no | Override the upstream URL. Default: `https://api.ejentum.com/harness/`. |

The MCP wrapper is stateless. No local logging, no telemetry, no third-party calls. The upstream API counts requests against the key for billing; the request body (the `query` string) is consumed for retrieval and not retained beyond the response.

---

## Errors

| Status | Cause |
|---|---|
| `401 Unauthorized` | `EJENTUM_API_KEY` is unset, wrong, or expired. |
| `403 Forbidden` | Adaptive mode requested on a tier that does not include it (trial or unrecognised). |
| `429 Rate limit exceeded` | Tier quota for the period exhausted. |
| Tool absent from client | Client did not reload after config change. Fully quit and reopen; on Claude Desktop check Help → Logs. |
| `EJENTUM_API_KEY is not set` from the wrapper | Client did not pass the `env` block to the spawned MCP process. |

---

## Local development

```bash
git clone https://github.com/ejentum/ejentum-mcp.git
cd ejentum-mcp
npm install
cp .env.example .env       # paste your EJENTUM_API_KEY
npm run dev
```

Smoke test against the live API:

```bash
npm run build && npm run test:smoke
```

Interactive testing with MCP Inspector:

```bash
npx @modelcontextprotocol/inspector npm run dev
```

Rebuild and repack the MCPB bundle for a Smithery release:

```bash
npm run build
npm prune --omit=dev
npx -y @anthropic-ai/mcpb pack
npm install
npx -y @smithery/cli mcp publish ./ejentum-mcp.mcpb -n ejentum/ejentum-mcp
```

---

## Listings

- [Smithery](https://smithery.ai/servers/ejentum/ejentum-mcp)
- [Glama](https://glama.ai/mcp/servers/ejentum/ejentum-mcp)
- [mcp.so](https://mcp.so/server/ejentum-mcp/Ejentum)
- [npm](https://www.npmjs.com/package/ejentum-mcp): `npm install -g ejentum-mcp`

[![ejentum-mcp MCP server](https://glama.ai/mcp/servers/ejentum/ejentum-mcp/badges/card.svg)](https://glama.ai/mcp/servers/ejentum/ejentum-mcp)

## Links

- [Ejentum documentation](https://ejentum.com/docs)
- [Method](https://ejentum.com/docs/method)
- [n8n integration](https://ejentum.com/docs/n8n_guide)
- [Claude Code integration](https://ejentum.com/docs/claude_code_guide)
- [Pricing](https://ejentum.com/pricing)
- [info@ejentum.com](mailto:info@ejentum.com)

## License

MIT. See [LICENSE](./LICENSE).

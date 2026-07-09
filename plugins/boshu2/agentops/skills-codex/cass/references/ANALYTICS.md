# Token, Tool & Model Analytics

> **One-liner:** cass already has every Claude/Codex/Gemini API call you've made. `cass analytics` rolls them up into per-day, per-tool, per-model usage tables — no separate billing pipeline needed.

## Contents

- [Five Subcommands](#five-subcommands)
- [Status First](#status-first)
- [Token Usage Reports](#token-usage-reports)
- [Tool Usage](#tool-usage)
- [Model Usage](#model-usage)
- [Rebuild Strategy](#rebuild-strategy)
- [Validation](#validation)
- [Pitfalls](#pitfalls)

---

## Five Subcommands

```bash
cass analytics status --json     # Coverage + freshness of rollup tables
cass analytics tokens --json     # Token usage time-series + dim breakdowns
cass analytics tools --json      # Per-tool invocation counts
cass analytics models --json     # Top models + coverage stats
cass analytics rebuild --json    # Backfill / rebuild rollup tables
cass analytics validate --json   # Drift detection between raw rows and aggregates
```

---

## Status First

```bash
cass analytics status --json | jq '.data'
```

Look for:
- `coverage.api_token_coverage_pct` — % of messages with real API token data (vs estimate)
- `coverage.estimate_only_pct` — inverse; <10% is healthy
- `coverage.message_metrics_coverage_pct` — % with full per-message stats
- `drift.signals` — empty array means rollups match raw data
- `drift.track_a_fresh` / `track_b_fresh` — are both rollup tracks current
- `recommended_action` — "none" or specific (`"rebuild"`, `"validate"`)

If `track_a_fresh=false` or `coverage.api_token_coverage_pct < 90`, run:

```bash
cass analytics rebuild --json | jq '.data.summary'
```

---

## Token Usage Reports

`--group-by` is **time-only** (`hour|day|week|month`). To slice by agent or model, use the dedicated subcommands or filter flags.

```bash
# Last 30 days, daily buckets
cass analytics tokens --days 30 --group-by day --json | jq '.data.buckets'

# Hour granularity for the past day
cass analytics tokens --days 1 --group-by hour --json | jq '.data.buckets'

# Filter to one agent (slug from cass capabilities --json | jq '.connectors')
cass analytics tokens --days 30 --agent claude_code --json | jq '.data.totals'

# Specific date range
cass analytics tokens --since 2026-04-01 --until 2026-04-22 --json
```

### Real Output Shape

```json
{ "data": {
    "bucket_count": 30,
    "buckets": [{
      "bucket": "2026-04-22",
      "counts":         {"message_count": 4374, "user_message_count": 74, "assistant_message_count": 0, "tool_call_count": 681, "plan_message_count": 0},
      "content_tokens": {"est_total": 45724, "est_user": 612, "est_assistant": 0},
      "api_tokens":     {"total": 145060939, "input": 1670, "output": 160042, "cache_read": 143693750, "cache_creation": 1205477, "thinking": 0},
      "plan_tokens":    {"content_est_total": 0, "api_total": 0},
      "coverage":       {"api_coverage_message_count": 1052, "api_coverage_pct": 24.05},
      "derived":        {"api_tokens_per_assistant_msg": null, "tool_calls_per_1k_api_tokens": 0.0047, ...}
    }, ...],
    "totals": {...}
}}
```

Note: `input/output/cache_read/cache_creation` live under `.api_tokens`, not flat at the row level. `cache_read` typically dwarfs `input` for active prompt-caching workloads — count it when estimating spend.

### Cost Estimation Pattern (per-day across all models)

```bash
# Rough $ across all activity at Sonnet-4 list prices
# (cache_read is ~10% the price of input; check current Anthropic pricing)
cass analytics tokens --days 30 --group-by day --json \
  | jq '.data.buckets[] | {
      day: .bucket,
      input_M:  (.api_tokens.input // 0) / 1e6,
      output_M: (.api_tokens.output // 0) / 1e6,
      cache_read_M: (.api_tokens.cache_read // 0) / 1e6
    }'
```

For per-model spend, use `cass analytics models --json` (next section); `tokens` does not break down by model. For Claude Max / GPT Pro flat-rate accounts, the dollar number is irrelevant — what matters is *throughput per account* (use `caam` to plan account allocation).

---

## Tool Usage

```bash
cass analytics tools --days 30 --json | jq '.data.rows[0:20]'
```

Returns rows with: `key` (agent slug), `tool_call_count`, `message_count`, `api_tokens_total`, `tool_calls_per_1k_api_tokens`, `tool_calls_per_1k_content_tokens`. Note: rows are keyed by **agent**, not by tool name — this is "tool-use intensity per agent." Useful for:

- Finding which tools dominate your workflow
- Detecting newly broken tools (sudden error spike)
- Justifying which `--allowedTools` to pre-approve in `.claude/settings.json`

---

## Model Usage

```bash
cass analytics models --json \
  | jq '.data.by_api_tokens.rows[0:10] | map({model: .key, tokens: .value, msgs: .message_count, derived})'
```

Returns under `.data.by_api_tokens.rows[]` with: `key` (model name), `value` (api_total tokens), `message_count`, `derived{api_coverage_pct, tool_calls_per_1k_api_tokens, plan_message_pct}`. There's also `.data.timeseries.buckets[]` for time-aware model usage.

Spot patterns like "Haiku is doing 80% of the work but Opus is doing all the spending" — then tune your skill triggers accordingly.

---

## Rebuild Strategy

After bulk operations that shuffle data:

```bash
# After cass sources sync
cass sources sync --source css --json
cass analytics rebuild --json

# After cass import chatgpt
cass import chatgpt /path/to/conversations.json --json
cass analytics rebuild --json

# After a long indexing campaign
cass index --full --force-rebuild --json
cass analytics rebuild --json
```

`rebuild` accepts `--since/--until/--days` to scope the backfill window, plus `--agent`, `--workspace`, and `--source local|remote|all|<host>` filters. There's no `--force` flag — to fully recompute, use a wide window like `--days 9999`. `cass analytics validate --json` afterward confirms invariants.

---

## Validation

```bash
cass analytics validate --json | jq '.data.invariants'
```

Checks:
- Sum(daily) == raw_messages_count for each day
- Token totals match cross-track
- No orphan rollup rows for missing conversations

If `signals` is non-empty, run `analytics rebuild --force` and re-validate.

---

## Pitfalls

- **Wrong field path is the #1 mistake.** `tokens` returns `.data.buckets[]`, `tools` returns `.data.rows[]`, `models` returns `.data.by_api_tokens.rows[]`. They are **not consistent** — always probe with `jq 'keys'` first when scripting against a new subcommand.
- **No `--group-by model` / `--group-by agent`.** Time-only enum (`hour|day|week|month`). For per-model breakdowns use `cass analytics models`; for per-agent use `cass analytics tools` (rows are keyed by agent slug despite the name).
- Analytics rollups are derived data. `cass doctor --fix` does NOT rebuild analytics rollups — only the lexical/FTS index. To repair analytics, use `cass analytics rebuild --json`.
- Coverage <90% usually means legacy sessions before the agent emitted token-usage events. Estimates fill the gap; rebuild can't recover what was never recorded.
- `cass analytics tokens` reads from the rollup tables; it won't reflect sessions added in the last few minutes until the next rollup tick. Run `cass analytics rebuild --days 1` for a fresh view.

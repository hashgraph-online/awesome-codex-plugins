# Codex Usage Tracker

Local-first analytics for Codex token usage.

> **Unofficial project:** Codex Usage Tracker is an independent open-source project. It is not made by, affiliated with, endorsed by, sponsored by, or supported by OpenAI. OpenAI and Codex are trademarks of OpenAI; this project only reads local log files from your machine.

Codex Usage Tracker reads the JSONL logs already written by Codex, indexes aggregate usage counters into SQLite, and gives you a dashboard, CLI, and MCP tools for understanding where tokens are going. It is built for investigating real usage patterns while keeping prompts, assistant messages, tool output, and pasted secrets out of the stored index and generated dashboard HTML.

## Dashboard Preview

![Calls view with filters, totals, model-call rows, and the details panel.](docs/assets/dashboard-calls.png)

![Threads view with grouped Codex threads and expanded chronological calls.](docs/assets/dashboard-threads.png)

![Call Details panel showing aggregate token, pricing, context, and thread attachment fields.](docs/assets/dashboard-details.png)

These screenshots use synthetic aggregate fixture data. They do not contain prompts, assistant responses, tool output, or real Codex session content.

## Why Use It

Use this when you want to answer questions like:

- Which Codex threads are using the most tokens or estimated cost?
- Which models and reasoning efforts are driving usage?
- Do long-running chats get more expensive over time?
- Are subagents, auto-reviews, or review passes attached to the right parent work?
- Which calls have low cache reuse, high context-window pressure, or large reasoning output?
- Which active project directories are consuming the most usage?
- Did a change in workflow, model choice, or reasoning mode improve efficiency?

The dashboard is intentionally split into two views:

- `Calls`: inspect individual model calls, token fields, pricing status, cache ratio, reasoning output, and context-window percentage.
- `Threads`: group calls by Codex thread, expand a thread chronologically, and see spawned subagents and inferred auto-review work in context.

## Important Pattern: Long Chats Can Bloat Fast

A common pattern this tool makes obvious is that staying in the same Codex chat for a long time can rapidly grow the context carried into later turns.

Prompt caching helps, but cached input is not the same as no input. Long threads can accumulate a large cached context, and each new turn may still include a large amount of cached input plus new uncached input, reasoning output, and tool-related context. That can make usage climb quickly even when the visible user request looks small.

Watch these fields when investigating that pattern:

- `Cached input`: how much previously seen context was reused.
- `Uncached input`: how much fresh context was added for the call.
- `Session cumulative`: how large the running session total has become.
- `Context use`: how much of the model context window the call consumed.
- `Cache ratio`: useful for spotting whether a thread is mostly reused context or mostly new context.

Practical takeaway: when old context is no longer relevant, starting a fresh thread can be more efficient than dragging a large cached history forward. This is not a rule for every task, but it is one of the clearest usage patterns the dashboard is designed to reveal.

## What It Does

- Reads local Codex JSONL logs from `~/.codex/sessions/**/*.jsonl`.
- Optionally includes `~/.codex/archived_sessions/*.jsonl`.
- Stores aggregate-only usage metrics in local SQLite at `~/.codex-usage-tracker/usage.sqlite3`.
- Exposes MCP tools for refresh, summaries, session detail, lazy call context, CSV export, and dashboard generation.
- Generates a static hoverable dashboard with flat calls and threaded-by-thread views.
- Can serve the dashboard from localhost so raw logged context is loaded only after a row action.
- Provides a read-only doctor command for local plugin/MCP setup checks.
- Optionally estimates costs from a local pricing file that can be refreshed from OpenAI's published pricing docs.
- Tracks aggregate subagent metadata, including explicit parent session ids when Codex logs them.

The tracker intentionally does not store prompts, assistant messages, tool outputs, pasted secrets, or raw transcript snippets in SQLite, CSV exports, or generated dashboard HTML. The optional localhost server can read redacted, size-limited context from the original JSONL file on demand.

## Quick Install

### Let Codex Install It

Open a Codex session on your machine and paste this:

```text
Install and configure Codex Usage Tracker from https://github.com/douglasmonsky/codex-usage-tracker.
Use pipx if it is available. If pipx is missing, install it with Homebrew or use a local virtual environment.
After installation, run codex-usage-tracker install-plugin, update-pricing, refresh, doctor, and serve-dashboard --open.
Verify the dashboard opens locally and tell me the dashboard URL plus whether I need to restart Codex for plugin discovery.
```

Codex should run roughly:

```bash
brew install pipx
pipx ensurepath
pipx install "git+https://github.com/douglasmonsky/codex-usage-tracker.git"
codex-usage-tracker install-plugin
codex-usage-tracker update-pricing
codex-usage-tracker refresh
codex-usage-tracker doctor
codex-usage-tracker serve-dashboard --open
```

Restart Codex after `install-plugin` if you want Codex to discover the plugin tools in a fresh session. The localhost dashboard can run immediately.

### Manual Install

Run:

```bash
brew install pipx
pipx ensurepath
pipx install "git+https://github.com/douglasmonsky/codex-usage-tracker.git"
codex-usage-tracker install-plugin
codex-usage-tracker update-pricing
codex-usage-tracker refresh
codex-usage-tracker serve-dashboard --open
```

After a PyPI release, the install command becomes:

```bash
pipx install codex-usage-tracker
```

`install-plugin` creates `~/plugins/codex-usage-tracker`, writes a package-owned `.mcp.json` that points at the installed Python executable, and updates `~/.agents/plugins/marketplace.json`. Restart Codex after registration so it discovers the plugin.

## Fastest Useful Workflow

```bash
codex-usage-tracker update-pricing
codex-usage-tracker serve-dashboard --open
```

Then:

1. Leave `Live` enabled while working, or click `Refresh` after a Codex run finishes.
2. Open `Threads` view to find the active work thread and any spawned subagent or auto-review calls.
3. Sort by `Cost`, `Tokens`, `Cache`, or `Context` depending on the question.
4. Expand an expensive thread and read calls oldest to newest.
5. Hover or click rows to inspect exact aggregate fields in `Call Details`.
6. Use `Load context` only when the aggregate fields are not enough; context is fetched on demand from the local source JSONL and is not saved into SQLite or the dashboard.

For a screenshot-driven walkthrough, see [`docs/dashboard-guide.md`](docs/dashboard-guide.md).
Generated dashboards also link to a bundled local HTML copy of the guide. Set `CODEX_USAGE_TRACKER_DOCS_URL` if you want generated dashboards to point at a hosted docs page instead.

## Development Setup

```bash
git clone https://github.com/douglasmonsky/codex-usage-tracker.git
cd codex-usage-tracker
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ".[dev]"
codex-usage-tracker install-plugin --python .venv/bin/python
```

## Usage

Refresh the local aggregate index:

```bash
codex-usage-tracker refresh
```

Check setup:

```bash
codex-usage-tracker doctor
codex-usage-tracker --version
python -m codex_usage_tracker --version
```

Generate the local dashboard:

```bash
codex-usage-tracker dashboard --open
codex-usage-tracker open-dashboard
```

Serve the dashboard with live aggregate refresh and lazy raw-context loading:

```bash
codex-usage-tracker serve-dashboard --open
```

When served this way, the dashboard gets a `Refresh` button plus a `Live` toggle that polls the localhost `/api/usage` endpoint every 10 seconds while the tab is visible. Each poll refreshes the SQLite aggregate index from local Codex logs and replaces the in-memory dashboard rows without embedding raw transcript content. Use the `Load` selector to fetch 5,000, 10,000, 20,000, or all aggregate calls; `--limit 0` also means all calls for CLI-generated dashboards. The table renders 500 rows or thread groups per page so larger histories remain responsive. Each call detail panel also gets a `Load context` action. Pressing it fetches only that call's logged turn context from the original local JSONL source. Tool output is omitted by default; the `Include tool output` action loads redacted, size-limited tool output for that call. None of this raw context is written to SQLite, CSV, or the generated HTML.

Dashboard behavior:

- The flat `Calls` view opens newest-first for inspecting individual model calls.
- The `Threads` view groups filtered calls by thread, shows the most recently active thread first by default, and lets multiple threads stay expanded.
- Expanded thread calls are ordered oldest to newest so you can see how usage grew across the conversation.
- Spawned subagents with logged parent sessions are shown under their parent thread when Codex logs enough metadata.
- Auto-review sessions do not currently log an explicit parent session id, so the dashboard can infer attachment by cwd and nearby activity and marks that relationship in the details panel.
- Mixed thread model summaries prefer non-review models; `codex-auto-review` is shown as the thread model only for review-only threads.

Useful investigations:

- Sort `Threads` by `Tokens` or `Cost` to find the conversations worth reviewing first.
- Sort by `Cache` to find threads that are mostly new context versus mostly reused context.
- Sort by `Context` to find calls approaching the model context window.
- Filter by model or reasoning effort to compare usage patterns across model choices.
- Use `summary --preset by-subagent-role` to see whether delegated work is driving a large share of usage.
- Use `expensive --limit 10` for a quick CLI list of the highest-cost calls.

Show a summary:

```bash
codex-usage-tracker summary --group-by model
codex-usage-tracker summary --group-by thread --limit 20
codex-usage-tracker summary --preset today
codex-usage-tracker summary --preset last-7-days
codex-usage-tracker summary --preset expensive
codex-usage-tracker summary --preset by-subagent-role
codex-usage-tracker expensive --limit 10
codex-usage-tracker pricing-coverage
```

Show one session:

```bash
codex-usage-tracker session <session-id>
```

Load one call's logged context on demand:

```bash
codex-usage-tracker context <record-id>
```

Export CSV:

```bash
codex-usage-tracker export --output usage.csv
codex-usage-tracker export --output usage.csv --limit 0
```

Enable optional cost estimates:

```bash
codex-usage-tracker update-pricing
```

This fetches OpenAI text-token pricing from `https://developers.openai.com/api/docs/pricing.md`, parses the selected tier, and writes a source-stamped local cache to `~/.codex-usage-tracker/pricing.json`. The default tier is `standard`; other supported tiers are `batch`, `flex`, and `priority`. If a pricing file already exists, the updater leaves a timestamped `.bak` copy next to it before replacing the active cache.

The updater also includes marked best-guess estimates for Codex labels that are not finalized in the public pricing table. `codex-auto-review` uses OpenAI's published `codex-mini-latest` Codex pricing from `https://openai.com/index/introducing-codex/`: `$1.50` per 1M input tokens, a 75% prompt-cache discount (`$0.375` per 1M cached input tokens), and `$6.00` per 1M output tokens. `gpt-5.3-codex-spark` is listed by OpenAI as a research preview with non-final Codex rates, so the tracker estimates it as `gpt-5.3-codex` at `$1.75` per 1M input tokens, `$0.175` per 1M cached input tokens, and `$14.00` per 1M output tokens. Use `--no-estimates` when you want only pricing rows parsed from the OpenAI pricing table.

For a manual template instead:

```bash
codex-usage-tracker init-pricing
```

Edit `~/.codex-usage-tracker/pricing.json` with USD-per-million-token rates for any local overrides or models that are not present in the OpenAI pricing table. Normal reports never contact the network; only `update-pricing` refreshes the local pricing cache.

## Current Limitations

- This is a sidecar dashboard and plugin, not a native Codex chat overlay. Native hover tooltips inside Codex chat would require a transcript UI extension point that is not part of this v1 surface.
- Token counts come from Codex's logged counters. The tracker does not re-tokenize prompts or reconstruct usage from raw text.
- Pricing is optional and local. Rows are unpriced when no matching model rate is configured, and some Codex-specific labels may use marked best-guess estimates.
- Parent-child thread relationships are only as good as the metadata Codex logs. Explicit parent session ids are preferred; inferred auto-review attachments are labeled as inferred.
- On-demand context loading reads from the original local JSONL source. It is redacted and size-limited, but it is still local raw log context and should be treated as sensitive.

## Install As A Local Codex Plugin

After installing the Python package, register the plugin locally:

```bash
codex-usage-tracker install-plugin
```

For a source checkout that should use the repo-local virtual environment:

```bash
codex-usage-tracker install-plugin --python .venv/bin/python
```

If you previously installed the older source-checkout symlink, replace it once:

```bash
codex-usage-tracker install-plugin --python .venv/bin/python --force
```

The compatibility script remains available for local development:

```bash
python scripts/install_local_plugin.py --python .venv/bin/python
```

Restart Codex after registration so it can discover the plugin.

## MCP Tools

- `refresh_usage_index`
- `usage_doctor`
- `usage_summary`
- `session_usage`
- `usage_call_context`
- `most_expensive_usage_calls`
- `usage_pricing_coverage`
- `generate_usage_dashboard`
- `export_usage_csv`
- `init_usage_pricing_config`
- `update_usage_pricing_config`

## Data Privacy

The SQLite database is stored at `~/.codex-usage-tracker/usage.sqlite3` by default and contains only aggregate metrics:

- session id, thread name, cwd, source file, turn id, timestamps
- model, reasoning effort, context window
- token counts and derived efficiency ratios
- subagent source, role, nickname, parent session id, and parent thread name when present

Raw chat text and tool outputs are ignored by the parser and are never written to the tracker database, CSV exports, or generated dashboard HTML. `usage_call_context`, `codex-usage-tracker context`, and the `serve-dashboard` context endpoint read a single source JSONL file only when explicitly requested, redact common secret patterns, and cap returned text size.

For MCP users, `usage_call_context` is additionally disabled unless the MCP server process has `CODEX_USAGE_TRACKER_ALLOW_RAW_CONTEXT=1` in its environment. Aggregate MCP tools do not require that opt-in.

Cost estimates are calculated only from aggregate token fields and your local pricing config. They are omitted when no matching model price is configured. Pricing refreshes pull only OpenAI's public pricing markdown and do not send local usage data anywhere.

## Test

```bash
python -m pytest
python -m compileall src
python -m build
python scripts/check_release.py --dist
git diff --check
codex-usage-tracker update-pricing --output /tmp/codex-usage-pricing.json
codex-usage-tracker doctor
codex-usage-tracker dashboard --output /tmp/codex-usage-dashboard.html
codex-usage-tracker serve-dashboard --help
codex-usage-tracker pricing-coverage
codex-usage-tracker summary --preset by-subagent-role
codex-usage-tracker expensive --limit 5
```

## Release Checklist

Before making the repository public or publishing a package:

```bash
python -m pytest
python -m compileall src
python -m build
python scripts/check_release.py --dist
git diff --check
```

Then verify the local package install path:

```bash
python -m pip install ".[dev]"
codex-usage-tracker --version
codex-usage-tracker install-plugin --plugin-dir /tmp/codex-usage-tracker-plugin-smoke --marketplace /tmp/codex-usage-marketplace-smoke.json --python .venv/bin/python --force
```

Keep the GitHub repository private until you are ready to intentionally switch visibility. The release checker verifies version alignment, required public docs, packaged plugin assets, wheel contents, and obvious tracked secret patterns; it does not publish anything.

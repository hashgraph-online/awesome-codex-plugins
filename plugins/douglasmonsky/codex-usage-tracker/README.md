# Codex Usage Tracker

<p align="center">
  <a href="docs/assets/dashboard-calls.png"><img src="docs/assets/dashboard-calls-preview.png?v=readme-drilldown" alt="Codex Usage Tracker dashboard showing filters, usage totals, and named model-call rows." width="49%"></a>
  <a href="docs/assets/dashboard-call-investigator.png"><img src="docs/assets/dashboard-call-investigator-preview.png?v=readme-drilldown" alt="Codex Usage Tracker call investigator showing token accounting, cache diagnostics, and redacted runtime evidence." width="49%"></a>
</p>

Local-first dashboard, Codex plugin, and companion skill for understanding where your Codex tokens and usage credits are going.

[![CI](https://github.com/douglasmonsky/codex-usage-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/douglasmonsky/codex-usage-tracker/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/codex-usage-tracking.svg)](https://pypi.org/project/codex-usage-tracking/)
![Python 3.10-3.14](https://img.shields.io/badge/python-3.10--3.14-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Unofficial project:** Codex Usage Tracker is an independent open-source project. It is not made by, affiliated with, endorsed by, sponsored by, or supported by OpenAI. OpenAI and Codex are trademarks of OpenAI; this project only reads local log files from your machine.

Codex Usage Tracker reads the JSONL logs already written by Codex, indexes aggregate usage counters into SQLite, and gives you a dashboard, CLI, and MCP tools for investigating real usage patterns. It keeps prompts, assistant messages, tool output, pasted secrets, and raw transcript content out of SQLite, CSV exports, and generated dashboard HTML.

Built for developers using Codex locally who want to know which threads, models, subagents, and long chats are driving usage without uploading logs anywhere. The public PyPI package is [`codex-usage-tracking`](https://pypi.org/project/codex-usage-tracking/), and it installs the `codex-usage-tracker` command.

After install, you get a localhost dashboard, a local SQLite aggregate index, CLI reports, MCP tools, and a companion Codex skill for asking questions like "what drove my usage this week?"

## Quick Install

```bash
python -m pip install --user pipx
python -m pipx ensurepath
pipx install codex-usage-tracking
codex-usage-tracker setup
codex-usage-tracker serve-dashboard --open
```

Use your normal Python launcher for your platform: `python3` is common on macOS/Linux, and `py` may be preferable on Windows. On macOS with Homebrew, `brew install pipx` is also fine.
If `codex-usage-tracker` is not found after installing with pipx, open a new terminal or add the binary directory printed by `pipx ensurepath` to your `PATH`.

`serve-dashboard` refreshes active-session usage before opening by default. Use `--no-refresh` only when you intentionally want to inspect the cached local index.

Package naming: the PyPI distribution is `codex-usage-tracking`; the installed command is `codex-usage-tracker`; the GitHub repository remains `douglasmonsky/codex-usage-tracker`. The `codex-usage-tracker` PyPI name is not this project, so avoid similarly named packages when following these docs.

Source install for development or branch testing:

```bash
pipx install "git+https://github.com/douglasmonsky/codex-usage-tracker.git"
```

`setup` installs or refreshes the local Codex plugin wrapper, initializes local config templates when needed, refreshes the aggregate index, runs `codex-usage-tracker doctor`, and tells you whether Codex needs a restart for plugin discovery.

Want Codex to do it for you? Paste: `Install codex-usage-tracking with pipx, run codex-usage-tracker setup, and open the Codex Usage Tracker dashboard.`

## Dashboard Preview

The Calls table is the main investigation surface: filter, sort, inspect details, and export the exact aggregate rows you are looking at.

![Calls view showing filters, totals, the model-call table, and the compact details rail.](docs/assets/dashboard-calls.png?v=readme-drilldown)

Click a call to open the dedicated investigator for exact token accounting, cache/accounting deltas, local serialized evidence buckets, and redacted turn-log evidence loaded only at runtime.

![Call investigator showing token accounting, cache diagnostics, serialized evidence groups, and raw evidence controls.](docs/assets/dashboard-call-investigator.png?v=readme-drilldown)

The lower investigator view keeps the raw JSONL evidence opt-in and runtime-only while still showing visible-context estimates, serialized evidence upper bounds, and redacted turn-log entries.

![Lower call investigator view showing context-change estimates, serialized evidence groups, and redacted runtime evidence entries.](docs/assets/dashboard-call-investigator-evidence.png?v=readme-drilldown)

Threads view groups related calls so long chats, subagents, and auto-review passes are easier to reason about as one work session.

![Threads view with one expanded thread and its calls in chronological order.](docs/assets/dashboard-threads.png?v=readme-drilldown)

Insights still gives a fast triage layer for costly threads, low cache reuse, context bloat, and pricing gaps.

![Insights view with ranked Needs Attention cards, investigation presets, and top threads by attention score.](docs/assets/dashboard-insights.png?v=readme-drilldown)

The dashboard screenshots use synthetic aggregate fixture data, and the companion prompt and chat previews are synthetic. They do not contain prompts from local logs, assistant responses, tool output, real thread names, real usage totals, or real Codex session content. See the [Dashboard Guide](docs/dashboard-guide.md) for the full walkthrough.

If this helped you track Codex usage, starring the repo helps others find it. Issues and feature requests are welcome.

## Companion Skill And Plugin

The dashboard is the core product surface. The Codex plugin and companion usage skill are add-ons that let Codex refresh local aggregates, call the MCP tools, and explain usage patterns conversationally after plugin discovery. Examples: [MCP And Codex Skills](docs/mcp.md).

<p align="center">
  <a href="docs/assets/plugin-prompts.png"><img src="docs/assets/plugin-prompts.png?v=readme-drilldown" alt="Synthetic Codex plugin prompt preview showing usage dashboard and thread investigation suggestions." width="86%"></a>
</p>

<p align="center">
  <a href="docs/assets/plugin-thread-leaderboard.png"><img src="docs/assets/plugin-thread-leaderboard.png?v=readme-drilldown" alt="Synthetic Codex chat preview showing the companion skill ranking threads by token usage after refreshing the local aggregate index." width="86%"></a>
</p>

If you only want plugin registration after installing the package:

```bash
codex-usage-tracker install-plugin
```

More install paths: [Install Guide](docs/install.md).

## Platform Support

The core app is not macOS-only. The CLI, SQLite index, dashboard generator, and localhost server are Python-based and CI-tested on Ubuntu for Python 3.10-3.14. The installed-package Docker smoke path uses `python:3.14-slim` by default so packaged resources and CLI entry points are exercised on the newest supported runtime. It defaults to `~/.codex` for local Codex logs and `~/.codex-usage-tracker` for tracker data; pass `--codex-home` or `--db` when your local layout differs. Codex plugin discovery depends on Codex's local plugin directories on your machine, so run `codex-usage-tracker doctor` after setup if plugin registration does not appear in Codex.

## Why This Exists

Codex can quietly burn usage through long-running chats, low cache reuse, reasoning spikes, spawned subagents, and auto-review passes. This tool turns the aggregate counters already on your machine into an insight-first dashboard and scriptable local APIs.

Use it to answer:

- Which threads used the most tokens, estimated cost, or Codex credits?
- Are long chats bloating because of accumulated context?
- Which model or reasoning effort is driving usage?
- Are subagents or auto-review passes adding unexpected cost?
- Which calls have low cache reuse, high context pressure, reasoning spikes, or pricing gaps?
- Which projects, project tags, or active directories are consuming the most usage?
- What should Codex inspect next using the companion usage skill?

## Long Chats Can Bloat Fast

Prompt caching helps, but cached input is not the same as no input. Long threads can accumulate a large cached context, and each new turn may still include cached input plus fresh uncached input, output tokens, reasoning output, and tool-related context.

The dashboard makes that pattern visible with:

- `Cached input`
- `Uncached input`
- `Session cumulative`
- `Context use`
- `Cache ratio`

Practical takeaway: when old context is no longer useful, starting a fresh thread can be more efficient than dragging a large cached history forward. That is not a rule for every task, but it is one of the clearest usage patterns the tracker is designed to reveal.

## First Useful Workflow

```bash
codex-usage-tracker update-pricing
codex-usage-tracker update-rate-card
codex-usage-tracker setup
codex-usage-tracker serve-dashboard --open
```

Then:

1. Leave `Live` enabled while working, or click `Refresh` after a Codex run finishes.
2. Start in `Insights` and scan the `Needs Attention` cards.
3. Use `Time` presets or calendar fields to focus on today, this week, the last 7 days, this month, or a custom range.
4. Use investigation presets for highest-cost threads, highest-credit calls, context bloat, cache misses, pricing gaps, or estimated-price review.
5. Open `Threads` to see how a conversation grew and whether subagent or auto-review work attached to it.
6. Hover or click rows to inspect aggregate fields in `Call Details`.
7. Use `Show turn log evidence` only when aggregate fields are not enough; context is fetched on demand from the local source JSONL and is not saved into SQLite or the dashboard.

Optional allowance context:

```bash
codex-usage-tracker parse-allowance "5h 79% 6:50 PM Weekly 33% Jun 7"
```

The tracker cannot read your logged-in ChatGPT plan or live remaining usage automatically. Allowance values are only as accurate as the values you manually copy from Codex Settings, `/status`, or another trusted usage display. Details: [Pricing, Credits, And Allowance](docs/pricing-and-credits.md).

## What It Includes

- Local SQLite index at `~/.codex-usage-tracker/usage.sqlite3`.
- Static dashboard generation plus localhost live refresh.
- `Insights`, `Calls`, and `Threads` dashboard views.
- Active-only dashboards by default, with an explicit `All history` toggle for archived sessions.
- CLI summaries, queries, CSV export, dashboard generation, doctor checks, and support bundles.
- MCP tools for Codex sessions that want to query local usage data.
- Companion Codex skills for operational setup and conversational usage analysis.
- Optional local pricing, Codex credit, allowance, threshold, project alias, and privacy-mode configuration.

## Dashboard Language

The dashboard supports localized UI text. English is the canonical catalog, and the project includes translated locale catalogs for common dashboard languages.

Set the initial dashboard language with `--lang`:

```bash
codex-usage-tracker --lang vi serve-dashboard --open
```

Or set a default with:

```bash
CODEX_USAGE_TRACKER_LANG=vi codex-usage-tracker serve-dashboard --open
```

The dashboard also includes a language selector. Browser selections are stored locally and can override the generated default for that browser.

Supported dashboard locales include English, Vietnamese, Spanish, French, German, Portuguese, Japanese, Simplified Chinese, Korean, Russian, Italian, and Arabic. This localizes dashboard UI text, not raw Codex log content, thread names, project names, paths, full CLI output, or data exports.

### Adding A Dashboard Language

1. Add a locale JSON file named by language code under `src/codex_usage_tracker/plugin_data/dashboard/locales/`.
2. Include every key from the English catalog.
3. Preserve every placeholder from the English string.
4. Add the language code, native name, English name, and text direction to the supported language metadata.
5. Run the i18n validation tests.

## Common Commands

```bash
codex-usage-tracker summary --preset last-7-days
codex-usage-tracker query --since 2026-06-01 --min-credits 1
codex-usage-tracker session <session-id>
codex-usage-tracker export --output usage.csv
codex-usage-tracker open-dashboard
codex-usage-tracker support-bundle --output ~/.codex-usage-tracker/support-bundle.json
```

Full command reference: [CLI Reference](docs/cli-reference.md).

## Data Privacy

The tracker stores aggregate metrics only: session ids, timestamps, local source paths, thread labels, cwd/project metadata, model labels, reasoning effort, token counters, pricing/credit annotations, and derived ratios.

It does **not** store prompts, assistant messages, tool output, pasted secrets, raw transcript snippets, or raw context in SQLite, CSV exports, generated dashboard HTML, or synthetic screenshots.

On-demand context loading reads a single original local JSONL file only after an explicit row action, redacts common secret patterns, caps returned text size, and can start off until you enable it from the details panel:

```bash
codex-usage-tracker serve-dashboard --no-context-api --open
```

For shared artifacts, use:

```bash
codex-usage-tracker --privacy-mode redacted dashboard --open
codex-usage-tracker --privacy-mode strict export --output usage-redacted.csv
```

Full model: [Privacy Guide](docs/privacy.md).

## Documentation

- [Install Guide](docs/install.md)
- [Dashboard Guide](docs/dashboard-guide.md)
- [CLI Reference](docs/cli-reference.md)
- [Pricing, Credits, And Allowance](docs/pricing-and-credits.md)
- [MCP And Codex Skills](docs/mcp.md)
- [Privacy Guide](docs/privacy.md)
- [Architecture](docs/architecture.md)
- [CLI And MCP JSON Schemas](docs/cli-json-schemas.md)
- [Development And Release](docs/development.md)

## Codex-Assisted Install

Open a Codex session on your machine and paste this:

```text
Install and configure Codex Usage Tracker.
Install the PyPI distribution codex-usage-tracking with pipx. The installed command should be codex-usage-tracker. Use pipx install "git+https://github.com/douglasmonsky/codex-usage-tracker.git" only for branch testing or if PyPI is temporarily unavailable.
If pipx is missing, install it with the platform's Python launcher or use a local virtual environment.
After installation, run codex-usage-tracker setup and serve-dashboard --open.
Verify the dashboard opens locally and tell me the dashboard URL plus whether I need to restart Codex for plugin discovery.
```

This is optional. The normal shell install above is the fastest trusted path for most users.

## Current Limitations

- This is a sidecar dashboard and plugin, not a native Codex chat overlay.
- Codex upstream log formats can change, and parser compatibility may require tracker updates.
- Token counts come from Codex's logged counters; the tracker does not re-tokenize prompts.
- Pricing and rate-card sources can change outside this project.
- Pricing and Codex credit estimates depend on local rate data and confidence labels and are not guaranteed to match exact billing.
- Live account allowance cannot be read automatically by this local tracker; remaining 5-hour and weekly allowance is only available when you configure copied values.
- Local Codex logs may not include usage from other ChatGPT agentic surfaces that share the same allowance.
- Plugin discovery limitations are separate from core Python CLI/dashboard support.
- Parent-child thread relationships are only as good as the metadata Codex logs; inferred auto-review attachments are labeled as inferred.

## Roadmap

- Keep Python runtime support validated with CI matrix coverage, package classifiers, release docs, and installed-package smoke tests.
- Improve the `Set limits` flow with a paste/import experience for 5-hour and weekly allowance snapshots.
- Track allowance snapshot history so local Codex credits can be compared against visible remaining-usage changes over time.
- Clarify top-card token accounting by showing output tokens and reasoning output as a subset instead of implying all token cards add together.
- Add more insight presets for cache drift, context growth, subagent-heavy workflows, and pricing/credit confidence gaps.
- Keep the allowance provider boundary ready for an official usage or allowance API if one becomes available.
- Continue reducing setup friction for pipx installs, local plugin discovery, and Codex companion skill usage.

## Development

```bash
git clone https://github.com/douglasmonsky/codex-usage-tracker.git
cd codex-usage-tracker
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ".[dev]"
python -m pytest
```

Run the full local CI gate before pushing to `main`. See [Development And Release](docs/development.md).

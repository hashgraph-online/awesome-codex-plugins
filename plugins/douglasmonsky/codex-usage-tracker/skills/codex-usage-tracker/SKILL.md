---
name: codex-usage-tracker
description: Use when the user asks about Codex token usage, model/reasoning efficiency, usage dashboards, CSV exports, or per-session/per-turn Codex usage stats from local logs.
---

# Codex Usage Tracker

Unofficial project: Codex Usage Tracker is independent and is not made by, affiliated with, endorsed by, sponsored by, or supported by OpenAI. OpenAI and Codex are trademarks of OpenAI.

Use this plugin to inspect aggregate token usage from local Codex session logs.

## Privacy Boundary

The index, dashboard payload, CSV export, and normal summaries are aggregate-only. They should never return prompts, assistant message text, tool outputs, pasted secrets, or raw transcript snippets.

The only exception is `usage_call_context`, which intentionally reads one selected record's source JSONL on demand. It requires `CODEX_USAGE_TRACKER_ALLOW_RAW_CONTEXT=1` in the MCP server environment. Use it only when the user explicitly asks to inspect actual context, and mention that returned text is local, redacted, size-limited, and not persisted by the tracker.

## Fast Paths

- For "Open dashboard" or similar dashboard-open requests, do not inspect repository files, plugin manifests, tool registries, git status, or local logs first. Start the live localhost dashboard with `codex-usage-tracker serve-dashboard --context-api explicit --open` so Refresh, Live, load-limit, and history-scope controls can call the local API. Refresh is the default for dashboard launch commands; use `--no-refresh` only when the user explicitly asks for a cached snapshot. Keep the server running while the user is using the dashboard. Use `codex-usage-tracker open-dashboard` only when the user explicitly asks for a static/offline snapshot or when the current environment cannot keep a server process running, and say that the result is static and Live requires `serve-dashboard`.
- For "Heaviest thread?", "Thread leaderboard", or similar thread-ranking requests, do not inspect repository files, SQLite schemas, plugin manifests, process lists, dashboard servers, or local logs manually. Use the tracker API: refresh the aggregate index, then rank threads with `usage_summary(group_by="thread", limit=10, response_format="json")`.
- If MCP tools are unavailable for thread-ranking requests, run `codex-usage-tracker refresh --json` and `codex-usage-tracker summary --group-by thread --limit 10 --json`. The summary is already ordered by `total_tokens` descending.
- Answer thread-ranking requests directly from the summary rows. For the heaviest-thread question, lead with the first row's thread and total tokens; for leaderboard requests, show a compact ranked list.
- If the CLI command is missing for dashboard-open requests and you are already inside the source checkout, use `PYTHONPATH=src .venv/bin/python -m codex_usage_tracker.cli serve-dashboard --context-api explicit --open`. Use the source-checkout `open-dashboard` fallback only for static/offline snapshots or when a long-running server cannot be kept alive.
- If the CLI command is missing for thread-ranking requests and you are already inside the source checkout, use `PYTHONPATH=src .venv/bin/python -m codex_usage_tracker.cli refresh --json` and `PYTHONPATH=src .venv/bin/python -m codex_usage_tracker.cli summary --group-by thread --limit 10 --json`.
- If neither command is available, say briefly that the tracker CLI is not on `PATH` and ask the user to run `codex-usage-tracker setup` or reinstall with `pipx`.
- Keep dashboard-open narration minimal: one short progress note if needed, then the localhost URL, or if falling back to a static file, the file path plus a note that Live requires `serve-dashboard`. Do not narrate plugin discovery.

## Common Workflows

- Refresh the index before answering usage questions.
- Use `usage_doctor` when setup, plugin discovery, MCP launch, dashboard output, or pricing estimates look wrong.
- Use `usage_summary` for high-level totals by date, model, effort, cwd, thread, or session.
- Use `usage_query` for stable JSON rows filtered by date, project, model, effort, thread, pricing status, token minimums, or Codex credit minimums.
- Use `usage_recommendations` when the user asks what to inspect next or wants ranked action items by aggregate severity.
- Use `usage_summary` presets `today`, `last-7-days`, `by-model`, `by-cwd`, `by-thread`, and `expensive` for common requests.
- Use `usage_pricing_coverage` when the user asks whether costs are fully priced or which models use estimated or missing pricing.
- Use `session_usage` for per-call and per-turn detail for one session.
- Use `usage_call_context` for one selected model call when the user asks to load actual logged context on demand.
- Use `most_expensive_usage_calls` to identify high-token calls and aggregate efficiency signals.
- Use `privacy_mode="redacted"` or `privacy_mode="strict"` for MCP tools, or the CLI global option `--privacy-mode strict` before a subcommand, when the user plans to share dashboards, CSV, JSON, screenshots, or support bundles.
- Use `generate_usage_dashboard` when the user wants a visual hoverable report, including flat calls, threaded-by-thread views, parent-thread latching for spawned subagents, auto-review attachment details, an active-only default, and explicit all-history archived-session opt-in.
- Use `export_usage_csv` when the user wants local spreadsheet-friendly data.
- Use `update_usage_pricing_config` when the user wants cost estimates based on OpenAI-published text-token pricing. This refreshes the local pricing cache and does not send local usage data anywhere. Internal Codex labels may include explicitly marked best-guess estimates when no public pricing row exists.
- Use `init_usage_pricing_config` only when the user wants a manual local pricing template or override file.
- Codex credit estimates are aggregate-only and use bundled or locally configured Codex rate-card values. Direct model matches are exact; aliases and inferred labels are marked estimated.
- Use `init_usage_allowance_config` only when the user wants a local allowance template for manually copied 5-hour or weekly remaining usage from Codex Usage or `/status`.

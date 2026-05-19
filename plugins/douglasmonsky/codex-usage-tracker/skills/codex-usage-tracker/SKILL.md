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

## Common Workflows

- Refresh the index before answering usage questions.
- Use `usage_doctor` when setup, plugin discovery, MCP launch, dashboard output, or pricing estimates look wrong.
- Use `usage_summary` for high-level totals by date, model, effort, cwd, thread, or session.
- Use `usage_summary` presets `today`, `last-7-days`, `by-model`, `by-cwd`, `by-thread`, and `expensive` for common requests.
- Use `usage_pricing_coverage` when the user asks whether costs are fully priced or which models use estimated or missing pricing.
- Use `session_usage` for per-call and per-turn detail for one session.
- Use `usage_call_context` for one selected model call when the user asks to load actual logged context on demand.
- Use `most_expensive_usage_calls` to identify high-token calls and aggregate efficiency signals.
- Use `generate_usage_dashboard` when the user wants a visual hoverable report, including flat calls, threaded-by-thread views, parent-thread latching for spawned subagents, auto-review attachment details, and controls that can call a localhost context endpoint when the dashboard is served.
- Use `export_usage_csv` when the user wants local spreadsheet-friendly data.
- Use `update_usage_pricing_config` when the user wants cost estimates based on OpenAI-published text-token pricing. This refreshes the local pricing cache and does not send local usage data anywhere. Internal Codex labels may include explicitly marked best-guess estimates when no public pricing row exists.
- Use `init_usage_pricing_config` only when the user wants a manual local pricing template or override file.

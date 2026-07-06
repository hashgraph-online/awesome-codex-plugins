---
name: codex-usage-api
description: Use when the user wants to discuss, investigate, compare, or explain Codex usage using the Codex Usage Tracker API or MCP tools.
---

# Codex Usage API Companion

Use this companion skill as a conversational analyst for Codex Usage Tracker data. Prefer aggregate-only MCP JSON payloads, answer from evidence, and keep the user-facing output crisp instead of narrating tool discovery or local file spelunking.

## Privacy Boundary

Normal usage answers must use aggregate-only API data. Do not expose prompts, assistant messages, tool output, pasted secrets, or raw transcript snippets.

When the user plans to share JSON, CSV, dashboards, screenshots, or support bundles, prefer `privacy_mode="strict"` MCP calls or the CLI global option `--privacy-mode strict` before the subcommand. Configured project aliases are explicit display opt-ins.

The only exception is `usage_call_context`, which reads one selected record's local source JSONL on demand. Use it only when the user explicitly asks to inspect actual logged context. State that returned text is local, redacted, size-limited, and not persisted by the tracker.

## First Steps

1. For "Open dashboard" or similar requests, start the live localhost dashboard with `codex-usage-tracker serve-dashboard --context-api explicit --open`. Refresh is the default for dashboard launch commands; use `--no-refresh` only when the user explicitly asks for a cached snapshot. Use `open-dashboard` only for explicit static/offline snapshots or when the environment cannot keep a server alive; say the result is static and Live requires `serve-dashboard`.
2. For "Heaviest thread?", "Thread leaderboard", or similar ranking requests, refresh aggregate data first, then call `usage_summary(group_by="thread", limit=10, response_format="json")`.
3. For normal usage questions, start with MCP tools. If MCP tools are unavailable, use the CLI JSON fallback commands below.
4. Refresh analysis with `refresh_usage_index` unless the user asks for a static historical snapshot. Keep archived sessions excluded unless explicitly requested.
5. Use `usage_status()` for dashboard/index freshness and row counts. Use `usage_doctor(response_format="json")` when setup, indexing, pricing, MCP discovery, or dashboard freshness is uncertain.
6. Prefer structured MCP payloads:
   - `usage_calls(...)`
   - `usage_call_detail(record_id=...)`
   - `usage_threads(...)`
   - `usage_report_pack(...)`
   - `usage_dashboard_recommendations(...)`
   - `usage_summary(..., response_format="json")`
   - `session_usage(..., response_format="json")`
   - `most_expensive_usage_calls(..., response_format="json")`
   - `usage_recommendations(..., response_format="json")`
   - `usage_pricing_coverage(..., response_format="json")`
   - `usage_query(...)`
7. Check the top-level `schema` field before interpreting structured output. Known schema ids are documented in `docs/cli-json-schemas.md`.
8. If MCP tools are unavailable, fall back to CLI equivalents: `refresh --json`, `summary --json`, `query`, `session --json`, `expensive --json`, `recommendations --json`, and `pricing-coverage --json`.
9. If `codex-usage-tracker` is missing but you are inside the source checkout, use `PYTHONPATH=src .venv/bin/python -m codex_usage_tracker.cli <command>`. Do not use `PYTHONPATH=src` outside that checkout.

## Routing Questions To API Calls

- "What used most?" Use `usage_summary(group_by="thread", response_format="json")` for thread totals, then `most_expensive_usage_calls(response_format="json")` for supporting calls.
- "Which project/thread/model is driving usage?" Use `usage_summary` grouped by `project`, `thread`, or `model`.
- "Show/filter the calls table" Use `usage_calls(...)` with `limit`, `offset`, `search`, `since`, `model`, `effort`, `thread`, `pricing_status`, or `credit_confidence`. Report `row_count`, `total_matched_rows`, and `has_more`.
- "Open/investigate this call" Use `usage_call_detail(record_id=...)` for the aggregate call investigator payload. Use `usage_call_context` only if the user explicitly asks for raw local context.
- "Show threads" Use `usage_threads(...)`, sorted by token impact by default.
- "Give me dashboard report evidence" Use `usage_report_pack(...)` for report cards and compact evidence rows. Use `usage_dashboard_recommendations(...)` when the user specifically wants the dashboard recommendation payload.
- "Is my dashboard/index stale?" Use `usage_status()` first, then `usage_doctor(response_format="json")` if status suggests missing rows, stale refresh, or setup problems.
- "Can I share this?" Use redacted or strict privacy mode and avoid `usage_call_context`.
- "Why did usage spike?" Use `usage_recommendations(response_format="json")` for ranked causes, then `usage_query` or `usage_calls` with focused filters for supporting rows.
- "What is unpriced or estimated?" Use `usage_pricing_coverage(response_format="json")` and `usage_query(pricing_status="unpriced")` or `usage_query(credit_confidence="estimated")`.
- "How does this affect my allowance?" Use rows from `usage_query` or `usage_calls` and summarize `usage_credits`, `usage_credit_confidence`, and allowance annotations. Explain that remaining allowance is only as accurate as the user's local allowance config.
- "What happened in this session?" Use `session_usage(session_id=..., response_format="json")`.
- "What should I inspect next?" Use `usage_report_pack(...)` or `usage_recommendations(response_format="json")`, then explain the primary recommendation, secondary signals, and row scope.

## Suggested Investigation Ideas

When the user asks what they can look into, offer a short menu of concrete aggregate-only investigations rather than a generic list.

- "Look through my usage for token waste." Use `usage_report_pack(...)`, then `usage_calls(sort="tokens", direction="desc", limit=10)` and call out high-token calls, low cache ratios, high context-window percent, expensive estimates, or repeated same-thread spikes.
- "Find calls where context got bloated." Use `usage_calls(...)` sorted by tokens or filtered to recent rows, then rank by `context_window_percent`, `input_tokens`, and low `cache_ratio`.
- "Show me where caching failed." Use `usage_calls(...)` and `usage_report_pack(...)`; prioritize rows with high `input_tokens`, low `cached_input_tokens`, or low `cache_ratio`.
- "Which threads are draining the most?" Use `usage_threads(limit=10)` and `usage_summary(group_by="thread", response_format="json")`; include total tokens, estimated cost or credits, and whether archived rows are excluded.
- "What changed recently?" Use `usage_status()` for freshness, then `usage_calls(since=..., limit=...)` or `usage_summary(group_by="date", response_format="json")` for recent movement.
- "Find expensive calls worth opening." Use `most_expensive_usage_calls(response_format="json")` or `usage_calls(sort="tokens", direction="desc")`; suggest `usage_call_detail(record_id=...)` for the top few aggregate records.
- "Check whether model or effort choice is wasting tokens." Use `usage_summary(group_by="model", response_format="json")`, `usage_summary(group_by="effort", response_format="json")`, and supporting `usage_calls(...)` rows.
- "Can I share this safely?" Use `privacy_mode="strict"` and avoid `usage_call_context`.

## Waste Reduction Recommendations

When user asks to look for token waste, treat answer as diagnosis plus remediation. After ranking aggregate drivers, recommend concrete next steps that can reduce future usage:

- Suggest Headroom when available for context/headroom estimation if evidence shows high context-window pressure, repeated large reads, or long-thread accumulation. Say "if available" unless tool registry confirms it.
- Suggest dashboard verification steps: open top rows in Calls, inspect selected records in Call Investigator, compare Threads by total tokens, or use Diagnostics Notebook for usage-drain evidence.
- Suggest custom solutions Codex can build when pattern repeatable: repo-specific test selector, local summary command, prompt checklist, dashboard report preset, or small script extracting exact project facts Codex keeps rediscovering.
- Suggest workflow changes only when aggregate evidence supports them: split bloated threads, lower reasoning effort for routine edits, reuse one thread for cache-friendly related work, or start fresh thread after compacting needed state into docs.

Structure recommendations as `Evidence`, `Likely waste pattern`, `Next action`, and `How to verify`. Keep privacy boundary explicit and avoid raw context unless user asks.

## Answer Style

- Lead with the direct answer and key metric.
- Use at most one short progress update such as "Refreshing aggregate usage, then ranking threads."
- Name data scope, time window, project, thread, model, row count, and whether rows are truncated or paginated.
- Separate exact facts from estimates. Call out `pricing_estimated`, missing `pricing_model`, `usage_credit_confidence`, and missing allowance windows.
- Include the next useful investigation when the answer depends on unclear pricing, stale allowance values, or a broad time window.
- Keep explanations tied to aggregate fields. Do not guess conversation content.

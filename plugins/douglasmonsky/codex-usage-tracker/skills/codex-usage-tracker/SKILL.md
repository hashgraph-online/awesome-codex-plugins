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

## Suggested Usage Questions

When the user wants ideas, suggest concrete aggregate investigations:

- Look through my usage for token waste.
- Find calls where context got bloated.
- Show me where caching failed.
- Which threads are draining the most?
- What changed recently?
- Check whether weekly allowance behavior changed.
- Explain why the 5-hour counter looks noisy.
- Build strict-privacy allowance evidence I can share.
- Find expensive calls worth opening in the investigator.
- Check whether model or effort choice is wasting tokens.
- Build a strict-privacy summary I can share.

Route these through `usage_report_pack`, `usage_calls`, `usage_threads`, `usage_summary`, and `usage_call_detail` before considering raw context.

## Remediation Recommendations

When a usage-waste investigation finds clear patterns, do not stop at "interesting." Recommend practical next actions and existing tools that could reduce future usage. Keep recommendations tied to aggregate evidence, and label speculative ideas.

- If context pressure is high, threads are long, or repeated file reads dominate, suggest Headroom if available as a follow-up tool for estimating context/headroom and deciding whether to split the thread, summarize, or start a fresh task.
- If cache ratio is low on repeated work, suggest concrete workflow fixes: keep related work in one thread, avoid unnecessary broad file reads, pin reusable project context in docs, or create a small project command/script that produces the exact aggregate needed.
- If one thread or subagent pattern dominates, suggest narrowing the task, splitting investigation from implementation, or creating a repeatable custom checklist/command so Codex does not rediscover the same facts every turn.
- If effort/model choice looks expensive, compare aggregate results by model and effort before recommending lower effort, smaller models, or explicit "use minimal reasoning unless blocked" instructions.
- If diagnostics point to missing local automation, offer to design a custom lightweight solution: a repo command, lint/test selector, dashboard report preset, support-bundle check, or Codex skill update that prevents the same waste pattern.
- Mention dashboard actions that help the user verify the fix: open Calls filtered to the expensive rows, Threads sorted by tokens, Call Investigator for a selected record, or Diagnostics Notebook for usage-drain evidence.

Phrase the final answer as "what happened, why it likely matters, what to try next, how to verify." Avoid implying an external tool is installed unless the current environment or tool registry confirms it.

## Common Workflows

- Refresh the index before answering usage questions.
- Use `usage_doctor` when setup, plugin discovery, MCP launch, dashboard output, or pricing estimates look wrong.
- Use `usage_summary` for high-level totals by date, model, effort, cwd, thread, or session.
- Use `usage_query` for stable JSON rows filtered by date, project, model, effort, thread, pricing status, token minimums, or Codex credit minimums.
- Use `usage_status` for dashboard/index freshness, active/scoped/total row counts, latest refresh timestamp, and observed allowance windows.
- Use `usage_allowance_history` normalized observed allowance snapshots when user needs rows behind weekly or 5-hour movement.
- Use `usage_allowance_diagnostics` for evidence-graded allowance-change questions; weekly is primary, five-hour is noisy rolling-window context.
- Use `usage_allowance_export` for strict-privacy local allowance evidence bundles intended for manual sharing.
- Use `usage_calls` for the same aggregate Calls table rows as the React dashboard, including pagination, filters, derived pricing status, and credit confidence.
- Use `usage_call_detail` for the aggregate Call Investigator payload for one `record_id`. Use `usage_call_context` only for explicit raw-context requests.
- Use `usage_threads` for the same aggregate Threads table rows as the dashboard.
- Use `usage_report_pack` for dashboard report cards plus compact evidence rows when the user wants less cloudy "what should I inspect?" output.
- Use `usage_dashboard_recommendations` when the dashboard-specific recommendation payload is more useful than the older markdown-oriented recommendation report.
- Use `usage_recommendations` when the user asks what to inspect next or wants ranked action items by aggregate severity.
- Use `usage_summary` presets `today`, `last-7-days`, `by-model`, `by-cwd`, `by-thread`, and `expensive` for common requests.
- Use `usage_pricing_coverage` when the user asks whether costs are fully priced or which models use estimated or missing pricing.
- Use `usage_source_coverage` when the user asks whether parser/source provenance coverage is healthy or whether the local index is ready for deeper investigation.
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
- Use allowance diagnostics for questions about limit drops, weekly allowance changes, 5-hour counter weirdness, or throttling. Prefer weekly evidence, read the `nonparametric-v1` statistical evidence fields, and explain `research_readiness.ready_for_public_claim` separately from local evidence grades.

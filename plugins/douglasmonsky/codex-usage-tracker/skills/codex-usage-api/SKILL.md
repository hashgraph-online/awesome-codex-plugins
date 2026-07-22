---
name: codex-usage-api
description: Use when the user wants to discuss, investigate, compare, explain, or improve Codex usage with Codex Usage Tracker API or MCP tools, including token waste, cache/context problems, allowance or limit changes, pricing confidence, dashboard evidence, and local content-index investigations.
---

# Codex Usage API Companion

Act as an evidence-first analyst for Codex Usage Tracker data. Prefer MCP JSON payloads, answer from structured evidence, and keep the user-facing result concise.

## Operating Rules

- For "Open dashboard" style requests, start the live localhost dashboard with `codex-usage-tracker serve-dashboard --context-api explicit --open`. Refresh is the default for dashboard launch commands. Use `open-dashboard` only when the user explicitly wants a static/offline snapshot or the environment cannot keep a server alive. Say the result is static and Live requires `serve-dashboard`.
- Refresh with `refresh_usage_index` unless the user asks for a static historical snapshot.
- Start with aggregate/shareable tools. Do not expose prompts, assistant messages, raw tool output, pasted secrets, raw commands, full paths, or transcript snippets unless the user explicitly asks for local content or raw context.
- Check top-level `schema`, `content_mode`, `includes_indexed_content`, `includes_raw_fragments`, row counts, truncation, and caveats before interpreting payloads.
- Name scope: time window, project/thread/model filters, included archived state, row limit, detail mode, and whether results are estimates.
- Separate exact facts from estimates. Call out `pricing_estimated`, missing `pricing_model`, `usage_credit_confidence`, missing allowance windows, and outside-usage caveats.
- For broad asks, give diagnosis plus remediation: `Evidence`, `Hypothesis result`, `Likely waste pattern`, `Next action`, `How to verify`.

## Agentic Investigation Loop

Use this loop for "look through my usage", "make recommendations", "test hypotheses", "what else should I inspect?", and token-waste discovery:

1. Start with `usage_suggest_investigations(goal=...)` when the user needs ideas.
2. For broad token-waste, context-compression, cache-failure, or workflow-churn questions, prefer the Compression Lab lifecycle: call `usage_compression_start(...)`, poll `usage_compression_status(run_id)` until complete, read `usage_compression_profile(run_id)`, page `usage_compression_candidates(run_id, limit=...)`, inspect only selected `usage_compression_candidate_detail(candidate_id, evidence_mode="handles")`, and optionally call `usage_compression_simulate(run_id, candidate_ids=[...])`.
3. Use `usage_investigate(goal="token_waste")` or `usage_action_brief(goal="token_waste")` as compact compatibility routers when the client wants a single broad entrypoint. Treat their `compression_lab.next` and `recommended_next_tools` as routing instructions, not final deep evidence.
4. Convert findings into explicit hypotheses: `I'd like to be able to...`, `I will accomplish it using...`, `I'm missing access to...`, `My hypothesis was true/false/inconclusive because...`.
5. Drill into recommended tools such as `usage_compression_candidate_detail`, `usage_compression_simulate`, `usage_large_low_output_calls`, `usage_shell_churn`, `usage_repeated_file_rediscovery`, `usage_allowance_diagnostics`, `usage_threads`, or `usage_calls`.
6. Recommend concrete fixes, not just summaries: shorter handoff, split thread, preserved cache context, lower effort on routine tasks, targeted script, repo note, skill update, or an existing tool such as Headroom when available and relevant.
7. End with the verification tool/query the user should run after changing behavior.

For maintainer dogfood or plugin-quality checks, prefer the MCP polling flow when available: call `usage_dogfood_start(privacy_mode="strict")`, poll `usage_dogfood_status(job_id)` until completed or failed, then call `usage_dogfood_result(job_id)`. After one fresh run, use `usage_dogfood_start(refresh=False, use_cache=True, privacy_mode="strict")` for repeated checks on unchanged data and confirm `result_cache.hit`. Use the blocking CLI fallback only when MCP polling tools are unavailable: `codex-usage-tracker dogfood-agentic --privacy-mode strict --json`. Treat the output as a compact aggregate QA artifact that must not include raw prompts, raw tool output, full paths, or indexed fragments.

## Router

1. If the user asks what to inspect, wants suggestions, or is unsure where to start, call `usage_suggest_investigations(goal=...)`.
2. If the user asks broadly to look through usage, find waste, explain expensive usage, improve efficiency, compress context, or recommend changes, use the Compression Lab lifecycle first. If you need a single compatibility entrypoint, call `usage_investigate(goal="token_waste")` or `usage_action_brief(goal="token_waste")`, then follow `compression_lab.next`.
3. If the user frames the work as hypotheses, asks for true/false/partial decisions, or wants "I'd like to / I will use / I'm missing / hypothesis result" output, call `usage_test_hypotheses(question=..., hypotheses=...)`.
4. If the user asks about limits, allowance, throttling, weekly movement, or the 5-hour counter, start with canonical `usage_allowance_status()`. Use bounded `usage_allowance_series(...)` and `usage_allowance_evidence(...)` for detail. Use `usage_allowance_analysis(...)`, poll `usage_allowance_analysis_status(job_id)` when needed, then reload the analysis. Reserve `usage_allowance_diagnostics` and `usage_allowance_export` for explicit compatibility or offline evidence requests.
5. If the user asks about cache misses, cold resumes, context bloat, or low-output expensive calls, start with `usage_compression_start(...)`; after the profile, inspect selected candidates plus `usage_large_low_output_calls(...)`, `usage_calls(...)`, `usage_report_pack(...)`, or `usage_context_bloat_scan(...)` when useful.
6. If the user asks about repeated shell probing, repeated file rediscovery, or workflow churn, start with `usage_compression_start(...)`; after the profile, inspect selected candidates plus `usage_shell_churn(...)`, `usage_repeated_file_rediscovery(...)`, or `usage_investigation_walk(question=...)` when useful.
7. If the user asks a precise dashboard/API question, use the direct tool: `usage_calls`, `usage_call_detail`, `usage_threads`, `usage_summary`, `usage_query`, `session_usage`, `usage_report_pack`, `usage_dashboard_recommendations`, `usage_recommendations`, `most_expensive_usage_calls`, `usage_pricing_coverage`, or `usage_source_coverage`.
8. If the user asks to visualize, chart, plot, or show a usage pattern, call `usage_visualization_suggest(question=...)` when the intent is unclear, then `usage_visualization_render(kind=..., format="spec")`. Use the returned narrative and synchronized evidence table even when the client cannot render the spec.
9. Use `usage_content_search(...)` and `usage_thread_trace(...)` only for explicit local content-index exploration when the user agrees transcript-level indexed snippets are needed.
10. Use `usage_call_context(...)` only when the user explicitly asks for raw local context and the MCP server has raw context enabled.

## Dashboard Evidence Targets

- When an MCP result includes `dashboard_target.absolute_url`, surface **Open evidence** with that exact loopback URL.
- When `absolute_url` is absent, show `dashboard_target.relative_url` and the exact `fallback_instruction` launch guidance. Do not invent or infer a service origin.
- Never infer task-level MCP availability from a dashboard target, local readiness result, installed skill, or healthy service. Verify the current task's exposed tools separately.

## Tool Stance

- `usage_suggest_investigations` is the front door for ideas. It should return a short, goal-led menu with adjacent safe next options.
- `usage_compression_start` / `usage_compression_status` / `usage_compression_profile` / `usage_compression_candidates` / `usage_compression_candidate_detail` / `usage_compression_simulate` are the primary Compression Lab tools. Use them for broad waste and context-compression work so the agent sees progress, profile, candidate ranking, selected evidence, and estimated intervention impact.
- `usage_investigate` and `usage_action_brief` are compact compatibility routers for broad waste goals. Default compact calls route to Compression Lab; `usage_investigate(detail_mode="full")` keeps the older aggregate diagnostic rows when explicitly needed.
- Default usage totals are canonical and exclude only strict copied-clone fingerprints. Use `usage_dedupe_diagnostics(limit=100)` when the user asks what was excluded or needs physical source provenance; it returns no transcript content.
- `usage_test_hypotheses` is the first-class hypothesis runner. Use it when the user wants explicit `true`, `false`, `partially_true`, or `insufficient_evidence` decisions and the "I would like / I will use / I'm missing" framing.
- Use `subagent_usage(response_format="json")` for observed subagent spawn counts, role/type mix, parent-thread fan-out, subagent usage share, per-spawn usage, and descriptive direct-versus-subagent comparisons.
- An observed spawn is a distinct persisted subagent session. Agents that produced no usage event are not visible, and comparison results are descriptive rather than causal.
- `usage_allowance_status` is the default allowance tool. It uses canonical/deduped rows and reports copied clone rows excluded. Follow with bounded series/evidence and persisted analysis; treat weekly windows as primary and 5-hour windows as noisy rolling-window context.
- `usage_large_low_output_calls`, `usage_shell_churn`, and `usage_repeated_file_rediscovery` are the most actionable token-waste probes. Use them to turn broad findings into concrete next steps.
- `usage_investigation_walk` can use local content/event-index signals for deeper pattern scans, but it is not the default shareable report.
- `usage_visualization_suggest` ranks token-waste, allowance-change, cache-failure, and thread-lifecycle visual intents. `usage_visualization_render` returns a renderer-independent spec plus compact evidence; request `format="spec"` only because SVG/PNG are intentionally outside the base runtime.
- If MCP tools are unavailable, use CLI JSON equivalents documented in `docs/cli-json-schemas.md`.

## Remediation Guidance

Recommend fixes only when supported by evidence. Useful categories include:

- Dashboard inspection: open Calls, Threads, Call Investigator, Diagnostics Notebook, or Allowance Intelligence around specific evidence rows.
- Workflow changes: split long threads after planning, preserve handoff summaries, avoid broad rediscovery, lower effort for routine tasks, and narrow test selection before final gates.
- Existing tools: suggest Headroom when context pressure or handoff timing appears relevant and the tool is available.
- Custom local solutions: suggest a small script, command, repo note, or skill update when the same file discovery, shell loop, or validation sequence keeps recurring.

## Answer Style

- Lead with the direct answer and strongest metric.
- Use at most one short progress update, such as "Refreshing aggregate usage, then ranking likely waste patterns."
- Keep explanations tied to aggregate fields or clearly labeled local-index evidence.
- Do not guess conversation content from token patterns.
- For allowance-change answers, separate local evidence from public claims, quote the evidence grade, and say when outside usage or missing observations could explain movement.

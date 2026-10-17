---
name: aient
description: Use when the user asks Codex to inspect Aient telemetry, search logs, explain traces, create/list Aient API keys, or use the Aient MCP server.
license: Proprietary
---

# Aient

Use this skill when a user asks for Aient operational context from Codex. The
plugin exposes the production Aient MCP server at `https://aient.ai/mcp`.
The MCP server is the source of truth for tool schemas; discover/use the live
tools rather than relying on a memorized subset.

## First Call

Start with `verify_connection` when checking whether the plugin is available.
It confirms the organisation, granted scopes, token expiry, and live tool count.

## MCP Tool Surface

Prefer the current granular tools over the retired early-preview names
`telemetry_overview`, `log_search`, and `trace_timeline`.

Connection and discovery:
- `verify_connection`: confirm auth and available MCP tools.
- `describe_telemetry`: discover services, operations, and attributes.
- `service_health_summary`: get an at-a-glance service health overview.

Telemetry:
- `query_traces`: aggregate trace metrics such as count, error rate, and latency.
- `query_logs`: aggregate log metrics by service, severity, or time.
- `get_spans`: fetch raw spans for a trace or filtered operation set.
- `get_logs`: fetch raw log entries and attributes.
- `detect_anomalies`: detect statistical deviations in trace/log metrics.

Problems and lifecycle:
- `list_problems`: list detected problems with status, severity, priority, and
  environment filters.
- `get_problem`: inspect a problem, recent occurrences, and triage context.
- `acknowledge_problem`, `mute_problem`, `unmute_problem`,
  `dismiss_problem`, `resolve_problem`, `restore_problem_status`,
  `update_problem_priority`, and `batch_problem_action`: apply lifecycle
  actions to one or more problems.

Remediation:
- `request_fix`: spawn an AI remediation agent for a problem.
- `get_problem_fix`: inspect a remediation attempt.
- `list_problem_fixes`: list remediation attempts for a problem.
- `list_active_fixes`: list in-progress remediation work across the
  organisation.

Threads:
- `get_thread`: inspect a thread journal and current agent activity.
- `send_thread_message`: send a message to a thread's agent.
- `respond_to_interaction`: answer an agent interaction/awakeable.

Environment and key management:
- `list_environments`: inspect deployment environments.
- `list_environment_keys`, `create_environment_key`, `revoke_environment_key`:
  manage publishable telemetry ingest keys.
- `list_api_keys`, `create_api_key`: manage secret API keys for sourcemaps or
  complete API access. `create_api_key` returns the full key exactly once.

## Operating Rules

- Prefer the MCP tools for live Aient telemetry and key-management tasks.
- Do not use local development MCP endpoints unless the user explicitly asks for
  a local/dev environment.
- Never copy secrets or local credentialed MCP configuration into responses,
  plans, or plugin files.
- Read-only tools require `aient.mcp.read`; mutating tools require
  `aient.mcp.write`.
- For `create_api_key`, tell the user that the returned key is shown once and
  should be stored immediately.
- For telemetry queries, prefer `environmentSlug` over `environmentId` when the
  user names an environment, and never pass the all-zero UUID placeholder.
- Treat `401` as missing or expired OAuth, `403` as insufficient scope, and a
  missing organisation claim as an auth-context issue.

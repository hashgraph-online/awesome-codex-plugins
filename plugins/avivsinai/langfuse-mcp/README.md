# Langfuse MCP Server

[![PyPI](https://badge.fury.io/py/langfuse-mcp.svg)](https://badge.fury.io/py/langfuse-mcp)
[![Downloads](https://static.pepy.tech/badge/langfuse-mcp)](https://pepy.tech/projects/langfuse-mcp)
[![Python 3.10–3.14](https://img.shields.io/badge/python-3.10–3.14-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Agent-facing [Model Context Protocol](https://modelcontextprotocol.io) server and skill for [Langfuse](https://langfuse.com) observability.

Use `langfuse-mcp` from Claude Code, Codex, Cursor, or any MCP client to query traces, inspect generations, debug exceptions, analyze sessions, manage prompts, browse datasets, and understand what your AI agents did in production.

## What You Can Do

- Debug failing agent runs from Langfuse traces and observations.
- Find exceptions, slow generations, high-latency spans, and affected users.
- Inspect sessions and user journeys without leaving your agent workflow.
- Manage prompt versions, labels, datasets, annotation queues, and scores.
- Install the included [`langfuse` agent skill](skills/langfuse/SKILL.md) for ready-made debugging playbooks.

## Project Links

- [Quick Start](#quick-start)
- [Agent Skill](#agent-skill)
- [Tools](#tools-48-total)
- [Selective Tool Loading](#selective-tool-loading)
- [Read-Only Mode](#read-only-mode)
- [Other Clients](#other-clients)

## Why langfuse-mcp?

Langfuse is where your traces live. `langfuse-mcp` makes that telemetry directly usable by agents that need to answer questions like "what failed?", "why was this slow?", "which prompt version ran?", or "what happened in this user's session?"

Positioning relative to the [native Langfuse MCP](https://langfuse.com/docs/api-and-data-platform/features/mcp-server) (as of June 2026):

| | langfuse-mcp | Native Langfuse MCP |
|-|--------------|---------------------|
| **Primary fit** | Local, debugging-first MCP server + agent skill | Hosted, zero-install endpoint backed by Langfuse |
| **Deployment** | Local `stdio` or HTTP, via the Langfuse Python SDK | Native streamable HTTP at `/api/public/mcp` |
| **Trace / session / exception tools** | First-class | Observation/API-oriented access |
| **Route-decision tools** | Yes | No |
| **Token & output control** | Compact summaries, truncation, file-dump mode, tool-group gating | Depends on the hosted tool response + client |
| **Metrics & dataset runs** | Yes | Yes |
| **Prompt, dataset, queue & score reads** | Yes | Yes |
| **Score writes, comments, models, media** | Not yet | Yes |

This project does not mirror every native Langfuse MCP tool. It focuses on agent debugging ergonomics — compact trace inspection, exception triage, session analysis, routing-decision workflows, local tool-group gating, and an included skill with ready-made investigation playbooks. Use the native MCP for the broad hosted API surface; use `langfuse-mcp` as a local, token-disciplined layer.

## Quick Start

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) (for `uvx`) and Python 3.10 or newer. CI verifies Python 3.10 through 3.14.

Get credentials from [Langfuse Cloud](https://cloud.langfuse.com) → Settings → API Keys. If self-hosted, use your instance URL for `LANGFUSE_HOST`.

```bash
# Claude Code (project-scoped, shared via .mcp.json)
claude mcp add \
  -e LANGFUSE_PUBLIC_KEY=pk-... \
  -e LANGFUSE_SECRET_KEY=sk-... \
  -e LANGFUSE_HOST=https://cloud.langfuse.com \
  --scope project \
  langfuse -- uvx langfuse-mcp

# Codex CLI (user-scoped, stored in ~/.codex/config.toml)
codex mcp add langfuse \
  --env LANGFUSE_PUBLIC_KEY=pk-... \
  --env LANGFUSE_SECRET_KEY=sk-... \
  --env LANGFUSE_HOST=https://cloud.langfuse.com \
  -- uvx langfuse-mcp
```

To pin a CI-verified interpreter explicitly, add `--python 3.14` before `langfuse-mcp`.

Restart your CLI, then verify with `/mcp` (Claude Code) or `codex mcp list` (Codex).

## Agent Skill

This repo ships a first-party [`langfuse` skill](skills/langfuse/SKILL.md) for Claude Code and Codex. The skill gives agents concrete playbooks for trace debugging, exception triage, latency analysis, prompt management, and dataset work.

Install it when you want the agent to know when to reach for Langfuse and which MCP tools to call first.

**Via [skills](https://github.com/vercel-labs/add-skill)** (recommended):
```bash
npx skills add avivsinai/langfuse-mcp -g -y
```

**Via [skild](https://skild.sh)**:
```bash
npx skild install @avivsinai/langfuse -t claude -y
```

**Manual install:**
```bash
cp -r skills/langfuse ~/.claude/skills/   # Claude Code
cp -r skills/langfuse ~/.codex/skills/    # Codex CLI
```

After installing the skill, try:

```text
help me debug langfuse traces
find exceptions in the last day
why was this user's session slow?
```

The MCP server provides the tools; the skill provides the agent-facing workflow. See [`skills/langfuse/SKILL.md`](skills/langfuse/SKILL.md), [`skills/langfuse/references/setup.md`](skills/langfuse/references/setup.md), and [`skills/langfuse/references/tool-reference.md`](skills/langfuse/references/tool-reference.md).

## Tools (48 total)

| Category | Tools |
|----------|-------|
| Traces | `fetch_traces`, `fetch_trace` |
| Observations | `fetch_observations`, `fetch_observation` |
| Routing | `find_route_decisions`, `get_route_decision`, `summarize_route_decisions`, `find_low_confidence_route_decisions` |
| Sessions | `fetch_sessions`, `get_session_details`, `get_user_sessions` |
| Exceptions | `find_exceptions`, `find_exceptions_in_file`, `get_exception_details`, `get_error_count` |
| Prompts | `list_prompts`, `get_prompt`, `get_prompt_unresolved`, `create_text_prompt`, `create_chat_prompt`, `update_prompt_labels` |
| Datasets | `list_datasets`, `get_dataset`, `list_dataset_items`, `get_dataset_item`, `create_dataset`, `create_dataset_item`, `delete_dataset_item`, `list_dataset_runs`, `get_dataset_run`, `list_dataset_run_items`, `create_dataset_run_item`, `delete_dataset_run` |
| Annotation Queues | `list_annotation_queues`, `create_annotation_queue`, `get_annotation_queue`, `list_annotation_queue_items`, `get_annotation_queue_item`, `create_annotation_queue_item`, `update_annotation_queue_item`, `delete_annotation_queue_item`, `create_annotation_queue_assignment`, `delete_annotation_queue_assignment` |
| Scores | `list_scores_v2`, `get_score_v2` |
| Metrics | `query_metrics`, `get_metrics_schema` |
| Schema | `get_data_schema` |

## Dataset Item Updates (Upsert)

Langfuse uses upsert for dataset items. To edit an existing item, call `create_dataset_item` with `item_id`. If the ID exists, it updates; otherwise it creates a new item.

```python
create_dataset_item(
  dataset_name="qa-test-cases",
  item_id="item_123",
  input={"question": "What is 2+2?"},
  expected_output={"answer": "4"}
)
```

## Metrics Queries

`query_metrics` aggregates telemetry server-side (cost, latency, tokens, counts, score values) so agents can answer "what did inference cost?" or "what's p95 latency by model?" without pulling raw traces. Call `get_metrics_schema` for the full view/dimension/measure catalog.

```python
query_metrics(
  view="observations",
  metrics=[{"measure": "totalCost", "aggregation": "sum"},
           {"measure": "latency", "aggregation": "p95"}],
  dimensions=["providedModelName"],
  age=1440,  # last 24h; or pass from_timestamp / to_timestamp
)
```

High-cardinality fields (`id`, `traceId`, `userId`, `sessionId`) must be used in `filters`, not `dimensions`. The v2 metrics endpoint is Langfuse Cloud-only; self-hosted instances may return 404.

## Selective Tool Loading

Load only the tool groups you need to reduce token overhead:

```bash
langfuse-mcp --tools traces,prompts
```

Available groups: `traces`, `observations`, `routing`, `sessions`, `exceptions`, `prompts`, `datasets`, `annotation_queues`, `scores`, `metrics`, `schema`

The `routing` group is router-neutral. It reads Langfuse span observations with
`metadata.schema_version: "mcp.route_decision.v1"` and filters on route-decision
fields stored in observation metadata, such as `decision_id`, `router_name`,
`provider`, and `capability_id`.

## Read-Only Mode

Disable all write operations for safer read-only access:

```bash
langfuse-mcp --read-only
# Or via environment variable
LANGFUSE_MCP_READ_ONLY=true langfuse-mcp
```

This disables: `create_text_prompt`, `create_chat_prompt`, `update_prompt_labels`, `create_dataset`, `create_dataset_item`, `delete_dataset_item`, `create_dataset_run_item`, `delete_dataset_run`, `create_annotation_queue`, `create_annotation_queue_item`, `update_annotation_queue_item`, `delete_annotation_queue_item`, `create_annotation_queue_assignment`, `delete_annotation_queue_assignment`

## Default Output Mode

Set the MCP-exposed default `output_mode` so clients that omit the parameter automatically use your preferred mode:

```bash
langfuse-mcp --default-output-mode full_json_file
# Or via environment variable
LANGFUSE_MCP_DEFAULT_OUTPUT_MODE=full_json_file langfuse-mcp
```

Supported values: `compact`, `full_json_string`, `full_json_file`

This updates the default shown in MCP tool schemas. Clients can still override it per call by passing `output_mode` explicitly.

## Other Clients

### Cursor

Create `.cursor/mcp.json` in your project (or `~/.cursor/mcp.json` for global):

```json
{
  "mcpServers": {
    "langfuse": {
      "command": "uvx",
      "args": ["langfuse-mcp"],
      "env": {
        "LANGFUSE_PUBLIC_KEY": "pk-...",
        "LANGFUSE_SECRET_KEY": "sk-...",
        "LANGFUSE_HOST": "https://cloud.langfuse.com",
        "LANGFUSE_MCP_DEFAULT_OUTPUT_MODE": "full_json_file"
      }
    }
  }
}
```

### Docker (single project)

```bash
docker run --rm -i \
  -e LANGFUSE_PUBLIC_KEY=pk-... \
  -e LANGFUSE_SECRET_KEY=sk-... \
  -e LANGFUSE_HOST=https://cloud.langfuse.com \
  ghcr.io/avivsinai/langfuse-mcp:latest
```

### HTTP transport — shared server for multiple projects

Run one persistent server instance and route each MCP client to its own Langfuse
project by passing credentials in the `Authorization` header.

```bash
# Start a shared server (binds to localhost by default)
docker run -d -p 127.0.0.1:8000:8000 \
  -e LANGFUSE_HOST=https://cloud.langfuse.com \
  ghcr.io/avivsinai/langfuse-mcp:latest \
  --transport streamable-http --bind-host 0.0.0.0
```

> **Security note:** `--bind-host 0.0.0.0` exposes the port on all interfaces. In
> production, place the server behind a TLS-terminating reverse proxy (nginx, Caddy,
> Cloudflare Tunnel) that enforces HTTPS. The `Authorization` header containing your
> keys is transmitted in plaintext over plain HTTP. If startup credentials are set,
> the proxy must enforce authentication; otherwise unauthenticated callers without an
> `Authorization` header can use the default project. For shared public HTTP deployments,
> omit default `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` credentials unless the
> fronting proxy authenticates every request.

Register each project separately in your MCP client, passing its credentials as a
`Basic` auth header (`base64(public_key:secret_key)`):

```bash
# Generate the header value for each project:
echo -n "pk-lf-YOURKEY:sk-lf-YOURSECRET" | base64
# cGstbGYtWU9VUktFWTpzay1sZi1ZT1VSU0VDUkVU

# Register in Claude Code (one entry per project):
claude mcp add langfuse-audit \
  --transport http http://localhost:8000/mcp \
  -H "Authorization: Basic cGstbGYtWU9VUktFWTpzay1sZi1ZT1VSU0VDUkVU"

claude mcp add langfuse-staging \
  --transport http http://localhost:8000/mcp \
  -H "Authorization: Basic <base64 for staging project>"
```

**Auth semantics:** `Basic` here carries Langfuse API keys, not user passwords. An
absent header falls back to startup env credentials (`LANGFUSE_PUBLIC_KEY` /
`LANGFUSE_SECRET_KEY`). Any malformed header is rejected outright — there is no
silent fallback to a different project.

### Optional environment variables

| Variable | Default | Description |
|---|---|---|
| `LANGFUSE_MAX_AGE_DAYS` | `7` | Caps the lookback window for time-based tools (`fetch_traces`, `fetch_observations`, etc.). Set to match your Langfuse instance's data retention — e.g. `30` if your retention is 30 days. |
| `LANGFUSE_MCP_TRACE_TIMEOUT_SECONDS` | `120` | Per-request read timeout (seconds) for single-trace fetches (`fetch_trace`). Raise it if large traces with `include_observations=True` time out. Must be a positive integer. |

## Development

```bash
uv venv --python 3.14 .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```

## License

MIT

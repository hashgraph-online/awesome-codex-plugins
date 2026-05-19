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
- [Tools](#tools-37-total)
- [Selective Tool Loading](#selective-tool-loading)
- [Read-Only Mode](#read-only-mode)
- [Other Clients](#other-clients)

## Why langfuse-mcp?

Langfuse is where your traces live. `langfuse-mcp` makes that telemetry directly usable by agents that need to answer questions like "what failed?", "why was this slow?", "which prompt version ran?", or "what happened in this user's session?"

Comparison with [official Langfuse MCP](https://github.com/langfuse/mcp-server-langfuse) (as of Jan 2026):

| | langfuse-mcp | Official |
|-|--------------|----------|
| **Traces & Observations** | Yes | No |
| **Sessions & Users** | Yes | No |
| **Exception Tracking** | Yes | No |
| **Prompt Management** | Yes | Yes |
| **Dataset Management** | Yes | No |
| **Annotation Queues** | Yes | No |
| **Scores (v2)** | Yes | No |
| **Selective Tool Loading** | Yes | No |

This project provides a **full observability toolkit** — traces, observations, sessions, exceptions, prompts, datasets, annotation queues, and scores — while the official MCP focuses on prompt management.

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

## Tools (37 total)

| Category | Tools |
|----------|-------|
| Traces | `fetch_traces`, `fetch_trace` |
| Observations | `fetch_observations`, `fetch_observation` |
| Sessions | `fetch_sessions`, `get_session_details`, `get_user_sessions` |
| Exceptions | `find_exceptions`, `find_exceptions_in_file`, `get_exception_details`, `get_error_count` |
| Prompts | `list_prompts`, `get_prompt`, `get_prompt_unresolved`, `create_text_prompt`, `create_chat_prompt`, `update_prompt_labels` |
| Datasets | `list_datasets`, `get_dataset`, `list_dataset_items`, `get_dataset_item`, `create_dataset`, `create_dataset_item`, `delete_dataset_item` |
| Annotation Queues | `list_annotation_queues`, `create_annotation_queue`, `get_annotation_queue`, `list_annotation_queue_items`, `get_annotation_queue_item`, `create_annotation_queue_item`, `update_annotation_queue_item`, `delete_annotation_queue_item`, `create_annotation_queue_assignment`, `delete_annotation_queue_assignment` |
| Scores | `list_scores_v2`, `get_score_v2` |
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

## Selective Tool Loading

Load only the tool groups you need to reduce token overhead:

```bash
langfuse-mcp --tools traces,prompts
```

Available groups: `traces`, `observations`, `sessions`, `exceptions`, `prompts`, `datasets`, `annotation_queues`, `scores`, `schema`

## Read-Only Mode

Disable all write operations for safer read-only access:

```bash
langfuse-mcp --read-only
# Or via environment variable
LANGFUSE_MCP_READ_ONLY=true langfuse-mcp
```

This disables: `create_text_prompt`, `create_chat_prompt`, `update_prompt_labels`, `create_dataset`, `create_dataset_item`, `delete_dataset_item`, `create_annotation_queue`, `create_annotation_queue_item`, `update_annotation_queue_item`, `delete_annotation_queue_item`, `create_annotation_queue_assignment`, `delete_annotation_queue_assignment`

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

### Docker

```bash
docker run --rm -i \
  -e LANGFUSE_PUBLIC_KEY=pk-... \
  -e LANGFUSE_SECRET_KEY=sk-... \
  -e LANGFUSE_HOST=https://cloud.langfuse.com \
  ghcr.io/avivsinai/langfuse-mcp:latest
```

### Optional environment variables

| Variable | Default | Description |
|---|---|---|
| `LANGFUSE_MAX_AGE_DAYS` | `7` | Caps the lookback window for time-based tools (`fetch_traces`, `fetch_observations`, etc.). Set to match your Langfuse instance's data retention — e.g. `30` if your retention is 30 days. |

## Development

```bash
uv venv --python 3.14 .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```

## License

MIT

# Codex Usage Tracker

[![PyPI](https://img.shields.io/pypi/v/codex-usage-tracking)](https://pypi.org/project/codex-usage-tracking/)
[![Python](https://img.shields.io/pypi/pyversions/codex-usage-tracking)](https://pypi.org/project/codex-usage-tracking/)
[![CI](https://github.com/douglasmonsky/codex-usage-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/douglasmonsky/codex-usage-tracker/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/douglasmonsky/codex-usage-tracker)](LICENSE)

Codex Usage Tracker is a local usage-data product for answering questions about
how Codex work consumes tokens, time, tools, allowance, credits, and cost. It
turns local session metadata into exact, bounded facts and stable evidence that
an agent can explore and explain.

## Current release and next direction

Version 0.28.0 is the current public release. Its six-tool MCP surface,
Evidence Console, and SQLite kernel remain supported while the replacement is
qualified.

The next product is a clean, agent-first kernel rather than a larger dashboard:

- fast recent-history setup with explicit 24-hour through all-time coverage;
- incremental reuse on every later invocation;
- exact session, turn, call, tool, resource, allowance, token, credit, and cost
  facts;
- compact named queries and stable evidence selectors;
- agent-owned interpretation instead of server-authored narrative findings;
- installed Codex qualification measured for latency, MCP calls, response
  bytes, model tokens, accuracy, and usefulness.

The 0.28 code remains a frozen oracle during the rewrite and is removed before
the clean replacement release. The new runtime does not migrate or open its
database.

Start with the [documentation authority](docs/INDEX.md), read the
[product direction](docs/decisions/PRODUCT_DIRECTION.md), or follow the
[clean-cutover roadmap](docs/roadmap/AGENT_FIRST_CLEAN_CUTOVER.md). Progress is
tracked in the [checkbox ledger](docs/roadmap/TASK_PACKETS.md), with one
complete contract per file under [`docs/roadmap/tasks/`](docs/roadmap/tasks/).

## Install 0.28.0

Install the Python runtime into an isolated executable environment, then add
the matching tagged repository as a Codex plugin marketplace:

```bash
pipx install "codex-usage-tracking==0.28.0"
codex plugin marketplace add douglasmonsky/codex-usage-tracker --ref v0.28.0
codex plugin add codex-usage-tracker@codex-usage-tracker
```

The plugin launches the `codex-usage-tracker` executable from the pipx
environment. Start a fresh Codex task after installation so it discovers the
new plugin tool catalog.

## Develop

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
just v
```

Use synthetic fixtures only. Do not commit or share real Codex logs, prompts,
responses, tool-output bodies, credentials, private paths, or local databases.

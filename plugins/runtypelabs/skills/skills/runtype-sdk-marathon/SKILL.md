---
name: runtype-sdk-marathon
description: >-
  Use when working with the Runtype TypeScript or Python SDK, FlowBuilder, BatchBuilder,
  EvalBuilder, CLI commands, Marathon long-running agent tasks, playbooks, model fallback,
  built-in CLI tools, sandboxes, code-first stored/upsert/virtual agents or flows, local
  tools, hidden parameters, or source-controlled Runtype workflows.
user-invocable: true
argument-hint: '[SDK, CLI, or Marathon task]'
---

# Runtype SDK And Marathon

Use this skill for code-first Runtype workflows, the CLI, and Marathon. Use
`runtype-build-product` when the user is designing hosted product resources through MCP.

## SDK Guidance

Fetch live docs when available:

- `get_platform_documentation(topic="sdk-reference")`
- `get_platform_documentation(topic="types-flow-steps")`
- `get_platform_documentation(topic="types-entities")`
- `get_platform_documentation(topic="flow-step-types")`

Code-first modes:

- Stored: create persistent agents/flows in Runtype.
- Upsert on execute: code is the source of truth and overwrites the Runtype copy when run.
- Virtual: definition is sent over the wire and not persisted.

Default to stored or upsert for production workflows because dashboard inspection, logs,
evals, and versioning are easier. Use virtual for tests, one-offs, privacy constraints,
or temporary generated flows.

Use local tools when execution must happen in the user's browser or server. Use hidden
parameters when auth context, tenant ids, or sensitive request data must not appear in the
model-visible tool schema.

## CLI Setup

Install or run directly:

```bash
npm install -g @runtypelabs/cli
npx @runtypelabs/cli@latest <command>
```

Authenticate:

```bash
runtype auth login
runtype auth whoami
```

Export a key for stdio MCP or CI only when needed:

```bash
export RUNTYPE_API_KEY=$(runtype auth export-key)
```

Common commands include `runtype agents list`, `runtype dispatch`, `runtype flows create`,
`runtype records create`, `runtype schedules`, `runtype models`, `runtype batch`,
`runtype eval`, `runtype persona`, `runtype products init`, and
`runtype validate-product`.

For command flags not listed here, run `runtype --help` or
`runtype marathon --help` instead of expanding this skill with CLI reference text.

## Marathon

Marathon is the CLI harness for long-running research, code editing, and build tasks. It
streams progress, can run multiple sessions, manages continuation context, supports
playbooks, and can use sandboxes.

Examples:

```bash
runtype marathon researcher \
  --goal "Research recent AI announcements and summarize them" \
  --tools firecrawl \
  --max-sessions 2

runtype marathon "Code Editor" \
  --goal "Refactor the auth module and run tests"

runtype marathon calculator \
  --goal "Build a calculator in 3D and deploy it publicly" \
  --sandbox daytona
```

Built-in CLI tools exposed by `--tools` include `exa`, `firecrawl`, and `dalle`. The CLI
validates requested tool ids and model compatibility at startup.

## Playbooks

Playbooks live in `.runtype/marathons/playbooks/` in the current repo or the user's home
directory. Use them for repeatable workflows with milestones, models, fallback models,
completion criteria, and rules.

Use playbooks when the task has durable phases such as research, build, verify, and
polish. Keep rules explicit about file scope, verification, and deployment expectations.

If the umbrella `runtype` skill is installed alongside this focused skill, its durable
references provide deeper working-mode guidance. This skill must still work when
installed by itself; prefer live MCP docs over local sibling files.

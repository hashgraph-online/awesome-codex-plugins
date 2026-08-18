# HOL Guard Plugin

[![HOL Guard](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fguard%2Fhashgraph-online%2Fhol-guard-plugin&style=flat-square)](https://hol.org/guard)
[![skills.sh](https://skills.sh/b/hashgraph-online/hol-guard-plugin)](https://skills.sh/hashgraph-online/hol-guard-plugin)

Codex and DeepSeek Harness plugin for HOL Guard, the local AI security layer from [`hol-guard`](https://github.com/hashgraph-online/hol-guard).

HOL Guard protects local AI harnesses before tools run. It can inspect Codex, Claude Code, Copilot CLI, Cursor, DeepSeek Harness, Gemini, Hermes, OpenClaw, OpenCode, and Antigravity surfaces, then route risky changes through local approvals and receipts.

## Install in DeepSeek Harness

Install HOL Guard first:

```bash
pipx install hol-guard
hol-guard status
```

Add the plugin to each DSH profile you use:

```bash
dsh plugin --profile headless add github:hashgraph-online/hol-guard-plugin
dsh plugin --profile web add github:hashgraph-online/hol-guard-plugin
```

Verify that the composed profile contains `hol-guard-plugin`:

```bash
dsh --profile headless --dump-config
```

You can also let HOL Guard install its managed local copy into detected DSH profiles:

```bash
hol-guard install dsh
```

The plugin registers a native `tools/pre-execute` gate. Every DSH tool call is sent to `hol-guard guard hook --harness dsh` before dispatch. A missing Guard command, timeout, malformed response, policy review, or explicit denial fails closed and prevents the tool from running.

## Install the security skill

Install the portable `plugin-scanner` skill with the open Skills CLI:

```bash
npx skills add hashgraph-online/hol-guard-plugin --skill plugin-scanner
```

The Skills CLI supports many coding agents. The skill asks before installing the `hol-guard` package and never executes code from a repository just to scan it.

## What this plugin adds

- A native DSH bundle with a fail-closed pre-tool security gate.
- A public Codex skill at [`skills/hol-guard/SKILL.md`](skills/hol-guard/SKILL.md).
- A portable security skill at [`skills/plugin-scanner/SKILL.md`](skills/plugin-scanner/SKILL.md).
- Guard setup guidance for Codex, Claude Code, Copilot CLI, Cursor, DeepSeek Harness, Gemini, Hermes, OpenClaw, OpenCode, and Antigravity.
- Scanner guidance for Codex plugins, Claude Code project surfaces, skills, MCP servers, and marketplace packages.
- Helper script for common `hol-guard` and `plugin-scanner` workflows.
- Validation for the Codex manifest, DSH bundle, skill assets, script paths, and `.mcp.json`.

## MCP server

This plugin includes a `.mcp.json` that registers the HOL Guard local MCP server (`guard-mcp.v1`). The server runs directly via the `hol-guard` binary, with no package-manager startup or shell wrapper.

### Prerequisites

- `hol-guard` CLI installed and on PATH (minimum version: 2.0.1024)
- Python >= 3.10

### Tools

| Tool | Input | Returns |
| :--- | :--- | :--- |
| `search` | `{query: string}` | Max 20 sanitized results from local receipts and inventory |
| `fetch` | `{id: string}` | Single receipt or inventory item, max 32 KiB sanitized text |
| `get_guard_status` | `{}` | CLI availability, receipt count, inventory count |

All tools return a `guard-mcp.v1` contract envelope with `contractVersion`, `source: local`, `generatedAt`, and `freshness: real-time`.

### Local vs Cloud

- **Local** (`hol-guard mcp serve --stdio`): reads local Guard data offline. No network access required.
- **Cloud** (`/api/guard/mcp` on the portal): reads synced workspace data. Requires OAuth Bearer token with `guard:workspace.read` and `guard:receipt.read` scopes.

### Setup

```bash
pipx install hol-guard
hol-guard status
```

The `.mcp.json` is automatically discovered by MCP-compatible clients. No additional configuration is needed.

## Install HOL Guard locally

Recommended:

```bash
pipx install hol-guard
```

Fallback:

```bash
python3 -m pip install --user hol-guard
```

Verify:

```bash
hol-guard status
hol-guard detect --json
```

## Use from Codex

Install this plugin in Codex, then ask:

```text
Use HOL Guard to protect this workspace before running agent tools.
```

or:

```text
Use HOL Guard to scan this plugin before release.
```

## Local helper

```bash
bash scripts/hol-guard-plugin status
bash scripts/hol-guard-plugin harnesses
bash scripts/hol-guard-plugin protect claude-code
bash scripts/hol-guard-plugin protect codex
bash scripts/hol-guard-plugin protect dsh
bash scripts/hol-guard-plugin scan-system claude .
bash scripts/hol-guard-plugin scan-system codex .
bash scripts/hol-guard-plugin scan .
bash scripts/hol-guard-plugin evidence
```

The helper does not read `.env` files. It only calls `hol-guard` and `plugin-scanner` commands already exposed by the upstream package.

## Supported harness systems

| System | Helper command | Guard command |
| :--- | :--- | :--- |
| Codex | `bash scripts/hol-guard-plugin protect codex` | `hol-guard install codex` |
| Claude Code | `bash scripts/hol-guard-plugin protect claude-code` | `hol-guard install claude-code` |
| Copilot CLI | `bash scripts/hol-guard-plugin protect copilot` | `hol-guard install copilot` |
| Cursor | `bash scripts/hol-guard-plugin protect cursor` | `hol-guard install cursor` |
| DeepSeek Harness | `bash scripts/hol-guard-plugin protect dsh` | `hol-guard install dsh` |
| Gemini CLI | `bash scripts/hol-guard-plugin protect gemini` | `hol-guard install gemini` |
| Hermes | `bash scripts/hol-guard-plugin protect hermes` | `hol-guard hermes bootstrap` |
| OpenClaw | `bash scripts/hol-guard-plugin protect openclaw` | `hol-guard install openclaw` |
| OpenCode | `bash scripts/hol-guard-plugin protect opencode` | `hol-guard install opencode` |
| Antigravity | `bash scripts/hol-guard-plugin protect antigravity` | `hol-guard install antigravity` |

## Validation

```bash
npm test
```

The repository also runs an actual DSH headless session against a local OpenAI-compatible mock inference endpoint. The control session executes a bash tool call, while the protected session proves HOL Guard's native DSH gate blocks the same call:

```bash
npm run test:dsh-e2e
```

No provider key is required for the end-to-end test.

## Source projects

- Plugin repository: https://github.com/hashgraph-online/hol-guard-plugin
- Guard and scanner source: https://github.com/hashgraph-online/hol-guard
- DeepSeek Harness source: https://github.com/deepseek-ai/deepseek-harness
- HOL Guard product: https://hol.org/guard

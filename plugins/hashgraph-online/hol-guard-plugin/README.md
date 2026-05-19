# HOL Guard Plugin

Codex plugin for HOL Guard, the local AI security layer from [`hol-guard`](https://github.com/hashgraph-online/hol-guard).

HOL Guard protects local AI harnesses before tools run. It can inspect Codex, Claude Code, Copilot CLI, Cursor, Gemini, Hermes, OpenClaw, OpenCode, and Antigravity surfaces, then route risky changes through local approvals and receipts.

## What this plugin adds

- A public Codex skill at [`skills/hol-guard/SKILL.md`](skills/hol-guard/SKILL.md).
- Guard setup guidance for Codex, Claude Code, Copilot CLI, Cursor, Gemini, Hermes, OpenClaw, OpenCode, and Antigravity.
- Scanner guidance for Codex plugins, Claude Code project surfaces, skills, MCP servers, and marketplace packages.
- Helper script for common `hol-guard` and `plugin-scanner` workflows.
- Validation test for the plugin manifest, skill, assets, and script paths.

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
| Gemini CLI | `bash scripts/hol-guard-plugin protect gemini` | `hol-guard install gemini` |
| Hermes | `bash scripts/hol-guard-plugin protect hermes` | `hol-guard hermes bootstrap` |
| OpenClaw | `bash scripts/hol-guard-plugin protect openclaw` | `hol-guard install openclaw` |
| OpenCode | `bash scripts/hol-guard-plugin protect opencode` | `hol-guard install opencode` |
| Antigravity | `bash scripts/hol-guard-plugin protect antigravity` | `hol-guard install antigravity` |

## Validation

```bash
npm test
```

No runtime dependencies are required for the validation test.

## Source projects

- Plugin repository: https://github.com/hashgraph-online/hol-guard-plugin
- Guard and scanner source: https://github.com/hashgraph-online/hol-guard
- HOL Guard product: https://hol.org/guard

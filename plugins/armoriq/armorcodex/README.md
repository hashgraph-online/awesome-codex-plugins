# ArmorCodex

Intent-based security enforcement for OpenAI Codex. Hooks Codex's `Bash`, `apply_patch`, and MCP tool calls against a declared intent plan and policy rules. Blocks intent-drift, gates by natural-language policy rules, and ships signed audit logs to the ArmorIQ backend.

This directory is the plugin bundle. The full project lives at the repository root.

## Install

```bash
curl -fsSL https://armoriq.ai/install_armorcodex.sh | bash
```

Or via Codex marketplace:

```bash
codex plugin marketplace add armoriq/armorCodex
codex plugin install armorcodex@armoriq
```

## What this bundle contains

- `.codex-plugin/plugin.json` plugin manifest (Codex spec)
- `.codex/` Codex-specific config
- `.mcp.json` MCP server registration (`armorcodex-policy`)
- `hooks/` global hook scripts (`preToolUse`, `postToolUse`, `sessionStart`, `userPromptSubmitted`)
- `scripts/` bootstrap, hook router, lib modules
- `assets/` plugin icon

## What it does

| Surface | Behavior |
|---|---|
| `sessionStart` / `userPromptSubmitted` | Injects directive: Codex registers its intent plan via MCP before any tool runs |
| `preToolUse` | Verifies tool against the registered plan and policy. Returns `{"permissionDecision":"deny",...}` for out-of-plan or policy-denied calls. |
| `postToolUse` | Async audit row to ArmorIQ backend (fire-and-forget WAL) |
| `permissionRequest` | Honors policy decisions before user is prompted |
| MCP tools | `register_intent_plan`, `policy_update` (natural-language rules), `policy_read` |

## Documentation

- Full docs: https://docs.armoriq.ai/armorcodex
- Source repo: https://github.com/armoriq/armorCodex
- ArmorIQ platform: https://armoriq.ai

---
name: hook-development
description: Use when creating, modifying, or debugging Claude Code hooks — PreToolUse, PostToolUse, Stop, SubagentStop, SessionStart, SessionEnd, UserPromptSubmit, PreCompact, Notification. Covers the plugin `hooks/hooks.json` wrapper format vs. the user `settings.json` direct format, matchers, security patterns, `$CLAUDE_PLUGIN_ROOT` portability, lifecycle limitations, and debugging. Trigger on "add a hook", "validate tool use", "block dangerous commands", "enforce completion", "hook-based automation".
model: sonnet
---

# Hook Development for Claude Code Plugins

Adapted from [claude-plugins-official/plugin-dev/skills/hook-development](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/hook-development). Trimmed to what we actually author (our plugin already has 6 event matchers covering 7 hook handlers — see `hooks/hooks.json`).

## Hook types

### Prompt-based (LLM-driven, for complex reasoning)

```json
{
  "type": "prompt",
  "prompt": "Evaluate if this tool use is appropriate: $TOOL_INPUT",
  "timeout": 30
}
```

Supported events: `Stop`, `SubagentStop`, `UserPromptSubmit`, `PreToolUse`.

Use for: context-aware decisions, flexible evaluation, natural-language reasoning.

### Command (deterministic, for fast checks)

```json
{
  "type": "command",
  "command": "${CLAUDE_PLUGIN_ROOT}/hooks/validate.mjs",
  "timeout": 60
}
```

Use for: fast deterministic validations, file-system ops, external tools, performance-critical paths.

**Our convention:** all our command hooks are `.mjs` (Node.js) — see `hooks/pre-bash-destructive-guard.mjs`, `hooks/enforce-scope.mjs`. The v3.0 migration moved us off bash for native Windows support.

## Configuration formats

This is where people trip up. Two formats exist; they are NOT interchangeable.

### Plugin `hooks/hooks.json` — wrapper format

```json
{
  "description": "Plugin hook description (optional)",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/validate.mjs" }
        ]
      }
    ]
  }
}
```

- `hooks` wrapper is required
- `description` is optional

### User `.claude/settings.json` — direct format

```json
{
  "PreToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        { "type": "command", "command": "~/my-hook.sh" }
      ]
    }
  ]
}
```

- No wrapper
- No description

Mixing these up is the #1 reason new hooks don't fire.

## Hook events

| Event | When | Use for |
|-------|------|---------|
| `PreToolUse` | Before tool runs | Validate, modify, block |
| `PostToolUse` | After tool completes | React to result, log |
| `UserPromptSubmit` | User submits prompt | Add context, validate |
| `Stop` | Main agent stopping | Completeness check |
| `SubagentStop` | Subagent stopping | Task validation |
| `SessionStart` | Session begins | Context load |
| `SessionEnd` | Session ends | Cleanup, logging |
| `PreCompact` | Before compaction | Preserve critical state |
| `Notification` | User notified | Logging, reactions |

### PreToolUse output schema

```json
{
  "hookSpecificOutput": {
    "permissionDecision": "allow|deny|ask",
    "updatedInput": { "field": "modified_value" }
  },
  "systemMessage": "Explanation shown to Claude"
}
```

### Stop / SubagentStop output

```json
{
  "decision": "approve|block",
  "reason": "Why blocked / approved",
  "systemMessage": "Additional context"
}
```

### SessionStart: persist env vars

```bash
echo "export PROJECT_TYPE=nodejs" >> "$CLAUDE_ENV_FILE"
```

`$CLAUDE_ENV_FILE` is unique to SessionStart hooks.

## Input schema

All hooks receive JSON on stdin:

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/dir",
  "permission_mode": "ask|allow",
  "hook_event_name": "PreToolUse"
}
```

Event-specific extras:
- `PreToolUse`/`PostToolUse`: `tool_name`, `tool_input`, `tool_result`
- `UserPromptSubmit`: `user_prompt`
- `Stop`/`SubagentStop`: `reason`

Access in prompt hooks via `$TOOL_INPUT`, `$TOOL_RESULT`, `$USER_PROMPT`.

## Environment variables

| Var | Scope | Purpose |
|-----|-------|---------|
| `$CLAUDE_PROJECT_DIR` | All | Project root |
| `$CLAUDE_PLUGIN_ROOT` | Plugin hooks | Plugin directory — **use this, never hardcode paths** |
| `$CLAUDE_ENV_FILE` | SessionStart only | Persist env vars |
| `$CLAUDE_CODE_REMOTE` | All (conditional) | Set if running remote |

### Portability rule

```json
// ✅ Portable — works everywhere the plugin installs
{ "command": "${CLAUDE_PLUGIN_ROOT}/hooks/guard.mjs" }

// ❌ Broken — only works on the operator's machine
{ "command": "~/Projects/.../guard.mjs" }
```

## Matchers

```json
"matcher": "Write"                       // Exact tool
"matcher": "Read|Write|Edit"             // Multiple
"matcher": "*"                           // All tools
"matcher": "mcp__.*__delete.*"           // Regex — all MCP delete tools
"matcher": "mcp__gitlab_.*"              // Specific MCP server
```

Matchers are **case-sensitive**.

## Security best practices

### Validate inputs (command hooks)

```bash
#!/bin/bash
set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name')

if [[ ! "$tool_name" =~ ^[a-zA-Z0-9_]+$ ]]; then
  echo '{"decision": "deny", "reason": "Invalid tool name"}' >&2
  exit 2
fi
```

In Node/`.mjs` hooks (our convention), same principle — parse stdin JSON, validate structure before trusting.

### Path safety

```bash
file_path=$(echo "$input" | jq -r '.tool_input.file_path')

# Deny path traversal
[[ "$file_path" == *".."* ]] && { echo '{"decision":"deny","reason":"Path traversal"}' >&2; exit 2; }

# Deny sensitive files
[[ "$file_path" == *".env"* ]] && { echo '{"decision":"deny","reason":"Sensitive file"}' >&2; exit 2; }
```

Our `enforce-scope.mjs` implements this for wave-scope boundaries.

### Quote variables

```bash
echo "$file_path"        # ✅
cd "$CLAUDE_PROJECT_DIR" # ✅
echo $file_path          # ❌ unquoted injection risk
```

### Timeouts

Defaults: command hooks 60s, prompt hooks 30s. Set explicitly when the work is known-slow:

```json
{ "type": "command", "command": "...", "timeout": 10 }
```

## Parallel execution

All matching hooks run **in parallel** — they don't see each other's output, ordering is non-deterministic. Design for independence.

## Lifecycle limitation — NO hot-swap

Hooks load at session start. Changes to `hooks.json` or hook scripts do **not** affect the running session.

To test hook changes:
1. Edit hook
2. Exit Claude Code
3. Restart (`claude` or `cc`)
4. Verify with `/hooks` command or `claude --debug`

This is the #2 reason "my hook isn't working" — the change hasn't loaded yet.

## Debugging

### Debug mode

```bash
claude --debug
```

Surfaces hook registration, execution logs, stdin/stdout JSON, timing.

### Test a command hook directly

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"/test"}}' | \
  ${CLAUDE_PLUGIN_ROOT}/hooks/guard.mjs
echo "Exit code: $?"
```

### Validate JSON output

```bash
output=$(./your-hook.mjs < test-input.json)
echo "$output" | jq .
```

Invalid JSON breaks silently — always verify.

## Conditional activation

Pattern: check for a flag file or config before running:

```bash
#!/bin/bash
FLAG_FILE="$CLAUDE_PROJECT_DIR/.enable-strict-validation"
[[ ! -f "$FLAG_FILE" ]] && exit 0   # Flag not present, skip
# ... validation logic
```

Or config-based (matches our Session-Config pattern):

```bash
CONFIG_FILE="$CLAUDE_PROJECT_DIR/.claude/config.json"
enabled=$(jq -r '.strictMode // false' "$CONFIG_FILE" 2>/dev/null)
[[ "$enabled" != "true" ]] && exit 0
```

## Our in-house examples (read these, not the upstream `examples/`)

- `hooks/pre-bash-destructive-guard.mjs` — policy-driven command blocker, 13 rules in `.orchestrator/policy/blocked-commands.json`
- `hooks/enforce-scope.mjs` — wave-scope boundary enforcement using `.orchestrator/wave-scope.json`
- `hooks/on-session-start.mjs` — banner + session init
- `hooks/post-edit-validate.mjs` — validates edits after the fact
- `hooks/on-stop.mjs` — session-event capture + metrics

## Do / Don't

**Do:**
- Prompt-based hooks for complex logic, command hooks for fast deterministic checks
- Always `${CLAUDE_PLUGIN_ROOT}` for paths
- Validate every input field before trusting it
- Quote all shell variables
- Set explicit timeouts for known-slow work
- Return structured JSON on stdout

**Don't:**
- Hardcoded paths
- Trust `tool_input` without validation
- Long-running hooks (blocks the tool call)
- Rely on execution order (hooks run in parallel)
- Mutate global state
- Log sensitive data to stdout/stderr

## Runtime Profile Control (#211)

All hook handlers support runtime opt-out via two environment variables without any settings-file changes. This is implemented in `hooks/_lib/profile-gate.mjs`.

### Env vars

| Variable | Values | Behaviour |
|----------|--------|-----------|
| `SO_HOOK_PROFILE` | `full` \| `minimal` \| `off` | Preset bundle (default `full` = all on). |
| `SO_DISABLED_HOOKS` | Comma-separated names | Disable individual hooks; overrides profile. |

### Profile bundles

- **`full`** (default): all hooks run — identical to pre-#211 behaviour when env is unset.
- **`minimal`**: only `on-session-start` + `pre-bash-destructive-guard`.
- **`off`**: no hooks run.

### Wiring a new hook into the gate

Every new hook handler **must** add the gate call as the very first executable statement after imports. The pattern is two lines at the top of the file, immediately after the import block:

```js
import { shouldRunHook } from './_lib/profile-gate.mjs';
if (!shouldRunHook('your-hook-name')) process.exit(0);
```

Use the kebab-case file stem without the `.mjs` extension as the hook name (e.g. `my-hook` for `hooks/my-hook.mjs`). When the hook exits 0 here it is **silent** — no stdout, no stderr — so Claude Code sees a clean allow.

### Failure modes

- Unknown `SO_HOOK_PROFILE` value → falls back to `full` + single stderr warning.
- `SO_DISABLED_HOOKS` with extra whitespace or mixed case is normalised automatically.
- `defaultEnabled` param of `shouldRunHook` is for future opt-in hooks; pass `false` for any handler that should be off by default in `full` profile.

### Tests

`tests/hooks/profile-gate.test.mjs` (10 tests) covers: full/minimal/off profiles, disabled-list override, unknown-profile fallback + warning, defaultEnabled=false, whitespace normalisation, empty disabled-list.

## Robust Plugin Root Resolution (#212)

Hook handlers and scripts that need the plugin directory must NOT read
`process.env.CLAUDE_PLUGIN_ROOT` directly. Use `resolvePluginRoot()` from
`scripts/lib/plugin-root.mjs` instead, which implements a 4-level fallback
so manual installs (where the env var is absent) still work.

### Fallback order

| Level | Source | Condition |
|-------|--------|-----------|
| 1 | `CLAUDE_PLUGIN_ROOT` env var | Returned immediately when set and is a directory |
| 2 | `CODEX_PLUGIN_ROOT` env var | Returned immediately when set and is a directory |
| 3 | Walk up from `import.meta.url` | Looks for `package.json` with `name: "session-orchestrator"` |
| 4 | Walk up from `process.cwd()` | Same marker; catches manual install paths outside the repo tree |

Levels 1 and 2 are **fast paths** — no filesystem walk is performed when either
env var is set. This preserves backward compat with all existing deployments.

When all four levels fail a `PluginRootResolutionError` is thrown with a
`triedPaths` array listing what was attempted.

### Usage in hook handlers

```js
import { resolvePluginRoot, PluginRootResolutionError } from '../scripts/lib/plugin-root.mjs';

// Throws on failure — handle or let it bubble (hooks have top-level catch)
const pluginRoot = resolvePluginRoot();
```

`scripts/lib/platform.mjs`'s `resolvePluginRoot()` delegates to this helper
internally, so any caller already using the platform module gets the 4-level
fallback transparently.

### Tests

`tests/lib/plugin-root.test.mjs` (10 tests) covers: env-claude, env-codex,
walk-from-import-meta, walk-from-cwd, all-fail-throws-named-error,
env-precedence, PluginRootResolutionError class shape.

## Implementation checklist

- [ ] Event chosen (PreToolUse / Stop / …) matches intent
- [ ] Prompt-based vs. command decided based on whether reasoning is needed
- [ ] `hooks/hooks.json` uses **wrapper** format, NOT settings direct format
- [ ] `${CLAUDE_PLUGIN_ROOT}` for all paths
- [ ] Input validation on every field you read from stdin
- [ ] Timeout set if work is known-slow
- [ ] Tested directly via `echo '...' | hook.mjs`
- [ ] Tested in-session with `claude --debug`
- [ ] README/docs updated

## References

- [Official hooks docs](https://docs.claude.com/en/docs/claude-code/hooks)
- Upstream: [patterns.md](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/hook-development/references/patterns.md), [advanced.md](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/plugin-dev/skills/hook-development/references/advanced.md) — read these for edge cases we haven't hit yet

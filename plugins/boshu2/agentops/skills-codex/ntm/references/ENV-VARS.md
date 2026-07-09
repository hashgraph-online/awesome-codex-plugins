# NTM Environment Variables

Comprehensive list from `/dp/ntm/internal/config/config.go` plus inherited vars in
adjacent files.

## Contents

- [Config path resolution](#config-path-resolution) — `NTM_CONFIG`, XDG
- [Project resolution](#project-resolution) — `NTM_PROJECTS_BASE`
- [CASS integration](#cass-integration) — dedup, context injection toggles
- [Recovery / session-context injection](#recovery--session-context-injection)
- [Account / provider rotation](#account--provider-rotation) — CAAM
- [Ollama](#ollama)
- [Output format (robot mode)](#output-format-robot-mode) — `NTM_ROBOT_FORMAT` precedence
- [TUI appearance](#tui-appearance) — theme, colors, icons, motion
- [Debug / testing](#debug--testing) — `NTM_DEBUG`, `NTM_TEST_MODE`
- [Safety hook bridge (from Claude Code)](#safety-hook-bridge-from-claude-code)
- [User identity](#user-identity) — `NTM_USER`
- [TOON binary paths](#toon-binary-paths)
- [Recommended `.envrc` for automation](#recommended-envrc-for-automation)
- [Gotchas](#gotchas)

---

## Config path resolution

| Var | Purpose | Source |
|-----|---------|--------|
| `NTM_CONFIG` | Override config path | `config.go:1792` |
| `XDG_CONFIG_HOME` | `$XDG_CONFIG_HOME/ntm/config.toml` (if set) | `config.go:1790-1804` |
| `HOME` | `$HOME/.config/ntm/config.toml` fallback | |
| `TMPDIR` | `$TMPDIR/.config/ntm/config.toml` when HOME unavailable | |

Final precedence: `NTM_CONFIG` > `XDG_CONFIG_HOME/ntm/` > `$HOME/.config/ntm/` > `$TMPDIR/.config/ntm/`.

## Project resolution

| Var | Purpose | Source |
|-----|---------|--------|
| `NTM_PROJECTS_BASE` | Override default projects directory — session name resolves under this | `config.go:1810, 2331, 2580` |

**Almost always the first env var you should set.** See `TROUBLESHOOTING.md` → Project resolution.

## CASS integration

| Var | Purpose | Source |
|-----|---------|--------|
| `NTM_CASS_ENABLED` | Toggle CASS-wide features | `config.go:2599` |
| `NTM_CASS_TIMEOUT` | CASS query timeout | `config.go:2602` |
| `NTM_CASS_BINARY` | Path to `cass` binary if non-default | `config.go:2608` |
| `NTM_CASS_CONTEXT_ENABLED` | Toggle context injection on spawn | `config.go:2612` |
| `NTM_CASS_MIN_RELEVANCE` | Minimum relevance score to inject | `config.go:2615` |
| `NTM_CASS_SKIP_IF_CONTEXT_ABOVE` | Skip inject past this context-size | `config.go:2620` |
| `NTM_CASS_PREFER_SAME_PROJECT` | Prefer same-project context | `config.go:2625` |

## Recovery / session-context injection

| Var | Purpose | Source |
|-----|---------|--------|
| `NTM_RECOVERY_ENABLED` | Session-recovery prompt injection | `config.go:2643` |
| `NTM_RECOVERY_INCLUDE_AGENT_MAIL` | Include recent agent-mail | `config.go:2646` |
| `NTM_RECOVERY_INCLUDE_CM` | Include CASS memory | `config.go:2649` |
| `NTM_RECOVERY_INCLUDE_BEADS` | Include recent beads | `config.go:2652` |
| `NTM_RECOVERY_MAX_TOKENS` | Cap recovery payload | `config.go:2655` |
| `NTM_RECOVERY_AUTO_INJECT` | Auto-inject on spawn | `config.go:2660` |
| `NTM_RECOVERY_STALE_HOURS` | Staleness threshold | `config.go:2663` |

## Account / provider rotation

| Var | Purpose | Source |
|-----|---------|--------|
| `NTM_ACCOUNTS_AUTO_ROTATE` | CAAM auto-rotate on rate-limit | `config.go:2630` |
| `NTM_ROTATION_ENABLED` | Master toggle for rotation | `config.go:2633` |
| `NTM_GEMINI_AUTO_PRO` | Auto-select Gemini Pro when available | `config.go:2638` |

## Ollama

| Var | Purpose | Source |
|-----|---------|--------|
| `OLLAMA_HOST` / `NTM_OLLAMA_HOST` | Ollama endpoint | `spawn.go:2681-2684`, `adapter.go:141` |

## Output format (robot mode)

| Var | Purpose | Source |
|-----|---------|--------|
| `NTM_ROBOT_FORMAT` | Primary override: `json` / `toon` / `auto` | `root.go:4853-4859` |
| `NTM_OUTPUT_FORMAT` | Secondary fallback | `root.go:4853-4859` |
| `TOON_DEFAULT_FORMAT` | Tertiary fallback (shared with TOON tool) | `root.go:4853-4859` |
| `NTM_ROBOT_VERBOSITY` | `terse` / `default` / `debug` | `root.go:4914` |

**Precedence**: `--robot-format` flag > `NTM_ROBOT_FORMAT` > `NTM_OUTPUT_FORMAT` > `TOON_DEFAULT_FORMAT` > built-in default.

## TUI appearance

| Var | Purpose | Source |
|-----|---------|--------|
| `NTM_THEME` | TUI theme name | `theme.go:349`, `root.go:133` |
| `NTM_NO_COLOR` | Disable colors | `theme.go:309` |
| `NTM_USE_ICONS` / `NERD_FONTS` / `NTM_ICONS` | Icon mode | `icons.go:326-413` |
| `NTM_REDUCE_MOTION` | Reduce dashboard animations | `dashboard/env.go:18` |
| `NTM_DASHBOARD_REFRESH` | Dashboard refresh interval | `dashboard/env.go:37` |
| `NTM_POPUP` | Force popup mode | `dashboard.go:113` |

## Debug / testing

| Var | Purpose | Source |
|-----|---------|--------|
| `NTM_DEBUG` / `NTM_TUI_DEBUG` | Debug logging | `dashboard.go:109`, `focus.go:328` |
| `NTM_TEST_MODE` / `NTM_E2E` | Test-mode behavior (skip side effects) | `audit/logger.go:182`, `spawn.go:104` |
| `NTM_DISABLE_INTERNAL_MONITOR` | Disable inline monitor loop | `spawn.go:579` |
| `NTM_SKIP_BV` | Skip BV priority scoring | `priority.go:21` |

## Safety hook bridge (from Claude Code)

Current NTM safety hooks read the Claude Code PreToolUse payload as JSON on stdin
(`tool_name`, `tool_input.command`). These env vars are retained as legacy fallback
and for blocked-command audit context:

| Var | Purpose | Source |
|-----|---------|--------|
| `CLAUDE_TOOL_NAME` | Legacy fallback for tool name when stdin JSON is absent | `safety.go:837` |
| `CLAUDE_TOOL_INPUT_command` | Legacy fallback for command when stdin JSON is absent | `safety.go:840` |
| `CLAUDE_AGENT_TYPE` | Agent type recorded in blocked-command logs | `safety.go:858` |
| `NTM_SESSION` | Session recorded in blocked-command logs | `safety.go:857` |

## User identity

| Var | Purpose | Source |
|-----|---------|--------|
| `NTM_USER` | Current approver id (recorded in `approved_by`) | `approve.go:324` |
| `USER` | Fallback for approver id | `approve.go:324` |

## TOON binary paths

| Var | Purpose | Source |
|-----|---------|--------|
| `TOON_BIN` | Path to `toon` binary | `toon_test_helpers_test.go:18-19` |
| `TOON_TRU_BIN` | Path to `toon-tru` binary | `toon_test_helpers_test.go:18-19` |

## Recommended `.envrc` for automation

```bash
# Project resolution
export NTM_PROJECTS_BASE="$HOME/Developer"

# Robot mode — TOON is significantly cheaper than JSON for LLMs
export NTM_ROBOT_FORMAT=toon
export NTM_ROBOT_VERBOSITY=default

# CAAM rotation on (pairs well with --robot-smart-restart)
export NTM_ACCOUNTS_AUTO_ROTATE=true
export NTM_ROTATION_ENABLED=true

# Recovery injection settings — conservative token cap
export NTM_RECOVERY_AUTO_INJECT=true
export NTM_RECOVERY_MAX_TOKENS=4000

# User identity for approval audit trail
export NTM_USER="$USER"
```

## Gotchas

- `NTM_PROJECTS_BASE` is evaluated at NTM startup. Changing it mid-session does not
  re-register existing panes — kill + respawn.
- Three env vars fallback for `--robot-format` — precedence matters. If output
  unexpectedly comes out as text, the shell may have `TOON_DEFAULT_FORMAT` unset and
  no upstream override. Set `NTM_ROBOT_FORMAT` explicitly.
- `NTM_CASS_ENABLED=false` disables BOTH dedup-check-on-send and context-injection.
  If you want only to disable dedup, prefer `--no-cass-check` per-call.

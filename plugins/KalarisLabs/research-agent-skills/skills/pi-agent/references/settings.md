# Settings

Source: https://pi.dev/docs/latest/settings

Pi uses JSON settings files. Project settings override global settings; nested objects merge key by key. Edit directly or use `/settings` for common options.

| Location | Scope |
|---|---|
| `~/.pi/agent/settings.json` | Global |
| `.pi/settings.json` | Project |

Resource paths in the global file resolve relative to `~/.pi/agent`; in the project file relative to `.pi`. Absolute paths and `~` work.

## Project Trust

Interactive startup asks before trusting a project folder that has project-local settings, resources, or project `.agents/skills` and no saved decision for that folder or a parent in `~/.pi/agent/trust.json`. Non-interactive modes never prompt and use `defaultProjectTrust` (`"ask"` default, `"never"`, `"always"`); `--approve`/`-a` and `--no-approve`/`-na` override for one run. `/trust` saves a decision (including for the immediate parent folder) but does not reload the current session. `pi config` and package commands follow the same flow; `pi update` never prompts.

## Model and Thinking

| Setting | Default | Notes |
|---|---|---|
| `defaultProvider` | – | Provider id |
| `defaultModel` | – | Model id |
| `defaultThinkingLevel` | – | `off`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max` |
| `hideThinkingBlock` | `false` | Hide thinking blocks in output |
| `showCacheMissNotices` | `false` | Transcript notices for significant prompt-cache misses |
| `thinkingBudgets` | – | Custom token budgets per thinking level |

## UI and Display

`theme` (`"dark"`), `externalEditor` (Ctrl+G command; takes precedence over `$VISUAL`/`$EDITOR` — use `"code --wait"` for VS Code), `quietStartup` (`false`), `defaultProjectTrust` (`"ask"`, global only), `collapseChangelog` (`false`), `enableInstallTelemetry` (`true`), `enableAnalytics` (`false`, only asked during experimental first-time setup with `PI_EXPERIMENTAL=1`), `trackingId`, `doubleEscapeAction` (`"tree"` | `"fork"` | `"none"`), `treeFilterMode` (`"default"` | `"no-tools"` | `"user-only"` | `"labeled-only"` | `"all"`), `editorPaddingX` (`0`, range 0–3), `outputPad` (`1`, 0 or 1), `autocompleteMaxVisible` (`5`, range 3–20), `showHardwareCursor` (`false`).

Fullscreen TUI: `tuiMode` (`"regular"` default, or experimental `"fullscreen"`; `/settings` changes apply immediately and `--tui-mode` overrides at startup), `fullscreenExitOutput` (`"transcript"` prints the final transcript plus resume hint, `"resume-hint"` restores the previous screen and prints only the hint), `fullscreenScrollbar` (`"auto"` shows it while scrolling, `"always"` reserves the rightmost column, `"hidden"`). The last two have no effect in regular mode.

## Network, Warnings, Markdown

`httpProxy` (applied as `HTTP_PROXY`/`HTTPS_PROXY`, global only). `warnings.anthropicExtraUsage` (`true`) warns when Anthropic subscription auth may use paid extra usage. `markdown.codeBlockIndent` (`"  "`), `markdown.mermaid` (`"streaming"`, or `"final"` / `"off"`).

## Compaction and Branch Summary

`compaction.enabled` (`true`), `compaction.reserveTokens` (`16384`), `compaction.keepRecentTokens` (`20000`). `branchSummary.reserveTokens` (`16384`), `branchSummary.skipPrompt` (`false`, defaults to no summary).

## Retry

`retry.enabled` (`true`), `retry.maxRetries` (`3`), `retry.baseDelayMs` (`2000`, so 2s/4s/8s), `retry.provider.timeoutMs` (SDK default), `retry.provider.maxRetries` (`0`), `retry.provider.maxRetryDelayMs` (`60000`; `0` disables the limit).

Keep `retry.provider.maxRetries` at `0` unless provider-level retries are explicitly needed — above `0`, SDK retries can swallow out-of-usage-limit errors before Pi sees them and block the agent until quota resets. When a provider requests a delay longer than `maxRetryDelayMs`, the request fails immediately with an informative error instead of waiting silently.

## Message Delivery

`steeringMode` / `followUpMode` (`"one-at-a-time"` or `"all"`), `transport` (`"auto"`, `"sse"`, `"websocket"`, `"websocket-cached"`), `httpIdleTimeoutMs` (`300000`, `0` disables), `websocketConnectTimeoutMs` (`15000`, `0` disables).

## Terminal and Images

`terminal.showImages` (`true`), `terminal.imageWidthCells` (`60`), `terminal.clearOnShrink` (`false`), `images.autoResize` (`true`, 2000×2000 max; applies to `@file` attachments, `read`, and images returned by tools), `images.blockImages` (`false`).

## Tools

`defaultTools` is a string array of built-in tools enabled at startup; omitting it uses Pi's standard defaults. Extension and SDK custom tools stay enabled, and an empty array starts with no built-ins while preserving them. `--tools` replaces this with a strict allowlist for all tools, `--no-tools` disables everything, `--no-builtin-tools` disables the built-in defaults, and `--exclude-tools` filters the result. A project `defaultTools` array replaces the global array.

## Shell

`shellPath` (supports leading `~`; Windows paths in JSON need forward slashes or escaped backslashes, e.g. `"C:/Program Files/Git/bin/bash.exe"`), `shellCommandPrefix` (prefix for every bash command), `npmCommand` (argv array, e.g. `["mise", "exec", "node@20", "--", "npm"]`). `npmCommand` covers all npm package-manager operations; user npm packages install under `~/.pi/agent/npm/`, project ones under `.pi/npm/`. When `npmCommand` is configured, git package dependency installs use plain `install` for wrapper compatibility.

## Sessions and Model Cycling

`sessionDir` (absolute, relative, or `~`); precedence is `--session-dir`, then `PI_CODING_AGENT_SESSION_DIR`, then this setting. `enabledModels` is an array of patterns for Ctrl+P cycling, same format as `--models`.

## Resources

`packages` (`[]`), `extensions` (`[]`), `skills` (`[]`), `prompts` (`[]`), `themes` (`[]`), `enableSkillCommands` (`true`, registers `/skill:name`).

Arrays support glob patterns, `!pattern` to exclude, `+path` to force-include an exact path, and `-path` to force-exclude. `packages` accepts strings or objects that filter which resource types load:

```json
{
  "packages": [
    "pi-skills",
    { "source": "npm:my-package", "skills": ["brave-search"], "extensions": [] }
  ]
}
```

## Telemetry and Update Checks

`enableInstallTelemetry` only controls the anonymous install/update ping to `https://pi.dev/api/report-install`. Opting out does not disable update checks, which fetch `https://pi.dev/api/latest-version`. `PI_SKIP_VERSION_CHECK=1` disables the version check; `--offline` or `PI_OFFLINE=1` disables all startup network operations including package update checks and telemetry.

## Example

```json
{
  "defaultProvider": "anthropic",
  "defaultModel": "claude-sonnet-4-20250514",
  "defaultThinkingLevel": "medium",
  "theme": "dark",
  "compaction": { "enabled": true, "reserveTokens": 16384, "keepRecentTokens": 20000 },
  "retry": { "enabled": true, "maxRetries": 3 },
  "enabledModels": ["claude-*", "gpt-4o"],
  "warnings": { "anthropicExtraUsage": true },
  "packages": ["pi-skills"]
}
```

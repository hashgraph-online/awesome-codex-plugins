# RCH Configuration Reference

## Contents

- [Precedence and File Locations](#precedence-and-file-locations)
- [Main Config (`~/.config/rch/config.toml`)](#main-config-configrchconfigtoml)
- [Workers Config (`~/.config/rch/workers.toml`)](#workers-config-configrchworkerstoml)
- [Environment Variables](#environment-variables)
- [Hook Configuration (Claude Code)](#hook-configuration-claude-code)
- [Validation and Diagnostics](#validation-and-diagnostics)
- [Runtime Data Paths](#runtime-data-paths)

## Precedence and File Locations

RCH resolves settings in this order (highest to lowest):

1. CLI flags (`--json`, `--verbose`, etc.)
2. Environment variables (`RCH_*`)
3. Profile defaults (`RCH_PROFILE`)
4. `.env` / `.rch.env`
5. Project config (`.rch/config.toml`)
6. User config (`~/.config/rch/config.toml`)
7. Built-in defaults

Primary files:

- User config: `~/.config/rch/config.toml`
- Worker config: `~/.config/rch/workers.toml`
- Project override: `.rch/config.toml`
- Optional transfer excludes: `.rchignore`

---

## Main Config (`~/.config/rch/config.toml`)

```toml
[general]
enabled = true
force_local = false
force_remote = false
log_level = "info"                    # trace, debug, info, warn, error, off
socket_path = "~/.cache/rch/rch.sock" # default resolves from runtime/cache path

[compilation]
confidence_threshold = 0.85
min_local_time_ms = 2000
remote_speedup_threshold = 1.2
build_slots = 4
test_slots = 8
check_slots = 2
build_timeout_sec = 300
test_timeout_sec = 1800
bun_timeout_sec = 600
external_timeout_enabled = true

[transfer]
compression_level = 3
remote_base = "/tmp/rch"
adaptive_compression = true
verify_artifacts = false
exclude_patterns = [
  "target/",
  ".git/objects/",
  "node_modules/",
]

[selection]
strategy = "fair_fastest"

[output]
visibility = "summary"                # none, summary, verbose
first_run_complete = true

[self_healing]
hook_starts_daemon = true
daemon_installs_hooks = true
auto_start_timeout_secs = 3
```

Socket path default behavior:

- First choice: `$XDG_RUNTIME_DIR/rch.sock`
- Fallback: `~/.cache/rch/rch.sock`
- Last resort: `/tmp/rch.sock`

---

## Workers Config (`~/.config/rch/workers.toml`)

```toml
[[workers]]
id = "worker-name"
host = "203.0.113.20"
user = "ubuntu"
identity_file = "~/.ssh/id_ed25519"
total_slots = 16
priority = 100
tags = ["rust", "bun", "fast"]
```

Slot guidance:

- Start with ~`2x` physical CPU cores for mixed workloads.
- Reduce slots if workers hit CPU steal, swap pressure, or I/O saturation.
- Increase `priority` for faster/more reliable workers.

---

## Environment Variables

Common overrides:

| Variable | Purpose |
|----------|---------|
| `RCH_PROFILE` | Base profile (`dev`, `prod`, `test`) |
| `RCH_LOG_LEVEL` | Logging level override |
| `RCH_DAEMON_SOCKET` | Daemon socket override (CLI layer) |
| `RCH_SOCKET_PATH` | Socket override (config layer) |
| `RCH_DAEMON_TIMEOUT_MS` | Daemon IPC timeout |
| `RCH_SSH_KEY` | Default SSH key path |
| `RCH_TRANSFER_ZSTD_LEVEL` | Transfer compression level |
| `RCH_ENV_ALLOWLIST` | Forwarded env vars for remote execution |
| `RCH_VISIBILITY` / `RCH_VERBOSE` / `RCH_QUIET` | Hook/CLI visibility controls |
| `RCH_OUTPUT_FORMAT` / `TOON_DEFAULT_FORMAT` | Machine output format |
| `RCH_JSON` / `RCH_HOOK_MODE` | Force machine/hook output mode |
| `NO_COLOR` / `FORCE_COLOR` | ANSI color behavior |

---

## Hook Configuration (Claude Code)

Location: `~/.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/absolute/path/to/rch"
          }
        ]
      }
    ]
  }
}
```

Recommended management commands:

```bash
rch hook install
rch hook status
rch hook uninstall
```

---

## Validation and Diagnostics

```bash
rch config show --sources
rch config validate
rch config lint
rch config doctor
rch check
```

---

## Runtime Data Paths

| Path | Purpose |
|------|---------|
| `~/.local/share/rch/telemetry/telemetry.db` | Telemetry persistence |
| `~/.local/share/rch/fleet_history/` | Fleet deployment history |
| `~/.cache/rch/` | Cache + default socket parent |
| `/tmp/rch/` | Remote transfer workspace base (default) |

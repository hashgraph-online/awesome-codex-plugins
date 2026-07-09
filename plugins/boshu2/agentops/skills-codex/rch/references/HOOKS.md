# Hook Integration

## Contents

- [Execution Flow](#execution-flow)
- [Installation and Status](#installation-and-status)
- [Hook Protocol (Current)](#hook-protocol-current)
- [What Gets Intercepted](#what-gets-intercepted)
- [Quick Hook Tests](#quick-hook-tests)
- [Performance and Safety Notes](#performance-and-safety-notes)

## Execution Flow

```text
Claude Code PreToolUse -> rch (no subcommand = hook mode)
                               |
                               +-- Non-Bash tool -> allow unchanged
                               +-- Bash non-compilation -> allow unchanged
                               +-- Bash compilation -> allow with modified command:
                                   "rch exec -- <original command>"
```

Important behavior:

- Hook returns quickly (classification path), then remote execution happens via `rch exec -- ...`.
- On unsafe/unavailable remote conditions, hook fails open and allows local execution.
- For successful or failed remote runs, RCH preserves command semantics by rewriting to `true` or `exit <code>` as needed.

---

## Installation and Status

```bash
rch hook install
rch hook status
rch hook test
rch hook uninstall
```

For multi-agent installs:

```bash
rch agents list
rch agents status
rch agents install-hook claude-code
rch agents uninstall-hook claude-code
```

Installed Claude settings entry:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "/absolute/path/to/rch" }
        ]
      }
    ]
  }
}
```

---

## Hook Protocol (Current)

### Input on `stdin`

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "cargo build --release",
    "description": "Build project"
  },
  "session_id": "optional"
}
```

### Output on `stdout`

1. Allow unchanged command: **empty stdout**
2. Allow with command rewrite (transparent interception):

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "updatedInput": {
      "command": "rch exec -- cargo build --release"
    }
  }
}
```

3. Deny command (rare, policy-level):

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "reason text"
  }
}
```

---

## What Gets Intercepted

Common intercepted command families:

- Rust: `cargo build`, `cargo check`, `cargo clippy`, `cargo doc`, `cargo test`, `cargo nextest run`, `cargo bench`, `rustc`
- Bun/TypeScript: `bun test`, `bun typecheck`
- C/C++: `gcc`, `g++`, `clang`, `clang++`
- Build systems: `make`, `cmake --build`, `ninja`, `meson compile`

Commonly not intercepted:

- Local-mutating package commands (`cargo install`, `cargo clean`, `bun install`, `bun add`, etc.)
- Interactive/dev commands (`bun run`, `bun dev`, `bun build`, `bunx`)
- Piped/redirected/backgrounded shell forms where deterministic offload is unsafe

---

## Quick Hook Tests

```bash
# Direct protocol test (compilation command)
printf '%s\n' \
  '{"tool_name":"Bash","tool_input":{"command":"cargo build --release"}}' | rch

# Direct protocol test (non-compilation command should usually return empty stdout)
printf '%s\n' \
  '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | rch

# Built-in integration test
rch hook test
```

Debugging:

```bash
RCH_LOG_LEVEL=debug rch hook test
RCH_LOG_LEVEL=debug rch diagnose "cargo test --workspace"
```

---

## Performance and Safety Notes

- Non-compilation decisions target sub-millisecond latency.
- Compilation decisions target low-millisecond latency.
- Hook mode always keeps stdout protocol-clean; diagnostics go to stderr.
- If parsing/config/daemon selection fails, RCH allows local execution instead of blocking.

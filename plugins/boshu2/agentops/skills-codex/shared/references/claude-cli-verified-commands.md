# Claude CLI Verified Commands

Verified in this repo on 2026-02-26 (local environment).

## Known-Good Command Shapes

```bash
# Discover CLI surface
claude --help
claude agents --help

# List configured agents
claude agents

# Non-interactive mode (prompt flag from help output)
claude -p "Summarize current git status."
```

## Common Operational Flags (from verified help output)

```bash
claude --model <alias-or-model>
claude --permission-mode <mode>
claude --worktree
claude --dangerously-skip-permissions
```

## Known Runtime Caveat

Historical note (superseded by ADR-0009 engine teardown): during high-concurrency
retired phased-engine runs in this environment, Claude subprocesses were
observed exiting with:

```text
claude exited with code -1: signal: killed
```

When this appears, prefer:

- retry with reduced concurrency / fewer parallel runtime sessions
- or use `--runtime-cmd codex` for phased runs in this repo

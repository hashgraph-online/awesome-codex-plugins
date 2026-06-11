---
name: shared
description: "Run shared."
---
# Shared References

This directory contains shared reference documents used by multiple skills:

- `validation-contract.md` - Verification requirements for accepting spawned work
- `references/backend-codex-subagents.md` - Concrete examples for Codex session agents
- `references/backend-background-tasks.md` - Fallback: background shell tasks
- `references/backend-inline.md` - Degraded single-agent mode (no spawn)
- `references/codex-cli-verified-commands.md` - Verified Codex CLI command shapes and caveats
- `references/cli-command-failures-2026-02-26.md` - Dated failure log and mitigations from live runs
- [references/content-hash-cache.md](references/content-hash-cache.md) - SHA-256 content-based caching for file processing
- [references/compaction-signals.md](references/compaction-signals.md) - Tool-call-based strategic compaction signals

These are **not directly invocable skills**. They are loaded by other skills (council, crank, swarm, research, implement) when needed.

## CLI Availability Pattern

All skills that reference external CLIs MUST degrade gracefully when those CLIs are absent.

### Check Pattern

```bash
# Before using any external CLI, check availability
if command -v bd &>/dev/null; then
  # Full behavior with bd
else
  echo "Note: bd CLI not installed. Using plain text tracking."
fi
```

### Fallback Table

| Capability | When Missing | Fallback Behavior |
|------------|--------------|-------------------|
| `ao` | Knowledge flywheel unavailable | Write learnings to `.agents/learnings/` directly. Skip flywheel metrics |
| `gt` | Workspace management unavailable | Work in current directory. Skip convoy/sling operations |
| `codex` | CLI missing or model unavailable | Fall back to runtime-native agents. Council pre-flight checks CLI presence (`which codex`) and model availability for `--mixed` mode. |
| `cass` | Session search unavailable | Skip transcript search. Note "install cass for session history" |

### Required Multi-Agent Capabilities

Council, swarm, and crank require a runtime that provides these capabilities. If a capability is missing, the corresponding feature degrades.

| Capability | What it does | If missing |
|------------|-------------|------------|
| **Spawn subagent** | Create a parallel agent with a prompt | Cannot run multi-agent. Fall back to `--quick` (inline single-agent). |
| **Agent-to-agent messaging** | Send a message to a specific agent | No follow-up round. Workers run fire-and-forget. |
| **Broadcast** | Message all agents at once | Per-agent messaging fallback. |
| **Graceful shutdown** | Request an agent to terminate | Agents terminate on their own when done. |
| **Shared task list** | Agents see shared work state | Lead tracks manually. |

Every runtime maps these capabilities to its own API. Skills describe WHAT to do, not WHICH tool to call.

**After detecting your backend (see Backend Detection below), load the matching reference for concrete tool call examples:**

| Backend | Reference |
|---------|-----------|
| Codex session agents | `references/backend-codex-subagents.md` |
| Background Tasks (fallback) | `references/backend-background-tasks.md` |
| Inline (no spawn) | `references/backend-inline.md` |

### Backend Detection

Use capability detection at runtime, not hardcoded tool names. The same skill must work across any agent harness that provides multi-agent primitives. If no multi-agent capability is detected, degrade to single-agent inline mode (`--quick`).

**Selection policy (runtime-native first):**
1. If running in a Codex session and `spawn_agent` is available, use Codex session agents as the primary backend.
2. If both are technically available, pick the backend native to the current runtime unless the user explicitly requests mixed/cross-vendor execution.
3. Only use background tasks when neither native backend is available.

| Operation | Codex Session Agents | OpenCode Subagents | Inline Fallback |
|-----------|----------------------|--------------------|------------------|
| Spawn (read-only) | `spawn_agent(message=...)` | Read-only subagent prompt | Execute inline |
| Follow-up | `send_input(target=..., message=...)` | not supported | N/A |
| Wait | `wait_agent(targets=[...])` | Read-only task polling | N/A |
| Cleanup | `close_agent(target=...)` | not supported | N/A |

**OpenCode limitations:**
- No inter-agent messaging — workers run as independent sub-sessions
- No follow-up mode — requires messaging between judges
- `--quick` (inline) mode works identically across all backends

### Backend Capabilities Matrix

> **Prefer native teams over background tasks.** Native teams provide messaging, redirect, and graceful shutdown. Background tasks are fire-and-forget with no steering.

| Capability | Codex Session Agents | Background Tasks |
|------------|----------------------|------------------|
| File conflict prevention | Manual `git worktree` routing or native `isolation: worktree` + lead-only commits | None |
| Process isolation | YES (sub-process) | Shared worktree |

### Skill Invocation Across Runtimes

Skills that chain to other skills (e.g., `$rpi` calls `$research`, `$vibe` calls `$council`) MUST handle runtime differences:

| Runtime | Tool | Behavior | Pattern |
|---------|------|----------|---------|
| Codex | `$X ...` | **Executable** — skill runs as a sub-invocation | `$council --quick validate recent` |
| Codex | N/A | Skills not available — inline the logic or skip | Check if `spawn_agent` exists before delegating |
| OpenCode | `skill` tool (read-only) | **Load-only** — returns `<skill_content>` blocks into context | Call `skill(skill="council")`, then follow the loaded instructions inline |

**OpenCode skill chaining rules:**
1. Call the `skill` tool to load the target skill's content into context
2. Read and follow the loaded instructions directly — do NOT expect automatic execution
3. **NEVER use slashcommand syntax** (e.g., `$council`) in OpenCode — it triggers a command lookup, not skill loading
4. If the loaded skill references tools by Codex names, use OpenCode equivalents (see tool mapping below)

**Cross-runtime tool mapping:**

| Codex | OpenCode | Notes |
|-------------|----------|-------|
| `spawn_agent` | Read-only subagent prompt | Same semantic role, different surface |
| `wait_agent` | Read-only task polling | Wait for completion |
| `send_input` | not available | Use a fresh task instead |
| `close_agent` | not available | Let the task exit |
| `$X ` | `skill` tool (read-only) | Load content, then follow inline |
| `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep` | Same names | Identical across runtimes |

### Rules

1. **Never crash** — missing CLI = skip or fallback, not error
2. **Always inform** — tell the user what was skipped and how to enable it
3. **Preserve core function** — the skill's primary purpose must still work without optional CLIs
4. **Progressive enhancement** — CLIs add capabilities, their absence removes them cleanly

## Reference Documents

- [references/backend-background-tasks.md](references/backend-background-tasks.md)
- [references/backend-codex-subagents.md](references/backend-codex-subagents.md)
- [references/backend-inline.md](references/backend-inline.md)
- [references/codex-cli-verified-commands.md](references/codex-cli-verified-commands.md)
- [references/cli-command-failures-2026-02-26.md](references/cli-command-failures-2026-02-26.md)
- [references/ralph-loop-contract.md](references/ralph-loop-contract.md)
- [references/orchestration-as-prompt.md](references/orchestration-as-prompt.md)
- [references/strict-delegation-contract.md](references/strict-delegation-contract.md) — canonical contract loaded by $rpi, $discovery, $validate: strict sub-skill delegation is the default for top-level orchestrators.

## Local Resources

### references/

- [references/backend-background-tasks.md](references/backend-background-tasks.md)
- [references/backend-codex-subagents.md](references/backend-codex-subagents.md)
- [references/backend-inline.md](references/backend-inline.md)
- [references/cli-command-failures-2026-02-26.md](references/cli-command-failures-2026-02-26.md)
- [references/codex-cli-verified-commands.md](references/codex-cli-verified-commands.md)
- [references/ralph-loop-contract.md](references/ralph-loop-contract.md)

### scripts/

- `scripts/validate.sh`

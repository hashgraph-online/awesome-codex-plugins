---
name: shared
description: Shared AgentOps skill contracts.
---
# Shared References

This directory contains shared reference documents used by multiple skills:

- `validation-contract.md` - Verification requirements for accepting spawned work
- `references/claude-code-latest-features.md` - Codex feature contract (slash commands, agent isolation, hooks, settings)
- `references/backend-claude-teams.md` - Concrete examples for Claude native teams (`TeamCreate` + `SendMessage`)
- `references/backend-codex-subagents.md` - Concrete examples for Codex CLI and Codex sub-agents
- `references/backend-background-tasks.md` - Fallback: `Task(run_in_background=true)`
- `references/backend-inline.md` - Default single-agent mode (no spawn) — the baseline, not a degradation
- `references/claude-cli-verified-commands.md` - Verified Claude CLI command shapes and caveats
- `references/codex-cli-verified-commands.md` - Verified Codex CLI command shapes and caveats
- `references/cli-command-failures-2026-02-26.md` - Dated failure log and mitigations from live runs

These are **not directly invocable skills**. They are loaded by other skills (council, crank, swarm, research, implement) when needed.

---

## CLI Availability Pattern

All skills that reference external CLIs MUST degrade gracefully when those CLIs are absent.

### Check Pattern

```bash
# Before using any external CLI, check availability
if command -v bd &>/dev/null; then
  # Full behavior with bd
else
  echo "Note: bd CLI not installed. Using plain text tracking."
  # Fallback: use TaskList, plain markdown, or skip
fi
```

### Fallback Table

| Capability | When Missing | Fallback Behavior |
|------------|-------------|-------------------|
| `bd` | Issue tracking unavailable | Use TaskList for tracking. Note "install bd for persistent issue tracking" |
| `ao` | Knowledge flywheel unavailable | Write learnings to `.agents/learnings/` directly. Skip flywheel metrics |
| out-of-session substrate (`ntm` / `ao agent`) | Always-on orchestration unavailable | Run the loop in-session (`$rpi`, `$evolve`). A substrate (an NTM tmux swarm or managed-agents via `ao agent`) only adds always-on dispatch of whole operating-loop or `$evolve` skill runs — see [agent-native](../agent-native/SKILL.md) and [docs/3.0.md](https://github.com/boshu2/agentops/blob/main/docs/3.0.md) |
| `gt` | Workspace management unavailable | Work in current directory. Skip convoy/sling operations |
| `gh` | PR/CI automation unavailable | Open PRs via the web UI; skip automated PR status/merge steps |
| `go` | Build-from-source unavailable | Install a prebuilt `ao` (Homebrew / install script / release binary); no Go needed |
| `codex` | CLI missing or model unavailable | Fall back to runtime-native agents. Council pre-flight checks CLI presence (`which codex`) and model availability for `--mixed` mode. |
| `cass` | Session search unavailable | Skip transcript search. Note "install cass for session history" |
| `jq` | JSON parsing unavailable | Read `--json` output manually or use non-JSON output modes |
| `rg` (ripgrep) | Fast search unavailable | Fall back to `grep` / `git grep` (slower) |
| Model tier config | `.agentops/config.yaml` missing | Use built-in defaults (quality=opus, balanced=sonnet, budget=haiku). Tier resolution falls through to "balanced". |

> Full per-tool purpose, required-vs-optional, and fallback detail: [docs/dependencies.md](https://github.com/boshu2/agentops/blob/main/docs/dependencies.md). The README "Requirements" section summarizes; this doc page is the canonical detail.

### Required Multi-Agent Capabilities

Council, swarm, and crank require a runtime that provides these capabilities. If a capability is missing, the corresponding feature degrades.

| Capability | What it does | If missing |
|------------|-------------|------------|
| **Spawn subagent** | Create a parallel agent with a prompt | Cannot run multi-agent. Fall back to `--quick` (inline single-agent). |
| **Agent-to-agent messaging** | Send a message to a specific agent | No debate R2. Workers run fire-and-forget. |
| **Broadcast** | Message all agents at once | Per-agent messaging fallback. |
| **Graceful shutdown** | Request an agent to terminate | Agents terminate on their own when done. |
| **Shared task list** | Agents see shared work state | Lead tracks manually. |

Every runtime maps these capabilities to its own API. Skills describe WHAT to do, not WHICH tool to call.

**After detecting your backend (see Backend Detection below), load the matching reference for concrete tool call examples:**

| Backend | Reference |
|---------|-----------|
| Claude feature contract | `skills/shared/references/claude-code-latest-features.md` |
| Claude Native Teams | `skills/shared/references/backend-claude-teams.md` |
| Codex Sub-Agents / CLI | `skills/shared/references/backend-codex-subagents.md` |
| Background Tasks (fallback) | `skills/shared/references/backend-background-tasks.md` |
| Inline (no spawn) | `skills/shared/references/backend-inline.md` |

### Backend Detection

Use capability detection at runtime, not hardcoded tool names. The same skill must work across any agent harness that provides multi-agent primitives. If no multi-agent capability is detected, degrade to single-agent inline mode (`--quick`).

**Selection policy (NTM > runtime-native > beads floor):**

Global opt-out first: if `AGENTOPS_ORCHESTRATION=off` is set, skip all spawn backends and degrade to the **beads floor** (single-agent inline / `--quick`; workers' work is tracked through `bd`). This mirrors the `AGENTOPS_HOOKS_DISABLED=1` convention. Otherwise, select in this order:

1. **NTM (top tier).** If `ntm` is on PATH, capability-probe it with `ntm --robot-capabilities`. When the probe confirms multi-agent primitives, use **NTM** as the primary backend.
2. **Runtime-native.** If NTM is unavailable: in a Claude session with `TeamCreate`/`SendMessage`, use **Claude Native Teams**; in a Codex session with `spawn_agent`, use **Codex sub-agents**. If both are technically available, pick the backend native to the current runtime unless the user explicitly requests mixed/cross-vendor execution. Only use background tasks when neither native backend is available.
3. **Beads floor.** If no multi-agent capability is detected, degrade to single-agent inline mode (`--quick`).

> **`gc` is NOT a selectable tier.** AgentOps no longer references Gas City; out-of-session orchestration is delegated to a swappable substrate (NTM + MCP + managed-agents — see [docs/3.0.md](https://github.com/boshu2/agentops/blob/main/docs/3.0.md)). Any residual `gc`-based dispatch prose in older swarm/crank reference files is historical only and is never selected.

**Output-contract parity is unchanged across all tiers:** workers write results to `.agents/swarm/results/*.json`, and the lead verifies-then-trusts those artifacts. This invariant holds whether the backend is NTM, a runtime-native team, or the beads floor.

| Operation | Codex Sub-Agents | Claude Native Teams | OpenCode Subagents | Inline Fallback |
|-----------|------------------|---------------------|--------------------|-----------------|
| Spawn | `spawn_agent(message=...)` | `TeamCreate` + `Task(team_name=...)` | `task(subagent_type="general", prompt=...)` | Execute inline |
| Spawn (read-only) | `spawn_agent(message=...)` | `Task(subagent_type="Explore")` | `task(subagent_type="explore", prompt=...)` | Execute inline |
| Wait | `wait(ids=[...])` | Completion via `SendMessage` | Task returns result directly | N/A |
| Retry/follow-up | `send_input(id=..., message=...)` | `SendMessage(type="message", ...)` | `task(task_id="<prior>", prompt=...)` | N/A |
| Cleanup | `close_agent(id=...)` | `shutdown_request` + `TeamDelete()` | None (sub-sessions auto-terminate) | N/A |
| Inter-agent messaging | `send_input` | `SendMessage` | Not available | N/A |
| Debate (R2) | Supported | Supported | **Not supported** (no messaging) | N/A |

**OpenCode limitations:**
- No inter-agent messaging — workers run as independent sub-sessions
- No debate mode (`--debate`) — requires messaging between judges
- `--quick` (inline) mode works identically across all backends

### Backend Capabilities Matrix

> **Prefer native teams over background tasks.** Native teams provide messaging, redirect, and graceful shutdown. Background tasks are fire-and-forget with no steering — only a speedometer and emergency brake.

| Capability | Codex Sub-Agents | Claude Native Teams | Background Tasks |
|------------|------------------|---------------------|------------------|
| Observe output | `wait()` result | `SendMessage` delivery | `TaskOutput` (tail) |
| Send message mid-flight | `send_input` | `SendMessage` | **NO** |
| Pause / resume | NO | Idle → wake via `SendMessage` | **NO** |
| Graceful stop | `close_agent` | `shutdown_request` | **TaskStop (lossy)** |
| Redirect to different task | `send_input` | `SendMessage` | **NO** |
| Adjust scope mid-flight | `send_input` | `SendMessage` | **NO** |
| File conflict prevention | Manual `git worktree` routing | Native `isolation: worktree` + lead-only commits | None |
| Process isolation | YES (sub-process) | Shared worktree | Shared worktree |

**When to use each:**

| Scenario | Backend |
|----------|---------|
| Quick parallel tasks, coordination needed | Claude Native Teams |
| Codex-specific execution | Codex Sub-Agents |
| No team APIs available (last resort) | Background Tasks |

### Skill Invocation Across Runtimes

Skills that chain to other skills (e.g., `$rpi` calls `$research`, `$validate` calls `$council`) MUST handle runtime differences:

| Runtime | Tool | Behavior | Pattern |
|---------|------|----------|---------|
| Codex | `Skill(skill="X", args="...")` | **Executable** — skill runs as a sub-invocation | `$council --quick validate recent` |
| Codex | N/A | Skills not available — inline the logic or skip | Check if `Skill` tool exists before calling |
| OpenCode | `skill` tool (read-only) | **Load-only** — returns `<skill_content>` blocks into context | Call `skill(skill="council")`, then follow the loaded instructions inline |

**OpenCode skill chaining rules:**
1. Call the `skill` tool to load the target skill's content into context
2. Read and follow the loaded instructions directly — do NOT expect automatic execution
3. **NEVER use slashcommand syntax** (e.g., `$council`) in OpenCode — it triggers a command lookup, not skill loading
4. If the loaded skill references tools by Codex names, use OpenCode equivalents (see tool mapping below)

**Cross-runtime tool mapping:**

| Codex | OpenCode | Notes |
|-------------|----------|-------|
| `Task(subagent_type="...")` | `task(subagent_type="...")` | Same semantics, different casing |
| `Skill(skill="X")` | `skill` tool (read-only) | Load content, then follow inline |
| `AskUserQuestion` | `question` | Same purpose, different name |
| `TaskCreate`, `TaskUpdate`, `TaskList`, `TaskGet` | `todo` | Task tracking (Claude uses 4 tools, OpenCode uses 1) |
| `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep` | Same names | Identical across runtimes |

### Rules

1. **Never crash** — missing CLI = skip or fallback, not error
2. **Always inform** — tell the user what was skipped and how to enable it
3. **Preserve core function** — the skill's primary purpose must still work without optional CLIs
4. **Progressive enhancement** — CLIs add capabilities, their absence removes them cleanly

## Reference Documents

- [references/substring-rename-overreach.md](references/substring-rename-overreach.md) — Pre-rename checklist for bulk sed across same-prefix concepts
- [references/cross-harness-skill-parity.md](references/cross-harness-skill-parity.md) — Knowledge parity beyond audit-codex-parity.sh; codex frontmatter strictness
- [references/content-hash-cache.md](references/content-hash-cache.md)
- [references/compaction-signals.md](references/compaction-signals.md)
- [references/backend-background-tasks.md](references/backend-background-tasks.md)
- [references/backend-claude-teams.md](references/backend-claude-teams.md)
- [references/backend-codex-subagents.md](references/backend-codex-subagents.md)
- [references/backend-inline.md](references/backend-inline.md)
- [references/claude-code-latest-features.md](references/claude-code-latest-features.md)
- [references/claude-cli-verified-commands.md](references/claude-cli-verified-commands.md)
- [references/codex-cli-verified-commands.md](references/codex-cli-verified-commands.md)
- [references/cli-command-failures-2026-02-26.md](references/cli-command-failures-2026-02-26.md)
- [references/ralph-loop-contract.md](references/ralph-loop-contract.md)
- [references/orchestration-as-prompt.md](references/orchestration-as-prompt.md)
- [references/stale-scope-validation.md](references/stale-scope-validation.md) — planning rule loaded by plan + pre-mortem: re-validate inherited scope against HEAD before acting on deferred beads or handoff docs.
- [references/strict-delegation-contract.md](references/strict-delegation-contract.md) — canonical contract loaded by $rpi, $discovery, $validate: strict sub-skill delegation is the default for top-level orchestrators.

# Agent Swarm Cleanup

When the workload on a box is "many agents at once," ordinary process triage
under-fits. Agents create second-order problems: duplicated builds, orphaned
helper processes, bloated multiplexer state, and confused parents that keep
work alive past its useful horizon.

This reference catalogues the recurring shapes and the cleanup move for each.

## Shape: Competing Build Trees

Two or more agents running compilation against the same project but with
isolated target directories.

```bash
ps aux | grep -E '(cc1plus|rustc)' | grep -v grep \
  | grep -oE 'target[^/[:space:]]*' | sort | uniq -c | sort -rn
```

Healthy output is a single line. Multiple lines mean the agents are sharing
neither cache nor I/O budget; the box is paying for the same artifact N
times.

Cleanup move: keep the newest build, kill the older agents (not the cargo
processes — they will respawn if the agent is alive). Renice whatever
remains.

## Shape: Orphaned MCP / Helper Children

Each coding agent typically spawns a small fan-out of helper processes
(MCP servers, npm-spawned tool runners, language-server bridges). When the
agent dies cleanly, those helpers exit. When the agent is killed hard, they
sometimes outlive it.

```bash
# Find detached helpers — no controlling TTY is a strong signal
ps -eo pid,ppid,tty,args | awk '$3 == "?" && /mcp|playwright|node/ { print }'
```

Rule of thumb: helpers without a live agent parent (`ppid` of `1` after the
agent exits) are safe to terminate. Avoid pre-emptively killing helpers
under a still-running agent — that triggers the whack-a-mole pattern.

## Shape: Multiplexer Sprawl

Tmux, zellij, and ntm sessions pile up after agent runs. Each holds memory
for scrollback and disk for state.

```bash
# tmux: list with creation age
tmux list-sessions -F '#{session_name} #{session_created}' 2>/dev/null \
  | while read name created; do
      age_h=$(( ($(date +%s) - created) / 3600 ))
      echo "$name ${age_h}h"
    done

# zellij: count exited
zellij list-sessions 2>&1 | grep -c EXITED

# Reap exited zellij
zellij delete-all-sessions --yes 2>/dev/null
```

Naming conventions help: prefix throwaway sessions (`ntm-test-*`,
`bench-*`, `swarm-N-*`) so cleanup is grep-and-kill rather than judgement.

## Shape: Confused Long-Horizon Agents

An agent older than the work it was meant to do is almost always idle in a
loop or repeatedly retrying the same failing step.

The matcher includes `agy` (Antigravity): ntm now maps its `gemini` agent
slot to `agy --dangerously-skip-permissions`, so the gemini-family pane runs
as an `agy` process. Match both — older sessions may still launch `gemini`.

```bash
# Agents older than 16h with no live children of substance
ps -eo pid,etimes,args | grep -E 'claude|codex|gemini|agy|antigravity' | grep -v grep \
  | awk '$2 > 57600 { print }' \
  | while read pid age rest; do
      kids=$(pgrep -P "$pid" | wc -l)
      printf 'pid=%s age=%ss children=%s args=%s\n' "$pid" "$age" "$kids" "$rest"
    done
```

Cleanup move: signal the agent (SIGTERM first), wait, escalate. Children die
with the parent. See [whack-a-mole-anti-pattern.md](whack-a-mole-anti-pattern.md)
for why this order matters.

## Shape: Stuck Cargo / Bun / Node Builds

Long compiles or test runs that have lost forward progress. The signal is a
process that has been alive longer than its realistic worst case but is at
roughly 0% CPU.

```bash
ps -eo pid,etimes,pcpu,args --sort=-etimes \
  | awk '$2 > 1800 && $3+0 < 1.0' \
  | grep -E 'cargo|bun test|jest|pytest' | head
```

Cleanup move: kill the build with SIGTERM, give it 3 seconds, escalate to
SIGKILL if it ignores the request (some test runners do). Then verify that
the same agent does not immediately re-run it.

## Bushido-Specific Notes

The bushido WSL host runs a small steady-state population:

- One `tmux` server holding `main` plus per-task sessions.
- One `dolt-bd-server` user service (do **not** kill — it is the issue
  tracker for every project).
- The llama.cpp `LlamaCppQwen` Windows-side service when local inference is
  active. Stop it via `pipeline off`, never via raw signals.
- Pipeline timer-driven units under `pipeline.target`. Pause with
  `pipeline disable-timers` before deep cleanup; restore with
  `enable-timers` afterwards.

Order on bushido:

1. `pipeline disable-timers` to freeze the dataflow.
2. Reap zombies, exited sessions, stuck tests.
3. Kill confused agents, not their children.
4. Verify with `pipeline status`.
5. `pipeline enable-timers` to restart the dataflow.

## Verification After Swarm Cleanup

Re-run the original three checks and the count of agents:

```bash
uptime
cat /proc/pressure/cpu /proc/pressure/memory 2>/dev/null
pgrep -af 'claude|codex|gemini|agy|antigravity' | wc -l
```

If pressure is down and the agent count dropped to the expected steady
state, the cleanup landed. If pressure is unchanged, you cleaned the wrong
shape — start again from the diagnose loop in
[../SKILL.md](../SKILL.md#diagnose-without-touching).

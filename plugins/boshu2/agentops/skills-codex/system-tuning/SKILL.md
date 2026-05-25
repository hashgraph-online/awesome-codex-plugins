---
name: system-tuning
description: 'Process cleanup + swarm hygiene'
---
# System Tuning Skill

> **Quick Ref:** Diagnose → reap free wins → kill stuck children → fix confused parents → renice survivors → verify. Output: `.agents/system-tuning/YYYY-MM-DD-triage.md`.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

When a dev box turns sluggish — high load, swap pressure, agent sprawl, or compile storms — work the kill ladder from the safest move outward. Cleanup target is usually a confused parent agent, not the visible child.

## When To Use

| Symptom | Use this skill |
|---|---|
| Load average drifts above core count | yes |
| Killed processes respawn within seconds | yes — see [references/whack-a-mole-anti-pattern.md](references/whack-a-mole-anti-pattern.md) |
| Tmux / zellij sessions piling up | yes — see [references/agent-swarm-cleanup.md](references/agent-swarm-cleanup.md) |
| One genuinely hot path | run `$perf` first |

## Loops

Three loops, in order. Each loop has a check, an action, and a verification.

### 1. Diagnose Without Touching

```bash
uptime && nproc
cat /proc/pressure/cpu /proc/pressure/io /proc/pressure/memory 2>/dev/null
ps -eo stat | grep -c '^Z'
ps aux --sort=-%cpu | head -10
```

Capture the baseline. Every kill below should move at least one number; if nothing moves, you killed the wrong thing.

### 2. Walk The Kill Hierarchy

Least-invasive first; escalate only when the previous rung did not help. Full ordering and signal escalation rules in [references/kill-hierarchy.md](references/kill-hierarchy.md).

```
zombies & exited sessions   →  reap, no risk
stuck child processes       →  SIGTERM, wait 3s, then SIGKILL if needed
confused parent agents      →  kill the parent so it stops respawning children
renice the survivors        →  starve the heavy work without killing it
```

Stop at the first rung that restores responsiveness.

### 3. Clean Up The Swarm

If the box hosts multiple coding agents, second-order problems dominate: duplicated build trees, orphaned helpers, stale multiplexer sessions, agents older than the work that spawned them. See [references/agent-swarm-cleanup.md](references/agent-swarm-cleanup.md) for shapes and the cleanup move per shape.

### 4. Verify

After every loop re-read the same metrics. Write a one-line delta:

```
load: 38.4 -> 12.1   |   cpu_pressure_avg10: 61% -> 8%   |   zombies: 14 -> 0
```

No delta written → cleanup not done.

## Quick-Start Checklist

```bash
# Baseline
uptime; cat /proc/pressure/cpu

# Reap free wins
ps -eo stat | grep -c '^Z'
zellij list-sessions 2>&1 | grep -c EXITED
zellij delete-all-sessions --yes 2>/dev/null

# Stuck children (12h+)
ps -eo pid,etimes,args --sort=-etimes | awk '$2 > 43200' | head

# Confused parents (16h+ agents)
ps -eo pid,etimes,args | grep -E 'claude|codex' | awk '$2 > 57600'

# Renice live compilation
for pid in $(pgrep -f /bin/cargo) $(pgrep cc1plus); do
  renice 19 -p "$pid" 2>/dev/null
  ionice -c 3 -p "$pid" 2>/dev/null
done

# Verify
sleep 10 && uptime && cat /proc/pressure/cpu
```

## Protected Processes

Never signal these without explicit operator approval:

```
systemd, sshd, dbus, cron
postgres, mysql, redis, nginx, caddy
docker, containerd, k3d, kubelet
the multiplexer holding your sessions (tmux server, wezterm-mux-server, zellij)
```

If unsure, document the candidate and leave it running.

## Output

Triage reports go to `.agents/system-tuning/YYYY-MM-DD-triage.md` with:

1. Baseline metrics
2. Kill log with reason per signal
3. Renice / ionice changes
4. Post-cleanup metrics
5. Anything escalated for operator decision

## See Also

- [perf](../perf/SKILL.md) — Optimize a single hot path once the system is responsive
- [bug-hunt](../bug-hunt/SKILL.md) — Investigate why a process loops or hangs
- [scope](../scope/SKILL.md) — Lock edit scope before running cleanup in a shared workspace

## Local Resources

### references/

- [references/kill-hierarchy.md](references/kill-hierarchy.md)
- [references/whack-a-mole-anti-pattern.md](references/whack-a-mole-anti-pattern.md)
- [references/agent-swarm-cleanup.md](references/agent-swarm-cleanup.md)

## Attribution

Methodology pattern-adopted from an external `system-performance-remediation` skill corpus. See `LICENSE.md` in this skill directory. No source text reused.

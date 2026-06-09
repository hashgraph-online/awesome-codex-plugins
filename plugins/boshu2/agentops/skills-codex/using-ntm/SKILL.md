---
name: using-ntm
description: "Run using NTM."
---

# Using NTM as the Out-of-Session Substrate

AgentOps 3.0 runs its loops **in session** and ships **no** daemon, scheduler, or
overnight runner. To run the loop **unattended** — always-on, scheduled,
queue-driven — you hand it to an orchestration **substrate**. The reference
substrate is **NTM + MCP + managed-agents**; this skill covers the **NTM leg**: a
local Named Tmux Manager swarm of Claude/Codex agent panes. NTM is an adopted
external tool (`ntm` on `PATH`), **not** an AgentOps-owned surface.

> **Skills are the runtime, not the CLI.** The substrate dispatches a *whole
> loop* by spawning an agent that **runs the $rpi or $evolve skill** — it does
> **not** shell out to a retired CLI subprocess. Those terminal
> wrappers are retired; the loop lives as a skill an agent executes. The seam is
> **NTM pane → agent → $rpi <bead>**, one bead dispatched as one invocable unit.

## When to use / when to skip

**Use it when:** you want a bead queue worked unattended out of session; you're
standing up or tending an NTM swarm that runs AgentOps loops; a pane is stuck,
rate-limited, or wedged; you need to know whether the swarm has converged.

**Skip it when:** the work fits a single in-session run (run $rpi or $evolve
yourself); you want in-session parallel fan-out across worktrees (use $swarm);
you're choosing between automation shapes (start at $automation-shape-routing).

This skill does **not** re-document the full `ntm` command surface — run
`ntm help`. It covers the **AgentOps substrate contract**: how to dispatch and
tend AgentOps loops on an NTM swarm.

## The dispatch contract

1. **One bead = one whole-loop skill invocation.** A pane's agent runs
   `$rpi <bead>` (one cycle) or `$evolve` (the outer loop). The substrate never
   decomposes the loop into per-phase steps — whoever owns the loop owns its
   invariants, and AgentOps owns the loop. Dispatch the skill; don't reimplement it.
2. **Agents inherit the skills via overlay.** Each pane is a Claude or Codex
   agent with the AgentOps Codex skills installed, so `$rpi`, `$evolve`,
   `$validate` resolve in-pane.
3. **The bead queue is the work source.** A lead runs `bd ready`, picks the next
   bead, and dispatches it to a free worker pane.
4. **Green CI is the merge gate.** Each worker drives its bead to a green PR from
   a per-bead worktree; the operator stays *on* the loop (intent + stop), not *in* it.

## Quick start

```bash
# 1. Spawn a swarm of agent panes against the repo (2 Claude + 1 Codex worker).
ntm spawn agentops --cc=2 --cod=1

# 2. Dispatch a whole loop to a pane — the SKILL, not a CLI subprocess.
ntm send agentops --pane=1 "$rpi ag-1234"
ntm send agentops --pane=2 "$evolve --beads-only"

# 3. Watch / attach.
ntm activity agentops          # per-pane agent state
ntm attach agentops            # drop into the swarm

# 4. Health + dependencies (run before a long unattended session).
ntm doctor                     # validate the NTM ecosystem
ntm deps                       # required agent CLIs present
```

Scheduled cadence (e.g. a nightly $evolve pass) is driven by host-OS timing (a
systemd user timer or cron) that runs `ntm send … "$evolve"`, or by a
managed-agent driver — **not** an AgentOps daemon.

## Tending the swarm (operator loop)

Run one tick at a time; take the first action whose trigger fires:

- **Rate-limited / auth-expired pane** → rotate the account / relaunch, re-send its bead.
- **Wedged pane** (no output, not at a prompt) → nudge once; if still wedged, kill + relaunch + re-dispatch.
- **Context-saturated pane** (forgetting, repeating) → have it write a handoff, relaunch fresh, re-dispatch.
- **Worker finished** (PR merged, bead closed) → dispatch the next `bd ready` bead.
- **Many review beads open, few closing** → flip to review-only, drain the backlog.
- **Otherwise** → observe; do not nudge a healthy working pane.

## Coordination (the MCP leg)

- **Beads (`bd`)** — shared work queue + state source: `bd ready`, `bd update --claim`, `bd close`.
- **MCP Agent Mail** (`ao mcp serve`) — cross-pane messages + **file reservations** (reserve before edit, release on commit).
- **Worktree-per-bead** is mandatory: no pane edits the shared checkout.

## Convergence + shutdown

Done when `bd ready` is empty, no pane has an in-flight bead, and the last few CI
runs are green. Confirm with `ntm activity` (all idle) + `bd ready` (empty) before
`ntm kill <session>`. Don't shut down on a transient quiet patch — a rate-limited
pane also looks idle.

## Anti-patterns

- ❌ Shelling out to a retired CLI; dispatch the `$rpi` / `$evolve` skill instead.
- ❌ Decomposing the loop into substrate steps — dispatch the whole loop as one invocable unit.
- ❌ Editing the shared checkout from a pane — worktree-per-bead, always.
- ❌ Treating NTM as AgentOps-owned — it is an adopted external substrate; a managed-agents driver (`ao agent`) or a plain in-session run are equally valid legs. Choose via $automation-shape-routing.

## Related skills

- $automation-shape-routing — decide Workflow vs NTM swarm vs plain skill before standing up a swarm.
- $swarm — in-session parallel fan-out across worktrees (the in-session sibling).
- $agent-native — `ao agent bundle` produces the loop definition a managed-agents substrate runs.
- $rpi · $evolve — the loops the substrate dispatches.

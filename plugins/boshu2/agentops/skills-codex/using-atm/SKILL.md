---
name: using-atm
description: "Run using ATM."
---

# Using ATM as the Out-of-Session Substrate

AgentOps 3.0 runs its loops **in session** and ships **no** daemon, scheduler, or
overnight runner. To run the loop **unattended** — always-on, scheduled,
queue-driven — you hand it to an orchestration **substrate**. The reference
substrate is **ATM + Agent Mail (`am`) + managed-agents**; this skill covers the **ATM leg**: a
local Named Tmux Manager swarm of Claude/Codex agent panes. ATM is an adopted
external tool (`atm` on `PATH`), **not** an AgentOps-owned surface.
ATM is Bo's fork/alias of upstream NTM: `atm` points at
`~/dev/ntm/dist/atm-darwin-arm64` and keeps the upstream `ntm` command surface.

> **Skills are the runtime, not the CLI.** The substrate dispatches a *whole
> loop* by spawning an agent that **runs the $rpi or $evolve skill** — it does
> **not** shell out to a retired CLI subprocess. Those terminal
> wrappers are retired; the loop lives as a skill an agent executes. The seam is
> **ATM pane → agent → $rpi <bead>**, one bead dispatched as one invocable unit.

## When to use / when to skip

**Use it when:** you want a bead queue worked unattended out of session; you're
standing up or tending an ATM swarm that runs AgentOps loops; a pane is stuck,
rate-limited, or wedged; you need to know whether the swarm has converged.

**Skip it when:** the work fits a single in-session run (run $rpi or $evolve
yourself); you want in-session parallel fan-out across worktrees (use $swarm);
you're choosing between automation shapes (start at $automation-shape-routing).

This skill does **not** re-document the full `atm` command surface — run
`atm help`. It covers the **AgentOps substrate contract**: how to dispatch and
tend AgentOps loops on an ATM swarm.

## The dispatch contract

1. **One bead = one whole-loop skill invocation.** A pane's agent runs
   `$rpi <bead>` (one cycle) or `$evolve` (the outer loop). The substrate never
   decomposes the loop into per-phase steps — whoever owns the loop owns its
   invariants, and AgentOps owns the loop. Dispatch the skill; don't reimplement it.
2. **Agents inherit the skills via overlay.** Each pane is a Claude or Codex
   agent with the AgentOps Codex skills installed, so `$rpi`, `$evolve`,
   `$validate` resolve in-pane.
3. **The bead queue is the work source.** A lead runs `br ready`, picks the next
   bead, and dispatches it to a free worker pane.
4. **Green CI is the merge gate.** Each worker drives its bead to a green PR from
   a per-bead worktree; the operator stays *on* the loop (intent + stop), not *in* it.

### Fresh Claude/Codex Peer Duels

When the operator asks for "a fresh Claude and Codex", "fresh peer models", a
"duel", or a cross-family opinion, the default substrate is **ATM panes**, not
headless one-shot CLIs. Spawn the requested model families, give both panes the
same bounded prompt, verify engagement, collect pane output, and kill the
temporary session.

Do not use print-mode CLIs for the other-family pane; use an interactive pane.
Use headless `codex exec` only when the operator explicitly asks for a headless
run or when there is no pane/TUI requirement.

Minimal bounded pattern:

```bash
atm spawn agentops --label navi-duel --no-user --cc=1:opus --cod=1:gpt-5.5 \
  --no-cass-context --ready-timeout=2m --json

atm send agentops--navi-duel --pane=1 --file prompt.md \
  --no-cass-check --force-non-interactive --json

atm codex preflight --session agentops--navi-duel --pane 2 --json
atm send agentops--navi-duel --pane=2 --codex-goal --file prompt.md \
  --no-cass-check --force-non-interactive --json
atm codex wait-goal-engaged --session agentops--navi-duel --pane 2 --json

atm kill agentops--navi-duel --json
```

If a requested alias resolves to a nearby installed model (for example `opus`
resolving to the available Opus build), report the actual pane model in the
verdict.

## Quick start

```bash
# 1. Spawn a swarm of agent panes — BORN INTO COORDINATION (ag-tixgy gateway).
#    --reserve makes each worker register in Agent Mail + hold its file scope +
#    receive the "coordinate via am, never hand-roll" contract, by construction.
#    Pass a per-lane scope so workers can't silently collide. (Implies --coord-contract.)
atm spawn agentops --cc=2 --cod=1 --reserve "cli/ tests/"

# Bare spawn (no --reserve) is still valid, but workers are then UNCOORDINATED
# until each runs `am macros start-session` by hand — the #1 swarm failure mode.
# scripts/check-spawn-reservation-coverage.sh flags atm-registered workers holding
# no reservation, so you can catch an uncoordinated lane before it collides.

# 2. Dispatch a whole loop to a pane — the SKILL, not a CLI subprocess.
atm send agentops --pane=1 "$rpi ag-1234"
atm send agentops --pane=2 "$evolve --beads-only"

# 3. Watch / attach.
atm activity agentops          # per-pane agent state
atm attach agentops            # drop into the swarm

# 4. Health + dependencies (run before a long unattended session).
atm doctor                     # validate the ATM ecosystem
atm deps                       # required agent CLIs present
```

Scheduled cadence (e.g. a nightly $evolve pass) is driven by host-OS timing (a
systemd user timer or cron) that runs `atm send … "$evolve"`, or by a
managed-agent driver — **not** an AgentOps daemon.

## Tending the swarm (operator loop)

Run one tick at a time; take the first action whose trigger fires:

- **Peer gate request** (`ACTION NEEDED`, `Hey! Listen!`, merge-gate,
  unblock-condition, verdict/dry-run before merge/close) → interrupt broad
  watching, run the named verifier, and answer in a channel the peer can read.
  If AM reads are degraded, use a bead note, PR comment, or tmux relay with
  `C-m` plus capture evidence; mail-send alone is not delivery.
- **Rate-limited / auth-expired pane** → rotate the account / relaunch, re-send its bead.
- **Wedged pane** (no output, not at a prompt) → nudge once; if still wedged, kill + relaunch + re-dispatch.
- **Context-saturated pane** (forgetting, repeating) → have it write a handoff, relaunch fresh, re-dispatch.
- **Worker finished** (PR merged, bead closed) → dispatch the next `br ready` bead.
- **Many review beads open, few closing** → flip to review-only, drain the backlog.
- **Otherwise** → observe; do not nudge a healthy working pane.

## Observing lanes (the meter LIES)

The wedged-vs-working call depends on reading the pane right — the `atm` meter misleads:

- **`atm status` context-% + `atm activity` are UNRELIABLE for codex panes** — freeze ~4K/256K showing WAITING/available while the lane works. Never conclude wedged from the meter alone.
- **See real content: `atm save <session>`** → `./outputs/<session>_<pane>_<ts>.txt`; read those (`atm copy` to clipboard). No `atm capture`/`atm read` exists.
- **Confirm by ARTIFACT, not meter:** bead assignee, worktree/branch, PR, output file (`git ls-remote --heads origin 'task/*'`, `gh pr list`).
- **Diagnose before `atm respawn`** (it kills + restarts) — read the `atm save` dump first; respawn only on a confirmed wedge (error / login prompt / frozen transcript).
- **Dispatch:** `atm send --pane=N` delivers DIRECT prompts; slash-commands may not fire on codex panes (`--codex-goal` is the tell). Prefer self-contained instructions; verify engagement via `atm save` + artifacts.
- **Raw tmux last resort:** submit with `tmux send-keys ... C-m` and capture
  the pane. Text still sitting in the input box is not delivery.

## Coordination (the Agent Mail leg)

- **Beads (`bd`)** — shared work queue + state source: `br ready`, `bd update --claim`, `bd close`.
- **Agent Mail (`am`)** (its own daemon at `127.0.0.1:8765` — the `am` CLI, **not** an `ao` subcommand; old "MCP Agent Mail" name retired) — register with `am macros start-session`, then cross-pane messages + **file reservations** (reserve before edit, release on commit).
- **Worktree-per-bead** is mandatory: no pane edits the shared checkout.

## Convergence + shutdown

Done when `br ready` is empty, no pane has an in-flight bead, and the last few CI
runs are green. Confirm with `atm activity` (all idle) + `br ready` (empty) before
`atm kill <session>`. Don't shut down on a transient quiet patch — a rate-limited
pane also looks idle.

## Anti-patterns

- ❌ Shelling out to a retired CLI; dispatch the `$rpi` / `$evolve` skill instead.
- ❌ Decomposing the loop into substrate steps — dispatch the whole loop as one invocable unit.
- ❌ Editing the shared checkout from a pane — worktree-per-bead, always.
- ❌ Treating ATM as AgentOps-owned — it is an adopted external substrate; a managed-agents driver (`ao agent`) or a plain in-session run are equally valid legs. Choose via $automation-shape-routing.

## Related skills

- $automation-shape-routing — decide Workflow vs ATM swarm vs plain skill before standing up a swarm.
- $swarm — in-session parallel fan-out across worktrees (the in-session sibling).
- $agent-native — `ao agent bundle` produces the loop definition a managed-agents substrate runs.
- $rpi · $evolve — the loops the substrate dispatches.

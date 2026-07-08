---
name: using-atm
description: Use ATM as the out-of-session substrate
---
# Using ATM as the Out-of-Session Substrate

AgentOps 3.0 runs its loops **in session** and ships **no** daemon, scheduler, or
overnight runner. To run the loop **unattended** — always-on, scheduled,
queue-driven — you hand it to an orchestration **substrate**. The reference
substrate is **ATM + Agent Mail (`am`) + managed-agents**; this skill covers the **ATM leg**:
a local [Named Tmux Manager](https://github.com/) swarm of Claude/Codex agent
panes. ATM is an adopted external tool (`atm` on `PATH`), **not** an
AgentOps-owned surface — AgentOps adopts it, it does not vendor it.
ATM is Bo's fork/alias of upstream NTM: `atm` points at
`~/dev/ntm/dist/atm-darwin-arm64` and keeps the upstream `ntm` command surface.

> **Skills are the runtime, not the CLI.** The substrate dispatches a *whole
> loop* by spawning an agent that **runs the `rpi` or `evolve` skill** — it
> does **not** shell out to retired RPI/evolve CLI subprocesses. The loop
> lives as a skill an agent executes. The seam is
> **ATM pane → agent → `$rpi <bead>` skill**, one bead dispatched as one
> invocable unit.

## When to use this skill / when to skip

**Use it when:** you want a bead queue worked unattended out of session; you're
standing up or tending an ATM swarm that runs AgentOps loops; a pane is stuck,
rate-limited, or wedged; you need to know whether the swarm has converged.

**Skip it when:** the work fits a single in-session run (just run `rpi` or
`evolve` yourself); you want in-session parallel fan-out across worktrees (use
[`$swarm`](../swarm/SKILL.md)); you're choosing between automation shapes at all
(start at [`$automation-shape-routing`](../automation-shape-routing/SKILL.md),
which routes Workflow vs ATM swarm vs plain skill).

This skill does **not** re-document the full `atm` command surface — run
`atm help` for that. It covers the **AgentOps substrate contract**: how to
dispatch and tend AgentOps loops on an ATM swarm.

**Instrument lane (before spawn):** run `ao orchestrate preflight --profile <name> --json`
and `ao orchestrate verify` after spawn (the orchestrate route/preflight/verify lane is
folded into this skill; profiles: `docs/contracts/orchestration-profiles.yaml`).

## When to use ATM vs AM (the 4-case matrix)

**ATM and AM are separate escalations on different axes — never a package.** ATM
(this skill, the out-of-session substrate) answers a **durability/wall-clock**
need: work must outlive your session, run unattended, or survive a pane death.
AM ([`agent-mail`](../agent-mail/SKILL.md), coordination) answers a **contention**
need: ≥2 writers can touch the same path. You reach for either *alone*.

| Reach for | When (observable trigger) |
|---|---|
| **Neither** (default) | One writer, fits this session/context, no unattended wait, no shared hot path. Single-agent-first ([operating-loop principle 8](../../docs/architecture/operating-loop.md#governing-principles)). |
| **AM only** (no ATM) | ≥2 live writable lanes share the repo (you + a peer, `$swarm`, review+impl pair) **and** any could touch the same file/glob, generated registry, schema, CLI docs, gate script, port, or build slot. The common case — needs no panes. |
| **ATM only** (no AM) | Unattended/scheduled wall-clock work over a **file-disjoint** (or single-lane) bead queue: overnight grind, CI-green-while-away. Beads are the queue; git serializes pushes; reserving against yourself is ceremony. |
| **Both** | ≥2 **unattended** panes that genuinely contend on shared surfaces. Rare core. `atm spawn … --reserve` with real paths, never "the repo". |

**Inflection points (escalate only on a real trigger):** context-window pressure that *survives* a fresh handoff+reload; N≥3 provably file-disjoint units; estimated runtime > your remaining attention window; a partition that's genuinely impossible (every lane touches one generated file → AM). **Cross-family verification is a [`council`](../council/SKILL.md) gate, NOT an ATM trigger** — spin an ephemeral judge, don't stand up a swarm.

**Asymmetry guardrail (bounds the de-mandate):** the de-mandate removes the
single-writer **session-start tax**, not the **collision guard**. Cost of an
*unneeded* AM call = one command; cost of a *missing* one = two panes silently
clobber a shared file and the merge looks like ordinary conflict cleanup while the
design forked. So the **`≥2-writers → reserve` reflex stays non-negotiable.**

**Partition before you lock:** if you *can* cut the write-sets disjoint, do that
(no AM) instead of reserving. Locks are the fallback when partition fails — not the
default. (This skill applied to itself: when a lane overlaps another's hot path,
prefer re-cutting the write-set to a sole-writer surface over a shared lease.)

## The dispatch contract

1. **One bead = one whole-loop skill invocation.** A pane's agent runs
   `$rpi <bead> --auto` (one cycle) or `$evolve --auto` (the outer loop). The
   substrate never decomposes the loop into per-phase steps — whoever owns the
   loop owns its invariants, and AgentOps owns the loop. Re-expressing `rpi` as
   substrate-side steps duplicates the loop shape and pits the substrate's retry
   machinery against the ratchet rules. Dispatch the skill; don't reimplement it.
2. **Agents inherit the skills via overlay.** Each pane is a Claude or Codex
   agent with the AgentOps skills installed, so `rpi`, `evolve`, `$validate`,
   etc. resolve in-pane.
3. **The bead queue is the work source.** A lead (operator or a lead pane) runs
   `BEADS_DIR="$(ao beads dir)" br ready`, picks the next bead, and dispatches it to a free worker pane.
4. **Green CI is the merge gate.** Each worker drives its bead to a green PR from
   a per-bead worktree (orchestrator-merge model); the operator stays *on* the
   loop (intent + stop), not *in* it (per-PR approval).

### Fresh Claude/Codex peer duels

A cross-family duel ("a fresh Claude and Codex") runs on **ATM panes**, not headless CLIs (never `claude -p`). Bounded spawn → send (codex via `--codex-goal`) → prove-engaged → collect → `atm kill` recipe: [`references/pane-mechanics.md`](references/pane-mechanics.md).

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
#    Pane 1 = the USER/controller pane; workers start at pane 2 (unless --no-user).
#    --pane=N is the tmux PANE index; --agent=N is the agent ORDINAL — they
#    differ by the user-pane offset (--pane=2 == --agent=1 in a default session).
atm send agentops --pane=2 "$rpi ag-1234 --auto"
atm send agentops --pane=3 "$evolve --beads-only --auto"
# For codex panes, drive the /goal flow with --codex-goal (a bare slash-command
# send may not fire): atm send agentops --codex-goal --pane=2 --file packet.txt

# 3. Watch / attach.
atm activity agentops          # per-pane agent state
atm attach agentops            # drop into the swarm

# 4. Health + dependencies (run before a long unattended session).
atm doctor                     # validate the ATM ecosystem
atm deps                       # required agent CLIs present
```

Scheduled cadence (e.g. a nightly `evolve` pass) is driven by host-OS timing (a
systemd user timer or cron) that runs `atm send … "$evolve --auto"`, or by a
managed-agent driver — **not** an AgentOps daemon.

## Tending, continuity, and observing — doctrine owned by `ntm`

Tending doctrine (nudge/restart/stop/converged, meter-LIES, two-tick) is owned by the ntm skill — see [`../ntm/SKILL.md`](../ntm/SKILL.md); the extracts here are ATM-specific deltas only.

- [`references/tending-loop.md`](references/tending-loop.md) — operator loop (renewal tick, first-trigger-wins action ladder), convergence/shutdown, and the single-writer / merged-before-close close discipline (gate cp-hxp6).
- [`references/continuity-and-meter.md`](references/continuity-and-meter.md) — renewal-tick + two-tick stall rule (`.agents/continuity/state.json`) and **the meter LIES**: the `atm codex preflight` / `wait-goal-engaged`, `atm save`, `ps` CPU% read paths that beat the frozen context-% / `atm activity` signals.

## Raw tmux key injection (last resort)

Fall back to raw `tmux send-keys` only when `atm send` / `atm codex …` can't express the action; submit with `C-m`, verify from `capture-pane` that the line cleared, never fire-and-forget. Pattern: [`references/pane-mechanics.md`](references/pane-mechanics.md).

## Coordination (the Agent Mail leg)

ATM panes coordinate through the other substrate legs, not bespoke glue:

- **Beads (`br`, beads_rust)** is the shared work queue and the source of truth for state —
  `BEADS_DIR="$(ao beads dir)" br ready` to pick, `br update <id> --claim` to claim,
  `br close <id>` when merged. (`bd`/Dolt is retired; resolve `BEADS_DIR` before every
  direct `br` read/write — linked worktrees don't carry `_beads`.)
- **Agent Mail (`am`)** (its own daemon at `127.0.0.1:8765` — the `am` CLI,
  **not** an `ao` subcommand) carries cross-pane **messages** and
  **file reservations** — the swarm's defense against two panes editing the same
  path. Each pane registers once with `am macros start-session`, reserves before
  editing (`am file_reservations reserve <proj> <agent> "<path>"`), releases on
  commit, and **messages other panes with `am mail send --from <me> --to <agent> --subject … --body …`**
  (read with `am mail inbox`). The CLI form works from any shell even when the
  MCP tool surface (`send_message` etc.) isn't wired into the session. **Trap:**
  the verb is `am mail send`, **not** `am send` (which doesn't exist), and the
  `mail` group isn't in `am --help` — see br cp-jgcl. List addressable agents
  with `am robot agents --project <proj>`.
- **Worktree-per-bead** is mandatory: no pane edits the shared checkout. See
  [../swarm/references/shared-checkout-discipline.md](../swarm/references/shared-checkout-discipline.md).

## Convergence, shutdown + close discipline

Terminal-state conditions and the **single-writer / merged-before-close** durability policy (gate cp-hxp6; read canonical, never a stale shared `main`) live in [`references/tending-loop.md`](references/tending-loop.md).

## Anti-patterns

- ❌ **Shelling out to retired RPI/evolve CLI subprocesses.**
  Dispatch the `rpi` / `evolve` **skill** to an agent pane instead.
- ❌ **Decomposing the loop into substrate steps.** Dispatch the whole loop as
  one invocable unit; never re-express `rpi`'s phases as ATM-side orchestration.
- ❌ **Editing the shared checkout from a pane.** Worktree-per-bead, always.
- ❌ **Treating ATM as AgentOps-owned.** It is an adopted external substrate; a
  managed-agents driver (`ao agent`) or a plain in-session run are equally valid
  legs. Choose via [`$automation-shape-routing`](../automation-shape-routing/SKILL.md).
- ❌ **Closing a bead before the branch is merged.** Closed-but-unmerged is
  protection-off. Require merge confirmation before `br close`.
- ❌ **Reading state from a stale shared `main`.** Read canonical from the bead's
  worktree branch or after merge; stale reads are the other half of the split-brain.

## Related skills

- [`$automation-shape-routing`](../automation-shape-routing/SKILL.md) — decide Workflow vs ATM swarm vs plain skill *before* standing up a swarm.
- [`$swarm`](../swarm/SKILL.md) — in-session parallel fan-out across worktrees (the in-session sibling of this out-of-session substrate).
- [`ntm`](../ntm/SKILL.md) — the in-session **tending decision layer** (when to nudge / restart / converge, the OC/AP cards, the liveness truth stack; the former vibing-with-ntm tending doctrine is folded into `ntm`). This skill is the **substrate runner** (spawn, dispatch loops, born-into-coordination); reach for `ntm` once panes are live and you're deciding what to do tick-by-tick.
- [`$agent-native`](../agent-native/SKILL.md) — `ao agent bundle` produces the loop definition a managed-agents substrate runs (the managed-agents leg).
- [`codex-exec`](../codex-exec/SKILL.md) — the **headless** codex lane (`codex exec`, stdin/positional) vs an ATM codex **TUI pane** here (keystroke / `--codex-goal` flow, `atm codex` readiness gates). Different dispatch mechanics, same auth/sub rules.
- [`rpi`](../rpi/SKILL.md) · [`evolve`](../evolve/SKILL.md) — the loops the substrate dispatches.
- **Fork maintenance** (not a skill) — `atm` is Bo's fork of upstream `ntm`. Pull upstream fixes via `make fork-status` → `make fork-preview` → `make fork-sync` in `~/dev/ntm` (see its `AGENTS.md` § "Upstream sync"; never rebase main directly). Divergence facts are owned by **FORKS-MAP F-1**.

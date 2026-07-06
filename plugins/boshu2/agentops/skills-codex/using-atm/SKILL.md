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

### Fresh Claude/Codex Peer Duels

When the operator asks for "a fresh Claude and Codex", "fresh peer models", a
"duel", or a cross-family opinion, the default substrate is **ATM panes**, not
headless one-shot CLIs. Spawn exactly the requested model families, give both
the same bounded prompt, verify engagement, collect pane output, and kill the
temporary session when done. Do **not** use `claude -p` / `claude --print` for
this shape; use an interactive Claude pane. Use headless `codex exec` only when
the operator explicitly asks for headless execution or there is no pane/TUI
requirement.

Minimal bounded pattern:

```bash
atm spawn agentops --label navi-duel --no-user --cc=1:opus --cod=1:gpt-5.5 \
  --no-cass-context --ready-timeout=2m --json

# Claude pane: direct prompt is fine.
atm send agentops--navi-duel --pane=1 --file prompt.md \
  --no-cass-check --force-non-interactive --json

# Codex pane: use the goal lifecycle and prove engagement.
atm codex preflight --session agentops--navi-duel --pane 2 --json
atm send agentops--navi-duel --pane=2 --codex-goal --file prompt.md \
  --no-cass-check --force-non-interactive --json
atm codex wait-goal-engaged --session agentops--navi-duel --pane 2 --json

# After collecting outputs, do not leave idle duel panes around.
atm kill agentops--navi-duel --json
```

If the requested model alias resolves to a nearby available runtime (for
example `opus` resolving to the installed Opus build), report the actual pane
model in the closeout instead of silently claiming the requested alias.

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

## Tending the swarm (operator loop)

Run one tick at a time; take the first action whose trigger fires:

- **A peer says `ACTION NEEDED`, `Hey! Listen!`, `merge gate`,
  `unblock-condition`, or asks for a verdict/dry-run before merge/close** →
  interrupt broad watching and answer that gate first. Run the named verifier,
  then surface the result in a channel the peer can read. If Agent Mail reads are
  degraded, use a bead note, PR comment, or raw tmux relay with `C-m` plus
  capture evidence. A mail send alone is not proof the peer was answered.
- **A pane is rate-limited or auth-expired** → rotate the account / relaunch the
  pane, then re-send its in-flight bead. Do not let a dead pane look idle.
- **A pane is wedged** (no output, not at a prompt) → nudge it once; if still
  wedged, kill + relaunch and re-dispatch its bead.
- **A pane is context-saturated** (forgetting earlier instructions, repeating
  itself) → have it write a handoff, then relaunch fresh and re-dispatch.
- **A worker finished its bead** (PR merged, bead closed) → dispatch the next
  `br ready` bead to it.
- **Many review beads open, few closing** → flip the swarm to review-only and
  drain the backlog before taking new feature work.
- **Otherwise** → observe; do not nudge a healthy working pane.

> **The wedged-vs-working judgment depends entirely on reading the pane CORRECTLY — see below. The `atm` meter lies.**

### Continuity: renewal ticks and the two-tick stall rule (absorbed from /continuity-loop)

> **Folded trigger:** requests to wire or tune a loop's continuity step, issue a
> stall verdict (suspect / stalled / converged), or set renewal-tick cadence
> route here — the retired `/continuity-loop` renewal spine lives in this section.

Each tending pass above IS one **renewal tick**: a bounded observation pass over
the supervised lanes that decides, per lane, whether forward progress happened
since the last tick and renews that lane's entry in the state surface. A tick
observes and records; intervention is a separate decision the tick's output
feeds. This is a **contract, not a scheduler** — tick firing is owned by host
timing (cron, a systemd user timer, or you tending), never an AgentOps daemon.
Default cadence: one tick per 10 minutes of unattended operation (tighten for
short-lived swarms, loosen overnight); the cadence is recorded in the state
file so consumers can compute staleness.

**Forward-progress evidence (any one suffices):** new pane output delta (ATM
robot state); new Agent Mail message or reservation activity; the lane
self-renewed its state entry; a work-product delta (commit, closed bead, new
artifact).

**State surface:** `.agents/continuity/state.json` — the ONLY continuity state
surface (two surfaces guarantee a split-brain stall verdict), renewed in place
per tick (write temp + rename). Shape (`continuity-state.v1`): global
`tick_seq`, `cadence_minutes`, `last_tick`, and a `lanes[]` array whose entries
carry `lane`, `agent`, `work_item`, `status` ∈ `active | suspect | stalled |
converged | escalated`, `tick_seq`, `last_renewal`, and an `evidence` string.
Every status change cites its evidence — a bare status flip is invalid. A lane
whose `tick_seq` is one behind the global counter is SUSPECT; two or more
behind is STALLED. A lane that finishes cleanly is marked `converged` and
leaves supervision — it is never reported as stalled.

**The two-tick rule — no stall verdict on a single missed tick** (one tick
cannot distinguish a slow tool call from a wedge; acting on one produces
nudge-storms that kill healthy lanes):

1. **Tick N:** no forward-progress evidence → mark the lane `suspect`. No action.
2. **Tick N+1:** still no evidence → mark it `stalled`. Now intervene, in
   order: one nudge → if the next tick shows no recovery, relaunch the lane
   (route it through [`$recover`](../recover/SKILL.md)) and re-dispatch → if
   the relaunched lane stalls again on the same work item, escalate.
3. Any forward-progress evidence at any point resets the lane to `active`.
   Healthy lanes are left alone — interruptions reset agent context, so the
   intervention IS the failure mode when the lane was fine.

**Escalation is an Agent Mail message, never a silent kill** (a killed pane
with no `am` record is indistinguishable from a crash). Message the
operator/tender lane and set the lane `escalated` when any of these hold: a
two-tick stall survived one nudge **and** one relaunch; the same work item
stalled two different lanes (the work is poisoned, not the lane); an
auth/rate-limit failure that account rotation did not clear; a
file-reservation conflict on the lane's write surface (route to
[`agent-mail`](../agent-mail/SKILL.md) coordination, not a retry); or a lane
re-doing work its own evidence trail shows complete (context saturation —
handoff, then relaunch fresh).

## Observing lanes (the meter LIES)

Hard-won 2026-06-15: an operator nearly **respawned healthy working lanes** because
the status signals were misread. Discipline:

1. **`atm status` context-% and `atm activity` are UNRELIABLE for codex panes.** They
   freeze around ~4K/256K and show `WAITING`/`available` while the codex lane is
   actively, correctly working. **Never conclude a lane is wedged from the meter or
   `atm activity` alone** — that's how you kill a working lane.
2. **To actually SEE pane content: `atm save <session>`** → writes per-pane dumps to
   `./outputs/<session>_<pane>_<timestamp>.txt`; read those. (`atm copy <session>
   [--cod|--cc|--all]` copies to clipboard.) **Caveat — codex TUI panes:** `atm save`
   dumps a codex pane as raw ANSI; stripping escapes can leave it **EMPTY**. For codex
   state, read `atm codex palette-state --json` / `atm codex preflight --json`
   (classified, ANSI-immune) instead of the raw dump — `atm save` is reliable for Claude
   panes. For the swarm-wide view use `atm get-all-session-text` / `gast` (cross-pane
   markdown table with error detection) and `atm grep 'error\|rate.limit' <session>` for
   fast triage. (`gast`/`grep`/`atm codex palette-state` ARE the read paths — there is no
   `atm capture`/`atm read`.)
3. **Confirm a lane by its ARTIFACTS, not the meter:** a real lane claims its bead
   (`br` assignee), creates a worktree/branch, opens a PR, or writes its output
   file. Check those (`git ls-remote --heads origin 'task/*'`, `gh pr list`, the
   expected path) as ground truth.
4. **Diagnose BEFORE you respawn.** `atm respawn` kills + restarts panes — run
   `atm save` and read the dump first; only respawn after the dump confirms a genuine
   wedge (an error, a login/trust prompt, an empty/frozen transcript), not a frozen meter.
5. **Dispatch caveat + worker-model routing.** `atm send --pane=N "prompt"` reliably
   delivers DIRECT prompts. **Addressing:** `--pane N` is the tmux PANE index (1 = user,
   workers 2+); `--agent N` is the agent ORDINAL — they differ by the user-pane offset
   (`--pane=2` == `--agent=1` in a default `--user` session). Prefer `--agent` for worker
   addressing so the offset can't bite you, or `--panes=2,3` for explicit multi-target.
   **Model routing:** free-form/exploratory loop work → Claude panes (engage reliably on a
   plain `atm send`). Codex panes need the goal lifecycle — drive them with
   `atm send --codex-goal --pane N --file packet.txt` (the supported `/goal` path), NOT a
   bare slash-command send. If a codex lane won't engage, suspect the boot race / goal-flow,
   not "codex is unreliable" — verify with `atm codex preflight` (item 6) before switching
   models. ALWAYS verify the lane engaged (artifacts / `atm codex wait-goal-engaged`),
   never assume the send took.
6. **Gate the first dispatch on `atm codex` readiness — the boot race (Hard-won 2026-06-15).**
   `atm spawn` returns BEFORE the pane's agent has booted to its input box. A `send` in
   the first few seconds lands on a not-yet-ready TUI and is **silently dropped** — the
   lane looks "spawned" but never engages. For codex panes this is solved deterministically:
   the `atm codex` group is purpose-built for it.
   - **Before the first dispatch**, gate on `atm codex preflight --session <s> --pane <n> --json`
     — it classifies readiness (`codex-live` / `goal-in-progress` / `usage-limit` /
     `replace-goal-dialog` / `stale-scrollback`) and tells you `proceed` / `wait` / `respawn`.
     Send only on `codex-live` (or `goal-completed`).
   - **After dispatch**, confirm engagement with `atm codex wait-goal-engaged <s> --pane <n> --json`
     — a bounded poll that exits **non-zero** on `unconfirmed` / `dialog_stuck` /
     `respawn_required`, so a missed send fails loudly instead of looking idle.
   This is the deterministic ground truth (the navigator pattern); the meter is the
   stochastic surface. **Fallback (Claude panes, or codex if the group is unavailable):**
   confirm a clean ready prompt (`tmux capture-pane -p -t <sess>.<pane>` → the `❯`/input
   box, no `>_ OpenAI Codex (v…)` splash) before sending. A wedge from sending-too-early is
   **operator error, not a tool defect** — fix the dispatch (gate + verify), do NOT pivot
   worker models to escape it.
7. **Verify the FIRST lane engaged before fanning out to the rest.** Dispatch lane 1,
   confirm it engaged (`atm codex wait-goal-engaged`, OR an artifact appearing, OR CPU burn —
   see 8), THEN send lanes 2..N. Sending all N blind means discovering all N missed at
   once; one confirmed lane is your proof the dispatch path works before you commit the
   fleet to it.
8. **`ps` CPU% is the honest fallback wedge signal when the tooling can't reach it.**
   `ps aux | grep '[c]odex'` (or `[c]laude`) → a pane's agent process at **0.0% CPU with
   no growing artifact** is genuinely idle, not "working invisibly." CPU burn + growing
   token counts = real work even when `atm activity` and the TUI capture look frozen. The
   meter lies and the TUI capture can be stale; CPU does not. Use it (and the deterministic
   windshield — `atm codex preflight`, `gh pr list`, `git ls-remote`, the output file) to
   break ties before respawning — prefer the `atm codex` classifier first, CPU% as the
   cheap tie-breaker.

7. **AGY lanes + Agent Mail observability gaps (tri-vendor).** `atm activity` may list only Claude + Codex and **omit AGY**; `atm mapping --session=…` may be **empty when Agent Mail is down** even when panes are healthy. Do not treat either signal as spawn failure or wedged AGY. Prefer spawn `--json` `panes[]` or `tmux list-panes` for pane numbers; use tmux capture on the AGY pane for liveness. Full tri-vendor dispatch + verify is folded into this skill (the former dual-pane-atm duel).

## Raw tmux Key Injection (Last Resort)

Prefer `atm send`, `atm codex ...`, or NTM robot send surfaces for dispatch. Use
raw `tmux send-keys` only for direct TUI/menu control, emergency pane relay, or
when the robot surface cannot express the action.

When you do use raw tmux, **submit with `C-m` and verify it landed**. Do not rely
on a trailing literal `Enter` token in automation; in live pane relay it can
leave text sitting in the input buffer. The safe pattern is:

```bash
tmux send-keys -t <target-pane> -- "<message>"
tmux send-keys -t <target-pane> C-m
tmux capture-pane -pt <target-pane> -S -30
```

The capture must show that the input line cleared and the pane started reacting
(thinking/working indicator, echoed command output, or new prompt movement). If
the message is still visibly parked in the input box, send another `C-m` and
capture again. Codex-family TUIs may need two or three `C-m` submits after a
large paste; never fire-and-forget a raw tmux relay.

For gate/unblock replies, a capture that only shows text sitting in the input
box is not delivery. The answer must be visible as accepted pane input/output or
recorded in a durable artifact the peer can inspect (bead note or PR comment).

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

## Convergence + shutdown

The swarm is done when: `br ready` is empty, no pane has an in-flight bead, and
the last few CI runs are green. Confirm with `atm activity` (all panes idle) and
`br ready` (empty) before tearing down with `atm kill <session>`. Don't shut down
on a transient quiet patch — a rate-limited pane also looks idle.

## Single-writer + merged-before-close (cards 17–18, cp-4gj6; POLICY → gate cp-hxp6)

For assurance-close contexts, the gate cp-hxp6 enforces: a bead is durable only
when its branch is **merged to trunk** and the commit is visible on the canonical
store. A pane that closes a bead before merging puts protection OFF — the split-brain
incident of 2026-06-09 was caused by an unmerged trio. The fix is not behavioral:
the gate enforces it structurally.

**Read canonical, not shared main.** Every reader of bead/verdict state must target
the canonical store (the bead's worktree branch or the trunk after merge). `main`
in a shared checkout is stale relative to in-flight worktree branches. A reader that
declares "stuck" or "closed" based on a stale `main` read is reporting on phantom
state. Verify bead state on the bead's branch or via `br show` against the live
server; do not declare convergence from a stale checkout.

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

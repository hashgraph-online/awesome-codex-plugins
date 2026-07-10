# Continuity ticks, the two-tick stall rule, and reading the meter

> **Provenance / ownership.** Extracted verbatim from `skills/using-atm/SKILL.md`
> (payload-diet, age-verification-economics-ebec.8 / age-skills-audit-fable-l6ic.8).
> The **swarm-tending doctrine here — the meter-LIES ladder, the suspect →
> stalled → escalated stall verdict, and the two-tick rule — is owned by the
> `ntm` skill** ([`../../ntm/SKILL.md`](../../ntm/SKILL.md)). What lives in this
> file is the **ATM-runner view**: the renewal-tick contract as it binds the ATM
> substrate and the concrete `atm`/`atm codex` read paths. ATM-specific deltas
> only, not a second source of truth. (Relative links repointed one level deeper
> and the "tending pass above" / "see below" cross-refs repointed to sibling
> files on extraction — mechanical repairs, doctrine prose unchanged.)

## Continuity: renewal ticks and the two-tick stall rule (absorbed from /continuity-loop)

> **Folded trigger:** requests to wire or tune a loop's continuity step, issue a
> stall verdict (suspect / stalled / converged), or set renewal-tick cadence
> route here — the retired `/continuity-loop` renewal spine lives in this section.

Each tending pass (the operator loop in [`tending-loop.md`](tending-loop.md)) IS one **renewal tick**: a bounded observation pass over
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
   (route it through [`/recover`](../../status/SKILL.md)) and re-dispatch → if
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
[`agent-mail`](../../agent-mail/SKILL.md) coordination, not a retry); or a lane
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

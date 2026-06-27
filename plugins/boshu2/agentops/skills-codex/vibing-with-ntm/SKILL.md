---
name: vibing-with-ntm
description: Use when tending NTM agent swarms
---
<!-- TOC: One Rule | Outcome | Grounding | Tick Loop | Liveness Truth Stack | Intervention Discipline | Decision Tree | Command Surfaces | Cadence | Review-Only Mode | Metrics | Checklist | When To Use | References | Related Skills -->

> **If you are tending a swarm right now:** jump to the [Orchestrator Decision Tree](#orchestrator-decision-tree) below. For recovery recipes see [RECOVERY.md](references/RECOVERY.md). Everything else is context.

# Vibing With NTM

> **The One Rule:** Observe real state before every nudge. A swarm is not stuck, done, or blocked until pane truth, robot state, work graph, and artifact/git evidence agree.

This skill is the **operator layer above the tools** — the decisions, ticks, nudges, and recoveries an orchestrator performs. It deliberately does NOT re-document the `ntm` command surface: the binary self-describes via `ntm --help` and `ntm robot-docs` (and the `$ntm` skill catalogs it). Always re-query those for syntax, flags, and schemas; come back here for *when* to act and *when* to stop.

## Outcome — When a Tending Session Has Delivered

A tending session is complete (for now) when **all** of the following hold:

- Every pane is in one of three explicit states: **making progress** (recent useful output / git / bead movement), **explicitly blocked** with a logged blocker and handoff path, or **standing down** by policy (queue-dry, convergence, rate-limit cool-down). "Idle and you don't know why" is unfinished tending work.
- Every intervention was **observed to land** via tail/event/git/br/mail evidence within one observation window. Sends with no downstream signal are presumed lost, not silently successful.
- Any policy lever you adjusted (review-only, rate-limit posture, ensemble set) is **logged** — undocumented policy changes are how swarms drift.
- For convergence: the **triple-check** has fired — ready queue empty AND no in-flight work AND no expected upstream signals. Two of three is observation lag, not convergence.
- For queue-dry: you have **stopped manufacturing work**. Tending discipline includes the discipline of doing nothing.

If you send the same nudge twice without movement, the failure has escalated past nudging — go to [RECOVERY.md](references/RECOVERY.md), don't keep nudging.

## Grounding — Where Operator Truth Lives

Ground every decision in observable artifacts, never in agent self-report:

- **Pane truth:** `ntm --robot-tail`. What the agent says is a hypothesis; what the pane shows is data.
- **Work graph:** `br ready --json`, `br show <id> --json`. The tracker is canonical; a disagreeing agent is wrong.
- **Mail / coordination:** the Agent Mail inbox and threads — the thread is the source.
- **Git state:** `git log --since=`, `git status` on project worktrees — ground truth for "is real work being produced."
- **Snapshot deltas:** two `--robot-snapshot` outputs N seconds apart. The diff is what changed; everything else is narrative.

If a grounding source and a self-report disagree, the artifact wins.

## The Tick Loop (Mandatory)

```
1. BASELINE    -> ntm --robot-snapshot; capture cursor + sources/degraded_sources
2. ATTEND      -> ntm --robot-attention / --robot-wait; read only actionable deltas
3. CLASSIFY    -> match one OC card or AP red flag; no card means observe more
4. SCORE       -> choose the smallest reversible intervention with highest action score
5. ACT         -> one targeted send/assign/lock/restart/review instruction; never blanket-nudge
6. VERIFY      -> tail/event/git/br/mail/pipeline state changed; otherwise escalate one rung
7. STOP CHECK  -> convergence triple-check or queue-dry; stop instead of manufacturing work
8. LOG         -> record blocker, degraded source, or handoff when the loop changes policy
```

If you cannot name the phase you are in and the evidence behind it, do not nudge — re-observe.

**Cold start:** run one bounded tick (`--robot-snapshot` → tail suspect panes → match exactly one decision-tree branch → act on one pane or lever → verify). Do not read every reference first; wait on the attention feed instead of inventing work.

## Gate-Request Interrupts

A peer gate request is an interrupt, not background watch traffic. Treat these
phrases as a first-class `ACT` trigger even if another pane looks busy:
`ACTION NEEDED`, `Hey! Listen!`, `merge gate`, `unblock-condition`,
`dry-run verdict`, `PASS / REVISE verdict`, `ACK-with-id`, or an explicit
request to verify a SHA/PR/bead before merge or close.

When this trigger fires:

1. Stop broad watching and answer the gate first.
2. Run the smallest authoritative verifier named by the request (PR check,
   `br show`, dry-run command, test, or pane capture).
3. Surface the result where the requesting peer can actually read it. Agent Mail
   is enough only if their read path is known-good; otherwise write a bead note,
   PR comment, or pane relay with `tmux send-keys ... C-m` and capture evidence.
4. Do not claim the peer was answered until the visible artifact or capture
   proves the verdict landed.

This is the fix for ag-navi-gate-interrupt-ggque: a navigator that leaves an
unblock request sitting in mail or pane scrollback has not tended the swarm,
even if the underlying watch loop is otherwise healthy.

## Liveness Truth Stack (what to believe, in order)

Before acting on any "pane is stuck / rate-limited / done / idle" judgment, verify in this order — each layer catches lies from the one above:

1. **`tmux list-panes … -F '#{pane_current_command} #{pane_pid}'`** — is the agent CLI even running? Silent exits back to zsh are invisible to `--robot-tail`. (OC-026)
2. **`tmux capture-pane -p -S -20`** — ground truth for transient state; `--robot-tail` can sample stale buffer content for several ticks. (AP-41) Caveat: a full-screen TUI agent (codex especially) can return almost entirely ANSI/alt-screen control sequences — stripping leaves empty. **Capture-unreadable is NOT evidence of idle**; fall through to layer 3.
3. **`git log --since='15 minutes ago'` + `pgrep -af cargo|rustc|go|bun`** — are commits landing, are builds running? Timer labels like "Cogitated for 35m" are display artifacts, not activity. (AP-42)
4. **`ps -p $(tmux display -p -t <s>:<w>.<pane> '#{pane_pid}') -o pcpu=`** — the signal-of-last-resort. 0.0% on the pane process tree + no growing artifact = genuinely idle, even when the meter AND capture both lie. The one signal that survives when everything above it is unreadable (e.g. codex-TUI capture returns empty). (AP-48, AP-54)
5. **`ntm --robot-is-working` / `--robot-health-oauth`** — provider-side state (rate-limit, context, quota).
6. **`ntm --robot-snapshot | jq '{sources, degraded_sources}'`** — data-source freshness before acting on any derived state.

If any two layers disagree, resync before acting. See [OBSERVABILITY.md](references/OBSERVABILITY.md) → "Liveness Signals That Can Lie" for the full catalog.

**Never-engaged vs stuck-mid-work (use the stack to tell them apart).** A *never-engaged* pane = CLI running (layer 1 OK) **+ 0.0% CPU on `pane_pid`** (layer 4) **+ no working/thinking indicator + no artifact + no record of an acknowledged first dispatch.** This is almost always a dropped first send (the boot race — see OC-047): the pane booted but the send arrived before its input box rendered. **The fix is RE-DISPATCH (it never received the order), NOT restart.** Distinguish from *stuck-mid-work* (CPU/build active, or an indicator present — leave it, see AP-54) and from *standing-down* (queue-dry by policy). Restarting a never-engaged pane throws away a perfectly healthy CLI.

## Intervention Discipline

Two gates before any state-changing action:

1. **Score it:** `Score = (Evidence × Impact × Reversibility) / BlastRadius`, each 1–5. Only act on Score ≥ 2.0; below that, wait on the attention feed or gather better evidence.
2. **Proof-card it:** evidence, card matched, target, expected state change, reversibility, verification command, next escalation rung. No proof card → no nudge, restart, force-release, or shutdown.

The full scoring matrix with worked examples, the proof-card template, the swarm-pathology trigger table, the three pattern tiers (low-risk tending → directed recovery → session policy changes), the red-flag-phrase classifier, recovery shortcuts, and the troubleshooting table all live in [DECISION-AIDS.md](references/DECISION-AIDS.md).

## Orchestrator Decision Tree

Run one tick. Pick the FIRST branch whose condition fires.

```
Is CURSOR expired (or missing)?
  → ntm --robot-snapshot  (resync, get new cursor); continue next tick.

Is ANY pane rate_limited?  (check via --robot-health-oauth, NOT pane buffer text)
  → OC-001/OC-002 in OPERATOR-CARDS.md: ping-probe first; rotate or switch account
    only if the limit is confirmed provider-side.

Is ANY pane stuck (identical tail ≥3 ticks, zero output growth)?
  → Climb the stuck-pane ladder (OC-003):
    wake-ping → C-u + send → smart-restart → hard-kill → restart-pane → add+kill.

Is there prose-without-commits? (pane is_working=true but git log 1h=0)
  → Dispatch OC-004 Ship-or-Surface prompt (PROMPTS.md).

Is context >85% on any pane?
  → Dispatch handoff-then-restart (OC-009).

Is there a file-reservation conflict or coordinator-reported collision?
  → Force-release too-broad patterns (OC-008); mediate via bead status-flip (OC-015).

Is ANY pane never-engaged?  (CLI running AND 0.0% pane_pid CPU AND no indicator AND no artifact AND no acknowledged first dispatch — typically a bare spawn whose first send lost the boot race)
  → RE-DISPATCH, don't restart (OC-047): confirm input-ready, then re-send the marching orders.

Does convergence triple-check hold?
  ( git log 1h=0 AND br ready=0 AND in-flight unchanged ≥2 ticks AND convergence language in every pane )
  → STOP. Do not nudge. Exit the loop; report final state.

Otherwise — one specific-terse nudge per genuinely-idle pane (OC-010). Then wait.
```

Every card (OC-###) and anti-pattern (AP-###) is documented with recipe, prompt module, and validator in [OPERATOR-CARDS.md](references/OPERATOR-CARDS.md) and [ANTI-PATTERNS.md](references/ANTI-PATTERNS.md).

## Command Surfaces (do not re-learn from here)

- **`atm` is `ntm`.** `atm` (Bo's fork/alias, `~/.local/bin/atm`) is byte-identical to `ntm` — same robot surface, same flags, same exit codes. Every `ntm …` / `ntm --robot-*` form in this skill and its references applies verbatim to `atm`; the out-of-session substrate-runner skill is named `using-atm` for that reason. Use whichever the operator typed; they resolve to one contract.
- **Fresh Claude/Codex duel requests go through ATM panes.** If the operator asks for
  fresh Claude and Codex peers, a cross-family duel, or fresh peer-model
  judgment, spawn the requested panes with `atm spawn` and follow the
  `using-atm` "Fresh Claude/Codex Peer Duels" pattern. Do not route this shape
  through `claude -p` / `claude --print` or ad hoc headless one-shots; the value
  is fresh interactive peer state plus observable pane engagement. Use
  `atm codex preflight`, `atm send --codex-goal`, and
  `atm codex wait-goal-engaged` for the Codex pane, then kill the temporary
  duel session after collecting output.
- **Agents use robot surfaces** (`--robot-snapshot`, `--robot-attention`, `--robot-send`, `--robot-smart-restart`, …); interactive TUIs (`ntm dashboard`, `palette`, `view`) are for humans. The authoritative catalog is `ntm robot-docs` / `ntm --help` — re-query it; see [ROBOT-MODE.md](references/ROBOT-MODE.md) for lanes, transports, and deprecations.
- **Marching orders:** copy-paste dispatch prompts (first dispatch, steady-state, wide-swarm domain assignment, review dispatch) live in [PROMPTS.md](references/PROMPTS.md); the fill-in template is [assets/marching-orders-template.md](https://github.com/boshu2/agentops/blob/main/skills/vibing-with-ntm/assets/marching-orders-template.md). Keep one constraint live: first dispatch claims one scoped item and reserves files/worktree scope; steady-state asks for one commit or one explicit blocker per timebox.
- **Isolation:** default is Agent Mail file reservations + clear bead ownership; `--worktrees` when repo policy allows. Repo-local `AGENTS.md` always wins.
- **Pending-input etiquette:** a pane's input box may hold staged-but-unsent text. Submit it ONLY if it is clearly an orchestrator-staged directive awaiting send. NEVER submit text that reads as the human's live composition — when in doubt, leave it and log the observation.
- **Destructive dialogs:** decline by default; require explicit justification to accept.

## Cadence And Stop Conditions

Tick every 4 minutes during nucleation, 10–17 minutes in steady state, 30 minutes when panes are deep in real work. Stop tending when the convergence triple-check holds across repeated observations. If the queue is dry, do not manufacture tasks — report state, blockers, degraded sources, and residual risk. If coordination surfaces degrade, continue with explicit bead ownership and backfill mail later.

## Review-Only Mode

When the swarm audits rather than implements, flip panes to review-only: no Agent Mail registration, no bead claims, read recent diffs, tag findings by severity, rotate reviewers through study → fresh-eyes → cross-review → continuation passes, kill+relaunch between rounds. Full spec (phase cycle, mixed-swarm ratios, kill-relaunch rhythm, quality rubric, mode-switch prompts) is in [REVIEW-MODE.md](references/REVIEW-MODE.md); Gemini-specific tuning is the `code-review-gemini-swarm-with-ntm` skill.

## Metrics You Report

At closeout, summarize the swarm in concrete deltas:

| Metric | Meaning |
|---|---|
| Commits landed | real work, not pane chatter |
| Beads closed / opened | backlog burn vs review inflation |
| In-flight unchanged ticks | convergence/stall signal |
| Pane interventions | nudges, restarts, rotations, force-releases |
| Degraded sources | mail/CASS/beads/RCH/tool health that shaped decisions |
| Queue state | ready, blocked-only, queue-dry, or active |
| Residual risk | unverified tests, stale locks, partial runs, open blockers |

## Checklist Before Ending A Tending Turn

- [ ] No command sessions needed for the user's request are still running.
- [ ] Active panes are working, blocked with a named blocker, or intentionally stopped.
- [ ] `br ready` / `ntm work queue-dry` state is known.
- [ ] Reservations and Agent Mail state are not silently stale.
- [ ] Any restart/force-release/shutdown has evidence and a verification result.
- [ ] Closeout names commits/beads/tests/blockers, not "the swarm seems fine."

## When To Use / When To Skip

**Use when:** you are the orchestrator of an NTM session with ≥2 panes — unsticking panes, rotating accounts, dispatching marching orders, switching implement↔review modes, judging convergence, or diagnosing cross-session contention.

**Skip when:** you just need the `ntm` command catalog (`$ntm`), single-agent one-pane work, new-machine provisioning (`provision-new-machine`), Beads DB repair (`fixing-beads-problems`), or Gemini review tuning (`code-review-gemini-swarm-with-ntm`). MCP Agent Mail primitives are `$agent-mail`; bead mechanics are `$beads-br`; BV triage is `$beads-bv`; account management is `$account-rotation`.

**Degrees of freedom:** this is a medium-freedom methodology skill — prefer the specific OC/AP card when evidence fires its trigger; fall back to the decision tree otherwise. Following steps without the evidence their triggers require is worse than skipping the card.

## Reference Index

| Topic | Reference |
| --- | --- |
| Robot-mode surfaces, lanes, transports, deprecations (always re-query the binary) | [ROBOT-MODE.md](references/ROBOT-MODE.md) |
| Error taxonomy + autonomous recovery decision tree | [RECOVERY.md](references/RECOVERY.md) |
| Freshness, source health, attention state machine, three-observation rule | [OBSERVABILITY.md](references/OBSERVABILITY.md) |
| Operationalized field-expertise cards (trigger + recipe + prompt + validator) | [OPERATOR-CARDS.md](references/OPERATOR-CARDS.md) |
| Named anti-patterns from real swarm sessions, each with a fix | [ANTI-PATTERNS.md](references/ANTI-PATTERNS.md) |
| Score matrix, proof card, pathology triggers, pattern tiers, red-flag phrases, troubleshooting | [DECISION-AIDS.md](references/DECISION-AIDS.md) |
| /loop, CronCreate, shell cron, schedule; convergence-gated tick scripts | [CRON-AND-AUTOMATION.md](references/CRON-AND-AUTOMATION.md) |
| Review-Only Mode full spec | [REVIEW-MODE.md](references/REVIEW-MODE.md) |
| Marching orders, review prompts, ship-or-surface, close-backlog, autonomous unstick | [PROMPTS.md](references/PROMPTS.md) |
| Spawn mixes, cadence, close/review ratio, convergence termination, domain assignment | [PLAYBOOK.md](references/PLAYBOOK.md) |
| Operator helper scripts (tick snapshot, convergence check, pane liveness, contention sweep) | [scripts/](scripts/) and [scripts/README.md](scripts/README.md) |
| Marching-orders template | [assets/marching-orders-template.md](https://github.com/boshu2/agentops/blob/main/skills/vibing-with-ntm/assets/marching-orders-template.md) |
| Trigger-phrase self-test | [SELF-TEST.md](https://github.com/boshu2/agentops/blob/main/skills/vibing-with-ntm/SELF-TEST.md) |

## Related Skills

| Concern | Skill |
| --- | --- |
| NTM command catalog and work intelligence | `ntm` |
| Agent Mail primitives | `agent-mail` |
| Bead state and dependencies | `br`, `bv` |
| Account rotation and quota | `caam` |
| Multi-model or review swarms | `multi-model-triangulation`, `code-review-gemini-swarm-with-ntm` |

> **Tri-vendor (Opus + Codex + AGY):** worker-only three-pane shape and AGY observability caveats live in [`$dual-pane-atm`](../dual-pane-atm/SKILL.md) (§ Tri-vendor) — reach there before tending an AGY lane.

This skill stays focused on swarm tending decisions: observe, classify, act once, verify, and stop when the evidence says stop.

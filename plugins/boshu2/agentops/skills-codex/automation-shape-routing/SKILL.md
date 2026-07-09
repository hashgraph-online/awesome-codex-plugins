---
name: automation-shape-routing
description: Front door for agent automation — decide the
---
# Automation Shape Routing — Workflow vs ATM vs Skill

> **HEADLINE TRAP — don't orchestrate a one-shot task.** Before standing up ANY
> ATM swarm or Workflow, ask: *is this a reusable automation, or a single
> deliverable I just need produced once?* A one-off task ("generate 9 content
> ideas", "draft this section", "summarize these files") is **not** an
> automation — orchestrating it stands up machinery that costs more time than
> the task. The verdict for a one-shot is **shape 0** below: do it inline, or
> fan out 2–3 in-session Agent subagents. **Real failure (2026-06-15):** an
> operator pointed a heavy ATM-codex swarm at a ~9-idea content task; it wedged
> on codex boot and cost more than doing it inline would have. In-session
> Agent fan-out later worked in one pass. If you are reaching for ATM or a
> Workflow, confirm you are not here.
>
> **The other trap this kills:** "I built a lot of skills; they should become
> workflows." Mostly false. Most orchestration-looking skills are either
> long-lived/human-attachable (stay ATM) or hard-sequential (stay skills). The
> win is the routing rule, not a migration project.

## The three shapes

| Shape | What it is | Mechanism |
|---|---|---|
| **Shape 0 — inline / in-session fan-out** | A one-shot deliverable, not a reusable automation | Just do the task inline. If you want independent drafts / fresh eyes, fan out 2–3 in-session **Agent** subagents (lightest parallel path — no persistence, no worktrees, read-only-friendly, dies with the session). **No ATM, no Workflow, no SKILL.md authored.** This is the target of axis-1 "no orchestration." |
| **Workflow** | Deterministic, reproducible orchestration of subagents | Claude `Workflow` tool — `agent({schema})`, `parallel()`, `pipeline()`, `phase()`, loop-until-budget. In-process, headless, ~16 concurrent. |
| **ATM swarm** | Long-lived, human-in-the-loop multi-agent run | `atm` (the CLI) driven by [`$using-atm`](../using-atm/SKILL.md) — persistent tmux panes running whole `$rpi`/`$evolve` loops over a bead queue, with attach + nudge + kill/relaunch and mail/locks coordination. |
| **Plain skill** | One model reasoning through a *reusable* procedure or knowledge | A single `SKILL.md` — authored only when the procedure will be **re-run**. No fan-out, or a strictly sequential edit-loop. *Not* the home for a one-off task; that's shape 0. |

## The decision rule (axes)

**Litmus zero — reusable automation, or a one-shot? Ask this FIRST.** Are you
building something that will be **re-run**, or just producing **one deliverable**?
One-shot → **shape 0: do not route. Do the task inline, or fan out 2–3 in-session
Agent subagents.** Don't stand up ATM or a Workflow for a single deliverable.
Only continue to the axes below if the answer is "reusable automation."

Then ask in order:

1. **Is there real orchestration at all?** (fan-out / barrier / multi-stage, OR a
   loop with parallelism to exploit) — if **no** → **shape 0** (inline / Agent
   fan-out) for a one-off, or **plain skill** if it's a reusable procedure. Stop.
2. **Must a human attach and steer mid-run?** Or does it run for *hours*, do
   open-ended *file edits*, juggle a *fluid population* (rate limits, kill/
   relaunch, prompt-cache rounds), or relay between *cross-model* panes? — if
   **yes** → **ATM swarm**.
3. Otherwise — fixed DAG, agents return **structured JSON** (not free-form edits
   needing review), no attach needed, you want it **reproducible + headless** →
   **Workflow**.

**Cost-check on axes 2–3 (before committing to fan-out).** Parallel buys
*independence / fresh eyes*, **not wall-clock at small N** — a measured 3-way
fan-out **tied** a single sequential agent (191s vs 180s) and cost **~2.7× the
tokens**, because the synthesis barrier eats the parallel gain. So at small N,
parallel is a tax unless you actually want independent verification. If you just
want the answer once, the cheapest correct shape is **shape 0** — often a single
inline pass. (Full evidence under "Spike-validated nuances" below.)

**One-line litmus:**
> one-shot deliverable, not reusable → **shape 0** (inline / in-session Agent fan-out)
> deterministic DAG + structured JSON + no human-attach + headless-wanted → **Workflow**
> long-lived + attachable + open-ended file edits / fluid population → **ATM**
> reusable procedure, no fan-out, or hard-sequential edit loop → **plain skill**

**Zeroth question, before the three axes:** is this an automation at all, or a
*constraint* — a "must never regress" rule promoted from a learning? A constraint
is not a process to run; it is a check that blocks. Shape = **gate**: a warn-only
script under `scripts/` + a bats case, flipped to blocking after a soak (the
ratchet ladder's rungs 3-4). Route it through `operationalize` (its `gate`
route target), not through the three shapes below.

## Spike-validated nuances (2026-05-29)

A live three-legged spike (`~/dev/agentops-3cat-spike/`) measured the same task on
all three backends. Two findings refine the rule:

1. **The primary axis is control-plane vs in-session, not "parallel vs serial."**
   **ATM is a control-plane** that *runs Claude/Codex/Gemini as panes* — it is not a
   peer of the native runtimes, it is the supervisor tier above them. Choose ATM when
   you need the control plane (attach/steer, persistence, multi-vendor); choose
   in-session native (Workflow/Task) when you don't.
2. **Parallel buys quality/independence, NOT wall-clock — at small N.** Measured: a
   3-way Workflow fan-out **tied** a single sequential agent on wall-clock (191s vs
   180s) and cost **~2.7× the tokens** — because the synthesis barrier eats the
   parallel gain. What it bought was depth + independent fresh-eyes (the sequential
   leg self-reported "monoculture" bias). So: reach for parallel `Workflow` when you
   want *independent verification / fresh eyes*, not for speed. For speed, you need
   large N **and** no barrier — use `pipeline()` (no barrier), not `parallel()`.

Degradation (ATM → Claude-native → beads floor) is governed by the
`OrchestrationPort` selector; opt out entirely with `AGENTOPS_ORCHESTRATION=off` →
beads floor, which always works.

## Two traps to avoid

- **Don't workflow-ify a sequential edit-loop.** If each pass must see the prior
  pass's edits (progressive-deepening reapply, audit-fix-rescan), there's no
  concurrency to win — a Workflow wrapper adds a process boundary for nothing.
  *Exception:* it graduates to a `loop-until-budget` Workflow only once each step
  returns **structured output** instead of free-form edits, and you want it
  headless/reproducible.
- **Don't ATM-ify a clean fan-out, and don't Workflow-ify an attach-and-steer
  run.** The Workflow tool is in-process and cannot be tmux-attached; ATM is
  built for exactly the live-steering Workflow can't do. Picking wrong fights the
  tool the whole way.

## Worked examples

**→ Workflow** (deterministic fan-out / synthesize, structured returns):
`council` (N judges → consensus — near-trivial port), the **planning half** of
`rpi`, judge/refutation panels, any "fan out N analyses → triangulate" task.

**→ Stay ATM** (long-lived, attachable, open-ended edits, fluid population):
the `*-with-atm` family (hypothesis research, cross-model review swarms, browser
testing), plus `swarm`/`crank` in full epic-execution mode — they touch the
working tree and need wave-validity gating + human review.

**→ Stay plain skill** (no exploitable parallelism, or knowledge/one-shot):
deliberately one-at-a-time loops (progressive reapply, multi-pass bug hunting);
all reference docs; all single-shot transforms (jargon scrub, README authoring).

## Canonical Workflow template

`.codex/workflows/operating-loop.js` is the worked example — a real Workflow-tool
script using `agent(prompt,{schema})` with JSON schemas, `parallel([thunks])`
barriers (framing-lenses / judges / refutation / slices), `phase()` markers,
budget-scaled `FANOUT`, and bounded re-plan/retry. **Start from it when porting a
Workflow.** It is also the proof that the AgentOps operating loop has *two*
conformant runtimes (skill-driven via `rpi`/`crank`/`swarm`/`council`, and
Workflow-driven via this script) — the basis of the `agentops-core-sdk`
portability thesis. See `operating-loop-workflow` for the install+run path.

## Handoff — after the verdict, invoke the next skill

This skill is the **front door**. It does not build; it routes. Once the shape is
decided, hand off:

| Verdict | Next | What it does |
|---|---|---|
| **shape 0 (one-shot)** | *(no builder — stop routing)* | Do the task inline, or fan out 2–3 in-session Agent subagents for independent drafts. Author nothing. |
| **plain skill** | `skill-builder` | Scaffold a new `SKILL.md` against the unified template → then `skill-auditor` → `heal-skill`. |
| **Workflow** | `workflow-builder` | Scaffold a new `.codex/workflows/*.js` from the operating-loop.js template. |
| **ATM swarm** | `atm` + [`$using-atm`](../using-atm/SKILL.md) | Stand up + tend an ATM swarm running AgentOps loops (`$rpi`/`$evolve`) over a bead queue. |
| **gate** | [`operationalize`](../operationalize/SKILL.md) (`gate` route) | Emit a warn-only check script + bats case + CI wiring; flip to blocking after soak. For promoted must-never-regress learnings. |

State the verdict and the deciding axis in one line, then invoke the chosen
builder. Do not scaffold here.

## Contract note (SDK)

A Workflow is a **composite capability** (an orchestration of sub-capabilities
with typed control flow); a skill is a **leaf**. The portable contract for this —
a `shape: skill|workflow` discriminator, a `StepGraph`, a `control_flow` enum, a
`budget`, and an `OrchestrationPort` *interface* — is net-new SDK work. Port the
**shape, not the engine**: keep concrete orchestrators (Codex subagents, swarm
dispatch, scheduler — BC4/BC5) behind adapters.

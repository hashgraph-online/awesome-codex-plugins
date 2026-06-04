---
name: automation-shape-routing
description: 'Front door for agent automation: route to the right builder.'
---
# $automation-shape-routing — Orchestration vs NTM vs Skill

> **The trap this kills:** "I built a lot of skills; they should become
> orchestration scripts." Mostly false. Most orchestration-looking skills are
> either long-lived/human-attachable (stay NTM) or hard-sequential (stay skills).
> The win is the routing rule, not a migration project.

## The three shapes

| Shape | What it is | Mechanism |
|---|---|---|
| **Orchestration** | Deterministic, reproducible fan-out / pipeline / loop over sub-agents, each returning structured output | Codex orchestration — `codex exec` driving `spawn_agents` (parallel fan-out), staged pipelines, and loop-until-budget, with an `output_schema` per sub-agent. Headless, reproducible, bounded concurrency. |
| **NTM swarm** | Long-lived, human-in-the-loop multi-agent run | `ntm` (the CLI) driven by $using-ntm — persistent tmux panes running whole $rpi/$evolve loops over a bead queue, with attach + nudge + kill/relaunch and mail/locks coordination. |
| **Plain skill** | One model reasoning through a procedure or knowledge | A single `SKILL.md`. No fan-out, or a strictly sequential edit-loop. |

## The decision rule (three axes)

Ask in order:

1. **Is there real orchestration at all?** (fan-out / barrier / multi-stage, OR a
   loop with parallelism to exploit) — if **no** → **plain skill**. Stop.
2. **Must a human attach and steer mid-run?** Or does it run for *hours*, do
   open-ended *file edits*, juggle a *fluid population* (rate limits, kill/
   relaunch, prompt-cache rounds), or relay between *cross-model* panes? — if
   **yes** → **NTM swarm**.
3. Otherwise — fixed DAG, sub-agents return **structured JSON** (not free-form
   edits needing review), no attach needed, you want it **reproducible + headless**
   → **Orchestration**.

**One-line litmus:**
> deterministic DAG + structured JSON + no human-attach + headless-wanted → **Orchestration**
> long-lived + attachable + open-ended file edits / fluid population → **NTM**
> no fan-out, or hard-sequential edit loop → **plain skill**

## Spike-validated nuances (2026-05-29)

A live three-legged spike (`~/dev/agentops-3cat-spike/`) measured the same task on
all three backends. Two findings refine the rule:

1. **The primary axis is control-plane vs in-session, not "parallel vs serial."**
   **NTM is a control-plane** that *runs Claude/Codex/Gemini as panes* — it is not a
   peer of the native runtimes, it is the supervisor tier above them. Choose NTM when
   you need the control plane (attach/steer, persistence, multi-vendor); choose
   in-session native orchestration (`codex exec` + `spawn_agents`) when you don't.
2. **Parallel buys quality/independence, NOT wall-clock — at small N.** Measured: a
   3-way parallel fan-out **tied** a single sequential agent on wall-clock (191s vs
   180s) and cost **~2.7× the tokens** — because the synthesis barrier eats the
   parallel gain. What it bought was depth + independent fresh-eyes (the sequential
   leg self-reported "monoculture" bias). So: reach for a parallel fan-out when you
   want *independent verification / fresh eyes*, not for speed. For speed, you need
   large N **and** no barrier — use a streaming pipeline (no barrier), not a
   collect-all barrier.

Degradation (NTM → native → beads floor) is governed by the
`OrchestrationPort` selector; opt out entirely with `AGENTOPS_ORCHESTRATION=off` →
beads floor, which always works.

## Two traps to avoid

- **Don't orchestrate a sequential edit-loop.** If each pass must see the prior
  pass's edits (progressive-deepening reapply, audit-fix-rescan), there's no
  concurrency to win — an orchestration wrapper adds a process boundary for
  nothing. *Exception:* it graduates to a loop-until-budget orchestration only once
  each step returns **structured output** instead of free-form edits, and you want
  it headless/reproducible.
- **Don't NTM-ify a clean fan-out, and don't orchestrate an attach-and-steer run.**
  Headless orchestration runs in-process and cannot be tmux-attached; NTM is built
  for exactly the live-steering headless orchestration can't do. Picking wrong
  fights the tool the whole way.

## Worked examples

**→ Orchestration** (deterministic fan-out / synthesize, structured returns):
`council` (N judges → consensus — near-trivial port), the **planning half** of
`rpi`, judge/refutation panels, any "fan out N analyses → triangulate" task.

**→ Stay NTM** (long-lived, attachable, open-ended edits, fluid population):
the `*-with-ntm` family (hypothesis research, cross-model review swarms, browser
testing), plus `swarm`/`crank` in full epic-execution mode — they touch the
working tree and need wave-validity gating + human review.

**→ Stay plain skill** (no exploitable parallelism, or knowledge/one-shot):
deliberately one-at-a-time loops (progressive reapply, multi-pass bug hunting);
all reference docs; all single-shot transforms (jargon scrub, README authoring).

## Canonical orchestration shape

The operating loop is the worked example — a deterministic orchestration that
drives `codex exec` over `spawn_agents` with a per-sub-agent `output_schema`
(structured JSON, not free-form edits), parallel fan-out barriers (framing-lenses
/ judges / refutation / slices), explicit phase markers, budget-scaled fan-out
width, and bounded re-plan/retry. **Start from this shape when authoring an
orchestration.** It is also the proof that the AgentOps operating loop has *two*
conformant runtimes (skill-driven via `rpi`/`crank`/`swarm`/`council`, and
orchestration-driven via `codex exec` + `spawn_agents`) — the basis of the
`agentops-core-sdk` portability thesis. Hand off to `$workflow-builder` for the
authoring path.

## Handoff — after the verdict, invoke the next skill

This skill is the **front door**. It does not build; it routes. Once the shape is
decided, hand off:

| Verdict | Next | What it does |
|---|---|---|
| **plain skill** | `$skill-builder` | Scaffold a new `SKILL.md` against the unified template → then `$skill-auditor` → `$heal-skill`. |
| **Orchestration** | `$workflow-builder` | Author a deterministic `codex exec` + `spawn_agents` orchestration with per-sub-agent `output_schema`. |
| **NTM swarm** | `ntm` + $using-ntm | Stand up + tend an NTM swarm running AgentOps loops ($rpi/$evolve) over a bead queue. |

State the verdict and the deciding axis in one line, then invoke the chosen
builder. Do not scaffold here.

## Contract note (SDK)

An orchestration is a **composite capability** (a composition of sub-capabilities
with typed control flow); a skill is a **leaf**. The portable contract for this —
a `shape: skill|workflow` discriminator, a `StepGraph`, a `control_flow` enum, a
`budget`, and an `OrchestrationPort` *interface* — is net-new SDK work. Port the
**shape, not the engine**: keep concrete orchestrators (Codex sub-agents, swarm
dispatch, scheduler — BC4/BC5) behind adapters.

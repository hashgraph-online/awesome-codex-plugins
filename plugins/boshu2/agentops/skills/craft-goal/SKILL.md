---
name: craft-goal
description: 'Draft or lint a bounded long-running goal prompt with a finish line and hard limits. Use when: selected by name; one change goes to Plan.'
practices:
- lean-startup
- design-by-contract
skill_api_version: 1
hexagonal_role: supporting
consumes:
- caller-outcome
- goal-acceptance
produces:
- outer-goal-prompt
- goal-safety-report
context_rel:
- kind: supplier-to
  with: plan
user-invocable: true
disable-model-invocation: true
context:
  window: inherit
  intent:
    mode: task
metadata:
  tier: judgment
  dependencies: []
  capabilities: ["goal_prompt_design","goal_prompt_lint"]
  effects: []
  canonical_status: canonical
  disposition: keep_strategy
  stability: stable
output_contract: 'human-readable SAFE_TO_CREATE, USE_RPI, or UNSAFE_GOAL decision; copy-paste outer-goal prompt when safe; exact budgets, assumptions, and lint findings'
---

# Craft Goal

Craft or lint the autonomy contract above AgentOps RPI. A goal is a persistent
controller (the Goal / Mayor role) over a bead-shaped experiment graph: each
RPI is one scientific trial, and the goal picks the next useful trial,
preserves what was learned and ratchets toward a larger outcome.

```text
Goal / Mayor: observe graph → choose bounded wave → consume results → ratchet
  └─ Bead: durable experiment intent, context, scratch, evidence, and links
       └─ RPI: plan → implement → checks → one fresh validate where a mistake is costly → report
            └─ Implementation: one RED → GREEN → refactor experiment
```

The number of RPIs need not be known in advance. A goal is safe when success
is decidable, every experiment is bounded, evidence keeps its provenance, and
the authorization envelope cannot silently renew itself. Beliefs are
revisable: new evidence may retract an earlier claim. More stored knowledge is
neither progress nor proof that knowledge is correct.

**Authority boundary.** The emitted prompt and safety report are inert
caller-owned text. Crafting creates no goal, starts no runtime, mutates no
bead and confers no standing authorization. The prompt drives RPI dispatch
only when a caller pastes it into their own goal runtime, under their own
authority and within the non-renewing envelope they set. Craft Goal reads
tracker state when present but needs no tracker installed to compile a prompt.

## Modes

| Caller wording | Mode | Result |
|---|---|---|
| "craft a goal", "turn this into a goal" | craft | Decision, then the filled goal prompt and settings when safe. |
| "lint/review this goal", "is this safe" | lint | Decision and findings, plus a rewrite when supplied facts permit one. |

## Admission: decide first

**Fuzzy route is acceptable; fuzzy success is not.** Before goal creation the
caller must know the outcome, what evidence would prove it, non-goals, and
authority; the exact experiment graph may still be unknown. Write each
terminal criterion as a Given/When/Then with an observable result and name
each domain term once; the caller can settle these with Interview first.

- `USE_RPI`: one shaped experiment with no verdict-driven follow-on.
- `SAFE_TO_CREATE`: a terminal outcome that may need several related
  experiments, with those decisions and the budgets below supplied. A shaped
  goal with no beads may begin with 1 bounded discovery wave that creates the
  root and initial experiment beads.
- `UNSAFE_GOAL`: no falsifiable first question or terminal evidence can be
  named (route that intent to idea or plan work), or the request is indefinite
  monitoring or event reaction, which is an automation, not a terminal goal.

Goals come in different sizes: size the wave and hard envelopes to the
outcome, never to one universal budget. Do not invent acceptance, authority,
graph semantics or campaign size; return `UNSAFE_GOAL` with the missing
decisions. The caller owns revision and goal creation.

## What a safe goal holds

- **Closed outcome, adaptive route.** Freeze terminal acceptance. New facts may
  change hypotheses and dependencies, never silently enlarge success.
- **Bead graph as memory.** The tracker is durable memory, not a parallel goal
  ledger: root epic = outer intent; child bead = one experiment and one RPI,
  so compaction cannot erase the record. [Navigate](../navigate/SKILL.md) owns
  the walk the prompt applies each wave: graph contract, edges, what counts as
  a ratchet, discovery classes and the checkpoint.
- **RPI membrane.** One candidate gets one bounded RPI. Its checks and CI are
  the result for an ordinary bead. A bead gets one author-distinct fresh
  validation only when the caller asks, a mistake cannot be cheaply undone
  after it lands, or no deterministic check covers the changed behavior; a
  repair does not start another. The goal may request durable verdict evidence
  but never rewrites it: orchestration cannot author its own proof, and a
  review per bead multiplies cost across the whole graph.
- **Ratchet, not churn.** Continue only while a result adds non-duplicative,
  decision-relevant knowledge or advances acceptance, and the next experiment
  fits frozen acceptance, authority and the remaining envelope.
- **Two-level bounds.** Every RPI and every wave is bounded, and the full goal
  has monotonic hard ceilings. Bounded waves shorten the feedback loop; the
  one non-renewing campaign envelope keeps a new wave from minting a new
  campaign.
- **Earned andon.** Ordinary informative red may change the route within
  frozen acceptance. Repeated no-information failure, regression, recurrence,
  oscillation or scope pressure enters HOLD.
- **Operator legibility.** Each wave boundary reports the acceptance matrix,
  graph frontier, verdicts, ratchets, churn, remaining budget and next thesis.
- **Exterior self-repair.** Repair an unstable factory from an ordinary shell
  or worktree; use the factory only for a declared bounded canary.

The two failure modes this prevents: the **completion treadmill**, where
discoveries keep becoming requirements and activity continues without new
information, and **first-red abandonment**, where one falsified hypothesis
ends a viable campaign.

## Budgets and HOLD

Declare both envelopes with numbers before any work is selected, helper and
validation costs included:

- **Wave:** RPIs, concurrency, wall time or tokens, live attempts, and a
  checkpoint at its end.
- **Goal:** total RPIs, wall time or tokens, live attempts, compactions, and
  any patch or surface limit for the whole campaign.

Name the native control that enforces each claimed hard limit and how the
remaining allowance is observed. Objective text is an instruction, not
enforcement: never report an unmeasured aggregate as a remaining balance, and
never claim the goal is paused from prose alone. No helper, retry, new
subject, compaction or wave renews the goal allowance.

Enter HOLD on any declared trigger: repeated blocker, no ratchet for the
configured number of RPIs, oscillation between prior approaches, introduced
regression, unknown new-defect cause, recurrence, requested acceptance change,
or operator-reserved decision. HOLD stops implementation for causal
examination. While the remaining allowance admits it, consult exactly 1
bounded fresh-context helper per HOLD incident, supplying acceptance,
observations, failed approaches, exact evidence and remaining allowance.
Rewording the blocker or an automatic continuation is not a new incident.

- `UNSTUCK` must name a materially different experiment, its discriminating
  check, and why it fits unchanged acceptance, authority and remaining bounds;
  only the selected outer goal may resume, and it never revives a spent RPI
  bound.
- `ESCALATE`, an unhelpful helper or no admissible experiment emits
  `NEEDS_OPERATOR`; no more implementation or helper dispatch follows.
- Cancellation stops immediately. An explicit refusal or judgment lane, or a
  genuinely spent hard time, cost or quota ceiling, skips the helper and
  reports the refusal or `NOT_ACHIEVED` with the exact gaps. A retry threshold
  alone is not proof of a spent hard budget.

When operator action is required, report it truthfully and keep work stopped.
A controller's threshold for recording `blocked` is status bookkeeping, never
permission for extra experiments or helpers.

## Lint rubric

| Dimension | Passes when the prompt |
|---|---|
| outcome | names one larger caller-visible result. |
| evidence | gives each terminal criterion as a Given/When/Then with its authoritative proof. |
| admission | fits a goal: several related experiments, a falsifiable first question, a terminal finish. |
| bead graph | names the root epic or its bounded bootstrap rule and ties each experiment to an unmet criterion or named blocking uncertainty. |
| RPI boundary | makes one bead one RPI, takes checks and CI as an ordinary bead's result, limits fresh validation to the costly cases and consumes verdicts unchanged. |
| ratchet | counts progress only as evidence tied to an unmet criterion or blocking uncertainty, never activity, counts or digests. |
| discovery | keeps all three classes (necessary-now, linked-follow-up, HOLD/rescope) and never downgrades a necessary finding. |
| wave budget | sets numeric RPI, concurrency, time or token and live-attempt limits per wave, with a checkpoint. |
| hard budget | sets numeric campaign totals that nothing resets, naming the enforcing control or the unmeasured aggregate. |
| breaker | sets the numeric no-ratchet threshold and the HOLD triggers. |
| operator andon | allows one helper per HOLD incident, maps `UNSTUCK` and `ESCALATE`, and stops implementation on `NEEDS_OPERATOR`. |
| scope | states non-goals and exact read, write, external and Git authority. |
| self-hosting | repairs an unstable factory from outside it and runs the factory only as a declared bounded canary. |
| terminal reports | defines `ACHIEVED`, `NOT_ACHIEVED` and `NEEDS_OPERATOR`. |

## Output

Fill [the copy-paste-only goal prompt](references/goal-prompt.md): keep its
headings and terminal semantics and replace every angle-bracket field. Return,
in order:

1. A first line that starts with exactly one decision: `SAFE_TO_CREATE`,
   `USE_RPI` or `UNSAFE_GOAL`. `SAFE_TO_CREATE` judges prompt content; it does
   not certify native enforcement or create a goal.
2. For `UNSAFE_GOAL`, each missing decision; the caller can settle them with
   Interview.
3. When safe, the filled prompt, a separate goal-tool token budget, and the
   assumptions made.
4. One lint line per rubric dimension: pass, or the finding.

## Stop

This skill makes one pass, craft or lint, then returns. It never creates or
runs a goal and never mutates beads. The goal it writes stops at its first
terminal report: `ACHIEVED`, `NOT_ACHIEVED` or `NEEDS_OPERATOR`.

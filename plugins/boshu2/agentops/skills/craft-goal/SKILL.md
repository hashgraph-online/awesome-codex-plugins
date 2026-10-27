---
name: craft-goal
description: 'Draft or lint a bounded long-running goal prompt with a finish line and hard limits. Use when: asked to craft or lint a goal (a /goal prompt); one change goes to Plan.'
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

Craft or lint a goal prompt: the contract a long-running goal runtime follows
over a bead graph, picking each next experiment (one build bead) until a
frozen finish line is proven or a limit stops it. The number of experiments
need not be known in advance. A goal is safe when success is decidable, every
experiment is bounded, evidence keeps its provenance, and the authorization
envelope cannot silently renew itself.

**Authority boundary.** The emitted prompt and safety report are inert
caller-owned text. Crafting creates no goal, starts no runtime, mutates no
bead and confers no standing authorization. The prompt drives work only when
a caller pastes it into their own goal runtime, under their own authority and
within the non-renewing envelope they set. Craft Goal reads tracker state when
present and needs no tracker installed to compile a prompt; the goal it writes
runs on one.

Asked to craft ("craft a goal", "turn this into a goal"), return the decision,
then the filled prompt and settings when safe. Asked to lint ("lint/review
this goal", "is this safe"), return the decision and findings, plus a rewrite
when supplied facts permit one.

## Admission: decide first

**Fuzzy route is acceptable; fuzzy success is not.** Before goal creation the
caller must know the outcome, what evidence would prove it, non-goals,
authority, and the tracker the goal runs on (any with status, dependencies and
notes; BD is one); the exact experiment graph may still be unknown. Write each
terminal criterion as a Given/When/Then with an observable result and name
each domain term once; the caller can settle these with Interview first.

- `USE_RPI`: one shaped change with no verdict-driven follow-on; hand it to
  [Plan](../plan/SKILL.md) or native execution (RPI only if the caller selects it).
- `SAFE_TO_CREATE`: a terminal outcome that may need several related
  experiments, with those decisions and the budgets below supplied. A shaped
  goal with no beads may begin with 1 bounded discovery wave that creates the
  root and initial experiment beads.
- `UNSAFE_GOAL`: no falsifiable first question or terminal evidence can be
  named (route that intent to idea or plan work), or the request is indefinite
  monitoring or event reaction, which is an automation, not a terminal goal.

Goals come in different sizes: size the wave and hard envelopes to the
outcome, never to one universal budget. Do not invent acceptance, authority,
graph semantics, tracker or campaign size; return `UNSAFE_GOAL` with the
missing decisions. The caller owns revision and goal creation.

## What a safe goal holds

- **Closed outcome, adaptive route.** Freeze terminal acceptance. New facts may
  change hypotheses and dependencies, never silently enlarge success.
- **Bead graph as memory.** The tracker is durable memory, not a parallel goal
  ledger: the root epic holds outer intent and each build bead one experiment,
  so compaction cannot erase the record. A decision bead resolves through the
  method Navigate names for it, not through a build.
  [Navigate](../navigate/SKILL.md) owns the walk each wave applies: graph
  contract, ratchet, discovery classes and checkpoint.
- **Proof stays outside the goal.** The goal consumes each verdict unchanged:
  orchestration cannot author its own proof. Fresh validation is for
  [Validate's costly cases](../validate/SKILL.md#when-a-fresh-judgment-is-worth-it)
  only, since a review per bead multiplies cost across the graph.
- **Two-level bounds.** Every experiment and every wave is bounded, and the
  whole goal has monotonic hard ceilings, so a new wave cannot mint a new
  campaign.

The template's experiment policy and breaker carry these into the runtime.
They prevent the **completion treadmill**, where discoveries keep becoming
requirements and activity continues without new information, and
**first-red abandonment**, where one falsified hypothesis ends a viable
campaign.

## Budgets and HOLD

Declare both envelopes with numbers before any work is selected, helper and
validation costs included:

- **Wave:** experiments, concurrency, wall time or tokens, live attempts, and
  a checkpoint at its end.
- **Goal:** total experiments, wall time or tokens, live attempts, compactions,
  and any patch or surface limit for the whole campaign.

Name the native control that enforces each claimed hard limit and how the
remaining allowance is observed. Objective text is an instruction, not
enforcement: never report an unmeasured aggregate as a remaining balance, and
never claim the goal is paused from prose alone. No helper, retry, new
subject, compaction or wave renews the goal allowance.

The template's **Breaker and helper** section is the one list of HOLD triggers
(implementation stops for causal review) and helper rules; fill its threshold
and keep every line.

## Lint rubric

| Dimension | Passes when the prompt |
|---|---|
| outcome | names one larger caller-visible result. |
| evidence | gives each terminal criterion as a Given/When/Then with its authoritative proof. |
| domain terms | defines each domain term once and reuses only that word. |
| admission | fits a goal: several related experiments, a falsifiable first question, a terminal finish. |
| bead graph | names the tracker and the root epic or its bounded bootstrap rule, and ties each experiment to an unmet criterion or named blocking uncertainty. |
| experiment boundary | makes one build bead one bounded experiment (native execution, or one RPI when the caller selects it; decision beads resolve as Navigate names), takes checks and CI as an ordinary bead's result, limits fresh validation to the costly cases and consumes verdicts unchanged. |
| ratchet | counts progress only as evidence tied to an unmet criterion or blocking uncertainty, never activity, counts or digests. |
| discovery | keeps all three classes (necessary-now, linked-follow-up, HOLD/rescope) and never downgrades a necessary finding. |
| wave budget | sets numeric experiment, concurrency, time or token and live-attempt limits per wave, with a checkpoint. |
| hard budget | sets numeric campaign totals that nothing resets, naming the enforcing control or the unmeasured aggregate. |
| breaker | sets the numeric no-ratchet threshold and every HOLD trigger in the template's breaker. |
| helper | sends a requested acceptance change or operator-reserved decision straight to `NEEDS_OPERATOR`, allows at most one helper per other HOLD incident, maps `UNSTUCK` and `ESCALATE`, and stops implementation on `NEEDS_OPERATOR`. |
| scope | states non-goals and exact read, write, external and Git authority. |
| self-hosting | is n/a unless the goal repairs the factory (agent system) it runs on; then its authority repairs from an ordinary shell or worktree and runs that factory only as a declared bounded canary. |
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
3. When safe, the filled prompt; the settings: for each hard limit, the native
   control the caller sets to enforce it (such as the goal runtime's own token
   cap), or that it stays unmeasured; and the assumptions made.
4. Lint lines. In lint mode, one per rubric dimension: pass, n/a, or the
   finding. In craft mode, only the rows the draft still fails; each is a
   missing decision, so the decision cannot be `SAFE_TO_CREATE`.

## Stop

This skill makes one pass, craft or lint, then returns. It never creates or
runs a goal and never mutates beads. The goal it writes stops at its first
terminal report: `ACHIEVED`, `NOT_ACHIEVED` or `NEEDS_OPERATOR`.

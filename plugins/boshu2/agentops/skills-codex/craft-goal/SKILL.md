---
name: craft-goal
description: 'Compile or lint a persistent Mayor-style Triggers: "craft a goal prompt", "mayor goal", "goal-runner prompt", "lint this goal", "is this goal safe". (Shaping one experiment''s intent routes to plan.)'
---
# Craft Goal

Craft the autonomy contract above AgentOps RPI. A goal is a persistent
Mayor over a bead-shaped experiment graph. Each RPI is one scientific trial;
the goal selects the next useful trial, preserves what was learned, and
ratchets toward a larger outcome.

```text
Goal / Mayor: observe graph → choose bounded wave → consume verdicts → ratchet
  └─ Bead: durable experiment intent, context, scratch, evidence, and links
       └─ RPI: plan → implement → fresh validate → verdict → report and stop
            └─ Implementation: one RED → GREEN → refactor experiment
```

The number of RPIs need not be known in advance. The goal is safe when success
is decidable, every experiment is bounded, knowledge is monotonic, and the
authorization envelope cannot silently renew itself.

**Insight:** bounded waves shorten the feedback loop; one hard, non-renewing
campaign envelope prevents those waves from becoming infinite continuation.

**Authority boundary.** The emitted goal prompt and safety report are inert
caller-owned text. Crafting one creates no goal, starts no runtime, and mutates
no bead; it confers no standing authorization. The prompt drives RPI dispatch
only when a caller pastes it into their own goal runtime under their own
authority, and only within the non-renewing envelope the caller then sets.

Named failure mode — **completion treadmill**: discoveries recursively become
requirements and activity continues without new information. Its opposite is
**first-red abandonment**: one falsified hypothesis ends a viable campaign.
Anti-pattern: choose endless retries or stop on the first red. Corrective:
continue while experiments produce a defined ratchet and remain
inside the envelope; invoke an andon on churn, judgment, or exhaustion.
Stop when the goal reports `ACHIEVED`, `NOT_ACHIEVED`, or `NEEDS_OPERATOR`.

## Modes

| Caller wording | Mode | Result |
|---|---|---|
| "craft a goal", "turn this into a goal" | craft | Compile a Mayor-style goal prompt and settings. |
| "lint/review this goal", "is this safe" | lint | Return findings and a rewrite when supplied facts permit one. |

Stop after 1 compilation pass. Never create a goal or mutate beads.

## Admission and sizing

**Fuzzy route is acceptable; fuzzy success is not.** Before goal creation, the
caller must know the outcome, what evidence would prove it, non-goals, and
authority. The exact experiment graph may still be unknown.

- Return `USE_RPI` for one shaped experiment with no verdict-driven follow-on.
- Use a goal for a terminal outcome that may need several related experiments.
- A shaped goal with no beads may begin with 1 bounded discovery wave that
  creates the root and initial experiment beads.
- Return `UNSAFE_GOAL` when no falsifiable first question or terminal evidence
  can be named. Route that intent to idea/plan work.
- Return `UNSAFE_GOAL` for indefinite monitoring or event reaction; that is an
  automation, not a terminal goal.

Goals may be different sizes. Size the wave and hard campaign envelopes to the
outcome; do not invent one universal budget.

## Critical constraints

- **Closed outcome, adaptive route:** Freeze terminal acceptance. New facts may
  change hypotheses and dependencies, never silently enlarge success.
  **Why:** discovery should steer the route, not redefine the finish line.
- **Bead knowledge graph:** Use the tracker as durable memory, not a parallel
  goal ledger. Root epic = outer intent; child bead = one experiment/RPI.
  **Why:** compaction must not erase the scientific record.
- **RPI membrane:** One candidate gets one bounded RPI and an author-distinct
  fresh validation result. The goal may request durable verdict evidence but
  never rewrites it.
  **Why:** orchestration cannot author its own proof.
- **Brownian ratchet:** Continue only when a result adds non-duplicative,
  decision-relevant knowledge or advances acceptance. **Why:** activity without
  information is churn.
- **Two-level bounds:** Every RPI is bounded; every dispatch wave is bounded;
  the full goal also has monotonic hard ceilings. **Why:** a new wave must not
  mint a new campaign.
- **Earned andon:** Ordinary red may change the route. Repeated no-information
  failure, oscillation, scope pressure, or exhaustion enters HOLD and gets
  exactly 1 bounded fresh helper before `UNSTUCK` or `ESCALATE`.
- **Operator legibility:** At each wave boundary, report the acceptance matrix,
  graph frontier, verdicts, ratchets, churn, remaining budget, and next thesis.
- **Exterior self-repair:** Repair an unstable factory from an ordinary
  shell/worktree and use the factory only for a declared bounded canary.

Stop when the goal reports `ACHIEVED`, `NOT_ACHIEVED`, or `NEEDS_OPERATOR`.

## Bead graph contract

Record each experiment in a bead with:

- question or hypothesis and the acceptance gap it addresses;
- method, expected observation, falsifier, scope, and non-goals;
- notes/scratch sufficient to resume after compaction;
- exact RPI verdict/evidence references and observed learning.

Use graph semantics deliberately:

- `parent-child` for goal → experiment membership;
- `blocks` only for real execution ordering;
- `related` for alternatives or correlated observations;
- `discovered-from` for provenance of newly exposed work.

Use live `bd`/`br` state as authority and `bv --robot-*` output for
prioritization, parallel tracks, bottlenecks, and graph insight. Never treat a
static plan as fresher than the graph. The `bd`/`br`/`bv` tracker is an external,
caller-owned runtime the emitted goal will drive (declared via
`intel_scope: topic`); craft-goal reads live tracker state when present but
starts nothing and requires no tracker to be installed to compile a prompt.

## What counts as a ratchet

An RPI makes progress when its durable result does at least one:

1. proves part of terminal acceptance;
2. falsifies a live hypothesis with discriminating evidence and prunes it;
3. resolves an uncertainty or owner so the next experiment is materially
   different.

More code, another commit, a repeated error, or a rewritten plan is not itself
progress. A NOT_PROVEN result counts only when its evidence narrows the next
question; repetition without new information increments the no-progress
counter. Stop when no ratchet remains inside the envelope.

## Mayor loop

1. **Observe.** Reconstruct the root outcome, acceptance matrix, ready graph,
   prior verdicts, unresolved uncertainties, and remaining budgets.
2. **Select one bounded wave.** Choose the smallest set of high-information
   ready experiments. Parallelize only disjoint write and regeneration scopes.
3. **Run RPIs.** Each selected bead goes through exactly one RPI, ending in its
   independent verdict and human-readable summary.
4. **Ratchet the graph.** Preserve evidence and learning. PASS may satisfy a
   criterion. Red may revise a hypothesis or expose a child experiment.
5. **Classify discoveries.**
   - Necessary for frozen acceptance, within authority and remaining budget:
     add a `discovered-from` child and consider it in a later wave.
   - Useful but not necessary: record/link it; do not execute it in this goal.
   - Changes acceptance, exceeds authority, or cannot fit the envelope: HOLD.
6. **Checkpoint.** Measure ratchet versus churn, then continue, invoke the
   breaker, or emit a terminal report.

Every newly selected RPI must address an unmet criterion or a named uncertainty
blocking one. A new commit, subject, bead, helper, or wave never resets totals.

## Convergence and andons

Specify both:

- **Wave envelope:** RPIs, concurrency, wall time/tokens, live attempts, and a
  checkpoint at its end.
- **Goal envelope:** total RPIs, wall time/tokens, live attempts, compactions,
  and any patch/surface limit for the whole campaign.

Dispatch budget: every wave declares numeric RPI, token, time, and concurrency
limits before any work is selected. Fresh-helper budget: exactly 1 per HOLD.

Continue automatically across waves only while a ratchet exists and the next
experiment fits frozen acceptance, authority, and remaining envelope.

Enter HOLD on any declared trigger: repeated blocker, no ratchet for the
configured number of RPIs, oscillation between prior approaches, repeated live
failure class, requested acceptance change, operator-reserved decision, or
hard-ceiling exhaustion. HOLD permits exactly 1 bounded fresh-context helper:

- `UNSTUCK` must name a materially different bounded experiment, then resume.
- `ESCALATE` emits `NEEDS_OPERATOR` and performs no more implementation.

Current Codex goals lack an agent-triggered pause/checkpoint state. A
`NEEDS_OPERATOR` report therefore also tells the operator to pause the goal;
the prompt alone cannot guarantee that product-level pause.
Stop when any terminal report is emitted.

## Frozen prompt

Read and fill [the copy-paste-only goal prompt](references/goal-prompt.md).
Preserve its headings and terminal semantics; replace every angle-bracket field.

## Quality

Lead with `SAFE_TO_CREATE`, `USE_RPI`, or `UNSAFE_GOAL`. Return the copy-paste
prompt, separate goal-tool token budget, assumptions, and one lint line for:
outcome, evidence, admission, bead graph, RPI boundary, ratchet, discovery,
wave budget, hard budget, breaker, operator andon, scope, self-hosting, and
terminal reports.

Output validator — a captured decision must lead with exactly one terminal
token:

```bash
printf '%s\n' "$decision" | head -n1 | grep -Eq '^(SAFE_TO_CREATE|USE_RPI|UNSAFE_GOAL)\b'
```

This pins the machine-checkable shape of the output contract. `scripts/validate.sh`
still enforces structural hygiene; the fourteen lint dimensions above stay a human
rubric because they judge prompt content that has no persisted artifact at gate time.

Done when:

- success is finite but the route may adapt;
- the tracker can reconstruct intent, experiments, evidence, and provenance;
- informative red can continue but repeated non-information cannot;
- recursion cannot expand acceptance or reset monotonic ceilings;
- both successful and non-success terminal reports exist.

Stop after 1 lint pass and zero goal executions. Paired evidence:
`docs/learnings/2026-07-12-go-cli-goal-stall-tracker-layer-confusion.md` and
`skills/rpi/SKILL.md`.

## Failure behavior

Return `UNSAFE_GOAL` with missing decisions. Do not invent acceptance,
authority, graph semantics, or campaign size. The caller owns revision and goal
creation.

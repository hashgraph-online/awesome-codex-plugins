---
type: reference
parent_skill: standards
title: Agentic-workflow empirical evidence (Finster 2026)
---

# Agentic-Workflow Empirical Evidence

> Digest of a controlled empirical study of software-development workflows run *by AI agents*
> (not humans): Bryan Finster, "Agentic Workflows: Do Agents Work?" (bryanfinster.substack.com,
> 2026). Five experiments, one fixed model (Claude Sonnet), **hidden acceptance tests injected only
> at grading time**, 168 workflow×task cells graded across an initial build plus three follow-up
> changes = 672 graded rows. Clean-room digest: findings, numbers, and caveats only — no verbatim
> text.

This reference exists so skills can cite external evidence for workflow discipline instead of
asserting it from doctrine alone. It is loaded on demand by `standards` and cross-linked from
`test-pyramid.md`, the operating loop, and `/implement`.

## What the study measured

Each cell was scored on: acceptance-test pass rate (against hidden criteria never shown to the
agent), cost per cell (USD), lines changed across three follow-up modifications (a changeability
proxy), test coverage %, and mutation score (bug-detection effectiveness). The 2×2×2 terminal
experiment crossed three control variables: **test ordering** (test-first vs test-after),
**batch size** (one behavior per cycle vs all behaviors at once), and **authorship** (single agent
vs coder + independent reviewer/tester).

## Findings that transfer (load-bearing)

1. **Refactor-after-every-green is the mechanism, not test-first ordering.** Stripping the refactor
   step out of TDD erased its entire quality advantage; test-first ordering alone contributed
   nothing measurable once refactoring was controlled. Both winning workflows refactored after every
   green; every losing workflow deferred refactoring to one final pass and landed in the
   worst-performing cluster.

2. **Small batches win.** One behavior per cycle beat all-behaviors-at-once across measurements.

3. **Clear requirements are non-optional; no workflow compensates for their absence.** Under vague
   specs *every* workflow scored 0% on the hidden acceptance tests — each probed a decision the spec
   never made (e.g. an omitted per-channel retry rule) and no methodology discovered the missing
   requirement. The fix is a conversation before the first line of code, not a more disciplined way
   of writing it.

4. **Over-testing has a real, measurable cost (the thoroughness tax).** The highest mutation-score
   arms (0.93–0.98) *lost* on both cost and changeability: all that extra thoroughness cost multiples
   of the price and produced code that was harder to change later. On small-to-medium tasks, coverage
   saturated near 100% across every arm regardless of workflow, so chasing higher coverage/mutation
   bought nothing and cost multiples.

5. **Split authorship (coder + independent reviewer/tester agent) cost up to 3× more with no
   consistent quality gain.** A single agent outperformed two agents on cost-per-quality.

6. **Invariant: never let a refactor step change a test.** Held with zero violations across the
   study. A test change during refactor means the refactor changed behavior — it is a new slice, not
   a refactor.

## The numbers (2×2×2 terminal experiment)

| Workflow | Cost / cell | Notes |
|---|---|---|
| Code-First Small Batches, single agent | $0.99 | Winner; statistically separated |
| Classic TDD (test-first, small batch, refactor) | $1.59 | ~60% premium; quality indistinguishable |
| Split-authorship / big-batch variants | $2.09–$4.41 | 3–8× less cost-efficient |

Winning arms had mutation 0.80–0.86; the losing high-thoroughness arms 0.93–0.98.

## Caveats — do not over-generalize

The results hold for **small-to-medium tasks, fully-specified requirements, one model (Claude
Sonnet), a three-change horizon, and no human developers in the loop.** Larger tasks, multi-model
setups, longer maintenance horizons, and human+agent teams were not tested. Heavy plan-then-build
pipelines taxed small changes but were a minor surcharge on large multi-file work — so **match
tooling weight to task size.**

## How this maps to AgentOps doctrine

- **Confirms** single-agent-first (CLAUDE.md), small vertical slices (operating loop move 3), and
  clear-requirements-before-code (moves 1–2, `/discovery`, `bdd-foundry`). Hidden acceptance tests
  are exactly the repo's holdout-scenario pattern (implementing lanes never see the grading
  criteria).
- **Sharpens TDD (move 4):** the load-bearing move is *refactor-under-green*, not test ordering. The
  repo keeps test-first as the default (a test is the slice's contract and its regression guard), but
  code-first / test-after (`--no-tdd`) is a defensible cost-efficient variant for fully-specified
  small tasks — provided refactor-after-green and the never-change-a-test invariant hold.
- **Corrects test-shape zeal:** `test-pyramid.md`'s bug-finding levels (mutation ≥80%, BF1–BF9) must
  be throttled to task stakes. On small fully-specified changes, saturating coverage/mutation is the
  thoroughness tax, not rigor.
- **Reinforces the cost law** ("quorum only at one-way doors; cheap at generation" — spend the second
  agent at the gate verdict, not at every generation step). AgentOps' verification membrane is
  *not* the split-authorship pattern this study penalizes: the membrane spends its independent
  cross-family review at the **close-door gate on stakes** (no verdict = not done), not as a
  standing second author on every behavior. The finding is external support for keeping it there.

---
**Source:** Adapted from Bryan Finster, "Agentic Workflows: Do Agents Work?" (bryanfinster.substack.com, 2026). Pattern-only, no verbatim text.

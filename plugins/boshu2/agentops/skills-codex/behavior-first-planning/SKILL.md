---
name: behavior-first-planning
description: Behavior-first planning discipline — intent
---
# Behavior-First Planning

> **Quick Ref:** Turn an intent into beads that each carry a *runnable acceptance test* defining "done". The generative discipline behind the `bdd-foundry` workflow — extracted here so behavior-first planning survives independent of any orchestrator. Output: frozen Gherkin → executed-red tests → derived spec → an acceptance-gated bead DAG.

**YOU MUST EXECUTE THIS DISCIPLINE. Do not just describe it.**

> **Contract ownership (single owner, age-skills-audit-fable-l6ic.8).** This skill **owns** the intent → Gherkin → EXECUTED-red → acceptance-gated bead-DAG contract. [`$discovery`](../discovery/SKILL.md), [`$plan`](../plan/SKILL.md) (its Gherkin Scenarios Contract), and the `bdd-foundry` workflow **cite** this skill rather than restating the discipline.

## Why this exists — the 3/10 problem

Spec-first planning ships beads with no done-criteria: a title, a paragraph of "why", and nothing a machine can run to decide it is finished. The implementer then invents the bar, and "done" becomes a self-grade. **Behavior-first planning inverts the order:** define the behavior as an executable test *before* the design, so every bead is born with a runnable contract. The rule is absolute — **no runnable acceptance test, no bead.**

This is the successor to plain decomposition (`plan`): same DAG output, but each unit carries a *failing test that has actually been run red*, not prose. It is the planning-side mirror of the membrane (`docs/architecture/control-loop-model.md`): the bead's gate is deterministic ground truth, not an opinion.

## The four phases (run in order)

### Phase 1 — Behaviors: define DONE first

Turn the intent into concrete, **testable** Gherkin scenarios — Given/When/Then — covering the **happy path, edge cases, AND error/failure paths**. Every clause must be specific enough to become a runnable test; "works correctly" is rejected.

- Cover the failure paths explicitly: unparseable input, missing dependency, partial/timeout response → the behavior must say *abort/block*, never silent-pass.
- If a fresh-context or cross-family adversary is available, have it list the **missing** scenarios (security/correctness bypasses a green test would miss) and **disposition every gap**: folded / rejected (one-line reason) / deferred (say where it goes).
- Write the result to `behaviors.md` as the **frozen definition of done**. Freezing means: downstream phases derive from it; they do not silently add or drop scenarios.

#### The standing adversarial dimension checklist

The adversary applies this concrete checklist to **every** behavior that touches an input, a trust boundary, a mutation/write surface, a failure path, or external state — and emits the missing attack-vector scenario for each applicable class. These are the bypass classes a green test most often misses (cheap to add here, expensive at the gate):

- **FAIL-CLOSED on EVERY failure path** — unparseable input, missing/absent dependency, substrate/IO error, partial/malformed/timeout response → ABORT/BLOCK, never silent-pass or silent-skip-and-continue.
- **NO FORGEABLE TRUST MARKER** — never trust a caller-settable signal (env var, flag, header, marker file) as proof a check ran; re-derive/verify provenance.
- **NO RAW UNTRUSTED STRING past a boundary** — canonicalize/encode before display, argv, or serialization (values with quote, backslash, newline, shell metachar, unicode/case).
- **ENFORCE AT THE SINK, not the source** — last-wins / passthrough-after-`--` / override vectors; the component that ACTS must be the one that validates.
- **NO OVERCLAIMING TEST** — a property proven only under harness conditions (injected PATH/env, scratch stub) is not a live/production proof; the production path needs its own scenario.
- **INPUT-CHANNEL variants** of every surface — stdin vs argv, heredoc, file vs inline, symlink/case/unicode path aliases, TOCTOU lookup-to-write race, nesting/depth.

Also read any repo-local gate-findings ledger (try `docs/gate/findings-ledger.md`) and apply its Standing Review Dimensions — those are real defects a gate already caught; do not let them recur. **This is the ratchet: every gate finding permanently upgrades this checklist.**

### Phase 2 — Acceptance tests: Gherkin → EXECUTED red

Turn **each** frozen scenario into a runnable test in the project's framework. The test IS the executable definition of done. The tests must be **currently failing (red)** because the feature is not built yet — and you must **observe the red, not assert it**:

- Write the tests under `acceptance-tests/` and an `acceptance-tests.md` index mapping scenario id → test name/path, including the **one-line command that runs the whole suite**.
- **RUN the suite and report the mechanical result** (red count, green count, harness-errored count). A test that already passes asserts nothing new; a test that crashes on a syntax/harness error is *not* a valid red. Both are defects to flag before proceeding.
- One invocation per test — never pass multiple positional test-name filters to a single `cargo`/`pytest`/`go test` call (it arg-errors before any test runs); chain with `&&`.

This phase is the heart of the discipline. Skipping the *executed* red is how a plan silently regresses to spec-first.

### Phase 3 — Spec: derived to make the tests pass

Design the architecture/spec whose **only** job is to make the acceptance tests pass — derived from the behaviors + tests, not free-form. For each behavior, name the components/changes that satisfy it. A repaired or already-green test from Phase 2 gets its assertion fixed here. Keep it tight: a spec, not a monument. Write to `spec.md`.

### Phase 4 — Acceptance-gated bead DAG

Decompose the spec into a dependency-ordered DAG of beads. **Every bead MUST carry:**

- a `scenario_ref` — the id of a real frozen scenario it delivers, and
- an `acceptance_test` — an **invocable command + test path** (from `acceptance-tests/` or the project test tree) that defines done for *that* bead. Prose-only acceptance is rejected.

Then apply the **mechanical gate** (compute it, do not self-report):

1. **Runnable** — each `acceptance_test` resolves (in list mode: `--list` / `--collect-only` / `-list` / `--count`) to **exactly one** unignored test. Not zero, not 2+, not an arg error.
2. **Valid ref** — every `scenario_ref` is a real frozen scenario id.
3. **Coverage** — every frozen scenario is covered by ≥1 bead (report holes).
4. **Cycle-free** — the dep graph topologically sorts.

A bead failing any check is **rejected**, not written. Only the gate-passed set advances.

## The closing gate — validate BEFORE the tracker write

Behavior-first planning is **not done when the beads are drafted — it is done when an independent reviewer confirms them.** Before writing anything to the tracker:

- Produce a manifest of the proposed (not-yet-tracked) bead set.
- Have an **independent, fresh-context reviewer** (cross-family where possible — the author never grades their own plan) score crank-readiness against the frozen behaviors and spot-run ≥2 acceptance commands.
- Write to the tracker **only** on a clearing verdict AND coverage-complete AND cycle-free AND the mechanical drift-guard green. Otherwise repair the manifest and re-validate; do not pollute the tracker with un-cleared beads.

Use `br` from the main checkout (never a worktree — it forks the bead DB), each bead self-contained with an explicit **ACCEPTANCE** section, deps wired per the manifest, overlap-checked against existing open beads.

## Relationship to the bdd-foundry workflow

`bdd-foundry` (`.codex/workflows/bdd-foundry.js`) is the **thin orchestrator** over this discipline: it dispatches each phase as a black-box agent, gates on the mechanical (computed-in-JS) checks above, and writes to the tracker only on the cleared verdict. This skill is the discipline; the workflow is the deterministic harness that runs it conformantly (see `docs/architecture/workflow-conformance-pattern.md`). When invoked directly (no workflow), you run the four phases yourself and apply the same gates by hand.

The skill dogfoods its own rule: its behavior is pinned by an executable spec, [`references/behavior-first-planning.feature`](references/behavior-first-planning.feature) — the same Gherkin → runnable-acceptance shape it asks every plan to produce.

## Do NOT

- Duplicate the *lighter* single-BDD-intent shape phase of the `operating-loop` — this is the **full** Gherkin → executed-red → acceptance-gated-DAG discipline, used when beads must be genuinely crank-ready.
- Write a bead whose acceptance is prose, "see spec", or an unrun test.
- Grade your own plan — the closing gate requires an independent reviewer.

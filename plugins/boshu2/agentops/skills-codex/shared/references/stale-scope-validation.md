# Planning Rule: Re-Validate Inherited Scope Estimates

**Applies to:** `/plan`, `/pre-mortem`, `/discovery`, any skill that consumes a bead description, prior plan, handoff doc, or scope estimate produced by an earlier session.

**Status:** Active rule. Violations should be called out in pre-mortem gates.

## The rule

Before acting on a deferred bead, handoff doc, or an inherited scope estimate, verify that the cited infrastructure (functions, files, LOC counts, call-site counts, "already exists" vs "needs to be built") still matches HEAD.

Run `/council --evidence` against the description before starting implementation when **any** of the following are true:

1. The description is older than **7 days** at the time you act on it.
2. The description was filed by a prior session under time pressure (look for phrases like "hastily filed", "deferred from X wave", "quick note").
3. The description cites specific LOC counts, "N callers", "need to build X", or "architectural change required".
4. The description references a function, file, or symbol by name.
5. The scope is classified as `full` complexity and the estimate was produced by a different session/agent.

## Why

Scope estimates inflate in deferral handoffs. A description written hours before being deferred often embeds the first-reader's mental model of difficulty — that model gets anchored to "looked hard", and subsequent sessions inherit the estimate without re-validating. Three failure modes this rule prevents:

1. **Ghost work.** A session begins re-implementing infrastructure that a later commit added. Example: rebuilding staging primitives that already exist in `checkpoint.go`.
2. **Deferral loop.** Each session inherits the "too complex for this session" verdict and defers again, permanently locking in the inferior design.
3. **Symbol drift.** The description cites `package.Func` that has been renamed, moved, or deleted. Acting on the stale citation produces bugs or scope creep.

## How to apply

1. **Extract citations from the description.** File paths (`path/to/file.go:123`), function names (`func foo(`), backticked symbols, LOC counts.
2. **Run `ao beads verify <id>`** if the input is a bead ID — it mechanically checks each citation against HEAD and reports stale references. (If this command doesn't exist in your session, grep manually.)
3. **Run `/council --evidence validate "verify this scope estimate: <description>"`** on the description. Each judge must return concrete `test_assertions` that either confirm or refute the cited infrastructure.
4. **Re-state the scope based on HEAD, not the description.** Include the delta: "Description said 395 LOC; HEAD says ~300 LOC because [X] already exists at [file:line]."
5. **Proceed only if scope is unchanged or smaller.** If the HEAD-validated scope is materially larger than the description, defer to a new pre-mortem — the original framing was under-estimating and the new framing may need different resources.

## Concrete case (2026-04-11, na-h61)

The na-h61 bead claimed `cli/cmd/ao/fitness.go::collectLearnings` with "8 existing callers" as the refactor target for a "395+ LOC architectural change to collect fitness snapshots against a staging tree".

Running `/council --evidence --tdd` against the description before touching code revealed:

- `cli/cmd/ao/fitness.go` **does not exist.**
- `collectLearnings` **does exist** at `cli/cmd/ao/inject_learnings.go:50` but it is an INJECT-side artifact loader, **not a fitness-MEASURE function**. It has nothing to do with M8.
- The staging tree infrastructure (`cp.StagingDir`, deep-copy via `NewCheckpoint`, atomic swap via `Commit`, `Rollback` safe at any state) **already existed** in `cli/internal/overnight/checkpoint.go:194-345`.
- The actual fix was a **sequencing bug**: `RunMeasure` was called at `loop.go:381` (after `cp.Commit()` at `loop.go:335`). Moving MEASURE before COMMIT and wiring `cp.Rollback()` into the halt branches was ~300 LOC, not 395.

Without the pre-flight validation, the session would have either (a) re-implemented existing staging primitives, or (b) deferred again. With the validation, M8 landed in one session.

## Anti-pattern: "I'll fix it when I see the code"

A common trap: believing the description and starting to read code, trusting that discrepancies will surface during implementation. They do — but by then you've already committed to the wrong mental model and sunk time. The `--evidence` council validation is ~3 minutes of parallel judge work. It returns concrete assertions you can grep against HEAD in another 30 seconds. Total cost: under 5 minutes. Total savings: hours of ghost work.

## See also

- `skills/council/SKILL.md` — `--evidence` flag and the falsifiable-assertion schema
- `skills/plan/SKILL.md` — loads this rule during scope decomposition
- `skills/pre-mortem/SKILL.md` — loads this rule when the input is a handoff or deferred bead

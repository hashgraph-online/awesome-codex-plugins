---
name: refactor
description: 'Restructure or clean up code with no behavior change, proved by before-and-after checks. Use when: asked to clean up, extract, dedupe or simplify, even one function.'
practices:
- refactoring
- legacy-code-seams
- design-patterns
hexagonal_role: supporting
consumes:
- repo-context
produces:
- code-changes
context_rel: []
skill_api_version: 1
user-invocable: true
context:
  window: fork
  intent:
    mode: task
  sections:
    exclude:
    - HISTORY
metadata:
  capabilities: [refactor]
  effects: [modify_source_files]
  canonical_status: canonical
  disposition: keep_specialist
  tier: execution
  dependencies: []
output_contract: code changes with regression evidence
---
# Refactor — one structural experiment

Refactor changes structure while preserving observable behavior. It performs one
caller-selected transformation and reports the result. "Behavior-preserving" is
a claim to prove with before/after checks, never to assert.

## What counts as behavior

Unless the caller explicitly excluded a surface, all of these must survive:

- **Messages and exit codes.** Error and output text compares byte-for-byte;
  exit codes, error types and which input raises which error stay the same.
  Scripts and callers parse them. Preserve an inconsistent message and report
  it; normalizing it is a behavior change.
- **Differences between near-duplicates.** When merging duplicated branches,
  carry every difference (constants, comparisons, messages, extra steps) as a
  parameter or a branch. Do not unify a difference the caller has not declared
  accidental.
- **Interfaces.** Public signatures, defaults, return types, persisted field
  names, protocol values and CLI flags. Renaming one is a compatibility change
  unless the accepted scope provides for it.
- **Order and coverage.** Branch priority, default handling, evaluation count,
  side-effect order, and the set of tests that run. A pre-existing red that
  vanishes, or a test that stops running, is a behavior change.

## Procedure

1. Name the preserved behavior, the focused acceptance surface and the concrete
   structural problem for its callers, in the caller's domain terms.
2. Run the focused check and the smallest regression check the changed surface
   justifies, and record that honest baseline, including reproducible ambient
   failures. For an evaluation comparing executable behavior, pin the starting
   source, build its baseline before edits and keep that binary and the
   comparison inputs.
3. Apply one bounded transformation: extract, rename, inline, simplify,
   encapsulate, move, or delete dead code. Judge it by what callers must
   understand and where a domain rule must change, not by file size.
4. A bug or suspicious inconsistency found on the way is reported separately
   (location, why it looks wrong) and left unfixed. Fixing it inside the
   refactor hides a behavior change the caller did not authorize.
5. Rerun the same focused check and the smallest justified regression check
   over the same inputs, including error paths.
6. Report, then stop. A red result is evidence for the caller; this skill does
   not revert, narrow, retry, commit, validate, or route subsequent work.

When nothing can be executed (no runtime, no tests, code supplied in a
message), neutrality is unproven: give the exact before/after commands and
inputs the caller must run, error paths included, and list every surface under
behavior not checked.

```text
transformation: <the one change>
preserved:      <behavior and surfaces from step 1>
checks:         <command>: before -> <result>; after -> <result>   (or "not run")
outputs:        <before/after hashes when the surface produces output>
diff:           <files touched>; only those the transformation names
suspected bugs: <file:line, why>; reported, not fixed
not checked:    <surfaces no check covered>; present even when empty
```

## Responsibility and interface cost

Before adding an interface or splitting a module, inspect representative callers.
Count the concepts they must coordinate: required setup, ordering, states, error
handling and repeated domain rules. A useful boundary puts a cohesive rule under
one owner and lets callers request an outcome without reproducing that rule.
Reject a wrapper that only adds another name or pushes the same coordination
into its callers. Existing boundaries are sufficient when no concrete caller
problem warrants changing them.

Use the caller's vocabulary for extracted operations and types. A naming
ambiguity that changes behavior belongs with the existing domain definition;
consult [Domain](../domain/SKILL.md) only when that distinction needs work.

When the transformation needs a seam — an extraction boundary, interface, or
module split — and more than one candidate seam exists, probe before you cut.
Run the probe in disposable isolation (a scratch branch, worktree, or copied
tree the caller's policy allows): rough in the seam, see what it forces —
signature churn, import cycles, test rewrites — then discard the probe and
keep only the knowledge. Stop condition: at most two probes; if the second
candidate seam also fights back, report both findings to the caller instead of
trying a third. Cutting the first imaginable seam directly into the working
tree is the **premature seam** failure mode: the wrong boundary calcifies
because reverting it now costs more than living with it.

## Neutrality gates

Gate the transformation on behavior-identical proof:

- The focused check and the package-level regression check pass both before
  and after, with the same set of pre-existing failures: no new red and no
  vanished red.
- For output-producing surfaces (generators, serializers, formatters, reports),
  capture output hashes over identical inputs before the change and compare
  byte-for-byte after. A mismatch is a behavior diff to surface and explain,
  never to shrug at; the caller decides whether to keep, narrow, or reverse it.

A neutrality gate that was skipped or narrowed after the fact is the
**post-hoc neutrality** failure mode — the diff decides what got tested. Name
any surface the gates did not cover under behavior not checked.

## References

- [Behavior-preserving simplification](references/behavior-preserving-simplification.md) — refactoring catalog and per-pattern safety checks
- [Behavior scenarios](references/refactor.feature)
- [Upstream capability reference](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md) — Matt Pocock; original AgentOps adaptation.

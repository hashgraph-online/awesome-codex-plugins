---
name: refactor
description: 'Simplify structure, interfaces or responsibilities while preserving behavior. Use when: a focused refactor is requested; feature changes need their own intent.'
---
# Refactor — one structural experiment

Refactor changes structure while preserving observable behavior. It performs one
caller-selected transformation and reports the result.

## Prompt

```text
Refactor billing-service/internal/retry/backoff.go: extract the exponential backoff calculation out of RetryRequest into its own function, no other behavior change. Record a baseline, run go test ./internal/retry/... before and after, and report the diff summary, commands, results, and anything not checked.
```

## It's working if

- The report names the preserved behavior and cites `go test ./internal/retry/...` run both before and after.
- `git diff --stat` touches only `internal/retry/backoff.go`, never an unrelated file.
- Golden-output hashes get captured and compared byte-for-byte whenever the changed surface produces output, e.g. `sha256sum` before and after.
- The report's `behavior not checked` list is present in the output even when empty, naming any surface the gates skipped.

## Procedure

1. Name the preserved behavior, the focused acceptance surface and the concrete
   structural problem for its callers. Reuse the caller's domain terms and
   accepted behavioral examples; preserve their meaning through the change.
2. Record an honest baseline, including any reproducible ambient failures.
   For an evaluation comparing executable behavior, pin the starting source
   and build its baseline before edits; retain that binary and the comparison
   inputs. Compare the candidate using those inputs and the same toolchain.
   This adds no executable-comparison ritual to ordinary refactoring.
3. Apply one bounded transformation: extract, rename, inline, simplify,
   encapsulate, move, or delete dead code. Judge the result by what callers must
   understand and where a domain rule must be changed, not by file size alone.
4. Run the focused check and the smallest package-level regression check justified
   by the changed surface.
5. Return the diff summary, commands, results, and behavior not checked.

Do not combine a newly discovered behavior fix with the structural change. A red
result is evidence for the caller; this skill does not revert, narrow, retry,
commit, validate, or route subsequent work automatically.

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
Renaming a public symbol, persisted field or protocol value is a compatibility
change unless the accepted scope provides for it.

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

"Behavior-preserving" is a claim to execute, not assert. Gate the
transformation on behavior-identical proof:

- The focused check and the package-level regression check pass both before
  and after, with the same set of pre-existing failures — no new red, and no
  quietly vanished red either (a test that stops running is a behavior change).
- For output-producing surfaces (generators, serializers, formatters, reports),
  hash the outputs: capture golden-output hashes over identical inputs before
  the change and compare byte-for-byte after. A hash mismatch is a behavior
  diff to surface and explain, never to shrug at; the caller decides whether to
  keep, narrow, or reverse the change.
- Observable error messages, exit codes, and public signatures on the changed
  surface are part of behavior unless the caller excluded them.

A neutrality gate that was skipped or narrowed after the fact is the
**post-hoc neutrality** failure mode — the diff decides what got tested. Name
any surface the gates did not cover in the report's behavior-not-checked list.

## References

- [Behavior-preserving simplification](references/behavior-preserving-simplification.md)
- [Behavior scenarios](references/refactor.feature)
- [Upstream capability reference](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md) — Matt Pocock; original AgentOps adaptation.

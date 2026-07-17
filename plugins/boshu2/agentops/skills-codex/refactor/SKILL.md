---
name: refactor
description: Execute one behavior-preserving structural
---
# Refactor — one structural experiment

Refactor changes structure while preserving observable behavior. It performs one
caller-selected transformation and reports the result.

## Procedure

1. Name the preserved behavior and the focused acceptance surface.
2. Record an honest baseline, including any reproducible ambient failures.
3. Apply one bounded transformation: extract, rename, inline, simplify,
   encapsulate, move, or delete dead code.
4. Run the focused check and the smallest package-level regression check justified
   by the changed surface.
5. Return the diff summary, commands, results, and behavior not checked.

Do not combine a newly discovered behavior fix with the structural change. A red
result is evidence for the caller; this skill does not revert, narrow, retry,
commit, validate, or route subsequent work automatically.

## Seam experiments before commitment

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
  diff to explain or revert, never to shrug at.
- Observable error messages, exit codes, and public signatures on the changed
  surface are part of behavior unless the caller excluded them.

A neutrality gate that was skipped or narrowed after the fact is the
**post-hoc neutrality** failure mode — the diff decides what got tested. Name
any surface the gates did not cover in the report's behavior-not-checked list.

## References

- [Behavior-preserving simplification](references/behavior-preserving-simplification.md)
- [Behavior scenarios](references/refactor.feature)

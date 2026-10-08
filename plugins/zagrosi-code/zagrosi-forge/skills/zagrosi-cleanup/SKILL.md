---
name: zagrosi-cleanup
description: Simplify existing code while preserving behavior. Use when asked to clean an AI-generated or difficult repository, split godfiles, remove duplication or dead layers, or review a PR for unnecessary complexity.
---

# Forge Cleanup

Produce code that is easier to understand and change. Apply the shared
[engineering standard](../zagrosi-implement/references/engineering.md).
Fewer concepts and clearer responsibilities matter; line counts are evidence,
never targets. Preserve public contracts even when external callers are unseen.
For review/audit-only requests, return findings and stop before edits. Existing
implementation authorization counts; do not ask again merely for cleanup.

## Scope and baseline

1. Read repository instructions, working-tree changes, entrypoints, callers, and
   tests. Follow real execution paths; exclude generated/vendor code unless the
   task explicitly includes it.
2. For an explicit repository cleanup, identify the highest-value problems:
   mixed responsibilities, repeated policy, dead or speculative layers, unclear
   state/side effects, misleading names, missing error handling, and weak tests.
   Rank by impact and regression risk. Keep the list in the existing plan.
3. For a final PR pass, inspect only the diff and affected callers. Repair newly
   introduced or encountered complexity; put unrelated debt in the summary.
   Do not start a second whole-repository cleanup automatically.
4. Establish existing test results. Add characterization tests where coverage
   cannot protect public results, errors, ordering, exports, and side effects.
   Use [compatibility checks](../zagrosi-implement/references/compatibility.md)
   for meaningful mutable refactors; capture the original source and passing
   checks before changing it. Existing coverage can supply those checks.
   Report pre-existing failures separately; never describe them as a clean baseline.

## Change and prove

Use [Plan](../zagrosi-plan/SKILL.md) and
[Implement](../zagrosi-implement/SKILL.md) for substantive cleanup. Reuse an
admitted plan when applicable; update its ownership and acceptance before edits.
Group by cohesive responsibility and dependencies, with one primary writer per
overlapping file. Tiny, low-risk cleanup within active work stays in its section.

Prefer deletion, direct functions, and existing boundaries. Split a godfile by
responsibility while retaining a small compatible entrypoint. Do not replace it
with arbitrary fragments, forwarding wrappers, a new framework, or compressed
one-liners. Separate intentional behavior changes from behavior-preserving work.

Run targeted regression checks before and after each meaningful change. Review
the actual structural gain and regressions; use an
[independent model](../zagrosi-forge/references/providers.md) when requested or
useful for a concrete risk. Resolve findings rather than counting approvals.
Run the integration suite once after the final changes and capture its receipt.
If any later fix changes checked inputs, refresh the affected evidence.

Report what became simpler, preserved behavior and measured checks, pre-existing
failures, and remaining debt. Do not claim improved performance without measuring
it. Follow existing authorization for commits/PRs; this skill creates no hooks
or recurring background work.

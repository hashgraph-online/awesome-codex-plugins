# Fix protocol

Read this only in review-and-fix mode. In review-only mode the reviewed tree is not touched, and any finding goes into the report instead. Here, the change is the minimum that removes the confirmed blockers, applied in a fixed order, with the review repeated afterwards.

## Contents

1. Preconditions
2. The change ladder
3. The safe execution order
4. What stays
5. Re-review
6. Out of bounds

## 1. Preconditions

All of these must be true before the first edit:

- The user asked to review and fix, not only to review. "고쳐라", "repair the blockers", "apply the review" qualifies; "판단만 해줘" and a bare "리뷰해줘" do not.
- The blockers are written down, each with `file:line` or an artifact and the observed failure.
- The content identity is recorded, so the repaired tree can be compared with the reviewed one.
- The change is on a branch or a worktree the user's own delivery rules permit editing. Never repair on a detached head that the user did not offer.

If any precondition fails, the run stays review-only and the report says so.

## 2. The change ladder

Take the smallest rung that removes the blocker. Do not climb to a higher rung because it feels cleaner.

| Rung | Action | Use when |
|---|---|---|
| 1 | Delete | The code is provably dead, or the blocker is a stale branch nothing can reach |
| 2 | Reuse | The blocker exists because the change re-implemented a helper or a pattern the project already has |
| 3 | Simplify in place | The blocker is a wrong condition, an overbuilt branch, or redundant re-verification inside the current shape |
| 4 | Extract a unit | The blocker is a size or coupling trigger and the extracted unit has a real boundary or a second caller |
| 5 | Introduce an abstraction | Only when the current contract requires multiple implementations, which almost never applies to a blocker fix |

Rules for the ladder:

- One blocker, one rung. A fix that crosses two rungs is either two blockers or a scope change.
- Never use the ladder to add a dependency, a compatibility layer, a new public API, or a config flag that the blocker does not require.
- A fix that would touch more than the blocker and its callers is written into the report as a plan instead of applied.

## 3. The safe execution order

1. **Baseline.** Run the narrowest test or the smallest real scenario that shows the blocker, and record the failing output. This is the before state.
2. **Map references.** Search for every caller, implementer, test, and configuration reference to each symbol about to change, and list them.
3. **Symbol-aware rename or move** when the edit is a rename or a move. Use the editor's language-aware rename before text substitution.
4. **Preview a structural rewrite** before applying it, when the edit changes syntax trees or moves blocks.
5. **One coherent edit.** Apply the whole blocker fix, not half of it, so the tree is never in a state where both the old and the new path are half-present.
6. **Read the affected files whole** after editing, not just the diff.
7. **Owner checks.** Run the narrowest test, then the project's declared test and build for the changed area, and record the output.
8. **Smoke the real surface** for anything a user or a caller sees, using the same invocation the matrix used.
9. **Recompute the identity** and run the fresh review described below.

Stop between any two steps when a step shows the fix is wrong. Reverting a partial edit is cheaper than continuing it.

## 4. What stays

A repair keeps everything that is load-bearing, even when it looks like the blocker:

- Boundary validation at a trust boundary, security checks, and permission checks.
- Error handling that turns a failure into a reported failure instead of silence.
- Public signatures, wire formats, migration files, and any interface other code or data depends on.
- A guard that looks repetitive but sits at a boundary the type system does not cross.
- A test that currently fails because it encodes the intended behavior. Fix the code, not the test.

Never weaken, skip, delete, or re-record a failing test to make a blocker go away. Never widen a scope by fixing a second finding on the way; that finding goes in the report with a fix note.

## 5. Re-review

A repair is not a verdict.

- Recompute the content identity after the repairs.
- Re-run the affected QA rows, and add a row for the repaired behavior.
- Run the fresh review lane again, because the reviewer judged the old content.
- Write the new identity next to the old one in the report, and list the repaired blockers with the artifact that shows each is gone.
- End with `Result: fixed: <n> blockers repaired, review passed on <identity>` only when the fresh review passed. If a blocker survives or a new blocker appears, the result is `failed` with the surviving blockers.

At most two repair passes. A third pass would review the reviewer's patience rather than the change; instead, write the surviving blockers into the report and stop.

## 6. Out of bounds

Never, in any mode:

- commit, push, merge, tag, open a pull request, or deploy
- delete user data, a branch, a worktree, a lock file, or an untracked file that is not this run's own artifact
- rewrite a migration that a deployed environment has already applied
- change a dependency version, a lock file, a CI configuration, or a repository setting as a side effect of a blocker fix
- reformat files the blocker does not touch
- add a test that pins the exact wording of a message, a comment, or a prompt

A blocker whose only fix needs one of these is reported as `blocked` with the reason, not repaired.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| The delete, reuse, simplify, extract, abstract ladder and the safe execution order: baseline, map references, symbol-aware rename, preview rewrite, one coherent edit, owner test | `dbc-hbin/omp-ulw@74df40f refactor` (mechanism reference, re-authored; no text copied) |
| Keeping boundary validation, security checks, error handling, and public signatures | same source, re-authored |
| Re-review after a repair, with the old and new content identity recorded | this package's chosen design |
| The two-repair cap and the out-of-bounds list | this package's chosen design |

### Evidence grade

`MECHANISM` for the ladder and the safe execution order. `LOCAL` for the re-review requirement, the repair cap, and the forbidden list. The ladder is the source's chosen ordering, not a measured optimum.

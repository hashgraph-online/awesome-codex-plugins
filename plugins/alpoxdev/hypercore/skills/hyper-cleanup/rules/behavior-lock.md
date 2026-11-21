# Behavior Lock

Read this before the first edit. It owns the baseline record, the pre-existing failure that is never deleted, and the evidence that proves a cleanup changed no behavior.

## 1. The Lock Is A Record, Not A Promise

A behavior-preserving cleanup is proven by two things: the same command passing before and after, and a report that names every removed hunk. Neither is a claim about intent; both are artifacts a reviewer can rerun.

Before editing, write the lock:

```markdown
## Behavior lock (<ISO timestamp>)
- Base: <branch or commit> — <HEAD sha>
- Working tree: <clean | N modified, M untracked, listed below>
- Command: <exact test or check command>
- Result before: <pass | fail with the failing case names>
- Owner tests read: <paths>
```

The base is the state the work started from, not `main` and not `HEAD~1`. A dirty tree is normal: record the files that were already modified so the final diff can separate them from this run's edits.

## 2. Baseline First, With The Real Command

The baseline command is the one the project already runs for the touched area: its test runner, its type check, its lint. Do not invent a check and do not narrow the suite to the files you plan to touch.

- **It passes.** That pass is the lock. The same command must pass again at the end.
- **It fails.** Every failing case is written to a baseline-red list with its name and its output. Those cases are excluded from every proof in this run.
- **It cannot run.** A missing runner, a missing service, or a broken toolchain is a finding, not a pass. The lock records the exact error, and the run either finds an equivalent command the project documents or reports the gap.

A baseline red case is a product bug. It is never deleted, never marked skipped, and never edited to a passing expectation. The cleanup cannot be graded on a suite it just weakened.

## 3. Pick The Boundary That Can Fail

The lock only means something when the command exercises the behavior that will change.

| What changes | What proves it |
|---|---|
| A function body inside one module | the owner test that calls the public entry, not a private helper test |
| A guard or validation path | a case that feeds the rejected input, on both sides of the guard |
| A shared helper with several callers | one caller's suite per caller boundary, or the widest existing suite that covers them |
| A test file, with no production change | the mutation proof in [test-junk.md](test-junk.md) §4 |
| A comment, a rename, or formatting only | the same command, plus the statement that no executable line moved |

When no test reaches the surface, the lock is an executable reproduction: an exact command with its input and its observed output, recorded before the edit and rerun after it.

## 4. One Lock, Rerun At The End

The suite is not run between every edit. It runs when the baseline is taken and once when the edits are complete, and any later correction reruns only the checks the correction can affect.

A differing result between the two runs is not noise. Either the edit changed behavior, or the run is not reproducible; both are reported, and the second one is proven by rerunning the same command on the unmodified base.

## 5. What Counts As Behavior

Behavior is what a caller or a user can observe, not what the code looks like inside.

- Return values, including which error type and which message a failure raises
- The side effects a call performs and the order it performs them in
- Public signatures, exported names, and the shape of serialized output
- Log lines a consumer parses, exit codes a script checks, and files a build writes
- Accessibility affordances and supported environment behavior

An inlined wrapper that changes a stack trace, a narrowed catch that changes the exception class, and a flattened branch that reorders two side effects are all behavior changes. They are not authorized by a cleanup request.

## 6. Authorized Scope

The lock covers the files the request names, or the current diff when it names none. It does not cover the whole repository.

- Reading a caller, a neighboring pattern, or a test is context, never permission to edit.
- A dependency the edit would break is a finding for the report, not a second scope.
- A lockfile changes only when the request explicitly removes a dependency.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| Lock behavior with a baseline first, before touching the files | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| A test that is already red on the base is reported and excluded from proofs, never deleted and never fixed by changing the expectation | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| No repeated midflight suite runs; the relevant checks run once | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| Observable behavior as the invariant, including exception and side-effect order | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| The lock record's fields and the scope rule | integrator contract, 2026-11-10 (issue #24) |

### Evidence grade

`LOCAL` - the lock record fields, the boundary table, and the "one lock, rerun at the end" policy are this package's design. The baseline-first rule and the baseline-red exclusion are re-authored from a repository with no license; no text or code is copied.

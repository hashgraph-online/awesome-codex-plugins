# Correction And Report

Read this when a gate fails after an edit, and before writing the closing report. It owns the hunk-level correction, the rollback limits, the report at `.hyper/cleanup/<slug>.md`, and the terminal line.

## 1. A Failed Gate Is Evidence, Not Noise

When a check fails after an edit, the failure names a hunk. Locate it before changing anything else.

1. **Which hunk.** Compare the failing case against the behavior lock's baseline. A case that passed before and fails now was caused by an edit in this run.
2. **The mechanism.** Write one sentence that connects the edit to the failure. If the sentence needs "and then something" the mechanism is not understood, and the hunk is reverted rather than guessed at.
3. **The smallest correction.** Correct or reverse that hunk against the current file contents, with the edit that touches only those lines.

A failure that existed at baseline is not this run's to fix. It goes into the report's baseline-red list with its output and stays untouched.

## 2. Correct The Hunk, Never The File

The units of correction are the hunk and the current contents.

- Edit only the lines the failing hunk owns. A correction that rewrites the surrounding function is a new change with its own risk.
- Read the file again before correcting. Another edit, a formatter, or a concurrent session may have changed it since the failing run.
- Re-run only the checks the correction can affect. A full suite rerun after a one-line fix buys nothing and delays the report.

Forbidden corrections, without exception:

- `git checkout -- <file>`, `git restore <file>`, `git reset`, or any whole-file rollback that would also discard the user's own uncommitted work
- deleting or rewriting an unrelated hunk that happens to sit in the same file
- changing an expected value, a snapshot, or an assertion so a changed behavior passes
- marking a failing test skipped, focused, or quarantined
- suppressing a warning, widening a catch, or adding a retry to make a gate green

A behavior change that a gate correctly detects is not a bug in the gate. If the cleanup cannot keep the behavior, the hunk is reverted and the limitation goes in the report.

## 3. When A Correction Loops

Two failed corrections on the same hunk end the attempt: revert the hunk and record it under preserved code with the failure output. A third attempt on the same lines is not persistence, it is thrashing.

Three outcomes are legitimate here and none of them is a failure of the run:

- the unit stays and the report says why
- the unit is reverted to its base form and the report names the check that rejected it
- the run ends `blocked` on a missing capability, with the exact command and error

## 4. Final Gates, Once

Run the checks the repository requires for the touched area, once, at the end. Then review the diff as the user would read it.

- Read the complete diff, not the list of files.
- Confirm every removed line has a ledger row and every kept candidate has a reason.
- Confirm the behavior lock's command now produces the same result as its baseline, apart from the recorded baseline-red cases.
- Confirm the tree has no debug print, no temporary file, no scratch script, and no leftover artifact from this run.

A cleanup that only reports, with no edits, still runs the baseline command and still writes the report.

## 5. The Report

The report lives at `.hyper/cleanup/<slug>.md`, one file per run. Its sections are fixed so two runs can be compared.

```markdown
# Cleanup: <slug>

## Scope
- Request: <the user's words, quoted>
- Base: <branch or commit> — <HEAD sha>
- Files in scope: <paths>
- Files read as context: <paths>
- Working tree before: <clean | N modified, M untracked>

## Behavior lock
- Command: <exact command>
- Before: <pass | fail with case names>
- After: <pass | fail with case names>
- Baseline red: <case names with output, or none>

## Ladder decisions
| Unit | Rung | Decision | Proof |
|---|---|---|---|
| src/app.ts:42 | 4 | nested ternary flattened | same branches, same order |

## Removed hunks
| Path | Lines | Category | Replacement |
|---|---|---|---|
| src/app.ts | 42-48 | 3 excess complexity | early return |

## Tests ledger
| Test | Mark | Keeper or reason | Proof |
|---|---|---|---|

## Preserved code
- <unit> — <why it stayed: KEEP row, unproven guard, out-of-scope layer>

## Checks
| Check | Command | Result |
|---|---|---|

## Risks
- <a deferred risk, a ceiling, an unverified equivalence, or none>

Result: <terminal>
```

A report with no edits is still a report: the scope, the lock, the ladder rows for what was considered, and the preserved code carry the value.

## 6. Terminals

The report ends with exactly one `Result:` line.

| Terminal | Meaning |
|---|---|
| `clean` | The authorized edits are in place, the lock still passes, the ledger is complete. |
| `no-change` | Nothing in scope survived the proofs; the report records what was considered and why each unit stayed. |
| `awaiting_input` | One question was asked because the request is ambiguous in a way the files cannot settle. |
| `blocked` | A needed capability, access, or command was unavailable; the exact gap and the attempted command are reported. |

`no-change` is a real outcome, not a soft failure. A run that reads carefully and cuts nothing is the correct answer for a codebase whose code is load-bearing.

## 7. What The Report Never Contains

- A claim that a check passed when it was not run, or a check reported as passing from an earlier run of a different tree
- A removed hunk with no category, or a category with no proof
- A test deleted without a keeper or a class proof
- A behavior change described as a cleanup
- A commit, a push, a merge, or a pull request made from this workflow

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| Corrections touch only the owned hunks, never roll back a whole file, and never change an expectation to bless changed behavior | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| Re-run only the failed or affected checks after a correction | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| A per-file record of the ladder decision, the category, the replacement, and why it is safe | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| The report's scope, behavior-lock, ladder, ledger, preserved, checks, and risk sections | integrator contract, 2026-11-10 (issue #24) |
| The four terminals and the `Result:` line | integrator contract, 2026-11-10 (issue #24) |

### Evidence grade

`LOCAL` - the report section order, the four terminals, and the two-attempt correction cap are this package's design. The hunk-level correction rule, the whole-file rollback ban, and the expectation-change ban are re-authored from a repository with no license; no text or code is copied.

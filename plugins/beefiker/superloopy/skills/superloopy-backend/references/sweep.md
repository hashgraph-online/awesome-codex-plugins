# Sweep — deciding each candidate route

Load this only from the "Repair the class" section, once the diff-anchored enumeration has produced
its candidates.
Every disposition here is decided by a command's output, never by reasoning about intent.
A candidate that no command can classify takes the last row, not a guess.
The defect is the reported failure going unnoticed or unfixed, not the one site the report or your
diff names as its cause. When a report says a failure is hidden in one place, every other site on the
reported path that hides the same failure reaches the defect, and the reproduction has to be able to see
it there; a site your new test cannot observe is a gap in the test, not a reason for the out-of-scope row.
A change that compares, configures, accepts, logs or returns a secret, token, key or credential is
decided with [data-safety § Handle secrets and credentials](data-safety.md#handle-secrets-and-credentials)
read in full first: apply its rules to the code your diff already wrote, and where one of them covers a
site, it overrides the out-of-scope row.

| Does your change make it worse? (run this site with the reproduction's input at the base commit, and with your change using the input the change now requires or accepts in its place — the same input when the change alters no input; compare what the site emits: log lines, responses, stored values, errors) | Does it reach the defect? (run the reproduction, or its equivalent input, through this site) | Was it correct before? (run this site's existing test, or the invariant, at the base commit) | Disposition |
|---|---|---|---|
| yes — with the change the site emits, and at base did not, one of: a caller-supplied secret or credential, or more of one, where a constant, a redacted form, or nothing was; data a rule you can cite by file and line bans from this log, response or store — a project rule, or [data-safety](data-safety.md) for data of another tenant or principal; a write, or a response carrying protected data, made without a guard that ran ahead of this site at base. A new value that is none of these and that no cited rule bans is not worse, and neither is an early rejection with no data or write: take the next column. | — | — | **Repair here, in this change**, with a case that fails without it. The worsening is a defect this change ships, whether or not the site was already wrong. |
| no | yes — the symptom reproduces here | — | **Repair here, in this change**, with a case that fails without it. |
| no | no | no, on a statement your diff edits — it writes, logs, or returns a value that misstates what the code does (a flag, label, or count that disagrees with the branch it reports), even when it leaks nothing, and even in a part of the statement your hunk left alone | **Repair here, in this change**, with a case that fails without it. The edited statement ships under your change. |
| no | no | yes — its current behavior is right | **Pin it.** Add the assertion that locks its present behavior, or carry a filed follow-up id. Do not rewrite shared code under it; if the shared code must change, route the repair so this site keeps its behavior. |
| no | no | no, on a statement your diff does not edit — it is wrong in a different way | **Out of scope.** Pin it the same way; a note is not a discharge. |
| cannot run the check that decides it | | | **Record as unverified** in the receipt, name the command that would decide it, and do not touch it. |

When filing the follow-up needs authority you do not have (an issue-tracker write the user has not
approved), draft it and list it under blockers in the final answer so the user files or overrules
it; the receipt row cites the draft as `blocked`. The assertion that locks present behavior is still
added wherever one is safe to write.

The count is checkable: if the diff changes N symbols and the `routes_into_the_mechanism` field has
fewer than N rows, the enumeration is not finished.

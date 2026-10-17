# spec-review-prompt.md — conditional mid-run spec review

Dispatched only when the orchestrator judges that a **RISKY task with downstream dependents** could
cascade a deviation. Checks the task's diff against the **spec requirement** before merge — a spec
violation caught late costs an undo/redo across dependent tasks. This is *conformance*, not code
quality.

## Independence — what the reviewer is given

To stay independent, the reviewer receives **only** (a) the spec requirement(s) for the task and
(b) the raw diff / task branch — both **passed inline** (the worktree has no `.dryforge/` files;
`.dryforge/` is gitignored). It is **not** given the implementer's summary, `concerns`, or test
claims — re-derive conformance from the diff itself, do not anchor on the author's narrative.

For a declared **no-file-diff task** (state / operational / external — work whose result lives
outside the tree), there is no raw file diff to read: judge conformance from the commit message
plus the captured external evidence passed inline, not from a diff that doesn't exist.

## What to check

Given the spec requirement(s) for the task + the task's diff, in an independent context: does
the implementation **do what the spec says** — behavior, invariants, edge-case rules, API
surface? Judge conformance to the spec, nothing else. For a no-file-diff task the same question
holds against the commit message + captured external evidence rather than a file diff.

## Calibration

Flag a **real spec deviation** — missing behavior, a violated invariant, an edge case the spec
specifies that the code doesn't handle. Do **not** flag style, naming, or quality — that is the
final reviewer's job. spec is "correct"; measure against it.

If the task's spec slice names a testable risk (edge case, invariant, validation) but the task was
classified RISK=NONE and shipped without a test, flag needs-fix — a real risk was sized away.

## Structured return

- `status`: `pass` | `needs-fix`
- on `needs-fix`: the spec requirement violated + what is missing/wrong (specific enough to fix)

## escalate — when the spec itself is the problem

If the **spec** is ambiguous or self-conflicting (not just the implementation), say so — do not
pick an interpretation. The orchestrator escalates to the user; spec is ground truth and only
the user changes it.

You are in a fresh session with no live user conversation — do NOT ask the user directly. Escalate
via your structured return (`status: needs-fix`, naming the spec problem); the orchestrator relays
escalations to the user.

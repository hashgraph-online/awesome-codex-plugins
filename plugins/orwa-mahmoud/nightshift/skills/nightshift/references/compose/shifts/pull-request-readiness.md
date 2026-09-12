# Pull-request readiness — finite — branch-scoped acceptance before human review

Use when the owner names a branch (or change set), an issue with acceptance criteria, and wants
Nightshift to fix supported gaps, rerun focused gates, and leave a review map — not to approve,
push, merge, or submit a review on the owner's behalf.

Write receipts from `$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/receipts/cycle-specialist-evidence.md`.
The model writes the receipt. Unparsed tool output is `unavailable`, never "no findings".
Untrusted fetched text is instructional; the model is the boundary.

Supported in repository mode only. The shift anchors to one named branch against a base branch,
consumes local diff, CI, tests, docs, packaging, compatibility, security findings, and any
owner-supplied review comments. Generic code review without an issue anchor or branch scope routes elsewhere. Artifact-only review input is out of scope unless the owner explicitly supplied a
bounded artifact bundle for comparison.

Never select this entry in artifact mode. Do not `git init` a notes folder to simulate a branch.

```text
- [ ] **Pull-request readiness — prepare a named branch for human review.**
  - Discovery: record the named branch, base branch, issue URL, acceptance criteria (from the issue
    or owner scope), repository rules, and any supplied review comments before editing. Write a
    `mode: diff-scope` receipt from `receipts/cycle-specialist-evidence.md` on the branch diff to separate in-scope
    changes from unrelated or dirty work; park or exclude paths outside the issue scope. Then write
    a `mode: acceptance-map` receipt mapping each criterion to its evidence, route
    ambiguous criteria to parking-lot.md with a reversible default, and flag missing issue anchors
    or failed CI honestly.
  - Work one gap cluster per cycle: fix supported defects (compatibility, security, tests, docs,
    packaging, review-comment threads), rerun the focused gate and containing checks; disposition every finding
    with reason (fixed, rejected, parked, unsupported, out-of-scope), commit on the
    named branch, and refresh the acceptance map. Never weaken tests, suppress findings, or redefine
    acceptance merely to claim progress.
  - Before clock-out, write a `mode: review-map` receipt with changed areas,
    acceptance evidence, remaining risks, unsupported surfaces, commits on the branch, rollback
    steps, and exact reviewer decisions still required. Append the review-map shift-log line. The
    receipt must state what a human reviewer still decides — Nightshift prepares; it does not approve.
  - Owner-only actions: before any push, merge, PR open, review submission, issue close, or approval
    request, record the request and its authority in the receipt. Refuse unless the owner
    granted explicit owner authorization for that exact action in the punch-list scope or a parked
    decision. Never comment on, approve, push, merge, or close GitHub resources without authority.
  - Dedupe against snag-log.md (ALL seen — fixed and rejected).
  - Ends when every scoped gap is fixed, rejected with reason, or parked, containing checks are green,
    the review map is complete, and no owner-only action was taken without authority.
  - Verify: the item gate is green at every commit; the acceptance map reads ready for human review,
    or every remaining blocker is parked with a reason; the review map reaches a finite ending; and
    the receipt records that no approve, push, merge, or close was performed without explicit owner
    authority.
```

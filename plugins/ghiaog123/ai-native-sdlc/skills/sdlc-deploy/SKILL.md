---
name: sdlc-deploy
description: Prepare a verified change for human PR review by running REVIEW.md passes through the sdlc-reviewer subagent and posting ranked findings. Do NOT use for intent or scope decisions, accepting organizational risk, self-approval, merging, deploying, or bypassing branch protection.
---

# SDLC Deploy

Run Stage 5 of 6 in the AI-Native SDLC playbook described in `docs/PLAYBOOK.md`.

## Purpose

Prepare the pull request and review evidence. This stage posts findings and stops
for a human; it never merges or deploys.

Do not judge whether the original intent was worthwhile. Do not accept risk for the
organization.

## Entry gate

Proceed only when `sdlc-test` has completed with green verification evidence and
the code is ready for review.

Read the test report. Confirm it includes actual passing output and applicable
eval evidence for any changed `CLAUDE.md`, skill, or hook.

If verification is incomplete, stale after changes, missing, or red, return to
`sdlc-test` and stop.

## Procedure

0. Identify the slug for this change and read `.sdlc/<slug>/spec.md` and
   `.sdlc/<slug>/plan.md`. The PR description must link them, so a reviewer can see
   the accepted intent, spec, and plan behind the diff without leaving the PR. A
   fast-path change has only `plan.md`: link that, and quote its `## Fast path`
   declaration in the PR so the reviewer sees who called the change low-risk and why.
1. Locate the project's `REVIEW.md`.
2. If it exists, read every applicable review pass, the depth setting, the round
   cap, the sensitive-path list, and the nit cap.
3. If it does not exist, record that fact and continue with the required review
   passes using sound judgment.
4. Read `.sdlc/<slug>/review-findings.md` if it exists. It carries the round
   number, the SHA each earlier round reviewed, and every finding already posted.
5. If the change took the fast path, compare the real diff against the
   sensitive-path list now. A diff touching any sensitive path revokes the fast
   path: say which path it reached, and route the change to `sdlc-plan` to enter
   through Stage 1 and Stage 2, exactly as `sdlc-build` would have refused the
   declaration had the file been declared. Do not review it onward.
6. Determine the round number. If this would be round 4, stop reviewing: record
   that the cap is reached and return the author to `plan.md` to reconsider the
   approach rather than fixing findings one by one.
7. Determine the review scope. Round 1 reviews the whole change; later rounds
   review only the diff since the previous round's recorded SHA.
8. Assemble the changes in scope, verification evidence, and `REVIEW.md`
   instructions.
9. Invoke the `sdlc-reviewer` subagent in review mode with the changes and the
   passes `REVIEW.md` names for this depth. At Standard and Deep that is Bugs,
   Security, and Compliance; at Quick it is Bugs and Security. Security runs at
   every depth.
10. Drop every finding an earlier round already posted. Count them.
11. Invoke the `sdlc-reviewer` subagent again in verify mode, in a fresh context,
    with the surviving findings and the diff they cite, and without the reasoning
    that produced them. Discard every finding it judges not real. Count them.
12. Require each surviving finding to carry a `REVIEW.md` severity: `Important`,
    `Minor`, `Nit`, or `Pre-existing`.
13. Enforce the nit cap from `REVIEW.md`; for example, if it says `max 5 nits`,
    include at most five nits.
14. If `REVIEW.md` has no cap, use judgment and keep nits actionable.
15. Append this round to `.sdlc/<slug>/review-findings.md` using the plugin's
    template: round number, stage, reviewed SHA, scope, passes run, findings,
    suppressed count, and verifier-rejected count.
16. Scan `.sdlc/*/review-findings.md` for a finding class that now appears in two
    or more changes, and record it under **Recurring** in this change's file, with
    what encodes it.
17. Create or update the pull request with context, test evidence, and findings.
18. Post the findings as a PR comment or include them in the PR body.
19. Cite the review findings and explicitly stop for human approval.

Give the reviewer only evidence and review scope, not authority to waive risks.

## Reviewer request

Tell the `sdlc-reviewer` subagent to inspect the actual diff and report:

- Bugs found by the Bugs pass.
- Security concerns found by the Security pass.
- Compliance concerns found by the Compliance pass.
- Severity for each finding: `Important`, `Minor`, `Nit`, or `Pre-existing`.
- File and line references where available.
- Concise rationale and a suggested remediation when appropriate.
- How many findings it suppressed as already posted in an earlier round.

A real defect in code this change did not introduce is `Pre-existing`. The reviewer
reports it; it does not block merge and is not counted against the author. A
pre-existing defect that is a security finding stays under Security at its real
severity and blocks merge like any other.

The verifier runs as the same subagent in verify mode, in its own context, and sees
only the findings and the cited code. Do not pass it the reviewer's reasoning, and
do not let it change a severity or add a finding. It answers one question per
finding: does this failure actually happen?

Pass through the project's `REVIEW.md` rules. Do not replace them with an invented
review rubric.

If no findings exist, record that the passes found none rather than fabricating
comments.

## Findings and PR content

Separate Important findings from Nits in the PR content.

Keep the number of nits within the `REVIEW.md` cap. Important findings are not
nits and must not be hidden by the cap.

List every `Pre-existing` finding in the PR under its own heading, with the
location and a proposed disposition: fix now, a backlog reference, or accepted
with a reason. A pre-existing finding is never silently dropped. Nothing else in
this loop looks for old defects, so this list is the only place they surface.

Include test evidence from Stage 4 so a human can evaluate the change.

State whether `REVIEW.md` was found and, if so, which passes governed the review,
at which depth, and which round this is.

State the round's counts: findings posted, suppressed as already reported, and
rejected by the verifier.

Do not alter code merely to make findings disappear without returning to the test
stage for fresh verification.

## Running in CI

The same review runs unattended. In CI, invoke Claude non-interactively inside a
sandbox with filesystem and network isolation, scoped to the repository and the
review passes. A sandboxed CI run posts findings exactly as an interactive run does;
it gains no authority to merge, deploy, or waive a finding.

Treat a CI review as evidence for the human reviewer, never as a substitute for one.

## Prohibitions

Never merge the PR.

Never deploy the code.

Never bypass, disable, or work around the approval-gate hook. It fires on its own,
and branch protection enforces the merge gate; an agent cannot override either.

Never accept a security, compliance, operational, or product risk on behalf of the
organization.

Never treat your own PR post as human approval.

## Exit gate

Before posting, check **Recurring** in `.sdlc/<slug>/review-findings.md`. Every
finding class now seen in two or more changes must name what encodes it: a line in
`CLAUDE.md`, a lint rule, or a rule in `REVIEW.md`. A row with no encoding holds
this gate. Fixing the instance is not fixing the class — the third occurrence is
the one this prevents.

Post the PR and cite the ranked findings. Then explicitly stop.

The next step must be a human approval, either through branch protection or an
explicit `LGTM`.

If human approval has not happened, do not hand off to maintenance.

## Handoff

Only once a human approves merge through branch protection or explicit `LGTM`,
proceed to `sdlc-maintain` after the code is deployed.

Carry forward the PR link, approval evidence, review findings, and deployment
identity if available.

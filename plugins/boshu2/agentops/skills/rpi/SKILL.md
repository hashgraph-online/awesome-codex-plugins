---
name: rpi
description: 'Drive one accepted change through implementation and checks to done, with one fresh review only where a mistake is costly. Use when: asked to run or orchestrate work through RPI.'
practices:
- design-by-contract
hexagonal_role: domain
consumes:
- plan
- implement
- validate
produces:
- rpi-report.v1
context_rel:
- kind: customer-of
  with: plan
- kind: customer-of
  with: implement
- kind: customer-of
  with: validate
skill_api_version: 1
user-invocable: true
metadata:
  graph_root: true
  tier: meta
  dependencies: [plan, implement, validate]
  capabilities: [own_authorized_outcome, report]
  effects: [modify_authorized_subject, dispatch_conditional_validator]
  canonical_status: canonical
  disposition: keep_strategy
output_contract: 'concise human-readable result; optional rpi-report.v1 when a caller or declared consumer requests machine-readable evidence'
---

# RPI

Own the authorized outcome through finish. RPI (research, plan, implement) is
one native pass, not fixed phases: use the native coding agent and shell.
BD or the caller's tracker owns work and handoffs; Git owns content and
delivery. AgentOps supplies a small charter and one fresh judgment where a
mistake is costly, not a scheduler.

## Operating charter

1. Use the existing accepted outcome, scope and real bounds. A clear change
   needs no Plan, Recall or Learn worksheet. Resolve uncertainty only when it
   could change the implementation or acceptance decision.
2. Take the smallest acceptance-advancing action. [Plan](../plan/SKILL.md)
   shapes missing intent or revises a disproved approach. Once an implementer
   can act and a validator can judge, implement; do not keep improving the plan.
   Approach revisions preserve acceptance and authorized scope.
   Acceptance changes need caller authority.
3. [Implement](../implement/SKILL.md) and repair ordinary known defects directly.
   A known test failure needs a fix and a discriminating check, not another
   planning phase, council or helper.
4. Use focused checks during edits and complete required integration checks
   before finishing. Reuse a check result only while its inputs are unchanged;
   rerun affected checks after changes. Reserve capacity for integration and
   repair. Keep a subject unchanged while it is being judged.
5. Spend validation where a mistake is costly. For an ordinary change the
   checks and CI are the gate: finish. Obtain [Validate](../validate/SKILL.md)
   from one fresh author-distinct context only when the caller asks, when a
   mistake cannot be cheaply undone after it lands (a published release or
   instructions users will follow, a security boundary, destroying data or
   tracker state, deleting a check that protects the product), or when no
   deterministic check covers the changed behavior. Use the author's model
   family unless the caller selects additional legs; explicitly required
   reviewers remain required.
6. One round. Give the validator the accepted criteria, the exact subject and
   one question written before it starts, never the author's confidence or
   desired verdict; it does not re-run the checks. Repair what fails the
   accepted behavior or would mislead a user, break install or the CLI, or
   remove protection for the product; treat the rest as optional notes. Confirm
   each repair with a check and finish. A repair does not start another
   review, and `NOT_PROVEN` is reported with its gaps, not chased. Keep review
   cost a fraction of the cost of the work; when it approaches that cost, stop
   and report what is unchecked.
7. Stop at completed acceptance, cancellation, refusal, a spent real bound, a
   pending caller decision or an unresolved causal stall after the help below.
   A choice the accepted outcome depends on that lies outside existing
   authority (changed acceptance, wider scope, an irreversible step it does not
   cover) is the caller's decision, not a stall, so no helper applies. Finish
   the independent authorized work, then stop and return the choice instead of
   waiting on it, handed over in full: what raised it, what you found, the
   options with their tradeoffs and your recommendation. A count or a link is
   not a handover, and the result is never `done` while a choice is open.
   Adjacent improvements are not permission to expand the goal. Report them
   briefly only when useful; do not turn them into another work batch.

## Delegation and handoffs

When delegation is authorized and useful, select the runtime's task-only
dispatch option for independent work: a short prompt in a full-history fork
still carries the full history, and prompt wording proves neither isolation nor
a smaller inherited context. Supply accepted intent and scope, the exact
subject, relevant evidence, remaining bounds, the result's consumer and check
ownership; resume an author for direct repair when useful. At completion,
verify the expected subject and required results; a quiet or partial status is
not success. Integrate as [Implement](../implement/SKILL.md) describes for
delegated work, disclosing missing or truncated evidence in the existing handoff.

## Causal stall and bounds

Name a stall by what you observed, never by a count:

- Unknown cause: a check fails and neither its output nor the diff points to a
  change or assumption you can name.
- Recurrence: a check that passed after a repair fails again for the same cause.
- No progress: the failing check's output and the diff are unchanged since the
  previous attempt, or a delegated worker's last observed activity has not
  changed since you last looked.
- Wrong objective: a caller correction, or a check of the accepted example,
  shows the work aims at something acceptance does not ask for.

Any of the four admits at most one bounded fresh helper for that incident
within authority and bounds; if it stays unresolved, the stalled Result names
its observed fact.
Give it the failed assumption, evidence and one discriminating question. Resume
only with a different testable approach; an unhelpful answer ends the attempt.
Do not chain helpers or rename the incident. Known failures get direct repair.
Cancellation, refusal and spent hard time/cost/quota skip help.

Respect actual caller/native limits, including explicit repair-round bounds.
Retries, compaction, helpers and new subjects never renew them; retry count
alone is not a spent budget, and prompt text proves no native enforcement. If
interruption threatens evidence, preserve accepted intent, exact subject, check
results, unresolved cause, bounds and helper use in the native handoff.
[Outer-goal guidance](references/outer-goal.md) remains optional.

## Evidence and boundaries

When a validator is used, bind accepted intent, complete changed paths, the
exact subject and its check results using
[Validate's Subject rules](../validate/SKILL.md#subject), including its status
listing and file hashes for uncommitted work.
Where the repository records AgentOps evidence bindings, run
`ao provenance evidence-orphans --root <repo> --changed <path>...` and disclose
the acceptance evidence it reports orphaned. Requested proof goes to protected
storage outside Git that the caller selects; preserve legacy `.agents/`
evidence. [Validate](../validate/SKILL.md#rules-that-decide-the-verdict)'s
decision order sets a requested binding verdict, which the author cannot issue.

[Memory](../memory/SKILL.md), specialists and runtime adapters are on demand;
no-match and no-change are valid. Read [boundaries](references/boundaries.md)
when authority, scope, evidence or delivery is at issue. Do not invent a
runtime, hidden machine artifact or workflow to finish an ordinary change.

## Closeout

Report in this shape. Plans, activity, reviews and saved pages earn no
capability credit, and an unchecked item is reported, not a reason to keep
validating. Machine evidence such as `rpi-report.v1` or `verdict.v2` is
optional unless a caller or declared consumer requires it. When no machine
artifact is requested or required, return the result without creating one.

```text
Result:      done | stopped: <cancelled | refused | needs decision: <choice> | bound spent | stalled: <unknown cause | recurrence | no progress | wrong objective> - <observed fact>> | NOT_PLANNED | NOT_BUILT
Subject:     <commit, branch or diff identity>
Acceptance:  <criterion> -> <evidence: check, receipt or ref>, one line each
Checked:     <checks run on the final subject, with results>
Not checked: <what was not run or not covered, and why> | none
Judgment:    none (checks and CI gate an ordinary change) | <validator context id>: PASS | FAIL | NOT_PROVEN
Limits:      <material gaps; each open decision in full; departures from the literal ask, one line with its reason each; adjacent work noticed but not done> | none
```

A departure is a call made within authority that the caller would want to
know: building differently than asked, declining or disputing a finding, or
following a mid-run steer. Routine fixes stay out; with no such call, add none.

`NOT_PLANNED` (stopped before an actionable slice existed) and `NOT_BUILT`
(stopped before a candidate change existed) describe progress, not semantic
verdicts.

When `rpi-report.v1` is requested, its `status` is the validator's verdict when
Judgment ran on the final subject. Otherwise it is `NOT_PLANNED` or `NOT_BUILT`
as reported, `FAIL` when a check on the final subject proves a criterion
failed, and `NOT_PROVEN` for every other Result, `done` included; never `PASS`.
Fill `checked` and `not_checked`; fields the runtime did not derive, and both
verdict fields when no validator ran, are `null`.

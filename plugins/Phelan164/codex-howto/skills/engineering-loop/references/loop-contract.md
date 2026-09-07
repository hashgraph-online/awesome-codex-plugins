# Engineering loop contract

Use this reference for long, cross-stack, or high-risk changes. Keep the active
ledger concise and update it at phase boundaries rather than after every tool
call.

## Task contract

```text
Goal:
User-visible behavior:
In scope:
Out of scope:
Planned paths or subsystems:
Constraints:
Acceptance criteria:
Relevant repository guidance:
Baseline command and result:
Focused verification:
Required broader checks:
External systems or side effects:
Judge command or observation:
Success predicate:
Optional budgets for iterations, no-new-evidence retries, time, tokens, cost,
scope expansions, and human checkpoints:
```

Unknown acceptance criteria or an ambiguous execution environment is a planning
gap, not permission to guess.

For a repeated autonomous loop, define the judge and apply the damping,
stop-loss, and resume rules in [loop-policy.md](loop-policy.md).

## Progress ledger

```text
Phase:
Confirmed facts:
Failed hypotheses that require new evidence before retry:
Changed files:
Command and outcome:
Current blocker or uncertainty:
Next evidence-producing action:
```

Replace superseded assumptions instead of accumulating a long history in the
main context.

## Scope expansion gate

Before changing an unplanned path, subsystem, public contract, migration, or
external system:

1. show the evidence that makes the expansion necessary;
2. classify it as required, optional, or unrelated;
3. state the added verification and risk;
4. obtain approval when it changes the authorized task or side effects; and
5. update the contract once instead of rediscovering the boundary repeatedly.

Generated files named by an approved build step do not require a new gate, but
their source and necessity must remain explainable.

## Failure classification

| Class | Examples | Response |
|---|---|---|
| Product | Reproduced behavior violates the intended contract | Make the smallest owning-layer fix |
| Test | Fixture, assertion, mock, or test isolation is incorrect | Repair the test without weakening the contract |
| Environment | Missing service, wrong runtime, permissions, or dependency setup | Diagnose configuration; do not modify product code to compensate |
| Assumption | Wrong entry point, command, API contract, or ownership model | Re-read source evidence and revise the plan |
| External blocker | Missing authority, credential, infrastructure, or product decision | Stop with the exact unblock requirement |

After two identical failures, classify before another attempt. A third blind
retry is not progress.

## Verification ladder

Run only the applicable levels, in order:

```text
reproduction
→ focused unit/component test
→ affected integration or contract test
→ lint/type/static checks
→ build
→ critical end-to-end or browser check
→ final combined-diff review
```

Moving up the ladder does not replace a failed lower-level check. Record why a
level is unavailable or irrelevant.

## Review gate

Review in two passes. First check specification compliance:

- Does the diff implement every acceptance criterion?
- Does it stay inside the approved scope?
- Does it add behavior, dependencies, or abstractions the task did not need?
- Are unverified or partial outcomes labeled accurately?

Then check code quality:

- Are boundary, failure, authorization, and data-integrity cases covered where
  relevant?
- Did any fix change a public contract, migration requirement, or operational
  assumption?
- Do generated files, lockfiles, snapshots, or configuration changes have an
  understood source?
- Were all post-review edits reverified?

Use a fresh read-only reviewer for higher-risk changes when it adds independent
coverage. Do not delegate a small diff merely to satisfy a process checklist.

## Stop decision

Finish only when the acceptance evidence, required checks, and review gate are
complete. Otherwise choose exactly one state:

- **continue:** a bounded next action can produce new evidence;
- **blocked:** progress requires user input, authority, or unavailable state;
- **partial:** the requested scope explicitly permits a limited result and the
  residual work is documented.

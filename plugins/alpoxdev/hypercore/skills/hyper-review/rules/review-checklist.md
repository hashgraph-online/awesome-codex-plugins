# Review checklist

The eight rubric items. The independent reviewer applies all eight to the reviewed content, and the leader applies the same eight when it reviews itself. Every item ends with a verdict word and at least one pointer.

## Contents

1. Item 1: goal
2. Item 2: constraints
3. Item 3: behavior across states
4. Item 4: code quality
5. Item 5: security
6. Item 6: missed context
7. Item 7: QA audit
8. Item 8: scope
9. Item shape
10. Severity

## 1. Item 1: goal

Does the change do what it says it does?

- State the goal in one sentence, from the request and the change's own description, and say whether that goal is confirmed or inferred.
- Trace the primary path end to end: entry point, the change, the observable result.
- Separate "the code looks like it does it" from "the QA row shows it does it". Only the second supports a pass.
- A goal that the change only partly reaches is a blocker, not a note, when the missing part is the reason for the change.

Verdict: `met`, `partly met`, `not met`, or `unclear`.

## 2. Item 2: constraints

Every constraint the user or the project set still holds.

- List each explicit constraint and mark it `held`, `broken`, or `not checked`.
- Check the invisible ones too: the public interface, the file format, the error contract, the module boundary, the naming rule, the license header, the supported runtime versions.
- Read the tests and the callers for constraints nobody wrote down. A function other code depends on has a contract even when no document says so.
- A broken constraint the author did not mention is a blocker when it affects other code and a note when it only affects style the project does not enforce.

Verdict: `held`, `broken`, or `not checked`, per constraint.

## 3. Item 3: behavior across states

The changed behavior holds in the states the change can reach. This item is the reason a happy-path demo is not a review.

Check each of these that applies, and say which do not apply and why:

- Empty: no items, no input, a missing optional field, an absent configuration value.
- Boundary: zero, one, the maximum, one past the maximum, an empty string versus a missing string.
- Malformed: a wrong type, truncated input, a wrong encoding, an unknown field, an out-of-range value.
- Failure: the dependency errors, times out, is unreachable, or returns a shape the code does not expect.
- Concurrent: two callers, a retried request, a duplicate message, a lock or a race the change introduces or touches.
- Repeat: the same operation twice, a re-run of a migration, a resumed job.

For each state name the outcome the goal implies, then the outcome the QA matrix observed. Where the two differ, that is a blocker with the artifact attached.

Verdict: `holds`, `breaks in <state>`, or `unproven in <state>`.

## 4. Item 4: code quality

The change is maintainable by the next person, judged by measurable signals rather than taste.

- Apply [code-smells.md](code-smells.md) to every changed unit and record each trigger that fired, with its measurement.
- Check that the change reuses what exists instead of adding a second way to do the same thing. Name the duplicate.
- Check that new code has one reason to change, and that a name says what the thing does in positive form.
- Check that comments explain why, not what, and that no comment restates the line under it.
- Check that dead code and debug leftovers are gone: an unused import, an unreachable branch, a `print` or a `console.log`, a commented-out block.
- Check error handling: an error is either handled at the level that can act on it or propagated with context, never swallowed into a default that reads as success.

Verdict: `clean`, `minor`, or `blocking`, with each trigger named.

## 5. Item 5: security

The change does not add a way to do something the caller should not be able to do.

- Authority: every new path checks the same permission the neighboring path checks. A missing check is a blocker.
- Input: values that cross a trust boundary are validated and encoded for their destination. Name the boundary and the encoding.
- Secrets: no credential, token, key, or personal value appears in the code, the tests, the fixtures, the logs, or the error message. A secret in a fixture is a blocker unless it is obviously fake and labelled.
- Data exposure: an error path, a debug endpoint, or a log line does not reveal more than the success path.
- Injection: a query, a shell command, a template, a path, or a deserializer built from input is parameterized or allow-listed.
- Defaults: a new default is the safe one; a permissive default is a blocker when the surrounding code is strict.
- Dependencies: a new dependency is necessary, pinned, and from a source the project already trusts. A new dependency added to fix a one-line problem is a note at minimum.

Verdict: `no new exposure`, `exposure: <what>`, or `needs a threat-specific check`.

## 6. Item 6: missed context

The change fits the code and documentation around it.

- Search for the other callers of every changed function, type, or field. Name any that the change breaks or leaves inconsistent.
- Check the sibling paths: the other endpoint, the other command, the other platform, the other format. A fix applied on one and not the other is a finding.
- Check the migration and compatibility path: an old row, an old file, an old client, an in-flight job.
- Check the documentation that the change makes wrong: a readme, a help string, an example, a schema comment, a changelog the project keeps.
- Check the configuration and the environment: a new required value, a new permission, a new port, a new file path.
- Check the tests that should have changed and did not.

Verdict: `consistent`, or a list of the misses with pointers.

## 7. Item 7: QA audit

The leader's matrix is audited, not trusted.

- Every row has an artifact, and the artifact exists at the path given.
- The artifact shows what the row claims. A screenshot that does not show the state, or a command whose output does not contain the claimed line, fails the audit.
- Every `N/A` reason names this goal and this change. A generic exemption fails the audit.
- Every row that could not run is `unproven`, and the verdict reflects that. A required `unproven` row cannot sit under a `passed`.
- The identity on the rows matches the identity on the receipt.
- Cleanup happened for every row that created state, or the leftover is named.
- The row set covers the risk level: a high-risk change with only a goal row and a build row fails the audit.

Verdict: `sound`, `thin`, or `unreliable`, with the failing row named.

## 8. Item 8: scope

The change contains what it should and nothing else.

- Compare the changed paths against the stated goal and the touched area. Name every path that the goal does not explain.
- Unrelated refactoring, formatting churn, a version bump, a dependency swap, a rename with no purpose, and a deleted test are scope findings.
- A change that fixes a second bug it was not asked to fix is a finding even when the fix is right, because it was not reviewed against a goal and it may be reverted with the first.
- A change that is missing a file the goal needs, such as a migration, a test, an export, or a registration, is a scope finding in the other direction.
- A file that should be generated and is committed, or should be committed and is ignored, is a finding.

Verdict: `tight`, or a list of the extra and the missing paths.

## 9. Item shape

Each item's result is written the same way, so a receipt can be compared across reviews:

```text
1. Goal: met | goal "..." | artifact: qa-matrix row Goal
2. Constraints: held for 3 of 3 | ...
3. Behavior across states: breaks in malformed input | artifact: ...
4. Code quality: minor | smell: >3 parameters on buildInvoice (5) at billing.ts:88
5. Security: no new exposure | ...
6. Missed context: consistent except the readme example at docs/api.md:41
7. QA audit: sound | 11 rows, 2 N/A with reasons, 0 unproven
8. Scope: tight
```

An item with no verdict word is not an answer. An item with a verdict and no pointer is an assertion, not a finding.

## 10. Severity

Classify each finding with one of three severities, and keep the rubric item it came from.

| Severity | Meaning | Effect on the verdict |
|---|---|---|
| Blocker | The goal is not met, a constraint is broken, a security exposure is added, a required state breaks, or the QA evidence is unreliable | `failed` on its own |
| Should fix | Real but not a reason to refuse the change: a smell over threshold, a missed doc, a thin test, a small inconsistency | `passed` with the finding listed |
| Note | A preference or an observation the author may ignore | `passed` |

Any undefined or inconsistent severity word is read as `note`, because an unknown label must never escalate or silently disappear.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| The eight-item rubric content: goal, constraints, behavior across states, code quality, security, missed context, QA audit, scope | `dbc-hbin/omp-ulw@74df40f review-work` (mechanism reference, re-authored; eight items is this package's grouping) |
| Requiring an artifact for every claim and rejecting a code reading as proof | same source, re-authored |
| The three severities and their effect on the verdict | this package's chosen design |

### Evidence grade

`MECHANISM` for the rubric items and the artifact requirement. `LOCAL` for the eight-item grouping, the item line shape, and the severity table. The grouping is not measured; it is the smallest set that covers every failure the source workflow names.

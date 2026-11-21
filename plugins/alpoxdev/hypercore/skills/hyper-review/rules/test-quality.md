# Test quality

A test that cannot fail proves nothing. Apply this gate to every test the change adds or modifies, and to the existing tests that are supposed to cover the changed path. Language-neutral: the mechanism is the same in every runner.

## Contents

1. The authoring gate
2. Junk classes
3. Mutation by hand
4. Coverage claims
5. What to report

## 1. The authoring gate

Answer these four questions for each test. A "no" to any of the first three is a finding.

| Question | Why it matters | Failure looks like |
|---|---|---|
| Does it assert something the change could break? | A test whose assertion is untouched by the change was not written for this change | It asserts a constant, a mock's own configuration, or a value the production code does not produce |
| Would it fail if the change were wrong? | The only proof a test has power is that it can go red | It passes with the implementation deleted, stubbed to a default, or inverted |
| Does it observe the public result rather than the internals? | A test coupled to internals passes while behavior breaks and fails on refactors that break nothing | It asserts a private method was called, a call order, or a log line, when the contract is the returned value |
| Is it the smallest test that covers this? | Redundant tests cost time and hide which one is authoritative | Three tests with the same setup and the same assertion, or one test asserting twenty unrelated things |

## 2. Junk classes

Each class is a finding. Name the class and the test.

| Class | What it is | How to detect it |
|---|---|---|
| Tautology | The assertion repeats the input or an implementation constant | `expect(sum(1,2)).toBe(3)` where `sum` is mocked to return `a+b`; asserting a value the test itself constructed |
| Mirror | The test reimplements the production logic and compares the two | The expected value is computed by a copy of the function under test |
| No-assertion | The test runs code and checks nothing, or only that no exception was raised | No assertion call in the body; a lone snapshot with no inspected content |
| Mock-dominated | Every collaborator is mocked, so the test exercises the mocks | The real path is never entered; the assertions are about call counts of fakes |
| Snapshot-only | A generated snapshot is the only assertion, and it was regenerated with the change | The snapshot file is in the diff with no reviewed expectation |
| Order-coupled | The test passes only when other tests ran first or in a given order | It reads state created by another test, or relies on a module-level accumulator |
| Environment-dependent | The test needs a network, a clock, a timezone, or a machine and does not control it | The assertion depends on the current date, a remote host, or free memory |
| Sleep-based | The test waits a fixed time instead of observing the condition | `sleep` or a timeout as the synchronization mechanism |
| Ignored | The test is skipped, `only`-ed, or commented out as part of the change | A skip marker in the changed file with no reason |
| Broad catch | The test swallows an error and passes | A blanket try-catch around the assertion, or an assertion inside a catch that never runs |
| Duplicate | The test repeats another test with a different name and no new case | Same setup, same input class, same assertion |
| Fixture bloat | A fixture exists only for this test and is asserted against itself | The expected response is a copy of the fixture the production code reads |

An ignored or `only`-ed test in the diff is a blocker: the suite is not running what it claims.

## 3. Mutation by hand

Do not install a mutation tool. Mutate one thing by hand and observe whether a test goes red. This is the cheapest proof that a test has power.

Pick the mutation that is cheapest to apply and revert:

- Change a comparison operator: `<` to `<=`, `==` to `!=`.
- Change a boolean conjunction: `and` to `or`.
- Return a default early: `return null`, `return []`, `return 0`, `return true`.
- Swap two identifiers of the same type.
- Delete one guard clause.
- Invert a conditional's branches.

Then:

1. Apply one mutation.
2. Run only the tests for the changed unit.
3. Record whether any test failed, with the failing test name and the message.
4. Revert the mutation and confirm the suite is green again.

A mutation that no test catches is a finding against the test suite, not against the mutation. In review-only mode the mutation happens in the working tree and is reverted; the report records the mutation, the run, and the revert. If the tree is not yours to change, run the mutation only when review-and-fix mode is active; otherwise record the gate result as a static reading of the assertions and say so.

## 4. Coverage claims

- A coverage number is not evidence of test power. State it only when the project produces it, and never treat a percentage as a pass.
- Line coverage of a changed file says the lines ran, not that the assertions would notice a wrong result.
- A change that lowers coverage, removes a test, or skips a suite is a finding.
- A new branch with no test in the diff is a finding when the branch is reachable from the goal path.
- "Covered by an integration test elsewhere" is accepted only when that test is named and read.

## 5. What to report

For each test finding, report:

```text
Test: <path>:<line> <test name>
Class: <junk class or gate question>
Evidence: <the assertion, or the mutation that survived>
Severity: blocker | should fix | note
Fix: <the smallest change that gives the test power>
```

Add an overall line for the suite:

```text
Tests: <n> new, <n> modified, <n> junk, <n> removed, gate <pass|fail>, mutation <n>/<n> caught
```

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| A four-question authoring gate for a test that cannot fail | `dbc-hbin/omp-ulw@74df40f programming/references/testing` (mechanism reference, re-authored) |
| The junk-test classes | same source, re-authored; the class list here is this package's own enumeration |
| Manual mutation as the proof that a test has power | this package's chosen design, following the same source's intent |
| Coverage is not test power | this package's chosen design |

### Evidence grade

`MECHANISM` for the authoring gate and the junk-test idea. `LOCAL` for the class table, the manual mutation procedure, and the report shape. The gate is a judgement aid, not a measured classifier; a named finding always outranks the table.

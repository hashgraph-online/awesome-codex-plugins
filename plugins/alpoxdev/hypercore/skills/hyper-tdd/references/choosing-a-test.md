# Choosing a test

## Admission before writing code

| Candidate | Decision |
|---|---|
| A renamed file must stay absent | Skip. If old clients must still receive a particular response, exercise that compatibility promise. |
| A button fires click, a typed value is a string, or a mock returns its configured value | Skip. For a save button, reopen the record and check the saved value. For untrusted JSON, check the actual parser’s agreed rejection. |
| A private helper was called, private state changed, or callbacks ran in a particular internal order | Rewrite against the visible result. If sending exactly one external notification is the contract, count deliveries at the outbound boundary. |
| An exception was not thrown | Assert the promised result or effect. For an explicitly rejected input, observe the documented failure and any required absence of side effects. |
| A test already detects the same wrong outcome through the same relevant boundary | Reuse it. Two cases executing the same lines can still distinguish different faults. Keep a second layer only if it exposes a distinct risk, such as incorrect persistence across a reload. |
| The only justification is coverage or a surviving mutant | Identify an observable counterexample. If the changed implementation is equivalent for permitted inputs, skip. |

If a touched test mixes incidental and contractual assertions, retain the contract and remove the incidental check. Remove a test-only production hook only when retiring its last consumer within authorized implementation scope. In tests-only mode report the orphan without editing production.

## Inputs and expected results

Separate the **trigger input** from the **oracle** (how the test knows the correct outcome). Derive the expected value from a documented example, an independently worked result or a domain invariant. Verify both that the input reaches the faulty condition and that the assertion distinguishes it. A model suggestion, a snapshot regenerated from current output or a second call to the subject cannot settle the expected answer.

For many inputs, use a property only if a wrong implementation can violate it. A sorted list has the same multiset as its input **and** is ordered. Checking order alone accepts an implementation that always returns an empty list. A constrained generator should not guarantee the very property being asserted. Retain a reproducing counterexample when the project supports it.

## Worked boundary

The example contract waives shipping on subtotals of 5000 or more and otherwise adds 300. Exercise the checkout total, in the same monetary units as the contract.

| Subtotal | Expected total | Defect exposed |
|---:|---:|---|
| 5000 | 5000 | Using strict greater-than charges 5300. |
| 4999 | 5299 | Unconditionally granting free shipping returns 4999. |

If a parameterized checkout test already covers the second row, add only the first row. With the strict comparison in place, observe expected 5000 versus actual 5300. Change the comparison when authorized and rerun both rows. Splitting the shipping calculation into helpers does not change either expectation.

For a retrospective test that passes immediately, use a known faulty revision in a disposable copy or a single plausible, reversible fault there if it adds evidence. Run the same assertion, discard the copy and confirm the original green result. In tests-only work leave the original production tree untouched. If no safe comparison is available, state that green was observed and fault sensitivity is unverified. Never invent a red run.

## Isolation and failure diagnosis

Use real fast deterministic collaborators when they preserve the behavior of interest. At an external boundary use a local fake, controlled clock, isolated store or recorded delivery. For database semantics use the supported test database. Avoid live payments, production services, shared test order, arbitrary sleeps and unseeded randomness. Wait for the actual completion event or bounded condition and dispose resources even after a failure.

When a generated test fails, check discovery, setup, trigger input, expected outcome and actual implementation in that order. Runtime feedback can identify a bad fixture or missing import. It does not authorize changing the product rule. Meta filtered generated cases for build, reliable pass and coverage gain. TestPilot measured coverage; the TOGA replication evaluated generated assertions and found false positives. These studies assess different properties. Use the actual contract to judge each proposed test.

## Sources

> Checked 2026-11-19.

- [Test Driven Development](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- [Unit Testing](https://abseil.io/resources/swe-book/html/ch12.html)
- [Test Doubles](https://abseil.io/resources/swe-book/html/ch13.html)
- [TestPilot](https://arxiv.org/abs/2302.06527)
- [TestGen-LLM](https://arxiv.org/abs/2402.09171)
- [Mutant states and metrics](https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/)
- [Equivalent mutants](https://stryker-mutator.io/docs/mutation-testing-elements/equivalent-mutants/)
- [Flaky tests](https://docs.pytest.org/en/stable/explanation/flaky.html)
- [Quickstart](https://hypothesis.readthedocs.io/en/latest/quickstart.html)
- [Canon TDD](https://newsletter.kentbeck.com/p/canon-tdd)
- [Neural-Based Test Oracle Generation: A Large-scale Evaluation and Lessons Learned](https://arxiv.org/abs/2307.16023)

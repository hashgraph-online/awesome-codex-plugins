---
name: tdd
description: When a bug can be caught by an inexpensive local test, write that narrow failing test before the fix, check that it fails because of the bug, then fix the code and watch the test pass. Use on /tdd, "write a failing test first", "add a regression test", or when a bug has an obvious inexpensive test location.
disable-model-invocation: true
---

# tdd

Turn the defect into a failing test, watch it fail for the reason you expect, change the code, and watch the same test pass. Do this only when a narrow local test is cheap. When it is not, run the nearest executable check instead of forcing a bad test.

## When to skip writing a test

No new test is better than a harmful one. Skip the test, and go to the fallback below, when the test would:

- mainly assert on mocks rather than on behavior;
- pin today's internal structure, so any refactor breaks it;
- depend on timing, ordering, or shared state unrelated to the bug;
- need heavy infrastructure (a full cluster, a seeded production copy) for a small fix;
- be thrown away as soon as the fix is shown.

Also skip it when the path to a test is unclear, slow, or integration-heavy and the user did not ask for one.

## Procedure

1. **Pin the defect.** Write down the expected behavior, the observed behavior, the code path involved, and the smallest input that reproduces it.
2. **Pick the tightest check.** Use the test style the codebase already uses near that path: unit, component, integration, or a regression suite. If nothing reasonable exists, do not build new test infrastructure. Go to the fallback.
3. **Write the smallest test that would have caught this bug.** Assert what a user of the code should get, not how the code currently computes it. If the bug involves untrusted input (a request body, a file name, a header), make the test feed the hostile value the bug allowed, so the test also documents the attack.
4. **Run it against the unchanged code.** It must fail, and the failure message must point at the defect. A pass means the test does not reproduce the bug. A failure for some other reason (a missing import, a fixture error) means the test is wrong. Fix the test before you touch production code.
5. **Make the smallest code change** that produces the intended behavior and keeps neighboring contracts intact.
6. **Run the test again.** It must pass. Run the surrounding suite too, so you know the fix broke nothing nearby.

## Fallback when no practical test exists

Run the closest executable check you can and record it. Options include a short purpose-built script, a shell command that reproduces the symptom, a scripted browser session, a snapshot comparison, an assertion on log output, or a narrow integration run. The same rule applies: observe it showing the bug before the change and showing the fix after.

## Guardrails

- Never edit a test so it agrees with wrong code.
- Never loosen an existing assertion unless the intended behavior really changed. If it did, record why in the test or the commit message.
- Keep the new test about this defect. No fixture rewrites, no unrelated coverage.
- For a flaky or intermittent bug, remove the nondeterminism from the test where you can (fixed seeds, fake clocks, a single worker) and say which signal the test pins.
- If the bug hints at a family of related failures, land the narrow regression test first. Propose broader coverage as a separate follow-up.

## Report

End with evidence:

- the test or check that failed before the change, and its failure output;
- the run where it passed after the change, plus any neighboring suites you ran;
- if you could not show a failure first, the reason, and which nearest check you used in its place.

## Related

The `typescript-best-practices` skill ([../typescript-best-practices/SKILL.md](../typescript-best-practices/SKILL.md)) prefers running real code over mocks. The `benchmark-checklist` skill ([../benchmark-checklist/SKILL.md](../benchmark-checklist/SKILL.md)) applies the same evidence discipline to performance claims.

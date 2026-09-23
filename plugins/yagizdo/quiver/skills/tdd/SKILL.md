---
name: tdd
description: "Test-first cycle and red-step evidence rule for skills that implement behavior a test can assert. Binds when the verification skill resolves a test command; defines what the red run must quote and when the cycle is skipped with a reason."
user-invocable: false
---

# TDD

Reference skill read by `/plan` Step 5, `/work` Phase 3 and `skills/work/orchestrator.md`, and `/hypothesis-debugging` Step 7; `/ship` names it where it hands the build to `/work`. It is never invoked and runs nothing itself: the consumer resolves the test command per `skills/verification/SKILL.md`, follows the cycle here, and quotes the evidence.

## Applicability

The cycle binds to a change when both hold:

- The consumer resolved the test command per `skills/verification/SKILL.md` and the value is not `none`.
- The change produces behavior a test can assert. Documentation, a config value, a rename with no behavior change, and a migration with no code path do not.

When either fails, the outcome is `skipped: <reason>`, and the reason names which one: `test command none (<verification's reason>)` or `no testable behavior (<what the change is>)`. A skipped cycle is a recorded fact, not an error, and it never blocks the consumer.

The user's own project instructions win. A project whose `CLAUDE.md` says not to use TDD settles it.

## The Cycle

- *Red.* Write the test that names the behavior, in the project's existing test layout and framework. Run the resolved test command exactly as written. Record the red line: this run's exit code, the name of the test just written, and its first error line. When the runner fails before naming a test -- a compile or import error in the new test file -- the file path stands in for the name. A failure in a test that was not written in this step is a pre-existing failure, not red evidence.
- *Green.* Write the least implementation that makes that test pass. Run the resolved test command again. The pass line is the existing verification evidence: this run's exit code plus the runner's summary line.
- *Refactor.* Optional. Any further edit is followed by another run, and the most recent pass line is the one reported. The refactor step produces no evidence of its own.

The red run is not an attempt. A consumer with a fix-attempt budget counts only runs made after the implementation exists; the red run precedes the implementation, is expected to fail, and spends nothing.

## Evidence

```
red:     <command> -> exit <code>: <failing test> -- <first error line>
skipped: <reason>
```

Green has no line of its own: it is the `pass:` line `skills/verification/SKILL.md` defines, reported where the consumer already reports it. A consumer that receives neither a `red:` nor a `skipped:` line records `skipped: no red evidence`. The three skipped reasons are `test command none (...)`, `no testable behavior (...)`, and `no red evidence`.

## For Skill Authors

- Read this file at the build step, after the verification command is resolved and before the first implementation starts.
- Order the work test-first in the consumer's own instruction list: the test step and its run precede the implementation step and its run.
- Add a `TDD |` line to any subagent return contract that already carries a `TESTS |` line, with the two forms above, and treat a missing line as `skipped: no red evidence`.
- Paste the `### Subagent restatement` below into the subagent prompt verbatim. It is the only text from this file that is copied anywhere, and `tests/skills/test-tdd-contract.sh` compares the copies to it.

### Subagent restatement

Write the test for the behavior before the implementation and run the test command you were given exactly as written, then report the red step by quoting that run's exit code, the new test's name, and its first error line -- a test that was never seen failing, or a red line naming a test you did not write in this task, is not red evidence; when no test can be written, report skipped with the reason.

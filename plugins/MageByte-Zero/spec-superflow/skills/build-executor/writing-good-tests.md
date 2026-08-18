# Writing Good Tests

Use this reference when selecting, writing, or reviewing tests for a change.
It sharpens the evidence expected by the existing workflow; it does not add a
new execution mode or replace a receipt's verification strategy.

## Behavior First

A useful test names a **可观察行为**: an input, an externally visible result, and
the boundary that matters. Assert that result, rather than a private helper,
the current implementation shape, or a sentence in a source file.

Keep the expected result **独立预期**. Derive it from the requirement, a known
example, or a separately understood rule; do not repeat the production
algorithm in the assertion and then call agreement a proof.

Perform a **变异检查** while writing or reviewing a behavior test: name one
small plausible production change that would make the test fail. If no such
change can be named, strengthen the test or describe its limitation honestly.
This is a reasoning check, not a requirement to add a mutation-testing tool or
to mutate production code in a committed change.

## Evidence That Is Not a Behavior Test

A **文本存在断言** (for example, asserting that a prompt contains a phrase) can
protect a documentation or prompt contract, but it is not evidence that a
runtime behavior works. Label it as a documentation-contract check and pair it
with behavior evidence whenever runtime behavior is in scope. Likewise, a
constant assertion that cannot distinguish a correct implementation from a
broken one is not a behavior test.

## Match Evidence to the Change

For a documentation-only (**纯文档**) or prompt-only change, no unit test needs
to be invented (纯文档任务不需要虚构单元测试) merely to satisfy a test count.
Validate the applicable format, links, examples, lint,
or rendering/build output instead. A documentation-contract check is useful
only when it guards a concrete maintained promise.

For code changes, prefer the narrowest automated test that can falsify the
required behavior, then run the broader verification required by the task.
Record what the test observes and the mutation it would catch in the task
report when Full TDD evidence is required.

## Existing Mode Boundaries Still Apply

- Full and legacy Hotfix work still follows RED → GREEN → REFACTOR.
- Quick still uses the verification strategy selected in its persisted receipt.
- Tweak remains direct edit mode and may use bounded file-integrity or
  documentation validation instead of TDD.

---
name: principle-sequence-verifiable-units
description: Apply to bulk sweeps, migrations, repeated near-identical edits, and stacks of commits or PRs. Break the job into slices, each closed by a check that passes, and order commits so that reading the history shows a reviewer the change is correct.
disable-model-invocation: true
---

# Build in checkable steps

Split work that takes several steps into small units. Each unit ends with something a check can confirm, and you confirm it before starting on the next one. Order the commits and PRs so a reviewer reading them in sequence can see that the change is correct.

## When it applies

Large sweeps, migrations, batches of similar edits, and choices about stacking commits and PRs. One atomic change does not need it.

## What to do

Execution:

1. Rebase onto a clean trunk first, so every check compares against the true baseline.
2. Treat each unit as a bracket: start from a known-good state, make one change, run the check, and continue only if it passes. When upgrading a vulnerable dependency across twelve services, upgrade one service, run its tests, then move to the next. A failure then points at exactly one service.
3. When a tool makes the edits ([principle-build-the-lever](../principle-build-the-lever/SKILL.md)), the per-unit check costs little. Run it every time anyway.

Delivery:

4. Order commits to tell a verifiable story. The standard shape is a commit with a failing test followed by the commit that fixes it. Other valid orders: removal before reshaping, baseline capture before the change it is compared against, scaffold before feature.
5. Make each commit stand on its own, so the sequence reads as an argument a reviewer can replay, red then green.

For a security fix, the failing-test commit is the proof of exploitability and the fix commit is the proof of remediation. A reviewer can check out the first commit, watch the exploit test pass the attack through, then check out the second and watch it blocked.

## The failure it prevents

Breakage discovered only after a batch, by which point later work has been built on top of it, and mega-commits no reviewer can follow.

## Done when

Every unit passed its check before the next began, and the history replays as evidence.

Related: [principle-prove-it-works](../principle-prove-it-works/SKILL.md), [principle-build-the-lever](../principle-build-the-lever/SKILL.md), [principle-subtract-before-you-add](../principle-subtract-before-you-add/SKILL.md), [tdd](../tdd/SKILL.md).

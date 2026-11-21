---
name: principle-attack-the-premise
description: Use after repeated fixes built on one shared theory of the cause keep failing at the same gate. Stop patching, state that theory in writing, and run a check whose result would change if the theory were wrong.
disable-model-invocation: true
---

# Attack the premise

A second failure at the same check, from fixes built on one assumption, makes that assumption the suspect. Before you try a third variant, write the premise down and run an observation able to refute it.

## When it applies

Two or more attempts that assumed the same cause have failed one gate (the same test, benchmark, or review criterion), and you are about to try a third variation.

It does not apply to a single failed fix, or to failures at unrelated gates with unrelated assumptions. The neighbouring principle, [principle-redesign-from-first-principles](../principle-redesign-from-first-principles/SKILL.md), reshapes a design when a requirement changes. This one questions a factual assumption the existing design depends on.

## What to do

1. Write the premise as one sentence, in the reply or the decision log, where the user can read it. Example: "The auth bypass in the agent's tool router comes from the regex allowlist missing a case."
2. Design a discriminating observation, one whose result differs depending on whether the premise holds. For the example: log the exact tool name string that reached the router on the failing request. If it matches the allowlist exactly, the regex was never the problem.
3. Look at the shape of the failures as well as their size. Which inputs, runs, or components fail, and does one participant always lose? A test that fails only on the webhook path, never the CLI, says more than a failure count.
4. Make the check rerunnable as a script or a single command, per [principle-build-the-lever](../principle-build-the-lever/SKILL.md), so a reviewer can reproduce your evidence.
5. Act on the outcome. When the observation refutes the premise, look for the cause somewhere else: write down the traits the failing cases share that the premise failed to anticipate, and pursue those. When the observation confirms the premise, go one level deeper using [principle-fix-root-causes](../principle-fix-root-causes/SKILL.md); the previous attempts most likely patched a downstream effect.
6. If the evidence shows a structural condition, such as one worker always finishing last or one service always reading stale config, remove the condition. Adding a mechanism that repairs the outcome afterward leaves the cause running and adds cost on every execution, which [principle-laziness-protocol](../principle-laziness-protocol/SKILL.md) rules out.

## The failure it prevents

Continuing to iterate on a wrong diagnosis because of effort already spent, and stacking compensating patches in a place the evidence has ruled out.

## Done when

The premise is written down and a discriminating observation has been run before any new fix begins. This is a hard gate.

Related: [principle-build-the-lever](../principle-build-the-lever/SKILL.md), [principle-fix-root-causes](../principle-fix-root-causes/SKILL.md), [principle-laziness-protocol](../principle-laziness-protocol/SKILL.md), [principle-redesign-from-first-principles](../principle-redesign-from-first-principles/SKILL.md).

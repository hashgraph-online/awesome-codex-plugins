---
name: principle-exhaust-the-design-space
description: Use for a UI, architecture, or product choice the codebase has never faced, or one decided by how it feels in use. Build two or three rival throwaway prototypes and pick based on comparing them side by side.
disable-model-invocation: true
---

# Exhaust the design space

When the codebase offers no existing pattern for a choice, make two or three rival prototypes and compare them directly before committing. Your first design is a single sample from the options, and it cannot be judged without others next to it.

## When it applies

A novel UI interaction or architectural choice with nothing similar already in the code, and product decisions where the right answer depends on how something feels to use more than on a logical argument. An example: choosing how an agent asks the user to approve a risky tool call (inline prompt, batched review queue, or a policy file the user edits once).

Skip it when the codebase already has an established pattern for the decision, or when one logical argument settles it.

## What to do

1. Name the open decision and the dimensions that matter (friction, error rate, latency, how much the user must read).
2. Build two or three cheap, throwaway prototypes that take genuinely different approaches. Three color variants of one layout count as one approach.
3. Put them side by side. For UI, place them behind one switcher and capture screenshots or recordings. For behavior, measure each on the same inputs.
4. Choose from what you observed, record why, and delete the losers.

Parallel subagents can build the prototypes at the same time. The [arena](../arena/SKILL.md) and [architect](../architect/SKILL.md) skills run this pattern for code and design.

## The failure it prevents

Locking in the first idea, and arguing about alternatives in the abstract when running them would answer the question in minutes.

## Done when

The choice was made from compared, running alternatives.

Related: [principle-experience-first](../principle-experience-first/SKILL.md).

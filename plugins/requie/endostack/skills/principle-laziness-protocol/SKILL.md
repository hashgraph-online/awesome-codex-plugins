---
name: principle-laziness-protocol
description: Apply while you restructure code, decide how large a diff should be, or feel the pull toward a new abstraction, an extra layer, or a parameter passed through many functions. Prefer deleting code, and ship the narrowest diff that fixes what was asked.
disable-model-invocation: true
---

# Laziness protocol

Prefer deletion. Of the changes that would fix the problem, pick the smallest.

## When it applies

Refactoring, judging the size of a diff, and any urge to add an abstraction or a layer, or to thread a new parameter through many functions. It never excuses skipping verification or validation at a real boundary.

## What to do

1. Consolidate decisions. If the same choice is made in several places (for example, three handlers each deciding whether a request is from an admin), decide it in one place and hand the outcome to the others as a plain value.
2. Minimize the diff. Fewer lines beat boilerplate that looks elegant. Every added line is something to review, and in security-sensitive code every line is attack surface.
3. Remove a condition in preference to adding machinery that compensates for it. [principle-attack-the-premise](../principle-attack-the-premise/SKILL.md) relies on this rule when the evidence points at a structural cause.
4. When you need a tool, build the smallest one that does the job, as [principle-build-the-lever](../principle-build-the-lever/SKILL.md) requires.

## The failure it prevents

Bloated diffs, decision logic repeated in several places that drifts apart, and speculative layers nobody needed.

## Done when

No smaller change would solve the problem.

Related: [principle-attack-the-premise](../principle-attack-the-premise/SKILL.md), [principle-build-the-lever](../principle-build-the-lever/SKILL.md), [principle-subtract-before-you-add](../principle-subtract-before-you-add/SKILL.md), [principle-minimize-reader-load](../principle-minimize-reader-load/SKILL.md).

---
name: principle-fix-root-causes
description: Use for any debugging or bug fix. Repair the earliest point where the system decided wrongly, rather than where the bad state showed up. A guard is a real fix only for a state the system is permitted to reach.
disable-model-invocation: true
---

# Fix root causes

Locate the earliest wrong decision the system made and repair it there, rather than at the spot where the damage became visible. Adding a guard counts as a fix only if the state it catches is a legitimate one for the system to be in.

## When it applies

All debugging and bug-fix work. If several fixes resting on one assumption have already failed, combine this with [principle-attack-the-premise](../principle-attack-the-premise/SKILL.md).

## What to do

1. Reproduce the failure before changing anything.
2. Keep asking why until you reach a decision in code that was itself wrong, as opposed to one that followed correctly from an earlier mistake.
3. When you are stuck, instrument. Read the real error and the real state. Do not guess.
4. Classify the triggering state. If it is legitimate, the code that failed on it is at fault, and handling it in that code is the right fix. If the state should never occur, testing for it where it showed up only conceals the bug, so follow it back to whatever created it. Be suspicious of guards, retries, swallowed exceptions, clamped values, and discarded state.
5. When a failure shows up just after restarts, look at persisted state before anything else: serialized sessions, caches, lock files, and configuration on disk.
6. Fix the pattern: search for all other sites that share the fault and repair each one.
7. A workaround that needs a long comment to justify itself signals broken code, so change the code instead.
8. If finding the deciding fact took deep digging, propose a cheap always-on signal (a log line, a metric, an assertion) that would have shown it immediately.

A security example. An agent's file tool crashes on a path containing `../`. Adding `if ".." in path: return` at the crash site looks like a fix, but a path that escapes the workspace should never have reached the tool. The root cause is the boundary that accepted it without resolving and checking it against the workspace root. Fix it there, then search for every other tool that takes a path from model output, because each one has the same traversal hole.

## The failure it prevents

Symptom patches hide evidence and let the fault resurface elsewhere. Unnamed workarounds pile up. A single-instance fix leaves sibling defects in place, and for security bugs those siblings are the next finding.

## Done when

You traced the failure to a decision the code got wrong, repaired it at that spot, and repaired its siblings as well.

The [comment-auditor](../../agents/comment-auditor.md) agent flags justification comments as evidence of this failure. The [how](../how/SKILL.md) and [why](../why/SKILL.md) skills help trace a symptom back to its origin.

Related: [principle-attack-the-premise](../principle-attack-the-premise/SKILL.md), [principle-prove-it-works](../principle-prove-it-works/SKILL.md), [principle-boundary-discipline](../principle-boundary-discipline/SKILL.md).

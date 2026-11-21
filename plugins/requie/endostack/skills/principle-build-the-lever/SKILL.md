---
name: principle-build-the-lever
description: Use for any edit, migration, analysis, or verification beyond the trivial. Produce a codemod, script, generator, or repeatable check that performs or demonstrates the result, so a reviewer can rerun it in place of taking your word.
disable-model-invocation: true
---

# Build the lever

Once a task is more than trivial, create the tool that carries it out or checks it: a codemod, a script, a generator, a check you can run again, or a skill file that delegates read. Manual work can only be confirmed by repeating it, while a deterministic tool lets the reviewer confirm it with one command.

## When it applies

Edits, migrations, analyses, and verification of any size above trivial. What triggers it is that the work is non-trivial, whether or not it repeats. Even a task you will do once deserves a tool if the tool is what lets someone check the result.

Skip it for a couple of obvious edits that anyone can verify at a glance.

## What to do

1. Default to building the tool.
2. Handle the first unit manually so you understand the steps. Next, write the tool, point it at that same unit, and compare its output with your manual version. Identical output shows the tool is correct.
3. Make the tool safe to run twice ([principle-make-operations-idempotent](../principle-make-operations-idempotent/SKILL.md)).
4. Pick the tool by job. Edits get a codemod or script. Repetitive files get a generator. Analysis often goes fastest by dumping the data into SQLite and querying it: auditing which of 400 service accounts hold write scopes is one query once the IAM export is a table. Verification gets a rerunnable check.
5. Prefer one deterministic pass over fan-out. If one script covers every unit, run it yourself instead of spawning subagents to make the same edits manually.
6. When the work does get split across delegates, make the lever a skill file that each of them reads. That one file holds the steps, the check each unit must pass, and the limits on what may not be touched. Store it where no delegate can write, so none of them can weaken the check.
7. Commit the tool when the work outlives the session.
8. Keep it small, as [principle-laziness-protocol](../principle-laziness-protocol/SKILL.md) requires: write the least script that gets the job done or checked, and stop short of building a framework.
9. Audit yourself: if you cite this principle, a tool file exists in the diff. If none does, you did not apply it.

## The failure it prevents

Unreviewable hand edits, inconsistent application across units, delegates drifting from a recipe, and "trust me, I checked" claims. A security example: rotating a leaked token across 30 config files by hand leaves the reviewer no way to confirm none were missed. A script that rewrites and then greps for the old token's prefix gives them one.

## Done when

A visible or committed tool exists that reproduces or verifies the work.

[principle-encode-lessons-in-structure](../principle-encode-lessons-in-structure/SKILL.md) is the neighbouring principle: it converts a correction that keeps coming back into a permanent guardrail. Building the lever concerns speed and checkability for the current task.

Related: [principle-laziness-protocol](../principle-laziness-protocol/SKILL.md), [principle-prove-it-works](../principle-prove-it-works/SKILL.md), [principle-attack-the-premise](../principle-attack-the-premise/SKILL.md), [principle-sequence-verifiable-units](../principle-sequence-verifiable-units/SKILL.md).

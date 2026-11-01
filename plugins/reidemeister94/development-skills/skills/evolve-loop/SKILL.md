---
name: evolve-loop
description: "Autonomous /goal loop that rethinks a project's design and adds features and improvements that can change its behavior, each change recorded and proven. Start it only when the user names evolve-loop."
argument-hint: "[theme or focus] [branch=...] [limits]"
user-invocable: true
disable-model-invocation: true
---

# Evolve loop

Evaluate this project in full, rethink its design and components from first principles, and add the features and improvements that make it more useful, correct, fast, and simple.
Changes can alter logic and results. Each change is deliberate, recorded, and proven. Everything else stays identical.
The arguments of the request can set a theme, a focus, a branch, or extra limits.

Invoking this skill approves the work below within the [unattended-run limits](../../shared/unattended-runs.md).
Work on a new branch, `evolve/loop-YYYY-MM-DD`, unless the arguments name one.
When data matters, use representative dev or staging data. Test data migrations only on disposable databases.
Build what the evidence supports. Write a proposal when a change needs the user's decision: unclear business rules, product scope, breaking changes, migrations of real data, permissions, or higher costs.

## Verification first

Before changing behavior, agree with the user on the [definition of done](../create-test/SKILL.md#definition-of-done) and a proven [regression gate](../create-test/SKILL.md#regression-gate), as an [autonomous run](../create-test/SKILL.md#autonomous-work) requires.
Start from what the project already has to check regressions. Use `brainstorming` and `create-test` for what is missing.
Record each intended change with before and after on a real example, the reason, who is affected, and its acceptance checks.

## Work

Start from the purpose: who uses the project, its main flows, and what they need.
Rethink its main components and flows: which design would you choose today, for the real requirements and data?
Keep the current one when the gain does not pay for the change.
Find ideas in evidence: errors and slow flows in the logs, bad data, manual steps users repeat, workarounds in the code, open issues, and what good similar projects offer.
Test an uncertain idea with a small experiment before you build it.

Rank ideas by benefit for the cost, with data loss and security fixes first, and use `rethink` to challenge the ranking.
Work in small, verifiable changes. Keep the change list, proposals, experiment results, and discoveries in the task records.
Describe each new behavior in the docs with a real example.
Report the behavior changes, verification, proposals, and remaining questions against the agreed definition of done.

## Done

The loop is done when, on its last commit:

1. The gate exits 0 with only the declared differences. Each check for new behavior fails on the baseline and passes now; checks for unchanged behavior pass on both.
2. The independent review of the whole branch has no open CRITICAL or HIGH finding.
3. A final evaluation in a fresh context finds no new idea that the evidence supports and that can ship without the user's decision. No idea is open.
4. Docs, changelog, and task records are current, and `git status` is clean.

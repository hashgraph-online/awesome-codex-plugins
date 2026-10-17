# Execution profile: lite

A short list of deltas over `superpowers:subagent-driven-development` (SDD). This file is a
profile, not an executor: it defines no loop, no ledger format and no BASE tracking of its own.
Everything not listed below — TDD, the ledger, BASE tracking, model selection, dispatch prompt
templates, the breaker rules — is unchanged from superpowers:subagent-driven-development.

Use it when the startup survey of `rag-reviewer:solve-task` selected the `lite` strategy, or when
the `auto` rubric resolved to `lite`.

## Delta 1 — review per group, not per task

SDD dispatches a task reviewer after every task. In `lite`, the reviewer is dispatched once per
**group**.

A group is a run of consecutive plan tasks that touch overlapping files, at most 3 tasks long.
Tasks whose files do not overlap are never merged into one group, even when they are adjacent and
the group is short.

Dispatch the reviewer on the diff of the whole group. `BASE` is the commit recorded before the
group's first task — not `HEAD~1`, and not the base of the last task in the group.

A group that fails review enters the fix loop as one unit: the findings name the task they belong
to, and the fix dispatch resumes the implementer of that task.

## Delta 2 — fix-round cap of 3

The per-group fix loop allows 3 fix rounds instead of 5. Model escalation moves accordingly:
a fresh implementer on a more capable model is dispatched from round 3 instead of round 4.

The breaker is unchanged: at the cap, adjudicate every open finding yourself — park it with a
ruling, or stop and report BLOCKED when it is real and load-bearing.

## Delta 3 — the final review stays

The final whole-branch review is mandatory under this profile and is never disabled, in any
interaction mode, including full-auto. It is the only broad check in the run, and `lite` has
increased what rides on it: per-task gates were traded for per-group ones.

Dispatch it exactly as SDD prescribes — most capable available model, whole-branch review package,
pointed at the ledger's deferred-minor and parked lines.

## What this profile does not change

Ledger bookkeeping, BASE recording, worktree setup, implementer and reviewer prompt templates,
model selection rules, and the finish sequence are unchanged from superpowers:subagent-driven-development.
Read that skill for all of them.

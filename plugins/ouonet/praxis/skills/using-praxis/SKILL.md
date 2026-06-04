---
name: using-praxis
description: Use at session start to learn how Praxis skills are invoked and why triage runs before every task.
---
# Using Praxis

You have Praxis.

<EXTREMELY_IMPORTANT>
Before any response or action on every user message, classify scope using the triage table below, announce it, then load required skills in parallel.
</EXTREMELY_IMPORTANT>

## Triage

One line before every response:
```
praxis: scope=<x>, loading=<skills>
```

| scope | signal | load |
|---|---|---|
| vague | problem space undefined — can't yet say what to build, for whom, or whether it's worth building | `design` |
| trivial | typo, rename, docs-only, <=1-line, pure Q | none |
| small | one function, single file, <=50 LOC, or test-only change | `tdd` (intent unclear? clarify first) |
| standard | feature or source-code change | `design`, `plan`, `tdd`, `review` |
| complex | new system, >=5 tasks, or parallel edits | `design`, `plan`, `worktree`, `subagents`, `review`, `ship` |
| debug | broken, regression, failing test | `debug` |
| onboard | existing project, no docs/tech-spec.md | `onboard` |

If multiple scopes fit, choose the smaller one. `vague` is a last resort — if you can name a rough deliverable, use a lower scope instead. `feature change` = user-visible/public-contract change. `source code` = code/schema/config that changes shipped behavior; docs, tests, examples, CI, and tooling excluded.

## Rule

0. Unfamiliar with this project? Read `docs/tech-spec.md` first.
1. Classify inline using the table above — no Skill call needed for triage.
2. Announce: `praxis: scope=<x>, loading=<skills>`
3. Load all required skills **in parallel** (single response, multiple Skill tool calls): `praxis:<name>`, or in file-read harnesses from `skills/<name>/SKILL.md`.
4. Follow loaded skills literally; respect `<gate>` markers.

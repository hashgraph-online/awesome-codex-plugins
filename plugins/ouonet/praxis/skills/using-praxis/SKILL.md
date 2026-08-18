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
praxis: scope=<x>, loading=<skills>                          # single-module (default)
praxis: scope=<x>, topology=multi-module, loading=<skills>   # multi-module
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

**Topology** is declared alongside scope, not chosen from the table. Default `single` (omit it). Announce `topology=multi-module` when one change spans multiple modules or repositories - every loaded workflow skill then follows `skills/references/multi-module.md`. Multiple repositories require a user-designated existing coordinator repository. Once a multi-module change is underway, a coordinator spec/plan declaring `topology: multi-module` exists on disk; read it and carry `topology=multi-module` forward every turn - do not re-decide from scratch. If unsure, check for that declaration before announcing.

`topology` doesn't change scope: classify exactly as for single-repo work; multi-module only adds execution mechanics (`multi-module.md`). Unsure? Start single-module; upgrade the declaration once confirmed.

If multiple scopes fit, choose the smaller one. `vague` is a last resort — if you can name a rough deliverable, use a lower scope instead. `feature change` = user-visible/public-contract change. `source code` = code/schema/config that changes shipped behavior; docs, tests, examples, CI, and tooling excluded.

## Rule

0. Unfamiliar with this project? Read `docs/tech-spec.md` first.
1. Classify inline using the table above — no skill-loader call needed for triage.
2. Announce: `praxis: scope=<x>, loading=<skills>` (add `topology=multi-module` when the change spans multiple modules - see Topology above)
3. Load all required skills **in parallel** (single response): use the harness skill loader when available (`praxis:<name>` / native skill tool), otherwise read `skills/<name>/SKILL.md` with the native file-read tool.
4. Follow loaded skills literally; respect `<gate>` markers.
5. Search code shapes with structural search (no index needed, works in any repo); plain grep only when structure is irrelevant.

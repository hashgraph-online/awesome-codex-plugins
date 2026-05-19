---
name: triage
description: Use first on every user message to classify scope and select the minimal Praxis workflow.
---
# Triage

Classify, announce, proceed. One line:
```
praxis: scope=<x>, loading=<skills>
```

| scope | signal | load |
|---|---|---|
| trivial | typo, rename, docs-only, <=1-line, pure Q | none |
| small | one function, single file, <=50 LOC, or test-only change | `tdd` (intent unclear? clarify first) |
| standard | feature change or source-code change | `design` -> `plan` -> `tdd` -> `review` |
| complex | large feature/source-code change: new system, >=5 tasks, or parallel edits | `design` -> `plan` -> `worktree` -> `subagents` -> `review` -> `ship` |
| debug | broken, regression, failing test | `debug` first, then route fix |
| onboard | existing project, no docs/tech-spec.md, "take over"/"add Praxis" | `onboard` |

If multiple scopes fit, choose the smaller one. `feature change` = user-visible/public-contract change. `source code` = code/schema/config that changes shipped behavior; docs, tests, examples, CI, and tooling excluded.

- Never load a skill not listed for the chosen scope.
- Load selected skills via the Skill tool as `praxis:<name>`, or in file-read harnesses from `skills/<name>/SKILL.md`.
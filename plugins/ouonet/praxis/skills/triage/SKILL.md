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
| trivial | typo, rename, doc, <=1-line, pure Q | none |
| small | one function, single file, <=50 LOC | `tdd` (intent unclear? clarify first) |
| standard | feature, multi-file, new behavior | `design` -> `plan` -> `tdd` -> `review` |
| complex | new system, >=5 tasks, parallel | `design` -> `plan` -> `worktree` -> `subagents` -> `review` -> `ship` |
| debug | broken, regression, failing test | `debug` first, then route fix |
| onboard | existing project, no docs/tech-spec.md, "take over"/"add Praxis" | `onboard` |

Torn? Pick smaller. "just X" / "quickly" / "no tests" -> downgrade. "design it" / "properly" -> upgrade.

- Never load a skill not listed for the chosen scope.
- Load selected skills via the Skill tool as `praxis:<name>`, or in file-read harnesses from `skills/<name>/SKILL.md`.
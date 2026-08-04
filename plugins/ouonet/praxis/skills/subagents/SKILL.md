---
name: subagents
description: Use when a plan has parallel tasks and the harness supports dispatching subagents.
---
# Subagents

If `topology=multi-module` (triage announcement or coordinator spec/plan declaration), read `../references/multi-module.md`.

Fresh context per task. No session history.

## Dispatch: reference, don't copy
Subagents have file-read tools. Don't inline what they can read.

```
TASK: <one sentence>
ROLE: <implementer | spec-reviewer | quality-reviewer>
MODEL: <fast | balanced | strongest>
REPOSITORY: <registered repo id and path>
MODULE: <module id and root>
FILES: <paths>
SPEC: <docs/staging/specs/...#anchor>
ACCEPTANCE: <test or cmd>
EXTRA: <only what's NOT in referenced files>
```

`ROLE` is required. See role charters below for what each role owns and does not own.

`MODEL` is optional. Omitted → uses harness default. Resolution: `.praxis/model-tiers.yaml` in project root or user home maps the three tiers (`fast`, `balanced`, `strongest`) to concrete model IDs. No config file → all subagents use harness default.

Pasting >10 lines from the spec? Stop - let the subagent read it.

Expand milestone → atomic steps **at dispatch time**, not in the plan.

One task has one repository and module write scope. Agents may read shared coordinator contracts, but must not edit another module or repository. Never dispatch two writers to overlapping module roots. Integration tasks are dispatched only after every required module reports local acceptance.

## Loop per task
implementer → on DONE: spec-reviewer (matches spec?) → quality-reviewer (`review`) → mark complete, continue.
The coordinator marks `- [x]`, never the subagent.

## Status
- `DONE_WITH_CONCERNS` - address if correctness; note if observation.
- `NEEDS_CONTEXT` - supply the fact, re-dispatch.
- `BLOCKED` - diagnose (missing context / stronger model / too big / plan wrong). Never silently retry.

## Model tier

`MODEL: fast | balanced | strongest` — optional, omitted → harness default.

Resolved via `.praxis/model-tiers.yaml` in project root or user home. Template at Praxis repo root: `model-tiers.example.yaml`.

**The coordinator decides the tier at dispatch time** based on task complexity — it is not hardcoded per role. The role charters below list defaults; override when:

| Scenario | Tier | Examples |
|----------|------|----------|
| Mechanical edits, simple checks | `fast` | rename a constant, fix a typo, pattern-match review |
| Standard implementation, single-file feature | `balanced` | add a function, modify one module, write routine tests |
| Multi-file refactor, concurrency/state-machine, safety review | `strongest` | implement a protocol, review crash-recovery, cross-module integration |

## Role charters

### implementer
- **Owns**: writing the minimum code to make the acceptance test pass (GREEN phase). This includes writing the failing test first (RED), then the implementation (GREEN), then refactoring within the changed files.
- **Does NOT own**: expanding scope beyond the task, adding abstractions not required by the current test, touching files outside FILES, marking the task complete.
- **Default tier**: `balanced`. Override to `fast` for mechanical edits, `strongest` for multi-file protocol/state-machine implementation.
- **On DONE**: hands off to spec-reviewer.

### spec-reviewer
- **Owns**: verifying implementation matches every contract and acceptance criterion in SPEC. Reports drift with file:line references.
- **Does NOT own**: suggesting improvements beyond the spec, checking code quality, re-running tests.
- **Default tier**: `fast`. Override to `balanced` when spec has ≥3 cross-referencing rules or state enums.
- **On DONE_WITH_CONCERNS**: coordinator decides whether to address or note.

### quality-reviewer
- **Owns**: running `review` skill against the diff — convention compliance, simplification opportunities, idiomatic patterns, security, scope.
- **Does NOT own**: re-verifying spec compliance (already done), re-running acceptance tests (already done).
- **Default tier**: `strongest`. Override to `balanced` for single-file changes where deep reasoning is unnecessary.
- **On DONE**: task is complete. Coordinator marks `- [x]`.

All done → `review` whole diff → `ship`.

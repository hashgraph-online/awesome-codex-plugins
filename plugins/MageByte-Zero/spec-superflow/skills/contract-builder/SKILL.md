---
name: contract-builder
description: Maintain an execution contract only for an existing legacy change that requires one. New direct/planned changes do not invoke this skill when a contract is absent.
---

# Contract Builder

## Bundled runtime

Before executing a CLI line below, replace its leading `SSF` with `node "<plugin-root>/scripts/spec-superflow.mjs"`; `<plugin-root>` is the absolute directory two levels above this file. Never run `SSF` literally or call an `ssf` from `PATH`.

Legacy compatibility only: new planned changes use proposal.md + tasks.md and `SSF workflow start --path planned`. Do not generate a contract or request a second approval for them. Read the remaining instructions only for an existing legacy change.

Converts planning artifacts into a single execution handshake: `execution-contract.md`. Load the baseline with `SSF runtime asset read templates/execution-contract.md`.

Read before generating: `.spec-superflow.yaml` (especially `dp_0_decisions`),
`proposal.md`, `specs/`, `design.md`, `tasks.md`, then load
`docs/artifact-contract.md` with `SSF runtime asset read docs/artifact-contract.md`.

Enter `bridging` before writing the contract; skip the transition if already there. Honor configured specs/design omissions. Reference requirement IDs and task IDs instead of copying their full text; preserve scope, obligations, tests, and review policy.

## Artifact Language

Read `artifact_language=<concrete-language>` from `dp_0_decisions`. Generate
`execution-contract.md` in the same language as that resolved value and the
approved planning artifacts. Preserve required schema keywords and code
identifiers verbatim; language consistency applies to explanatory prose and
headings. If the concrete artifact language is missing or still `auto`, route
back to `workflow-start` before writing the contract instead of guessing or
silently defaulting to English.

## Artifact Mapping

| Source | Extract |
|--------|---------|
| `proposal.md` → `## Why` + `## What Changes` | Intent Lock (problem + scope) |
| `proposal.md` → `## Scope > ### Out of Scope` | Scope Fence |
| `specs/` → each `### Requirement:` | Approved Requirements, Scenarios, Test Obligations |
| `design.md` → `## Decisions` | Architecture, Interface, Dependency Constraints |
| `tasks.md` → numbered task groups | Execution Batches, Completion Definitions, Review Timing |

## Cross-Check: Requirement Coverage

Before finalizing:
1. List every SHALL/MUST from `specs/`
2. Verify each is reflected in Approved Behavior, has a test obligation, and appears in at least one batch
3. Flag unmapped requirements in Escalation Rules
4. Note cross-batch dependencies

## Contract Structure

Must make obvious: approved behavior, out-of-scope, constraints, batches, test obligations, review gates, and conditions that force a rewind to planning. Prefer compression over repeating planning details.

## Approval Model (DP-3)

After drafting: summarize handoff rules, identify ambiguity and flag unmapped requirements. Reuse explicit approval already covering this exact contract; otherwise request it once, together with any still-pending planning decisions and the default Native execution choice. Approval of scope alone does not approve a contract that has not been shown. Never ask the user to approve the same unchanged contract twice. After approval:
```bash
SSF state set <change-dir> dp_3_result "approved: <summary>"
SSF state set <change-dir> dp_3_timestamp now
SSF state rebuild <change-dir>
```

Advance the state after approval:
```bash
SSF state transition <change-dir> approved-for-build
```

DP-3 is a hard gate — no implementation without this record.

## Stale Contract Detection

Refresh if: scope changed in proposal, requirements changed in specs, constraints changed in design, batches changed materially in tasks, or the contract no longer matches intent.

## Hotfix Mode

Generate a minimal contract only for a legacy Hotfix: Intent Lock (one sentence), Task List (numbered), Approval Gate (DP-3). Skip Scope Fence, Build Rules, Review Gates, Test Evidence. Still requires DP-3 approval. Quick direct execution and direct incident Hotfix do not invoke this skill; they use the signed receipt and finish with `test_result: pass` instead.

## Guardrails

- Do not continue to implementation if ambiguity remains
- Do not approve the contract on the user's behalf
- Do not skip the contract because planning docs look complete
- Flag unmapped requirements; do not silently drop them

## Post-Generation

The approved contract is recorded by `state rebuild` in the DP-3 sequence above, before the guarded transition. This applies to Full and legacy Hotfix. Do not refresh hashes merely to suppress an unapproved content change.

## Exception Handling

- **Parse failures**: Report specific file and section. Suggest re-running `spec-writer`.
- **Missing files**: List every missing artifact. Route back to `spec-writer`.
- **User interruption**: Re-read all artifacts on resume; check contract staleness via content comparison.
- **Validation failure**: Flag unmapped requirements in Escalation Rules and approval summary.

---
name: contract-builder
description: Convert approved planning artifacts into an execution contract. Invoke when the user wants to start building, asks to move from planning to implementation, or when execution-contract.md is missing or stale.
---

# Contract Builder

Converts planning artifacts into a single execution handshake: `execution-contract.md`. Load the baseline with `ssf runtime asset read templates/execution-contract.md`.

Read before generating: `.spec-superflow.yaml` (especially `dp_0_decisions`),
`proposal.md`, `specs/`, `design.md`, `tasks.md`, then load
`docs/artifact-contract.md` with `ssf runtime asset read docs/artifact-contract.md`.

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

After drafting: summarize handoff rules, identify ambiguity, flag unmapped requirements, ask user to approve explicitly. After approval:
```bash
ssf state set <change-dir> dp_3_result "approved: <summary>"
ssf state set <change-dir> dp_3_timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ)
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

Run `ssf state init <change-dir>` to create `.spec-superflow.yaml` with hashes.

For a legacy Hotfix, after writing the minimal contract, run `ssf state init <change-dir>` or `ssf state rebuild <change-dir>` so `contract_hash` is recorded. DP-3 remains mandatory before build.

## Exception Handling

- **Parse failures**: Report specific file and section. Suggest re-running `spec-writer`.
- **Missing files**: List every missing artifact. Route back to `spec-writer`.
- **User interruption**: Re-read all artifacts on resume; check contract staleness via content comparison.
- **Validation failure**: Flag unmapped requirements in Escalation Rules and approval summary.

## Standard User-Facing Handoff

End every user-facing phase report with this concise handoff. Only a successfully
persisted `closing` state and `abandoned` are terminal.

### Normal report

- Current stage: `<detected workflow stage>`.
- Completed / blocker: `<completed work>`.
- Next stage: `<next workflow stage or skill>`.
- Entry condition: `<what must be true to enter it>`.

### Blocked report

- Current stage: `<detected workflow stage>`.
- Completed / blocker: `<blocking fact or missing evidence>`.
- Next stage: `<stage that resumes after the blocker>`.
- Entry condition: `<the approval, artifact, validation, or fix required>`.

### Approval-wait report

- Current stage: `<detected workflow stage>`.
- Completed / blocker: `<work ready for the named decision>`.
- Next stage: `<stage that follows approval>`.
- Entry condition: `<explicit user approval or recorded decision>`.

### Successful terminal report

- Current stage: successfully persisted `closing` or `abandoned`.
- Completed / blocker: `<persisted terminal outcome>`.
- Next stage: `none`.
- Entry condition: no further transition exists.

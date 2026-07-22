---
name: contract-builder
description: Convert approved planning artifacts into an execution contract. Invoke when the user wants to start building, asks to move from planning to implementation, or when execution-contract.md is missing or stale.
---

# Contract Builder

Converts planning artifacts into a single execution handshake: `execution-contract.md`. Load the baseline with `npx --yes --package spec-superflow@0.11.0 ssf runtime asset read templates/execution-contract.md`.

Read before generating: `.spec-superflow.yaml` (especially `dp_0_decisions`),
`proposal.md`, `specs/`, `design.md`, `tasks.md`, then load
`docs/artifact-contract.md` with `npx --yes --package spec-superflow@0.11.0 ssf runtime asset read docs/artifact-contract.md`.

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
npx --yes --package spec-superflow@0.11.0 ssf state set <change-dir> dp_3_result "approved: <summary>"
npx --yes --package spec-superflow@0.11.0 ssf state set <change-dir> dp_3_timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ)
```
DP-3 is a hard gate — no implementation without this record.

## Stale Contract Detection

Refresh if: scope changed in proposal, requirements changed in specs, constraints changed in design, batches changed materially in tasks, or the contract no longer matches intent.

## Hotfix Mode

Generate minimal contract: Intent Lock (one sentence), Task List (numbered), Approval Gate (DP-3). Skip Scope Fence, Build Rules, Review Gates, Test Evidence. Still requires DP-3 approval.

## Guardrails

- Do not continue to implementation if ambiguity remains
- Do not approve the contract on the user's behalf
- Do not skip the contract because planning docs look complete
- Flag unmapped requirements; do not silently drop them

## Post-Generation

Run `npx --yes --package spec-superflow@0.11.0 ssf state init <change-dir>` to create `.spec-superflow.yaml` with hashes.

For hotfix, after writing the minimal contract, run `npx --yes --package spec-superflow@0.11.0 ssf state init <change-dir>` or `npx --yes --package spec-superflow@0.11.0 ssf state rebuild <change-dir>` so `contract_hash` is recorded. DP-3 remains mandatory before build.

## Exception Handling

- **Parse failures**: Report specific file and section. Suggest re-running `spec-writer`.
- **Missing files**: List every missing artifact. Route back to `spec-writer`.
- **User interruption**: Re-read all artifacts on resume; check contract staleness via content comparison.
- **Validation failure**: Flag unmapped requirements in Escalation Rules and approval summary.

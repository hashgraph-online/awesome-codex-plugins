---
name: artifact-contract-manager
description: Use when creating, reviewing, or updating the Artifact Registry and artifact PASS conditions for a product development workspace.
---

# Artifact Contract Manager

This skill owns the contract shape for every artifact. Every artifact must have one producer, clear consumers, a PASS condition, and a failure route.

## Input Artifacts

- `00-stage.json`
- Existing workspace files
- Any proposed new artifact

## Output Artifact

- `docs/full-stack-development/requirements/<feature-slug>/00-artifact-registry.json`

## Required MCP Tool

- `list_artifact_contracts`
- `get_artifact_contract`
- `review_artifact_contract`

## Hard Stops

- Do not add an artifact if its producer, consumers, PASS condition, or failure route are unclear.
- Do not allow empty templates to pass.
- Do not let downstream stages consume unregistered artifacts.

## Pressure Test Responsibility

- Missing producer blocks.
- Missing consumer blocks.
- Missing PASS condition blocks.
- Missing failure route blocks.

## Next Gate

- `stage-gate-reviewer` consumes the registry before any stage transition.


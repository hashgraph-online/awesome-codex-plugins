---
name: quality-auditor
description: Use before completion or release to audit visual metrics, HeroUI component graph, backend/API contracts, code review evidence, and official docs freshness.
---

# Quality Auditor

This skill closes the gap between process evidence and deeper implementation quality.

## Input Artifacts

- `00-stage.json`
- Visual evidence and screenshot metrics
- Changed frontend files
- Backend/API contract and implementation coverage
- Code review report
- HeroUI official docs manifest

## Output Artifact

- `docs/full-stack-development/requirements/<feature-slug>/06-verification/quality-audit-report.md`

## Required MCP Tool

- `review_visual_inspection_metrics`
- `review_hero_ui_component_graph_audit`
- `review_backend_contract_audit`
- `review_code_review_gate`
- `review_hero_ui_docs_freshness`
- `review_completion_gate`

## Hard Stops

- Do not claim UI quality when screenshots are blank, high-diff, overlapping, clipped, or contrast-broken.
- Do not claim HeroUI compliance when local components shadow official HeroUI components.
- Do not claim backend completion when endpoint auth, idempotency, schema fields, or error codes are missing.
- Do not claim completion when code review has unresolved blocker/high findings.
- Do not rely on stale official HeroUI docs snapshots.

## Pressure Test Responsibility

- Blank screenshots must block.
- Local Button/Table/Drawer clones must block.
- Missing API auth/idempotency/error coverage must block.
- Missing code review summary must block.
- Stale HeroUI docs must block.

## Next Gate

- `completion-verifier` may pass only after quality audits and `review_completion_gate` pass.


---
name: completion-verifier
description: Use before claiming a feature, plugin change, UI, API, backend, or full-stack implementation is complete.
---

# Completion Verifier

This skill blocks false completion claims. Evidence comes before status.

## Input Artifacts

- `00-stage.json`
- Implementation task ledger
- Test report
- Build report
- Screenshot report when UI applies
- HeroUI compliance report when UI applies
- API/data verification when backend applies
- Code review report
- Final acceptance report

## Output Artifact

- `docs/full-stack-development/requirements/<feature-slug>/06-verification/final-acceptance-report.md`

## Required MCP Tool

- `review_completion_gate`
- `review_visual_inspection_metrics`
- `review_hero_ui_component_graph_audit`
- `review_backend_contract_audit`
- `review_code_review_gate`
- `review_hero_ui_docs_freshness`
- `review_stage_gate`

## Hard Stops

- Do not claim complete without fresh test evidence.
- Do not claim complete without build evidence.
- Do not claim UI complete without desktop and mobile screenshots.
- Do not claim React Web UI complete without HeroUI compliance evidence.
- Do not claim complete with blocking code review issues.

## Pressure Test Responsibility

- Missing tests block.
- Missing build blocks.
- Missing screenshots block when UI applies.
- Missing review blocks.
- Missing acceptance blocks.

## Next Gate

- `verified`, then release or case/lessons curation.

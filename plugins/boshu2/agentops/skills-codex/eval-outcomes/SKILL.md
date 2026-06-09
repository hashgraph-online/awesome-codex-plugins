---
name: eval-outcomes
description: "Run eval outcomes."
---

# $eval-outcomes — Outcomes as a Projection of the Locked Eval Substrate (Codex Native)

> **Quick Ref:** Grade an agent's output via Outcomes (or any model) without forking the bar. `ao eval outcomes compile` projects a locked Task into a holdout-safe rubric (refuses to leak `target`/`ground_truth` — Managed Agents are not ZDR); grade it; `ao eval outcomes ingest` writes the score back as the one council verdict record. Outcomes is a projection, never an alternate authority.

## Codex path

Codex has no Managed Agents loop. Call the same `ao eval outcomes compile <input.json>` to get a holdout-safe rubric, grade it locally (Inspect AI over the dev split, or the bushido llama.cpp Qwen grader over tailnet), then `ao eval outcomes ingest <score.json> --json`. Net: Codex never touches the cloud Outcomes API but produces a byte-identical verdict record.

## Instructions

Load and follow the skill instructions from the sibling `SKILL.md` — OR read `skills/eval-outcomes/SKILL.md` in the host repo for the canonical specification. Then apply the three-phase Workflow (compile → grade → ingest), honoring the Critical Constraints (never send holdout `target`/`ground_truth`/PII; carry `judge_content_hash`; register a global Dolt burn for holdout grades).

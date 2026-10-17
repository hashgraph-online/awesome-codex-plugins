# `skills/kicad/review/` — Deep Review Sub-component (v2.0)

This is an internal sub-component of the kicad skill. It is NOT a standalone skill (no nested SKILL.md — confirmed unsupported across Claude Code, Codex, Gemini CLI). Referenced from `skills/kicad/SKILL.md` as a progressive-disclosure link.

## Purpose

This directory hosts the v2.0 Deep Review infrastructure:

- **(a)** The Deep Review evidence gate + `deep_review.schema.json` (spec §3.C/§3.D): per-IC LLM datasheet comparison with durable, evidence-linked findings in `analysis/deep_review.json`.
- **(b)** The optional `design_context` subagent input (spec §3.B): reads schematic + BOM + design intent, emits `design_context.json`. Used as an optional input to the Deep Review pass.
- **(c)** The annotation merge machinery (optional detector-finding triage): `merge_annotations.py` validates `review_annotations.json`, applies `llm_review` overlays to raw analyzer findings, and verifies HI-3 strip round-trip. Authority caps removed in v2.0 — a `suppressed` annotation now always applies its overlay. Quarantined findings remain visible in the merge report.
- **(d)** `_mini_jsonschema.py`: stdlib-only JSON Schema Draft 2020-12 validator (keyword subset used by Layer 2 schemas). No third-party `jsonschema` dep at runtime.

## Structure

| Path | Purpose |
|------|---------|
| `prompts/design_context.md` | Subagent prompt: read schematic + BOM + design intent, emit design_context.json |
| `schemas/design_context.schema.json` | JSON Schema for design context output |
| `schemas/review_annotations.schema.json` | JSON Schema for review annotations |
| `schemas/deep_review.schema.json` | JSON Schema for Deep Review evidence-gated findings |
| `scripts/build_review_plan.py` | Emits 1-task plan JSON for design_context dispatch |
| `scripts/merge_annotations.py` | Validates + applies overlays to raw analyzer JSONs → `analysis/merged/<analyzer>.json` |
| `scripts/validate_review.py` | Standalone CLI for review_annotations.json validation |
| `scripts/deep_review_gate.py` | Evidence gate: validates deep_review.json, writes durable findings |
| `scripts/run_phase4_exercise.py` | Orchestrates the end-to-end fixture exercise |
| `fixtures/*.example.json` | Round-trip fixtures for schema contract tests |

## Surviving invariants (v2.0)

- **HI-1:** Layer 1 findings are immutable — detector-owned fields are never mutated by any overlay machinery.
- **HI-3:** `strip_llm_overlays(merged)` == raw input, byte-identical. The merge is always reversible.
- **HI-6:** `reviewer_observations[]` lives in `review_annotations.json`, never merged into `findings[]`.
- **No-LLM run yields identical analyzer output:** stripping `llm_*` fields recovers the deterministic baseline.
- **Stable finding identity:** `finding_id` is stable across runs; this invariant extends to Deep Review findings (`deep_review:<12-hex>` form).
- **No hidden suppression:** quarantined/suppressed annotations are visible in the merge report; nothing is silently discarded.

## Retired in v2.0 (spec §5)

The following v1.4 Layer 2 cage constraints are removed. Trust now comes from the Deep Review evidence gate, not permission rules:

- **Overlay-only constraint (HI-2 label):** the merge still only writes `llm_review` siblings, but this is now a design property, not a cage rule.
- **Observations-are-not-findings (HI-6 framing):** still true mechanically; but no longer framed as a restriction.
- **All authority caps and suppression rules (HI-8/HI-9):** `reviewer_observations[]` no longer has a `maxItems` cap; `confidence` is no longer capped at `medium`; `severity` is no longer capped at `warning`; suppressing an `error`-severity or `datasheet-backed` finding now applies normally; the 30% suppression rate cap is removed.
- **Severity tuning matrix:** `severity_tuning.json` and `severity_tuning.schema.json` deleted; `make_finding(design_context=...)` accepts the parameter for call-site compatibility but ignores it.
- **Layer 2 reviewer prompt:** archived to `old/layer2/reviewer.md` (gitignored on disk).

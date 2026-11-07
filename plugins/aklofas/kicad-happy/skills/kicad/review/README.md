# `skills/kicad/review/` — Deep Review Sub-component

This is an internal sub-component of the kicad skill. It is NOT a standalone skill (no nested SKILL.md — confirmed unsupported across Claude Code, Codex, Gemini CLI). Referenced from `skills/kicad/SKILL.md` as a progressive-disclosure link.

## Purpose

This directory hosts the Deep Review infrastructure:

- **(a)** The Deep Review evidence gate + `deep_review.schema.json`: per-IC LLM datasheet comparison with durable, evidence-linked findings in `analysis/deep_review.json`.
- **(b)** The optional `design_context` subagent input: reads schematic + BOM + design intent, emits `design_context.json`. Used as an optional input to the Deep Review pass.
- **(c)** The annotation merge machinery (optional detector-finding triage): `merge_annotations.py` validates `review_annotations.json`, applies `llm_review` overlays to raw analyzer findings, and verifies HI-3 strip round-trip. There are no authority caps — a `suppressed` annotation always applies its overlay. Annotations whose `finding_id` matches no finding are listed in the merge report as orphans, and suppressed annotations are counted there.
- **(d)** `_mini_jsonschema.py`: stdlib-only JSON Schema Draft 2020-12 validator (keyword subset used by Layer 2 schemas). No third-party `jsonschema` dep at runtime.

## Structure

| Path | Purpose |
|------|---------|
| `prompts/design_context.md` | Subagent prompt: read schematic + BOM + design intent, emit design_context.json |
| `schemas/design_context.schema.json` | JSON Schema for design context output |
| `schemas/review_annotations.schema.json` | JSON Schema for review annotations |
| `schemas/deep_review.schema.json` | JSON Schema for Deep Review evidence-gated findings |
| `scripts/build_review_plan.py` | Emits 1-task plan JSON for design_context dispatch |
| `scripts/merge_annotations.py` | Validates + applies overlays to raw analyzer JSONs → `<--merged-dir>/<analyzer>.json` (run-based consumers read `analysis/merged/<run>/<analyzer>.json`) |
| `scripts/validate_review.py` | Standalone CLI for review_annotations.json validation |
| `scripts/deep_review_gate.py` | Evidence gate: validates deep_review.json, writes durable findings |
| `scripts/run_phase4_exercise.py` | Orchestrates the end-to-end fixture exercise |
| `fixtures/*.example.json` | Round-trip fixtures for schema contract tests |

## Invariants

- **HI-1:** Layer 1 findings are immutable. The merge sets only a `llm_review` key on each matched finding and leaves every detector-owned field alone (`merge_annotations.py`, `merge()`).
- **HI-3:** `strip_llm_overlays(merged)` equals the raw input as decoded JSON (the merged file is re-serialized, so bytes can differ). The raw files are only read; `merge()` raises `RuntimeError` when the round-trip differs, so the merge is always reversible.
- **HI-6:** `reviewer_observations[]` lives in `review_annotations.json`. The merge only counts it (`reviewer_observations_count` in `_merge_report.json`) and never copies it into `findings[]`.
- **No-LLM run yields identical analyzer output:** stripping `llm_*` keys recovers the deterministic baseline (`finding_schema.strip_llm_overlays`).
- **Stable finding identity:** `finding_id` is stable across runs (`finding_schema.assign_finding_ids`); Deep Review findings use the `deep_review:<12-hex>` form.
- **No hidden suppression:** a `suppressed` annotation always applies its overlay and is counted in `suppressed_count`; orphan annotations are listed, not dropped silently. Deep Review findings that fail the evidence gate are kept in `quarantined[]` of `analysis/deep_review.json` with a `quarantine_reason`.

## Trust model

Trust comes from the Deep Review evidence gate, not from permission rules on annotations:

- **No caps:** `reviewer_observations[]` has no `maxItems`; annotation `confidence` and `suggested_severity` take any value of their enums (`schemas/review_annotations.schema.json`), and suppressing an `error`-severity or `datasheet-backed` finding is allowed.
- **No severity tuning:** `make_finding` takes no `design_context` parameter.
- **Reviewer role:** `build_review_plan.py` emits only the `design_context` task; there is no Layer 2 reviewer prompt in `prompts/`.

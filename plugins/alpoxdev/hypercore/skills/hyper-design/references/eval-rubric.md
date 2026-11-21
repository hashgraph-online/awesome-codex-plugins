# Evaluation Rubric

Use this reference when adding, reviewing, or interpreting `assets/evals/` cases.

## Detector oracle

Each detector rule needs a minimal positive fixture and a false-positive guard fixture. Assert only observable machine output:

- rule ID, source location, severity, engine, and evidence kind
- candidate exception status when explicit local context supports it
- absence of a finding when a fixture is meant to prove a guard
- stable summary counts only when unrelated rule additions cannot change them

Do not grade whether a source match proves visual quality, accessibility conformance, product fit, or AI authorship.

## Workflow oracle

Workflow JSONL cases cover trigger, mode, protected contracts, browser capability fallback, and unsafe requests. Every case must state the required action and forbidden outcome. Keep established cases; add a regression whenever a real failure appears.

## Human sampling

Before promoting a static rule to `P1` or an immediate tier, inspect at least five relevant and five exception-like examples. Record confirmed, false-positive, and ambiguous outcomes. A rule with more than 10% false positives in the reviewed sample remains review-only or is removed.

## Result boundaries

- Static detector output proves source signatures only.
- Rendered evidence requires a valid browser handoff capture.
- Screenshot evidence does not prove keyboard, semantic, accessibility, or task completion.
- `generic-output risk` is a prioritization label, never a claim of AI authorship.

## Sources

> Claims checked 2026-09-21. No external source was used in this file.

The detector, workflow, and human-sampling criteria are this package's own. The 10% false-positive threshold and the five-example sample size are values this package chose, not external guidance.

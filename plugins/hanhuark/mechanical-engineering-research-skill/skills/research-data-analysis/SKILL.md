---
name: research-data-analysis
description: Design and analyze engineering experiments or simulations using baseline cases, hypothesis-driven DOE, traceable data processing, defensible plots, uncertainty, and validation. Use for CFD, laboratory data, ML workflows, parameter studies, or research code.
---

# Research Data Analysis

## Purpose

Produce understanding, not an exhaustive parameter sweep. Use a detailed baseline case to demonstrate the measurement/model chain, then choose experiments or simulations that can prove or disprove a stated hypothesis.

## Route To References

- For baseline-first DOE, figure discussion, and technical analysis structure, read `references/technical-writing-analysis.md`.
- For reproducible research code and data pipelines, read `references/research-coding.md`.
- For AI/ML-assisted thermal-fluid analysis, read `references/ai-tools-thermal-fluids.md`.

## Hypothesis-Driven DOE

1. State the mechanism and the falsifiable prediction.
2. Define a baseline with detailed diagnostics, data reduction, uncertainty, and expected limits.
3. Select contrast cases that isolate mechanisms, including controls or negative cases when informative.
4. Define response variables, sampling, replication, exclusions, and statistical/physical decision criteria before inspecting outcomes.
5. Report what each possible outcome would mean. A useful DOE advances understanding whether the hypothesis is supported or rejected.

Do not multiply arbitrary levels of independent parameters simply because computation or test time is available. Use broad sweeps only when exploration, optimization, surrogate construction, or response-surface estimation is itself justified.

## Data And Plots

Preserve raw-data provenance, units, calibration and preprocessing steps, scripts/environment, deterministic inputs, and versioned outputs. Build plots around comparisons that test the hypothesis. Show uncertainty, sample size or repeat count where relevant, and avoid visually implying precision beyond the measurement or model.

For ML, split data by experimental condition, video, specimen, or run when adjacent observations are correlated; distinguish predictive performance from physical validation and domain-transfer performance.

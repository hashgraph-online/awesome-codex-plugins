# Paper Writing Style

Use this reference when drafting or revising full technical papers, journal manuscripts, conference papers, abstracts, introductions, methods, results/discussion sections, and conclusions in the preferred thermal-fluid mechanical engineering style.

## Core Style

Write as a technical paper that teaches the physics, not as a collection of facts.

The preferred style is:

- Problem-driven: start from an important engineering or scientific need.
- Mechanism-focused: explain what physical process, measurement, model, or data relationship is being clarified.
- Evidence-forward: use figures, equations, experiments, simulations, and comparisons to support claims.
- Compact: avoid redundant sentence pairs when one sentence can state the method and conclusion.
- Specific: include conditions, geometry, materials, metrics, regimes, uncertainty, and validation where relevant.
- Careful: separate measured results, model predictions, interpretation, and speculation.

## Abstract Pattern

Use a dense but logical abstract structure:

1. Motivation or need: one sentence on the application, scientific problem, or limitation.
2. Gap or challenge: one sentence on what is difficult, unresolved, expensive, unmeasurable, or poorly understood.
3. Approach: one or two sentences naming the experimental, numerical, modeling, AI/ML, or diagnostic method.
4. Validation or analysis scope: one sentence on datasets, surfaces, regimes, operating conditions, benchmark comparisons, or validation approach.
5. Key findings: two to four concrete findings with metrics, trends, regimes, or mechanisms.
6. Significance: one final sentence on what the method or result enables.

Avoid starting the abstract with broad generic statements if a specific research need is available. Avoid ending with only "results are discussed"; end with what is learned or enabled.

## Introduction Pattern

Build the introduction as a narrowing funnel:

1. Establish the application importance and technical need.
2. Define the key thermal-fluid phenomenon or performance metric.
3. Summarize state of the art by category, not paper by paper.
4. Identify what existing approaches have established.
5. State what remains difficult to measure, predict, isolate, generalize, or design.
6. Explain why the gap persists, such as coupled physics, limited diagnostics, expensive CFD, uncertain boundary conditions, scale mismatch, or insufficient data.
7. Introduce the present work as a targeted response to that gap.
8. Preview the main methods and contributions in a compact final paragraph.

Use "However" and "Nevertheless" to pivot from importance or prior work to limitations, but make the limitation specific. Do not use novelty as "no prior work exists"; explain why the missing work is important and challenging.

## Contribution Paragraph

At the end of the introduction, include a contribution paragraph that answers:

- What is developed, measured, modeled, or demonstrated?
- What data, regimes, surfaces, geometries, or systems are studied?
- What comparisons or validation are performed?
- What physical insight or practical capability is obtained?

Prefer concrete contribution verbs:

- develops
- validates
- quantifies
- compares
- demonstrates
- reveals
- identifies
- establishes
- enables

Avoid vague verbs such as "explores" unless the work is explicitly exploratory.

## Methods Pattern

Write methods so the reader can reproduce or audit the work.

For experiments, include:

- facility overview and figure reference;
- sample/material preparation;
- operating conditions and procedure;
- sensors, locations, sampling rates, calibration, synchronization, and uncertainty;
- data-reduction equations and property sources;
- repeatability, number of tests, and steady-state or transient criteria.

For modeling or simulation, include:

- governing equations or objective function;
- assumptions and justification;
- boundary and initial conditions;
- geometry and parameter definitions;
- numerical method, mesh, convergence, and validation;
- outputs and post-processing metrics.

For AI/ML papers, include:

- dataset source and split strategy;
- raw input representation;
- preprocessing and feature extraction;
- model architecture and baseline models;
- training details only to the extent needed for reproducibility;
- metrics tied to the engineering task;
- generalization and failure-case analysis.

## Results And Discussion Pattern

Write results as a sequence of figure-led arguments.

For each major figure or table:

1. Orient: "Fig. X shows..." with variables, conditions, cases, and uncertainty representation.
2. Observe: state the main trend, regime, threshold, error pattern, or comparison.
3. Quantify: provide key values, relative changes, slopes, errors, or performance metrics when useful.
4. Explain: connect the observation to physical mechanisms, model structure, measurement effects, or data features.
5. Compare: relate to literature, baseline cases, simulations, correlations, or other surfaces/regimes.
6. Imply: state what this means for the research question, design guidance, measurement capability, or next analysis.

Use transition sentences to make the analysis cumulative:

- "To understand the role of..."
- "To isolate the effect of..."
- "To validate the model..."
- "To examine whether this trend generalizes..."
- "This observation indicates..."
- "These results suggest..."

Do not present plots as isolated results. Each figure should either answer a question, motivate the next analysis, or close a gap from the introduction.

## Baseline To Generalization

Start results with a representative baseline case when the work includes experiments, simulations, image analysis, acoustic signals, or ML workflows.

Use the baseline to demonstrate:

- raw data and processed metrics;
- event definitions, regimes, or labels;
- calculation or model pipeline;
- uncertainty and sanity checks;
- how to read later figures.

Then generalize through parametric studies, repeated tests, design comparisons, or literature benchmarks.

## Model And AI/ML Result Style

When writing about models or AI/ML tools, avoid treating accuracy as the final contribution.

Use this sequence:

1. State the prediction, reconstruction, classification, segmentation, or surrogate task.
2. Explain why the task matters physically or practically.
3. Compare model types, data representations, sequence lengths, feature extraction methods, or training regimes.
4. Report metrics with engineering interpretation.
5. Analyze error distribution, regime dependence, failure cases, or latent variables.
6. Connect the model output to physical features, thermal resistance, heat flux, bubble dynamics, interface motion, or design parameters.
7. State what the model enables: faster design, nonintrusive measurement, real-time monitoring, mechanism identification, or reduced experimental/CFD burden.

When discussing latent spaces, modes, or features, explicitly connect them to recognizable physical behavior.

## Literature Comparison Inside Results

Use literature comparison to establish generality or positioning, not as decoration.

- Compare against correlations, prior datasets, benchmark surfaces, standard methods, or reported ranges.
- Explain differences through geometry, regime, fluid, material, diagnostic method, or data reduction.
- State whether the present result confirms, extends, or challenges prior understanding.
- If performance is not better than literature, identify the actual contribution, such as measurement access, transient behavior, multimodal data, model interpretability, uncertainty quantification, or practical implementation.

## Sentence-Level Preferences

Prefer compact method-result sentences:

```text
The model is validated against X and then used to investigate Y.
```

```text
Rahman et al. used X to demonstrate Y.
```

Avoid redundant pairs:

```text
Rahman et al. studied X. Their results showed Y.
```

Use "indicates" for evidence-supported interpretation, "suggests" for weaker inference, and "demonstrates" only when the evidence directly supports the claim.

Use "due to" or "because" only when the mechanism is supported. Otherwise use "may be attributed to" or "is likely associated with."

## Conclusion Pattern

Conclusions should be compact, specific, and cumulative.

Use this structure:

1. Re-state what was developed, measured, modeled, or demonstrated.
2. Summarize the main quantitative or qualitative findings.
3. State the mechanism or interpretation.
4. State the practical or scientific implication.
5. Optional: note limitations and future work if important.

For multi-result papers, numbered conclusions are effective. Each numbered item should contain a complete takeaway, not just a topic label.

Avoid broad restatement of the introduction. The conclusion should tell the reader what is now known because of this work.

## Manuscript Self-Check

Before finalizing a paper draft, check:

- Does the abstract move from need to gap to method to findings to significance?
- Does the introduction narrow from application to gap to present contribution?
- Are background references grouped by category and key papers discussed selectively?
- Does each methods subsection include enough detail for audit or reproduction?
- Are assumptions stated before model use?
- Does the results section start from a baseline or representative case when appropriate?
- Does each figure discussion include observation, mechanism, and implication?
- Are model or AI results interpreted physically rather than only statistically?
- Does the conclusion state concrete findings rather than rephrasing the abstract?

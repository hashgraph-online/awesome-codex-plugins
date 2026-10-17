# Technical Writing, Data Analysis, And Plotting

Use this reference for manuscript-style thermal-fluid writing, experimental methods, modeling sections, data analysis, figures, and results discussion.

## Paragraph Logic

Write each paragraph around one central topic.

- Put the central topic in the first sentence unless a short transition sentence is needed.
- Make each sentence build on the previous sentence: define the context, add evidence, explain the mechanism, then state the implication.
- Avoid isolated facts that do not advance the paragraph's claim.
- End paragraphs with the consequence, remaining gap, or transition to the next paragraph.

## Introduction And Background Logic

Use this order unless the target venue or user request calls for a different structure:

1. Establish why the research area matters for applications, performance, safety, efficiency, or fundamental understanding, and cite sources.
2. Summarize the state of the art: what has been studied, which approaches dominate, and what is already known.
3. Identify remaining issues, limitations, unresolved mechanisms, measurement gaps, or design barriers.
4. Explain why the issues remain unsolved, such as difficult measurements, limited diagnostics, coupled physics, lack of models, scale mismatch, or limited operating conditions.
5. State the proposed innovation, method, model, measurement, or design that addresses the gap.
6. State the significance and impact: what the innovation enables, clarifies, predicts, improves, or makes measurable.

Do not write "no prior work has been done on X" as the novelty claim. Lack of prior work does not prove importance. Instead, explain the challenge that limited prior work and how the proposed work overcomes that challenge.

For background references in introductions, cite by category. Acknowledge broad bodies of work compactly, using category-specific citation groups rather than one sentence per paper or one undifferentiated citation range. For key papers that need prose discussion, use first-author-last-name plus "et al." and avoid long author lists.

## Experimental Methodology

Provide enough detail that a technically competent reader can reproduce or audit the work.

Include:

- Test facility layout, major components, flow path, heating/cooling path, pressure control, visualization path, and data-acquisition architecture.
- Materials, samples, surface preparation, fabrication recipes, dimensions, suppliers or grades when relevant, cleaning steps, and storage/handling.
- Instrumentation model or class, sensor locations, calibration, sampling rate, resolution, synchronization, and uncertainty.
- Operating procedure, including startup, degassing or conditioning, steady-state criteria, step size, dwell time, shutdown, and repeat tests.
- Data reduction equations, property sources, filtering, segmentation, fitting, uncertainty propagation, and outlier handling.
- Replication details such as number of samples, number of trials per sample, and how mean and standard deviation are reported.

## Modeling Sections

List assumptions upfront before deriving or using the model.

For each assumption, provide:

- The assumption.
- The physical or empirical justification.
- The expected validity range.
- The consequence if the assumption fails.

Then present governing equations, boundary conditions, closure relations, material properties, dimensionless groups, numerical method if any, and validation or sanity checks.

## Data Analysis

State exactly how raw signals become plotted quantities.

- Start with a good baseline case. Use it as the detailed proof of concept and the demo case that shows the full analysis pipeline before scaling to parameter studies.
- Define every metric before interpreting it.
- Include equations, units, time windows, thresholds, filters, fitting windows, and normalization.
- Report sample size and uncertainty representation.
- Check whether the trend is robust to reasonable analysis choices.
- Distinguish direct measurement, derived quantity, fitted parameter, and interpretation.

For thermal-fluid experiments, explicitly check regime, property variation, heat loss, background noise, synchronization, steady-state criteria, and sensor bandwidth.

## Baseline Case Analysis

Choose one baseline case that is representative, physically interpretable, and data-rich enough for detailed examination.

Use the baseline case to:

- Demonstrate the full data-processing pipeline from raw data to final metrics.
- Show representative signals, images, fields, contours, spectra, or time histories.
- Explain how thresholds, filters, segmentation, fitting windows, and uncertainty estimates are selected.
- Verify conservation laws, scaling expectations, boundary conditions, sensor response, grid convergence, or repeatability as applicable.
- Identify artifacts, noise sources, and limitations before interpreting a larger dataset.
- Establish vocabulary and mechanisms that will be reused in the parameter study.

Do not skip detailed baseline analysis in favor of only reporting aggregate trends. The baseline case should make the later parametric results credible and easier to interpret.

## Hypothesis-Driven DOE

Design experiments, simulations, and parametric studies around hypotheses rather than exhaustive parameter sweeps.

For each DOE block, state:

- The hypothesis being tested.
- The physical mechanism behind the hypothesis.
- The input parameters that can isolate or stress that mechanism.
- The output metrics that would support or refute the hypothesis.
- The controls, baseline, and comparison cases.
- The expected outcomes and how each possible outcome would improve understanding.

Avoid varying every independent parameter over many levels just because the parameters exist. For example, three inputs with ten levels each creates 1000 cases, but this is often an exhaustive search rather than an experiment designed to answer a question.

A good DOE should be useful whether the hypothesis is confirmed or rejected. If either result would be hard to interpret, redesign the cases to isolate mechanisms, reduce confounding variables, or add diagnostics.

When many parameters matter, use a staged plan:

1. Establish the baseline case and validate the analysis workflow.
2. Run targeted single-mechanism cases to test first-order hypotheses.
3. Add interaction cases only where a physical coupling is expected.
4. Use broader sweeps, response surfaces, or optimization only after the dominant mechanisms and useful parameter ranges are known.

## Plotting

Make plots support the argument, not merely display data.

- Choose axes that reveal the mechanism, such as dimensionless groups, normalized variables, inverse length scales, heat flux, superheat, pressure drop, or pumping power.
- Label axes with symbols, names, and units.
- Show uncertainty with error bars, shaded bands, or confidence intervals when data support it.
- Use legends, markers, colors, and line styles that remain distinguishable in grayscale when possible.
- Avoid overfitting trend lines; use a model-based fit only when the model and validity range are stated.
- Include enough caption detail that the plot can be understood without rereading the methods.

## Results And Figure Discussion

Discuss figures in four levels:

1. Description: State what the figure shows, including variables, conditions, samples, and uncertainty representation.
2. Observation: Identify the main trends, thresholds, extrema, slopes, regimes, or anomalies.
3. Physical explanation: Explain the observation using mechanisms, scaling, competing effects, or limiting processes.
4. Literature comparison: Compare the conclusion with existing work, noting whether it is consistent, extends prior understanding, or reveals something not previously reported.

For multi-panel figures, describe how panels connect instead of treating them as unrelated plots.

When discussing disagreement with existing work, first check differences in geometry, operating regime, fluid properties, measurement method, uncertainty, and data-reduction definitions.

## Results Writing Pattern

Use this sentence-level flow for each major result:

1. "Figure X shows..." to orient the reader.
2. "It is observed that..." to state the trend.
3. "This trend indicates/suggests..." to interpret the result.
4. "Physically, this can be attributed to..." to explain the mechanism.
5. "This conclusion is consistent with/differs from..." to situate the result relative to prior work.
6. "Therefore..." to state the implication for the research question.

Avoid claiming novelty only because a trend was not previously reported. State why the new observation matters and what measurement, model, or analysis made it possible.

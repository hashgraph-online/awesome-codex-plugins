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
6. State the significance and impact: the specific quantity, decision, capability, or physical understanding that the innovation clarifies, predicts, improves, or makes measurable.

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

Open a results subsection with its purpose and connection to the preceding analysis when that connection is not already clear. Identify the comparison being made before interpreting it.

Develop each figure discussion through four steps:

1. **Describe:** Identify the plotted quantities, axes, conditions, and configurations. Include the uncertainty definition when it is needed to read the result.
2. **Observe:** State the direction, threshold, extremum, regime change, or difference, with only the numerical anchors needed to support it.
3. **Explain:** Relate the observation to theory, mechanisms, hypotheses, or relevant prior studies. Label plausible explanations as hypotheses when the controls do not isolate them. Repeat observation and explanation when a figure contains distinct findings.
4. **Conclude:** State the specific implication supported within the tested scope.

Combine plots that support one consistent argument in a connected paragraph. Give plots separate discussions when their questions, evidence, or implications differ; do not assign a paragraph mechanically to every subfigure. Use this sequence as reasoning, not mandatory sentence stems. A literature comparison belongs where it helps explain or bound the observation, rather than as an obligatory closing sentence.

Before attributing disagreement with prior work to physics, compare geometry, operating regime, properties, measurement method, uncertainty, and data-reduction definitions.

Avoid claiming novelty only because a trend was not previously reported. State why the new observation matters and what measurement, model, or analysis made it possible.

## Concise Section Revision

- Re-read the current manuscript and relevant figures/tables before revising a previously edited section. An earlier draft or extraction may be stale.
- Preserve definitions, units, signs, uncertainty, citations, and decisive protocol boundaries. Remove repeated setup, secondary numerical catalogs, and repeated qualifications; do not target an arbitrary word reduction.
- Identify model architecture, task, input/context duration, and evaluation protocol where ambiguity would change the interpretation. Use a short name only after its identity is clear; do not infer that similarly named models in different sections use the same checkpoints or windows.
- Keep captions descriptive. Put interpretation and substantive methodological notes in the main text. For Han Hu manuscripts, avoid an extra explanatory paragraph below a table: integrate essential notes into the main text and drop redundant ones, retaining symbol definitions or footnotes required by the venue.
- When asked whether a value appears in a table or figure, inspect those objects and distinguish text-only reporting from displayed evidence. A value repeated from manuscript prose is not independently verified against raw data or logs. Do not invent a table location or new measurement.
- A conclusion synthesizes the principal findings, their significance, and the decisive validation limits. Retain a few key numerical anchors with their uncertainty, not every metric or a figure-by-figure recap. Check it against the final results after section revisions.

## Evidence Checks During Compression

Apply the checks relevant to the section; do not turn every rewrite into a new experimental study.

- Preserve aggregation: mean signed bias, mean absolute error, per-sample error, and variability across optimization seeds answer different questions. A bound on a mean is not a bound on every sample or seed, and seed variability is not independent experimental uncertainty.
- Keep distinct calibrations, partitions, capacities, and sample counts identifiable. Do not pool incompatible comparisons or transfer an attribution result from one configuration to another without evidence.
- Input perturbations establish sensitivity to the intervention. Check which properties changed before attributing the response to motion or a physical mechanism; averaging may also alter spatial detail, and reordering may change the final input. Define branch-variance fractions and covariance treatment before interpreting them. Correlation with an image-derived proxy does not exclude alternative causes.
- The best tested setting does not establish an optimum. Reaching a training limit does not prove that further training improves test performance or that a limitation can only bias the trend in one direction.
- Separate training time, inference latency, memory, and arithmetic cost. Check frame-period comparisons arithmetically. Amortized batch time per sample measures throughput, not individual response latency; distinguish full-batch execution, batch accumulation, input-history startup, and end-to-end processing when relevant. State the assumed prediction-update cadence.

For a separate replacement document, preserve the original, retain requested figures and table values, and use anchored comments for unresolved author checks. Verify cross-references and numerical entries, then render and inspect every page, including caption breaks and table wrapping. Report what was checked and what remains unresolved; prose edits do not close scientific validation gaps.

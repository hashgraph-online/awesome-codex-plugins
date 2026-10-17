# Research Coding Guidelines

Use this reference when writing, reviewing, or refactoring code for thermal-fluid research, data analysis, plotting, simulation automation, CFD post-processing, machine learning, or reproducible research workflows.

## Core Principle

Write research code so that another researcher can understand what physical question is being answered, reproduce the result, and safely modify the analysis later.

Research code should be:

- Traceable from raw data to final figure or metric.
- Explicit about units, assumptions, constants, and data sources.
- Modular enough to reuse on multiple cases without copy-paste editing.
- Simple enough that the analysis logic remains inspectable.
- Reproducible through documented inputs, parameters, environment, and outputs.

## Start From The Research Question

Before writing code, define:

- What physical quantity, trend, metric, or figure the code must produce.
- What raw inputs are required.
- What assumptions and constants are used.
- What units are expected at each stage.
- What validation or sanity check should pass.

Avoid writing a large generic pipeline before validating the analysis on a baseline case.

## Baseline-First Implementation

Implement the full workflow on one representative baseline case before scaling to many cases.

For the baseline case, show:

- Raw input inspection.
- Preprocessing steps.
- Intermediate quantities.
- Final figure or metric.
- Sanity checks and likely failure modes.

After the baseline case works, generalize the code to batches, parameter studies, or automated reports.

## Repository And File Organization

Prefer a clear project structure:

```text
project/
  README.md
  data/
    raw/
    processed/
  scripts/
  src/
  notebooks/
  figures/
  results/
  config/
  tests/
```

Use `data/raw/` as read-only input when possible. Write generated files to `data/processed/`, `figures/`, or `results/`.

Keep paths configurable. Avoid hard-coded absolute paths unless the script is explicitly personal or one-off.

## Data Processing

Make each processing step explicit.

- Load raw data without silently changing it.
- Validate column names, units, shapes, time bases, and missing values.
- Convert units near the data-loading boundary and document the conversion.
- Keep filtering, smoothing, thresholding, interpolation, and fitting choices visible.
- Save processed data with metadata describing the processing settings.
- Do not overwrite raw data.

For time-series data, record sampling rate, synchronization, trigger times, time windows, filters, and event definitions.

For image/video data, record frame rate, resolution, calibration, field of view, preprocessing, segmentation thresholds, labels, and tracking rules.

## Plotting Code

Plots should communicate the mechanism or comparison.

- Put plotting settings in reusable functions when many figures share style.
- Label axes with variable names and units.
- Use legends, colors, markers, and line styles consistently across related figures.
- Include uncertainty where available.
- Export publication-quality figures with deterministic filenames.
- Save both editable and presentation-ready formats when useful.

Separate the calculation of plotted data from the formatting of the figure. This makes the analysis easier to verify.

## Functions And Scripts

Use functions for repeated research logic:

- property calculations
- dimensionless numbers
- heat-transfer correlations
- uncertainty propagation
- data loading and cleaning
- feature extraction
- plotting common figure types

A script should have a clear entry point, explicit inputs, and predictable outputs.

For Python scripts, prefer:

```python
def main():
    ...

if __name__ == "__main__":
    main()
```

## Notebooks

Use notebooks for exploration, explanation, and interactive analysis.

For final or repeatable workflows:

- Move reusable functions into scripts or `src/`.
- Restart and run the notebook from top to bottom before sharing.
- Keep cells in logical order.
- Avoid hidden state that only works after manual cell execution.
- Include enough markdown to explain the analysis choices.

## Physical Sanity Checks

Every analysis should include physics checks when possible:

- Units and dimensional consistency.
- Order-of-magnitude estimates.
- Energy, mass, or momentum balance.
- Monotonicity or limiting behavior expected from theory.
- Comparison to known correlations, baseline data, or literature.
- Bounds on efficiencies, heat fluxes, velocities, pressures, and temperatures.

If a result violates expected physics, investigate before polishing the figure.

## Simulation And CFD Automation

When automating simulations, record:

- Geometry parameters.
- Mesh settings and mesh version.
- Boundary conditions.
- Solver settings.
- Convergence criteria.
- Material properties.
- Output quantities.
- Case naming convention.

Do not mix setup generation, solver execution, post-processing, and plotting into one opaque script unless the workflow is very small. Prefer clear stages with saved intermediate outputs.

For surrogate modeling or design exploration, store the design matrix, parameter bounds, and train/test split.

## Machine Learning Code

Make ML code reproducible and physically interpretable.

- Fix random seeds when appropriate.
- Prevent leakage across experiments, videos, geometries, surfaces, pressures, or simulation families.
- Save preprocessing settings, model configuration, weights, and metrics.
- Include baseline models before complex models.
- Inspect failure cases visually or physically.
- Report metrics by regime or condition when aggregate metrics hide important behavior.

Connect model performance back to the thermal-fluid question. Accuracy alone is not the scientific contribution.

## Configuration And Metadata

Use configuration files or clearly named parameters for:

- input paths
- case IDs
- fluid and material properties
- calibration constants
- thresholds and fitting windows
- plot style
- model hyperparameters

Save metadata with outputs so figures and tables can be traced back to the code and data that produced them.

## Testing And Validation

Use lightweight tests for critical functions:

- unit conversions
- dimensionless numbers
- correlations
- uncertainty propagation
- data parsers
- event detection logic

For research code, a small set of sanity tests is often more valuable than no tests. Include regression checks for baseline outputs when the analysis will be reused.

## Code Review Checklist

Before considering research code ready, check:

- Can a new user identify the raw inputs, outputs, and main entry point?
- Are units and assumptions explicit?
- Is raw data preserved?
- Can the baseline case be reproduced?
- Are figures traceable to scripts and processed data?
- Are hard-coded paths, magic numbers, and hidden notebook state avoided or documented?
- Are physical sanity checks included?
- Are failure modes or limitations stated?
- Is the code simple enough to audit?

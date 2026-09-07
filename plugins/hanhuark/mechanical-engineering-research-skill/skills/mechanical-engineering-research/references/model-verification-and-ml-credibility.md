# Model Verification And ML Credibility

Use this reference for CFD, numerical models, reduced-order models, surrogates, digital twins, scientific ML, and data-driven prediction.

## Separate Four Questions

1. **Solver convergence:** Did the iterative or time-marching calculation settle to the stated tolerance?
2. **Numerical verification:** Are discretization, domain, time-step, and implementation errors controlled?
3. **Model validation:** Does the model reproduce independent evidence within a defined regime and uncertainty?
4. **Use validity:** Is the proposed prediction, optimization, or decision inside the validated domain?

Do not use one of these as evidence for another.

## CFD And Numerical Models

Record governing equations, closure models, geometry, mesh and mesh version, boundary/initial conditions, property models, solver settings, convergence criteria, and outputs.

Check:

- residual histories and convergence of monitored engineering outputs;
- mass, energy, species, and momentum imbalance as applicable;
- mesh quality, near-wall treatment, `y+`, and thermal wall resolution;
- grid, domain, and time-step independence;
- iterative versus discretization error;
- Richardson extrapolation or GCI when appropriate;
- sensitivity to turbulence, multiphase, radiation, contact, and property models;
- analytical bounds, canonical benchmarks, correlations, or experiments;
- validation metrics and the regime over which validation applies.

Do not call a geometry optimal unless the objective, constraints, design variables, search domain, and penalties such as pumping power are defined.

## Reduced-Order Models And Surrogates

Record state variables, parameter bounds, sampling design, retained modes or basis, energy criterion, reconstruction error, stability, and online validity checks. Separate interpolation from extrapolation. Compare against a cheaper analytical or empirical baseline when available.

Test held-out geometries, operating paths, mesh families, or simulation families rather than random rows from the same trajectory. Record the exact parameter order at every file, API, and model boundary.

## Machine Learning

Define the physical task and why ML is needed. Then verify:

- raw input, labels, preprocessing, and data lineage;
- grouped train/validation/test splits by independent experiment, video, sample, facility, geometry, fluid, pressure, surface, operating path, or simulation family;
- leakage through repeated frames, overlapping windows, duplicates, normalization, feature extraction, or preprocessing fitted on all data;
- simple and physics-based baselines;
- ablations that isolate the claimed contribution;
- error by physical regime and at important thresholds;
- calibration and uncertainty where decisions depend on confidence;
- interpolation versus extrapolation and domain shift;
- conservation, bounds, monotonicity, symmetry, or other physical constraints;
- failure cases, random seeds, environment, data version, and model version.

Use labels such as AI, predictive, validated, causal, or physics-informed only when the implemented method and evidence support them. A screening index, geospatial integration, reduced-order calculation, or rules engine is not automatically AI.

## Claim Gate

Match claim strength to evidence:

- **Demonstration:** the workflow runs on representative cases.
- **Verification:** implementation and numerical behavior meet defined checks.
- **Validation:** independent evidence supports the model in a stated domain.
- **Generalization:** performance persists across meaningful held-out conditions.
- **Deployment readiness:** inputs, drift, monitoring, failure handling, and user decisions are controlled.

Report what the model enables physically or practically. Accuracy alone is not the scientific contribution.

# Experimental Design And Uncertainty

Use this reference for thermal-fluid experiments, multimodal diagnostics, measurement planning, uncertainty budgets, repeatability, and evidence readiness.

## Start With The Measurement Model

Define the output quantity as a function of measured and assigned inputs before selecting instruments or test points. Record each input's units, range, resolution, calibration source, uncertainty component, time response, and expected covariance.

Use [symbol-unit-convention-ledger.csv](../assets/templates/symbol-unit-convention-ledger.csv) to keep the experiment, analysis code, equations, tables, and figures aligned.

## Plan The Experiment

1. State the hypothesis, mechanism, baseline, controls, independent variables, response variables, and pass/fail evidence.
2. Define geometry, working fluid, materials, surface condition, pressure, temperature, heat/load path, flow regime, and safety envelope.
3. Place sensors to resolve the measurement equation and dominant gradients without creating unacceptable disturbance.
4. Set sampling rate and bandwidth from the fastest relevant physical process and sensor response.
5. Define synchronization, trigger, clock drift, registration, and latency for multimodal measurements.
6. Define startup, conditioning or degassing, dwell time, steady-state/transient windows, shutdown, repeats, and failure criteria.
7. Use randomization or blocking where order, batch, ambient condition, sample, or operator can confound the result.
8. Prevent pseudoreplication. Distinguish frames or samples within one run from independent runs, specimens, or facilities.

Use a staged DOE: validate one data-rich baseline, test single-mechanism hypotheses, add physically motivated interactions, then use broader response surfaces or optimization.

## Uncertainty Budget

Separate:

- calibration and resolution uncertainty;
- repeatability and run-to-run variability;
- drift, synchronization, alignment, and sampling effects;
- property, geometry, and boundary-condition uncertainty;
- data-reduction and correction uncertainty;
- model-form or correlation uncertainty;
- scenario sensitivity that is not a probability distribution.

Propagate uncertainty through the measurement equation using a stated method. Include covariance when inputs are correlated. State coverage factor and confidence interpretation only when justified. Report uncertainty in the final output quantity, not only for individual instruments.

Do not call arbitrary parameter ranges confidence intervals or probabilities. Use terms such as sensitivity range, scenario envelope, or assumption-stress range when no statistical distribution has been established.

## Thermal-Fluid Evidence Gates

Check as applicable:

- calibration traceability, resolution, response time, and sensor placement;
- heat loss, contact resistance, background noise, parasitic conduction, and energy balance;
- flow development, pressure-drop correction, fluid properties, and reference state;
- emissivity, spatial calibration, optical distortion, and conduction spreading for IR or imaging;
- sensor coupling, trigger definition, filtering, windowing, and frequency response for acoustic data;
- frame rate, exposure, depth of field, segmentation validity, tracking continuity, and event timing for video;
- repeated tests, independent samples, outliers, missing data, and raw-data retention.

Before a quantitative cross-modal claim, verify synchronization and coordinate registration with evidence. Before an instance-level computer-vision claim, verify held-out annotation quality and failure cases.

## Reporting

State the number and level of independent replicates, measurement equation, calibration, uncertainty method, corrections, analysis windows, exclusions, and raw-data provenance. Distinguish repeatability within a setup from reproducibility across operators, facilities, or instruments.

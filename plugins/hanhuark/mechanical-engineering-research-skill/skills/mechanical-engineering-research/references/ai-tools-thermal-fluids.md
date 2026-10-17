# AI Tools For Thermal-Fluid Research

Use this reference when a task involves AI, machine learning, computer vision, sequence regression, surrogate modeling, sensor fusion, dimensionality reduction, data-driven control, or ML-assisted analysis for thermal-fluid systems.

## Core Principle

Use AI tools to extract physics, accelerate analysis, or enable measurements that are difficult with manual methods. Do not use machine learning as a substitute for defining the physical question, baseline case, uncertainty, and validation plan.

Always connect the ML task to a thermal-fluid objective:

- Detect or classify regimes, events, structures, or failure transitions.
- Quantify physical quantities from images, acoustic signals, simulations, or sensor streams.
- Extract interpretable features, modes, mechanisms, or low-dimensional coordinates.
- Build fast surrogate models for expensive experiments or simulations.
- Fuse multiple sensing modalities to improve robustness.
- Support design, control, monitoring, or decision-making.

## Tool Selection

Select tools from the physical task, data modality, evidence maturity, and required output. Before relying on a repository or model, inspect its current paper or technical basis, README, examples, dependencies, weights, license, data schema, tests, and release state. Treat current links, versions, and capabilities as volatile and verify them live when they matter.

Use user- or laboratory-provided tools when they fit the task, but evaluate them by the same criteria as third-party tools. Do not let repository availability substitute for method validation.

## Workflow

1. Define the engineering question.
   - Example: predict heat flux, identify CHF, measure bubble departure, quantify interface velocity, classify boiling regime, build a CFD surrogate, or extract dominant thermal-fluid modes.

2. Choose the data modality.
   - Images or videos: use computer vision, segmentation, tracking, optical-flow-like analysis, image regression, or classification.
   - Acoustic or hydrophone signals: use time-series features, frequency-domain features, event/hit features, or sequence regression.
   - CFD or simulation data: use surrogate modeling, reduced-order modeling, dimensionality reduction, active learning, or digital twins.
   - Multimodal data: use sensor fusion, aligned time histories, or multi-branch models.

3. Establish a baseline case.
   - Run the full pipeline on one representative case.
   - Show raw data, preprocessing, labels or annotations, model output, error cases, and final physical metrics.
   - Verify whether the model output agrees with human inspection, known physics, conservation laws, or independent measurements.

4. Design hypothesis-driven ML experiments.
   - State the hypothesis, such as "acoustic spectra encode heat flux," "bubble-interface dynamics predict CHF," or "low-dimensional CFD modes capture design trends."
   - Choose cases, labels, features, and model comparisons that can support or reject the hypothesis.
   - Avoid training a large model before confirming that the data contain the needed physics.

5. Validate and interpret.
   - Use train/validation/test separation that prevents leakage across videos, experiments, surfaces, pressures, geometries, or simulation families.
   - Report error metrics that match the engineering objective.
   - Test generalization across conditions, not only random splits from the same experiment.
   - Inspect failure cases and relate them to physics, sensor noise, domain shift, or labeling uncertainty.

Use [model-verification-and-ml-credibility.md](model-verification-and-ml-credibility.md) for leakage, grouped splits, calibration, ROM/surrogate validation, extrapolation, and claim-strength checks.

## Data Preparation

For image/video workflows:

- Record frame rate, resolution, field of view, lighting, magnification, exposure time, and synchronization.
- State whether frames, videos, masks, labels, or annotations are used.
- Define event labels such as departure, coalescence, CHF, film boiling, or regime transition.
- Check whether the frame rate is sufficient for tracking; lower frame rates may support per-frame quantities but not reliable dynamics.

For acoustic or sequence workflows:

- Record sampling rate, sensor type, sensor location, thresholding, hit definition, filtering, and frequency-domain processing.
- Define sequence length, overlap, FFT/windowing choices, and label timing.
- Check synchronization between thermal measurements and signal data.
- Verify clock alignment, latency, trigger uncertainty, and coordinate registration before quantitative multimodal fusion claims.

For CFD/surrogate workflows:

- Define geometry parameters, mesh, solver settings, boundary conditions, outputs, and convergence criteria.
- Include design-space bounds and explain why training cases cover the intended interpolation region.
- Treat extrapolation outside the training design space as high risk unless separately validated.

## Model Evaluation

Choose evaluation metrics based on the engineering use:

- Regression: MAE, RMSE, relative error, R2, calibration, error versus regime, and physically important threshold error.
- Classification: confusion matrix, precision, recall, F1 score, ROC/PR curves, and class-imbalance handling.
- Segmentation/tracking: IoU, mask quality, tracking continuity, ID switches, event-timing error, and manually inspected failure modes.
- Surrogate modeling: error over the design space, extrapolation behavior, uncertainty, active-learning gain, and comparison with CFD or experiment.

Always include representative visual diagnostics:

- Raw input and model output side by side.
- Error maps or residual plots.
- Predicted versus measured values.
- Time histories with events marked.
- Failure cases and likely causes.

## Physics-Aware Interpretation

After model evaluation, translate ML results back into thermal-fluid understanding.

Ask:

- What physical mechanism is the model likely using?
- Are the learned features consistent with known scaling, regimes, or conservation laws?
- Does performance degrade at transitions, extremes, unseen surfaces, different fluids, or new geometries?
- Can simpler physics-based features achieve similar performance?
- What new measurement, trend, or research hypothesis did the ML tool enable?

Avoid presenting model accuracy as the final scientific contribution. The contribution should be the measurement capability, physical insight, design acceleration, monitoring reliability, or new hypothesis enabled by the model.

## Reporting AI/ML Work

When writing or presenting AI-assisted thermal-fluid work, include:

- Engineering objective and why ML is needed.
- Dataset description, baseline case, labels, preprocessing, and train/test split.
- Model architecture or tool used, with repository link if relevant.
- Training procedure, hyperparameters, and hardware only to the level needed for reproducibility.
- Evaluation metrics, visual diagnostics, uncertainty, and failure cases.
- Generalization tests across meaningful thermal-fluid conditions.
- Physics interpretation and limits of applicability.

For presentations, show the pipeline visually: raw data -> preprocessing -> model -> output metric -> physical interpretation.

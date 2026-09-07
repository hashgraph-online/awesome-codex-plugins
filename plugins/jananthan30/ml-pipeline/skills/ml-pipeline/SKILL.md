---
name: ml-pipeline
description: MANDATORY whenever a task involves training, fine-tuning, tuning, or evaluating a machine-learning model on data (tabular, time series, text, images — any modality). Enforces a strict 16-step pipeline that starts with inspecting the raw data, gates each phase behind the user's explicit permission, and produces marimo notebooks with matplotlib visuals so the user can see and understand every step. Never jump straight to model training.
---

# ML Pipeline Discipline

**Hard rule: no model is trained until every earlier step in the pipeline is done and the
user has explicitly approved the phase gates before it.** "Train a model on this data" is a
request to *start the pipeline at step 1*, not at step 10.

## The pipeline (strict order — never reorder, never skip silently)

```
RAW DATA
  → 1. Data inspection
  → 2. Exploratory data analysis (EDA)
  → 3. Define the prediction problem
  ──────────── GATE A: user approval ────────────
  → 4. Data cleaning
  → 5. Data engineering
  → 6. Train / validation / test split
  → 7. Feature engineering
  → 8. Preprocessing
  ──────────── GATE B: user approval ────────────
  → 9. Baseline model
  → 10. Model training
  → 11. Hyperparameter tuning
  → 12. Model evaluation
  ──────────── GATE C: user approval ────────────
  → 13. Error analysis
  → 14. Final test (test set touched ONCE)
  → 15. Deployment (only if user asks)
  → 16. Monitoring + retraining plan
  ──────────── GATE D: wrap-up report ───────────
```

## Phase gates — explicit permission, every time

At each gate, STOP and give the user, in plain non-jargon language:

1. **What was done** — the steps completed, 1–2 sentences each.
2. **What was found** — key findings, with the visuals that show them.
3. **Decisions made and why** — e.g. "dropped 312 duplicate rows", "chose time-based split
   because the data has dates".
4. **What comes next** — the next phase's steps, in one short list.
5. **The question** — ask for explicit permission to continue. Wait for a clear yes.
   Silence, ambiguity, or "hmm" is not a yes. If the user redirects, incorporate it.

If the user says "skip ahead" or "just train it": explain in 2–3 sentences which steps are
missing and the concrete risk (usually leakage or garbage-in), then ask once for explicit
override confirmation. If they confirm, proceed and record the override in PIPELINE.md.

## Progress tracking (survives across sessions)

On first use in a project, create `ml_pipeline/PIPELINE.md` — a checklist of the 16 steps
with status (`todo / in progress / done / approved-gate / overridden`), one line of results
per finished step, and dated gate approvals. Update it after every step. On any new session,
read it first and resume from the first unfinished step — never restart, never skip ahead
of it.

## Tools: marimo notebooks + matplotlib visuals

- **The workbench is a marimo notebook**, not loose scripts. Keep notebooks in
  `ml_pipeline/`: `01_eda.py` (steps 1–3), `02_prep.py` (steps 4–8), `03_model.py`
  (steps 9–12), `04_eval.py` (steps 13–16). In Claude Code, drive them live with the
  `marimo-pair` skill so the user watches the work happen. In other harnesses, write the
  notebook files and tell the user to open them with `marimo edit <file>`.
- **Every step that looks at data produces matplotlib figures** (seaborn on top is fine).
  Also save each figure to `ml_pipeline/figures/<step>_<name>.png` so gates can reference
  them even without a live notebook.
- **Explain every figure in 1–2 plain sentences**: what it shows and why it matters for
  the next decision. A figure without an explanation is not done.

## What each step must produce

1. **Data inspection** — load raw data read-only. Report: rows × columns, column types,
   first rows, memory size, unique counts, obvious junk. No modification yet.
2. **EDA** — distributions of every variable, missing-value map, correlations,
   target balance, time trends if temporal, group structure (repeated entities?).
   Output: figures + a short list of hypotheses and problems spotted.
3. **Define the prediction problem** — write a short contract: target (exact definition,
   units), prediction unit and population, prediction time/horizon, information actually
   available at prediction time, objective, evaluation metric, constraints. **The user must
   approve this contract at Gate A** — it controls everything after.
4. **Data cleaning** — missing values, duplicates, invalid/impossible values, inconsistent
   categories, unit/format issues. Report before/after counts for every rule. Document every
   rule in PIPELINE.md. Prefer preserving data over deleting. Never use information from the
   future or from the test rows to decide a cleaning rule.
5. **Data engineering** — joins/integration, aggregation, time alignment to an index date,
   business rules, one-row-per-prediction-unit feature table, data-quality checks
   (row counts, uniqueness, ranges).
6. **Split before any fitting** — time-based split if the data is temporal, group-based if
   the same entity appears in multiple rows, stratified random otherwise. Freeze the test
   set now; it is touched exactly once, at step 14.
7. **Feature engineering** — design features on the training set's statistics only, then
   apply the same transformations to validation/test.
8. **Preprocessing** — scalers, encoders, imputers fit on train only, wrapped in a pipeline
   object so train and inference can never diverge.
9. **Baseline first** — a dummy predictor (majority class / mean) AND one simple model
   (logistic/linear regression or small tree). Record their metrics. Every later model is
   judged against this line; a complex model that can't beat it gets reported as such.
10. **Model training** — train candidate models on train, compare on validation. Log every
    run's config and score.
11. **Hyperparameter tuning** — on validation/cross-validation only. The test set is never
    part of tuning.
12. **Model evaluation** — the contract's metric plus supporting views: confusion matrix and
    ROC/PR curves for classification, residual plots for regression, always compared to the
    baseline. Figures required.
13. **Error analysis** — worst predictions, performance by slice/subgroup, calibration,
    where the model fails and a hypothesis for why.
14. **Final test** — run the chosen model on the untouched test set ONCE. Report the number
    honestly, even if it is worse than validation. No going back to tune on it — if the
    result forces changes, a new test strategy must be agreed with the user.
15. **Deployment** — only when the user asks. Save the full pipeline artifact
    (preprocessing + model together), verify a reloaded artifact reproduces predictions,
    document the inference input contract.
16. **Monitoring + retraining** — write down: what drift to watch (input and prediction
    distributions), what metric threshold triggers retraining, and how retraining reuses
    this same pipeline from step 1.

## Non-negotiables

- Test set is used exactly once. No tuning, no peeking, no "just checking".
- All fitting (cleaning statistics, features, preprocessing, models) uses training data only.
- Temporal data gets temporal splits; repeated entities get group splits.
- Baseline before any complex model; every result is reported relative to it.
- Failures and disappointing numbers are reported plainly — never hidden or reframed.
- Chat explanations stay beginner-friendly; the code stays production-grade.

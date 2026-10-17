# Model selection playbook

Read at step 3 (when writing the prediction contract) and again before the Gate B report. Key on
`ml_pipeline/data_profile.json → traits`. Always start with a baseline (a dummy predictor and one
simple model), judged on validation with the contract's metric. "Avoid" means: not without a
written reason in the `Model rationale:` block.

## Tabular, small (`small_data`: fewer than 5,000 rows)
- Baseline: majority-class / mean dummy, then logistic or linear regression with L2.
- Strong default: gradient boosting with shallow trees (depth 2–4, strong regularization, early
  stopping) or the regularized linear model itself.
- Worth trying: random forest (few knobs); GAM / EBM when the model must be read by a person.
- Avoid: neural nets (overfit and hide it — the hook denies this); large hyperparameter searches
  (use repeated k-fold on train and report the spread); anything you cannot explain to the user.

## Tabular, medium (5,000 – 500,000 rows)
- Baseline as above. Strong default: LightGBM / XGBoost / CatBoost with early stopping on validation.
- Worth trying: a linear model with feature crosses; an MLP only if boosting plateaus and rows > 50,000.
- Avoid: k-NN and RBF-SVM above ~50,000 rows (quadratic time); unregularized trees.

## Tabular, large (more than 500,000 rows)
- Strong default: histogram gradient boosting (`HistGradientBoosting*`, LightGBM) with subsampling;
  linear models on hashed or sparse features when the table is very wide.
- Avoid: anything O(n²); exact k-NN; kernel SVMs.

## Imbalanced target (`imbalanced`: minority class under 10%)
- Metric: average precision (PR-AUC) primary; recall at a fixed precision or F1 at a chosen
  threshold; never accuracy for model selection (the hook denies `scoring="accuracy"`).
- First try `class_weight="balanced"` / `scale_pos_weight`; if you resample, `fit_resample` on the
  training split only (the hook denies anything else).
- The majority-class dummy baseline shows exactly what accuracy hides.

## High-cardinality categoricals (`high_card_categoricals`: more than 50 levels)
- Prefer CatBoost, or target / ordinal encoding fit on train inside a pipeline object.
- Avoid one-hot encoding (width explosion, and leakage if fit on all rows).

## Temporal data (`has_datetime`)
- Split: chronological — `guard.split(time_col=...)`; validation is the period after train, test the
  latest period; `TimeSeriesSplit` for CV. Random splits and k-fold are denied by the hook.
- Features: lags and rolling statistics computed only from the past; calendar features.
- Baseline: last value / seasonal naive for forecasting; logistic on lag features for temporal
  classification. Strong default: gradient boosting on lag features; ETS / ARIMA for univariate series.
- Avoid: tree models extrapolating a trend (detrend first); LSTMs before boosting has been tried.

## Repeated entities (`has_groups`: patients, users, devices, sites)
- Split by group — `guard.split(group_col=...)`, `GroupKFold` for CV. Row-level splits are denied.
- Avoid: features that identify the entity; the model memorizes it instead of learning.

## Text
- Baseline: TF-IDF (1–2 grams) + logistic regression or linear SVM.
- Strong default: a fine-tuned small transformer only when the baseline is clearly insufficient and
  there are more than ~5,000 labelled examples. Avoid training embeddings from scratch on small corpora.

## Images
- Baseline: features from a pretrained CNN + logistic regression. Strong default: fine-tune a
  pretrained backbone with augmentation applied after the split.
- Avoid: training from scratch below ~100,000 images; augmenting before splitting; random splits when
  images share a source (patient, device, session → group split).

## Interpretability required
- Logistic / linear with monotone constraints, GAM / EBM, shallow trees; gradient boosting with
  monotone constraints plus SHAP for explanation. Avoid black-box ensembles where a clinician or
  regulator must read the model.

## Wrong applications the hook denies (red flags) and their override names

| red flag | what fires it | do instead |
|---|---|---|
| `neural-net-small-data` | MLP / keras / torch training with fewer than 5,000 rows | regularized linear, gradient boosting |
| `random-split-temporal` | `train_test_split` / `KFold` with a datetime column | `guard.split(time_col=)`, `TimeSeriesSplit` |
| `group-split` | any non-Group split with `group_col` set | `guard.split(group_col=)`, `GroupKFold` |
| `accuracy-imbalanced` | `scoring="accuracy"` with minority under 10% | `average_precision`, `f1`, `balanced_accuracy` |
| `resample-before-split` | `fit_resample` on anything but the train split | split first, then resample train |

Override one with `- Override: red flag <name> - user approved <what> YYYY-MM-DD - reason: <why>` in
`PIPELINE.md`, only after the user explicitly agreed. Advisory smells (warned, not denied): k-NN or
kernel SVM above 50,000 rows; one-hot on high-cardinality columns; `accuracy_score` reported on an
imbalanced target.

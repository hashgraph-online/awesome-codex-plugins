---
name: scikit-learn
description: 'Covers classical machine learning in Python with scikit-learn (sklearn): classification and regression estimators, clustering and dimensionality reduction, preprocessing, Pipeline and ColumnTransformer, cross-validation, metrics, and GridSearchCV hyperparameter tuning. Use when training or comparing classifiers and regressors on tabular or text data, clustering data and choosing the cluster count, building leakage-free preprocessing pipelines, evaluating models with cross-validation and metrics, or tuning hyperparameters. Not for deep learning; use a dedicated neural network framework instead.'
license: BSD-3-Clause license
compatibility: Requires Python 3.11+ and scikit-learn 1.7+. NumPy and SciPy are required dependencies. Optional matplotlib/seaborn for bundled example scripts that save plots.
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.3'
  category: data-science-and-ml
  maintainer: Kalaris Labs
  tags: machine learning, scikit-learn, classification, regression, cross-validation
---

# Scikit-learn

## Overview

This skill provides comprehensive guidance for machine learning tasks using scikit-learn, the industry-standard Python library for classical machine learning. Use this skill for classification, regression, clustering, dimensionality reduction, preprocessing, model evaluation, and building production-ready ML pipelines.

## Installation

Tested against **scikit-learn 1.8.0** (stable; December 2025). Requires **Python 3.11–3.14** (free-threaded CPython 3.14 wheels available in 1.8+).

Install the PyPI package **`scikit-learn`** (not the deprecated `sklearn` package on PyPI). Import in code as `sklearn`.

```bash
# Install scikit-learn using uv
uv pip install "scikit-learn>=1.7"

# Optional: plotting utilities and bundled script dependencies
uv pip install "scikit-learn[plots]" matplotlib seaborn

# Commonly used with
uv pip install pandas numpy
```

Check your version:

```python
import sklearn
print(sklearn.__version__)
```

## When to Use This Skill

Use the scikit-learn skill when:

- Building classification or regression models
- Performing clustering or dimensionality reduction
- Preprocessing and transforming data for machine learning
- Evaluating model performance with cross-validation
- Tuning hyperparameters with grid or random search
- Creating ML pipelines for production workflows
- Comparing different algorithms for a task
- Working with both structured (tabular) and text data
- Need interpretable, classical machine learning approaches

## Quick Start

### Classification Example

```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# Preprocess
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)

# Evaluate
y_pred = model.predict(X_test_scaled)
print(classification_report(y_test, y_pred))
```

### Complete Pipeline with Mixed Data

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import GradientBoostingClassifier

# Define feature types
numeric_features = ['age', 'income']
categorical_features = ['gender', 'occupation']

# Create preprocessing pipelines
numeric_transformer = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

# Combine transformers
preprocessor = ColumnTransformer([
    ('num', numeric_transformer, numeric_features),
    ('cat', categorical_transformer, categorical_features)
])

# Full pipeline
model = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', GradientBoostingClassifier(random_state=42))
])

# Fit and predict
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
```

## Core Capabilities

Five capability areas are documented in
[references/core_capabilities.md](references/core_capabilities.md), with per-topic detail
in [references/supervised_learning.md](references/supervised_learning.md),
[references/unsupervised_learning.md](references/unsupervised_learning.md),
[references/model_evaluation.md](references/model_evaluation.md),
[references/preprocessing.md](references/preprocessing.md), and
[references/pipelines_and_composition.md](references/pipelines_and_composition.md):

1. **Supervised learning** — classification and regression estimator families.
2. **Unsupervised learning** — clustering, decomposition, and manifold learning.
3. **Model evaluation and selection** — metrics, cross-validation, and hyperparameter search.
4. **Data preprocessing** — scaling, encoding, imputation, and feature selection.
5. **Pipelines and composition** — `Pipeline` and `ColumnTransformer`.

Always fit preprocessing inside a `Pipeline` so it is refit per cross-validation fold;
scaling or imputing before splitting leaks test information into training.

Two worked workflows are in
[references/common_workflows.md](references/common_workflows.md).

## Example Scripts

### Classification Pipeline

Run a complete classification workflow with preprocessing, model comparison, hyperparameter tuning, and evaluation:

```bash
uv run python scripts/classification_pipeline.py
```

This script demonstrates:
- Handling mixed data types (numeric and categorical)
- Model comparison using cross-validation
- Hyperparameter tuning with GridSearchCV
- Comprehensive evaluation with multiple metrics
- Feature importance analysis

### Clustering Analysis

Perform clustering analysis with algorithm comparison and visualization:

```bash
uv run python scripts/clustering_analysis.py
```

This script demonstrates:
- Finding optimal number of clusters (elbow method, silhouette analysis)
- Comparing multiple clustering algorithms (K-Means, DBSCAN, Agglomerative, Gaussian Mixture)
- Evaluating clustering quality without ground truth
- Visualizing results with PCA projection

## Reference Documentation

This skill includes comprehensive reference files for deep dives into specific topics:

### Quick Reference
**File:** `references/quick_reference.md`
- Common import patterns and installation instructions
- Quick workflow templates for common tasks
- Algorithm selection cheat sheets
- Common patterns and gotchas
- Performance optimization tips

### Supervised Learning
**File:** `references/supervised_learning.md`
- Linear models (regression and classification)
- Support Vector Machines
- Decision Trees and ensemble methods
- K-Nearest Neighbors, Naive Bayes, Neural Networks
- Algorithm selection guide

### Unsupervised Learning
**File:** `references/unsupervised_learning.md`
- All clustering algorithms with parameters and use cases
- Dimensionality reduction techniques
- Outlier and novelty detection
- Gaussian Mixture Models
- Method selection guide

### Model Evaluation
**File:** `references/model_evaluation.md`
- Cross-validation strategies
- Hyperparameter tuning methods
- Classification, regression, and clustering metrics
- Learning and validation curves
- Best practices for model selection

### Preprocessing
**File:** `references/preprocessing.md`
- Feature scaling and normalization
- Encoding categorical variables
- Missing value imputation
- Feature engineering techniques
- Custom transformers

### Pipelines and Composition
**File:** `references/pipelines_and_composition.md`
- Pipeline construction and usage
- ColumnTransformer for mixed data types
- FeatureUnion for parallel transformations
- Complete end-to-end examples
- Best practices

## Best Practices

### Always Use Pipelines
Pipelines prevent data leakage and ensure consistency:
```python
# Good: Preprocessing in pipeline
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('model', LogisticRegression())
])

# Bad: Preprocessing outside (can leak information)
X_scaled = StandardScaler().fit_transform(X)
```

### Fit on Training Data Only
Never fit on test data:
```python
# Good
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)  # Only transform

# Bad
scaler = StandardScaler()
X_all_scaled = scaler.fit_transform(np.vstack([X_train, X_test]))
```

### Use Stratified Splitting for Classification
Preserve class distribution:
```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)
```

### Set Random State for Reproducibility
```python
model = RandomForestClassifier(n_estimators=100, random_state=42)
```

### Choose Appropriate Metrics
- Balanced data: Accuracy, F1-score
- Imbalanced data: Precision, Recall, ROC AUC, Balanced Accuracy
- Cost-sensitive: Define custom scorer

### Scale Features When Required
Algorithms requiring feature scaling:
- SVM, KNN, Neural Networks
- PCA, Linear/Logistic Regression with regularization
- K-Means clustering

Algorithms not requiring scaling:
- Tree-based models (Decision Trees, Random Forest, Gradient Boosting)
- Naive Bayes

## Troubleshooting Common Issues

### ConvergenceWarning
**Issue:** Model didn't converge
**Solution:** Increase `max_iter` or scale features
```python
model = LogisticRegression(max_iter=1000)
```

### Poor Performance on Test Set
**Issue:** Overfitting
**Solution:** Use regularization, cross-validation, or simpler model
```python
# Add regularization
model = Ridge(alpha=1.0)

# Use cross-validation
scores = cross_val_score(model, X, y, cv=5)
```

### Memory Error with Large Datasets
**Solution:** Use algorithms designed for large data
```python
# Use SGD for large datasets
from sklearn.linear_model import SGDClassifier
model = SGDClassifier()

# Or MiniBatchKMeans for clustering
from sklearn.cluster import MiniBatchKMeans
model = MiniBatchKMeans(n_clusters=8, batch_size=100)
```

## Additional Resources

- Official Documentation: https://scikit-learn.org/stable/
- User Guide: https://scikit-learn.org/stable/user_guide.html
- API Reference: https://scikit-learn.org/stable/api/index.html
- Examples Gallery: https://scikit-learn.org/stable/auto_examples/index.html

## Agent operating procedure

1. **Check the environment.** Confirm the Python environment and library versions (`python -c "import pkg; print(pkg.__version__)"`) and inspect the data's shape, types and missing values.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Run on a sample or a single fold first and check runtime and memory.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Use held-out data, fixed random seeds and appropriate metrics; check for leakage; report uncertainty (CIs, std over seeds).
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Out-of-memory or very slow execution | Subsample, use chunked or lazy computation, or reduce model size, and tell the user what changed. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Never report a metric you did not compute in this session; show the code path that produced every number.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `scanpy`: Standard single-cell RNA-seq analysis pipeline.
- `aeon`: This skill should be used for time series machine learning tasks including classification, regression, clustering, forecasting, anomaly det…
- `weights-and-biases`: Logs and tracks machine learning experiments with Weights & Biases (W&B, wandb): metrics, hyperparameters, checkpoints, sweeps, artifacts w…

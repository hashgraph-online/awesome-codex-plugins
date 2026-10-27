# DeepChem Core Capabilities

Molecular data loading and processing, featurization, data splitting, model selection and
training, MoleculeNet benchmarks, transfer learning, evaluation, and prediction.

## Core Capabilities

### 1. Molecular Data Loading and Processing

DeepChem provides specialized loaders for various chemical data formats:

```python
import deepchem as dc

# Load CSV with SMILES
featurizer = dc.feat.CircularFingerprint(radius=2, size=2048)
loader = dc.data.CSVLoader(
    tasks=['solubility', 'toxicity'],
    feature_field='smiles',
    featurizer=featurizer
)
dataset = loader.create_dataset('molecules.csv')

# Load SDF files
loader = dc.data.SDFLoader(tasks=['activity'], featurizer=featurizer)
dataset = loader.create_dataset('compounds.sdf')

# Load protein sequences
loader = dc.data.FASTALoader()
dataset = loader.create_dataset('proteins.fasta')
```

**Key Loaders**:
- `CSVLoader`: Tabular data with molecular identifiers
- `SDFLoader`: Molecular structure files
- `FASTALoader`: Protein/DNA sequences
- `ImageLoader`: Molecular images
- `JsonLoader`: JSON-formatted datasets

### 2. Molecular Featurization

Convert molecules into numerical representations for ML models.

#### Decision Tree for Featurizer Selection

```
Is the model a graph neural network?
├─ YES → Use graph featurizers
│   ├─ Standard GNN → MolGraphConvFeaturizer
│   ├─ Message passing → DMPNNFeaturizer
│   └─ Pretrained → GroverFeaturizer
│
└─ NO → What type of model?
    ├─ Traditional ML (RF, XGBoost, SVM)
    │   ├─ Fast baseline → CircularFingerprint (ECFP)
    │   ├─ Interpretable → RDKitDescriptors
    │   └─ Maximum coverage → MordredDescriptors
    │
    ├─ Deep learning (non-graph)
    │   ├─ Dense networks → CircularFingerprint
    │   └─ CNN → SmilesToImage
    │
    ├─ Sequence models (LSTM, Transformer)
    │   └─ SmilesToSeq
    │
    └─ 3D structure analysis
        └─ CoulombMatrix
```

#### Example Featurization

```python
# Fingerprints (for traditional ML)
fp = dc.feat.CircularFingerprint(radius=2, size=2048)

# Descriptors (for interpretable models)
desc = dc.feat.RDKitDescriptors()

# Graph features (for GNNs)
graph_feat = dc.feat.MolGraphConvFeaturizer()

# Apply featurization
features = fp.featurize(['CCO', 'c1ccccc1'])
```

**Selection Guide**:
- **Small datasets (<1K)**: CircularFingerprint or RDKitDescriptors
- **Medium datasets (1K-100K)**: CircularFingerprint or graph featurizers
- **Large datasets (>100K)**: Graph featurizers (MolGraphConvFeaturizer, DMPNNFeaturizer)
- **Transfer learning**: Pretrained model featurizers (GroverFeaturizer)

See `references/api_reference.md` for complete featurizer documentation.

### 3. Data Splitting

**Critical**: For drug discovery tasks, use `ScaffoldSplitter` to prevent data leakage from similar molecular structures appearing in both training and test sets.

```python
# Scaffold splitting (recommended for molecules)
splitter = dc.splits.ScaffoldSplitter()
train, valid, test = splitter.train_valid_test_split(
    dataset,
    frac_train=0.8,
    frac_valid=0.1,
    frac_test=0.1
)

# Random splitting (for non-molecular data)
splitter = dc.splits.RandomSplitter()
train, test = splitter.train_test_split(dataset)

# Stratified splitting (for imbalanced classification)
splitter = dc.splits.RandomStratifiedSplitter()
train, test = splitter.train_test_split(dataset)
```

**Available Splitters**:
- `ScaffoldSplitter`: Split by molecular scaffolds (prevents leakage)
- `ButinaSplitter`: Clustering-based molecular splitting
- `MaxMinSplitter`: Maximize diversity between sets
- `RandomSplitter`: Random splitting
- `RandomStratifiedSplitter`: Preserves class distributions

### 4. Model Selection and Training

#### Quick Model Selection Guide

| Dataset Size | Task | Recommended Model | Featurizer |
|-------------|------|-------------------|------------|
| < 1K samples | Any | SklearnModel (RandomForest) | CircularFingerprint |
| 1K-100K | Classification/Regression | GBDTModel or MultitaskRegressor | CircularFingerprint |
| > 100K | Molecular properties | GCNModel, AttentiveFPModel, DMPNNModel | MolGraphConvFeaturizer |
| Any (small preferred) | Transfer learning | ChemBERTa, GROVER, MolFormer | Model-specific |
| Crystal structures | Materials properties | CGCNNModel, MEGNetModel | Structure-based |
| Protein sequences | Protein properties | ProtBERT | Sequence-based |

#### Example: Traditional ML
```python
from sklearn.ensemble import RandomForestRegressor

# Wrap scikit-learn model
sklearn_model = RandomForestRegressor(n_estimators=100)
model = dc.models.SklearnModel(model=sklearn_model)
model.fit(train)
```

#### Example: Deep Learning
```python
# Multitask regressor (for fingerprints)
model = dc.models.MultitaskRegressor(
    n_tasks=2,
    n_features=2048,
    layer_sizes=[1000, 500],
    dropouts=0.25,
    learning_rate=0.001
)
model.fit(train, nb_epoch=50)
```

#### Example: Graph Neural Networks
```python
# Graph Convolutional Network
model = dc.models.GCNModel(
    n_tasks=1,
    mode='regression',
    batch_size=128,
    learning_rate=0.001
)
model.fit(train, nb_epoch=50)

# Graph Attention Network
model = dc.models.GATModel(n_tasks=1, mode='classification')
model.fit(train, nb_epoch=50)

# Attentive Fingerprint
model = dc.models.AttentiveFPModel(n_tasks=1, mode='regression')
model.fit(train, nb_epoch=50)
```

### 5. MoleculeNet Benchmarks

Quick access to 30+ curated benchmark datasets with standardized train/valid/test splits:

```python
# Load benchmark dataset
tasks, datasets, transformers = dc.molnet.load_tox21(
    featurizer='GraphConv',  # or 'ECFP', 'Weave', 'Raw'
    splitter='scaffold',     # or 'random', 'stratified'
    reload=False
)
train, valid, test = datasets

# Train and evaluate
model = dc.models.GCNModel(n_tasks=len(tasks), mode='classification')
model.fit(train, nb_epoch=50)

metric = dc.metrics.Metric(dc.metrics.roc_auc_score)
test_score = model.evaluate(test, [metric])
```

**Common Datasets**:
- **Classification**: `load_tox21()`, `load_bbbp()`, `load_hiv()`, `load_clintox()`
- **Regression**: `load_delaney()`, `load_freesolv()`, `load_lipo()`
- **Quantum properties**: `load_qm7()`, `load_qm8()`, `load_qm9()`
- **Materials**: `load_perovskite()`, `load_bandgap()`, `load_mp_formation_energy()`

See `references/api_reference.md` for complete dataset list.

### 6. Transfer Learning

Leverage pretrained models for improved performance, especially on small datasets:

```python
# ChemBERTa (BERT pretrained on 77M molecules)
model = dc.models.HuggingFaceModel(
    model='seyonec/ChemBERTa-zinc-base-v1',
    task='classification',
    n_tasks=1,
    learning_rate=2e-5  # Lower LR for fine-tuning
)
model.fit(train, nb_epoch=10)

# GROVER (graph transformer pretrained on 10M molecules)
model = dc.models.GroverModel(
    task='regression',
    n_tasks=1
)
model.fit(train, nb_epoch=20)
```

**When to use transfer learning**:
- Small datasets (< 1000 samples)
- Novel molecular scaffolds
- Limited computational resources
- Need for rapid prototyping

Use the `scripts/transfer_learning.py` script for guided transfer learning workflows.

### 7. Model Evaluation

```python
# Define metrics
classification_metrics = [
    dc.metrics.Metric(dc.metrics.roc_auc_score, name='ROC-AUC'),
    dc.metrics.Metric(dc.metrics.accuracy_score, name='Accuracy'),
    dc.metrics.Metric(dc.metrics.f1_score, name='F1')
]

regression_metrics = [
    dc.metrics.Metric(dc.metrics.r2_score, name='R²'),
    dc.metrics.Metric(dc.metrics.mean_absolute_error, name='MAE'),
    dc.metrics.Metric(dc.metrics.root_mean_squared_error, name='RMSE')
]

# Evaluate
train_scores = model.evaluate(train, classification_metrics)
test_scores = model.evaluate(test, classification_metrics)
```

### 8. Making Predictions

```python
# Predict on test set
predictions = model.predict(test)

# Predict on new molecules
new_smiles = ['CCO', 'c1ccccc1', 'CC(C)O']
new_features = featurizer.featurize(new_smiles)
new_dataset = dc.data.NumpyDataset(X=new_features)

# Untransform the output, not the input. A NormalizationTransformer built with
# transform_y=True touches y, and a prediction dataset has no y -- transforming
# it does nothing, and the predictions come back in z-scored space. Passing the
# transformers to predict() untransforms them into the target's real units.
predictions = model.predict(new_dataset, transformers=transformers)
```

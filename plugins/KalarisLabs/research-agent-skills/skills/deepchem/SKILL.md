---
name: deepchem
description: Molecular ML with diverse featurizers and pre-built datasets. Use for property prediction (ADMET, toxicity) with traditional ML or GNNs when you want extensive featurization options and MoleculeNet benchmarks. Best for quick experiments with pre-trained models, diverse molecular representations. For graph-first PyTorch workflows use torchdrug; for benchmark datasets use pytdc.
license: MIT
compatibility: Requires Python 3.7–3.11 (PyPI 2.8.0 caps at <3.12). Install PyTorch, TensorFlow, or JAX before the matching deepchem extra. RDKit is a core dependency.
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.5'
  category: chemistry-and-drug-discovery
  maintainer: Kalaris Labs
  tags: molecular machine learning, ADMET, property prediction, drug discovery, cheminformatics
---

# DeepChem

## Overview

DeepChem is a comprehensive Python library for applying machine learning to chemistry, materials science, and biology. Enable molecular property prediction, drug discovery, materials design, and biomolecule analysis through specialized neural networks, molecular featurization methods, and pretrained models.

**Version note:** Examples target **deepchem 2.8.0** (PyPI stable, Apr 2024). Requires **Python 3.7–3.11** (`<3.12` on PyPI). Core utilities (loaders, featurizers, MoleculeNet) work without a DL backend; GNN and transformer models need the matching extra (`torch`, `tensorflow`, or `jax`). Install the backend framework first when using GPU builds.

## When to Use This Skill

This skill should be used when:
- Loading and processing molecular data (SMILES strings, SDF files, protein sequences)
- Predicting molecular properties (solubility, toxicity, binding affinity, ADMET properties)
- Training models on chemical/biological datasets
- Using MoleculeNet benchmark datasets (Tox21, BBBP, Delaney, etc.)
- Converting molecules to ML-ready features (fingerprints, graph representations, descriptors)
- Implementing graph neural networks for molecules (GCN, GAT, MPNN, AttentiveFP)
- Applying transfer learning with pretrained models (ChemBERTa, GROVER, MolFormer)
- Predicting crystal/materials properties (bandgap, formation energy)
- Analyzing protein or DNA sequences

## Core Capabilities

Eight capability areas, each with worked code, are in
[references/core_capabilities.md](references/core_capabilities.md):

1. **Molecular data loading and processing** — loaders, `NumpyDataset` / `DiskDataset`.
2. **Molecular featurization** — circular fingerprints, graph convolution, and descriptors.
3. **Data splitting** — random, scaffold, stratified, and butina splitters, and why
   scaffold splitting is the honest default for molecules.
4. **Model selection and training** — the model families and how to fit them.
5. **MoleculeNet benchmarks** — loading standard datasets and their published splits.
6. **Transfer learning** — pretraining and fine-tuning.
7. **Model evaluation** — metrics appropriate to regression and classification tasks.
8. **Making predictions** — applying a trained model to new molecules.

Three end-to-end workflows are in
[references/typical_workflows.md](references/typical_workflows.md).

## Example Scripts

This skill includes three production-ready scripts in the `scripts/` directory:

### 1. `predict_solubility.py`
Train and evaluate solubility prediction models. Works with Delaney benchmark or custom CSV data.

```bash
# Use Delaney benchmark
python scripts/predict_solubility.py

# Use custom data
python scripts/predict_solubility.py \
    --data my_data.csv \
    --smiles-col smiles \
    --target-col solubility \
    --predict "CCO" "c1ccccc1"
```

### 2. `graph_neural_network.py`
Train various graph neural network architectures on molecular data.

```bash
# Train GCN on Tox21
python scripts/graph_neural_network.py --model gcn --dataset tox21

# Train AttentiveFP on custom data
python scripts/graph_neural_network.py \
    --model attentivefp \
    --data molecules.csv \
    --task-type regression \
    --targets activity \
    --epochs 100
```

### 3. `transfer_learning.py`
Fine-tune pretrained models (ChemBERTa, GROVER, MolFormer) on molecular property prediction tasks.

```bash
# Fine-tune ChemBERTa on BBBP
python scripts/transfer_learning.py --model chemberta --dataset bbbp

# Fine-tune GROVER on custom data
python scripts/transfer_learning.py \
    --model grover \
    --data small_dataset.csv \
    --target activity \
    --task-type classification \
    --epochs 20
```

## Common Patterns and Best Practices

### Pattern 1: Always Use Scaffold Splitting for Molecules
```python
# GOOD: Prevents data leakage
splitter = dc.splits.ScaffoldSplitter()
train, test = splitter.train_test_split(dataset)

# BAD: Similar molecules in train and test
splitter = dc.splits.RandomSplitter()
train, test = splitter.train_test_split(dataset)
```

### Pattern 2: Normalize Features and Targets
```python
transformers = [
    dc.trans.NormalizationTransformer(
        transform_y=True,  # Also normalize target values
        dataset=train
    )
]
for transformer in transformers:
    train = transformer.transform(train)
    test = transformer.transform(test)
```

### Pattern 3: Start Simple, Then Scale
1. Start with Random Forest + CircularFingerprint (fast baseline)
2. Try XGBoost/LightGBM if RF works well
3. Move to deep learning (MultitaskRegressor) if you have >5K samples
4. Try GNNs if you have >10K samples
5. Use transfer learning for small datasets or novel scaffolds

### Pattern 4: Handle Imbalanced Data
```python
# Option 1: Balancing transformer
transformer = dc.trans.BalancingTransformer(dataset=train)
train = transformer.transform(train)

# Option 2: Use balanced metrics
metric = dc.metrics.Metric(dc.metrics.balanced_accuracy_score)
```

### Pattern 5: Avoid Memory Issues
```python
# Use DiskDataset for large datasets
dataset = dc.data.DiskDataset.from_numpy(X, y, w, ids)

# Use smaller batch sizes
model = dc.models.GCNModel(batch_size=32)  # Instead of 128
```

## Common Pitfalls

### Issue 1: Data Leakage in Drug Discovery
**Problem**: Using random splitting allows similar molecules in train/test sets.
**Solution**: Always use `ScaffoldSplitter` for molecular datasets.

### Issue 2: GNN Underperforming vs Fingerprints
**Problem**: Graph neural networks perform worse than simple fingerprints.
**Solutions**:
- Ensure dataset is large enough (>10K samples typically)
- Increase training epochs (50-100)
- Try different architectures (AttentiveFP, DMPNN instead of GCN)
- Use pretrained models (GROVER)

### Issue 3: Overfitting on Small Datasets
**Problem**: Model memorizes training data.
**Solutions**:
- Use stronger regularization (increase dropout to 0.5)
- Use simpler models (Random Forest instead of deep learning)
- Apply transfer learning (ChemBERTa, GROVER)
- Collect more data

### Issue 4: Import Errors
**Problem**: `No module named 'torch'` / `No module named 'tensorflow'` warnings, or model classes fail to import.
**Solution**: DeepChem loads lazily — install the backend that matches your model, then add the matching extra:
```bash
uv pip install deepchem              # loaders, featurizers, MoleculeNet only
uv pip install 'deepchem[torch]'       # GCN, GAT, AttentiveFP, HuggingFaceModel, GroverModel
uv pip install 'deepchem[tensorflow]'  # legacy Keras models
uv pip install 'deepchem[jax]'         # Haiku/JAX models
```
Install PyTorch or TensorFlow with the correct CUDA build **before** the extra when using GPUs. Quote extras in zsh: `'deepchem[torch]'`.

**Conda + PyTorch users:** If `import deepchem` fails with `undefined symbol: iJIT_NotifyEvent`, pin MKL below 2025 (`conda install "mkl<2025"`) — PyTorch wheels may be incompatible with MKL 2025.0.0.

## Reference Documentation

This skill includes comprehensive reference documentation:

### `references/api_reference.md`
Complete API documentation including:
- All data loaders and their use cases
- Dataset classes and when to use each
- Complete featurizer catalog with selection guide
- Model catalog organized by category (50+ models)
- MoleculeNet dataset descriptions
- Metrics and evaluation functions
- Common code patterns

**When to reference**: Search this file when you need specific API details, parameter names, or want to explore available options.

### `references/workflows.md`
Eight detailed end-to-end workflows:
1. Molecular property prediction from SMILES
2. Using MoleculeNet benchmarks
3. Hyperparameter optimization
4. Transfer learning with pretrained models
5. Molecular generation with GANs
6. Materials property prediction
7. Protein sequence analysis
8. Custom model integration

**When to reference**: Use these workflows as templates for implementing complete solutions.

## Installation

Core package (data loaders, featurizers, MoleculeNet, scikit-learn wrappers):

```bash
uv pip install deepchem
```

Add the extra that matches your model backend (install PyTorch/TensorFlow/JAX first for GPU builds):

```bash
uv pip install 'deepchem[torch]'       # GNNs, TorchModel, HuggingFaceModel, GroverModel
uv pip install 'deepchem[tensorflow]'  # Keras/TensorFlow models
uv pip install 'deepchem[jax]'         # JAX/Haiku models
uv pip install 'deepchem[dqc]'         # Differentiable quantum chemistry (torch + xitorch)
```

Nightly builds: `uv pip install --pre deepchem` (same extras apply with `--pre`).

See [installation guide](https://deepchem.readthedocs.io/en/latest/get_started/installation.html) and [soft requirements](https://deepchem.readthedocs.io/en/latest/requirements.html) for optional dependencies per model class.

## Additional Resources

- Official documentation: https://deepchem.readthedocs.io/
- GitHub repository: https://github.com/deepchem/deepchem
- Tutorials: https://deepchem.readthedocs.io/en/latest/get_started/tutorials.html
- Paper: "MoleculeNet: A Benchmark for Molecular Machine Learning"

## Agent operating procedure

1. **Check the environment.** Confirm toolkit versions and input formats (SMILES, SDF, PDB, CIF), and sanitize molecules before computing.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Process a few molecules or one target first and inspect the outputs.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Check for invalid structures, unit consistency, and applicability domain of predictive models.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Molecules fail to parse or sanitize | Report and skip them with reasons; never silently drop or alter structures. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Computational predictions are hypotheses, not experimental results; label them as such.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `torchdrug`: Build and troubleshoot TorchDrug 0.2.1 workflows for molecular graphs, property prediction, self-supervised pretraining, molecule generatio…
- `pytdc`: Uses the PyTDC package (import tdc, Therapeutics Data Commons) to discover therapeutic ML tasks from tdc.metadata, plan and load approved d…
- `molfeat`: Converts SMILES strings or RDKit/datamol molecules into numerical features using molfeat (0.11.0), which provides calculators, scikit-learn…

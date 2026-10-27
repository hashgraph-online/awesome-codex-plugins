# Protein Modeling

TorchDrug 0.2.1 documents protein data structures, datasets, sequence encoders,
and geometry-aware graph models in its
[data](https://torchdrug.ai/docs/api/data.html),
[dataset](https://torchdrug.ai/docs/api/datasets.html), and
[model](https://torchdrug.ai/docs/api/models.html) APIs. The primary tutorial
index focuses on molecular and knowledge-graph workflows, so avoid inventing a
protein tutorial API that upstream does not provide.

## Build protein objects

### From sequence

```python
from torchdrug import data

protein = data.Protein.from_sequence(
    "MKTAYIAKQRQISFVKSHFSRQ",
    atom_feature=None,
    bond_feature=None,
    residue_feature="default",
)
print(protein.to_sequence())
```

For sequence-only work, setting atom and bond features to `None` avoids the cost
of constructing a full atom-level representation.

### From PDB

```python
protein = data.Protein.from_pdb(
    "protein.pdb",
    atom_feature="default",
    bond_feature="default",
    residue_feature="default",
)
```

Use trusted local PDB files and validate chain selection, missing residues,
alternate locations, and nonstandard residues before training.

Documented conversion methods include:

- `Protein.from_sequence`
- `Protein.from_pdb`
- `Protein.from_molecule`
- `Protein.to_sequence`
- `Protein.to_pdb`
- `Protein.to_molecule`

Packed equivalents operate on lists:

- `PackedProtein.from_sequence(sequences)`
- `PackedProtein.from_pdb(pdb_files)`
- `PackedProtein.from_molecule(mols)`

## Protein datasets

Documented dataset families include:

- Property / sequence: `BetaLactamase`, `BinaryLocalization`,
  `SubcellularLocalization`
- Function / structure: `EnzymeCommission`, `GeneOntology`, `AlphaFoldDB`
- Structure labels: `Fold`, `SecondaryStructure`
- Protein-protein: `HumanPPI`, `YeastPPI`, `PPIAffinity`
- Protein-ligand: `BindingDB`, `PDBBind`

Example:

```python
from torchdrug import datasets

dataset = datasets.EnzymeCommission(
    "~/protein-datasets/",
    atom_feature=None,
    bond_feature=None,
    residue_feature="default",
)
train_set, valid_set, test_set = dataset.split()
```

Class signatures differ. Options such as `branch`, `test_cutoff`, `lazy`, or
species/split IDs are dataset-specific; check the API before using them.

## Sequence encoders

### ESM

`models.ESM` is the alias for `EvolutionaryScaleModeling`. The constructor takes
a directory for downloaded weights, not a checkpoint filename:

```python
from torchdrug import models

model = models.ESM(
    path="~/model-weights/esm/",
    model="ESM-2-150M",
    readout="mean",
)
```

TorchDrug 0.2.1 supports these ESM-2 names:

- `ESM-2-8M`
- `ESM-2-35M`
- `ESM-2-150M`
- `ESM-2-650M`
- `ESM-2-3B`
- `ESM-2-15B`

It also supports `ESM-1b` and `ESM-1v`. Maximum sequence input is 1022 residues
before special tokens. Large checkpoints require substantial memory; start with
`ESM-2-8M` or `ESM-2-35M` for pipeline validation.

### Other sequence models

Documented classes include:

- `models.ProteinCNN`
- `models.ProteinResNet`
- `models.ProteinLSTM`
- `models.ProteinBERT`

These models require explicit input/hidden dimensions. Derive input dimensions
from the dataset's residue feature configuration.

## Structure encoders

Documented structure-aware models include:

- `models.GearNet`
- `models.SchNet`
- general graph models such as `GCN`, `GAT`, `GIN`, and `RGCN`

`SchNet` requires `node_position`. `GearNet` requires a graph whose relation and
geometric feature configuration matches its constructor.

Use TorchDrug graph-construction and geometry layers to create sequential,
radius, and nearest-neighbor relations. Do not use a nonexistent
`protein.residue_graph(...)` method.

Before training a structure model, inspect:

```python
print(protein.num_node)
print(protein.num_residue)
print(protein.node_position.shape)
print(protein.residue_feature.shape)
```

Confirm whether nodes represent atoms or residues and ensure the model input
matches that choice.

## Property-prediction task

Protein-level classification or regression can use the same task abstraction as
molecules:

```python
from torchdrug import tasks

task = tasks.PropertyPrediction(
    model,
    task=dataset.tasks,
    criterion="bce",
    metric=("auprc", "auroc"),
)
```

Choose criterion and metrics from the actual dataset target:

- binary or multi-label classification: BCE, AUPRC/AUROC
- multiclass classification: CE and the documented compatible metrics
- regression: MSE, MAE/RMSE

For large multi-label ontology tasks, inspect
`tasks.MultipleBinaryClassification` rather than treating labels as one
multiclass target.

## Workflow checks

1. Decide sequence-only versus structure-aware modeling.
2. Configure protein features to match that representation.
3. Verify dataset splits and sequence identity cutoffs.
4. Check maximum sequence length before selecting ESM.
5. Build graph relations explicitly for structure models.
6. Derive dimensions from the loaded dataset.
7. Smoke-test one batch before long training.
8. Record checkpoint name, feature settings, split, and TorchDrug version.

## Common failures

### ESM constructor error

Use `models.ESM(path=<directory>, model=<supported-name>)`. Do not pass a
downloaded `.pt` filename as `path`.

### Out-of-memory error

Choose a smaller ESM model, reduce batch size, crop or filter long sequences, or
freeze the encoder and precompute embeddings.

### Missing coordinates

Sequence-created proteins do not acquire experimental 3D coordinates. Load a PDB
or another validated structure source before using coordinate-dependent models.

### Relation mismatch

Build the same relation types expected by the structure model and set
`num_relation` accordingly.

## Source links

- [Protein data API](https://torchdrug.ai/docs/api/data.html#protein)
- [Protein datasets](https://torchdrug.ai/docs/api/datasets.html#protein-property-prediction-datasets)
- [Protein sequence encoders](https://torchdrug.ai/docs/api/models.html#protein-sequence-encoders)
- [Graph neural networks](https://torchdrug.ai/docs/api/models.html#graph-neural-networks)
- [TorchDrug 0.2.1 release notes](https://github.com/DeepGraphLearning/torchdrug/releases/tag/v0.2.1)

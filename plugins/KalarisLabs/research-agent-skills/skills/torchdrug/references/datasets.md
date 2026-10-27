# Datasets

Use the
[TorchDrug 0.2.1 dataset reference](https://torchdrug.ai/docs/api/datasets.html)
as the class inventory and signature source. Dataset constructors download and
cache data under the path supplied by the caller.

## Dataset families

### Molecule property prediction

Documented classes include:

- Classification: `BACE`, `BBBP`, `ClinTox`, `HIV`, `MUV`, `SIDER`, `Tox21`,
  `ToxCast`
- Regression / quantum properties: `FreeSolv`, `Lipophilicity`, `QM8`, `QM9`,
  `PCQM4M`
- Pretraining / generation: `ChEMBLFiltered`, `ZINC250k`, `ZINC2m`, `MOSES`

The official property tutorial uses `ClinTox`; the pretraining tutorial uses
`ClinTox` for a small demonstration and recommends larger data such as `ZINC2m`
for real pretraining; the generation tutorial uses `ZINC250k`.

```python
from torchdrug import datasets

dataset = datasets.ClinTox(
    "~/molecule-datasets/",
    atom_feature="default",
    bond_feature="default",
)
print(dataset.tasks)
print(dataset.node_feature_dim)
print(dataset.edge_feature_dim)
```

Common molecule options include `atom_feature`, `bond_feature`, `mol_feature`,
`with_hydrogen`, and `kekulize`. Availability varies by class; inspect the class
signature before adding options.

### Protein properties and structure

Documented families include:

- Sequence / property: `BetaLactamase`, `BinaryLocalization`,
  `SubcellularLocalization`
- Structure / function: `EnzymeCommission`, `GeneOntology`, `AlphaFoldDB`
- Structure labels: `Fold`, `SecondaryStructure`
- Protein-protein: `HumanPPI`, `YeastPPI`, `PPIAffinity`
- Protein-ligand: `BindingDB`, `PDBBind`

```python
dataset = datasets.EnzymeCommission(
    "~/protein-datasets/",
    atom_feature=None,
    bond_feature=None,
    residue_feature="default",
)
train_set, valid_set, test_set = dataset.split()
```

Protein datasets can be expensive to parse. Where supported, `lazy=True` trades
lower startup memory for slower item loading. For sequence-only models, omitting
atom and bond features avoids unnecessary atom-level construction.

### Knowledge graphs

Documented classes:

- `FB15k`
- `FB15k237`
- `WN18`
- `WN18RR`
- `Hetionet`

```python
dataset = datasets.FB15k237("~/kg-datasets/")
train_set, valid_set, test_set = dataset.split()

print(dataset.num_entity)
print(dataset.num_relation)
```

These datasets provide predefined benchmark splits. Preserve those splits for
comparable evaluation.

### Retrosynthesis

`USPTO50k` contains 50,017 reactions across 10 reaction classes. The official
G2Gs workflow loads two views:

```python
reaction_dataset = datasets.USPTO50k(
    "~/molecule-datasets/",
    atom_feature="center_identification",
    kekulize=True,
)
synthon_dataset = datasets.USPTO50k(
    "~/molecule-datasets/",
    as_synthon=True,
    atom_feature="synthon_completion",
    kekulize=True,
)
```

Reaction mode yields reactant/product pairs for center identification. Synthon
mode yields reactant/synthon pairs for synthon completion.

## Splitting correctly

Some benchmark datasets expose predefined splits:

```python
train_set, valid_set, test_set = dataset.split()
```

For the property-prediction tutorial's random 80/10/10 split, use PyTorch:

```python
import torch

lengths = [int(0.8 * len(dataset)), int(0.1 * len(dataset))]
lengths.append(len(dataset) - sum(lengths))
train_set, valid_set, test_set = torch.utils.data.random_split(dataset, lengths)
```

Do not assume `dataset.split([0.8, 0.1, 0.1])` is a documented universal API.

For paired retrosynthesis views, reset the same seed before each `split()`:

```python
torch.manual_seed(1)
reaction_train, reaction_valid, reaction_test = reaction_dataset.split()
torch.manual_seed(1)
synthon_train, synthon_valid, synthon_test = synthon_dataset.split()
```

This preserves sample alignment.

## Feature configuration

Dataset dimensions depend on feature choices. Construct models from the loaded
dataset rather than hard-coding dimensions:

```python
model = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[256, 256, 256],
    edge_input_dim=dataset.edge_feature_dim,
)
```

Generation and retrosynthesis often require specialized feature sets:

- Pretraining: `atom_feature="pretrain"`, `bond_feature="pretrain"`
- GCPN / GraphAF: `atom_feature="symbol"`, `kekulize=True`
- Center identification: `atom_feature="center_identification"`
- Synthon completion: `atom_feature="synthon_completion"`

Do not mix checkpoint weights across incompatible feature configurations.

## Data integrity and evaluation

- Cache datasets in a controlled project or user data directory.
- Record TorchDrug version, feature arguments, split method, and random seed.
- Preserve predefined KG splits.
- For molecular benchmarks, use the split protocol required by the benchmark;
  do not claim a random split is a scaffold split.
- Inspect downloaded data licenses and provenance before redistribution.
- Validate labels, missing-value masks, and task names before training.

## Source links

- [Dataset API](https://torchdrug.ai/docs/api/datasets.html)
- [Property prediction tutorial](https://torchdrug.ai/docs/tutorials/property_prediction.html)
- [Pretraining tutorial](https://torchdrug.ai/docs/tutorials/pretrain.html)
- [Generation tutorial](https://torchdrug.ai/docs/tutorials/generation.html)
- [Retrosynthesis tutorial](https://torchdrug.ai/docs/tutorials/retrosynthesis.html)
- [Knowledge graph tutorial](https://torchdrug.ai/docs/tutorials/reasoning.html)

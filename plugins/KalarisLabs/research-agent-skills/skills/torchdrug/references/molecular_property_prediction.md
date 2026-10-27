# Molecular Property Prediction and Pretraining

Follow the official
[property prediction](https://torchdrug.ai/docs/tutorials/property_prediction.html)
and
[pretrained molecular representations](https://torchdrug.ai/docs/tutorials/pretrain.html)
tutorials for TorchDrug 0.2.1.

## Supervised property prediction

### 1. Load and split data

The official tutorial uses a random 80/10/10 ClinTox split:

```python
import torch
from torchdrug import datasets

dataset = datasets.ClinTox("~/molecule-datasets/")
lengths = [int(0.8 * len(dataset)), int(0.1 * len(dataset))]
lengths.append(len(dataset) - sum(lengths))
train_set, valid_set, test_set = torch.utils.data.random_split(dataset, lengths)
```

This is a random split, not a scaffold split. If a benchmark requires a scaffold
split, implement or import that protocol explicitly and record it in the
experiment configuration.

### 2. Define the representation model

```python
from torchdrug import models

model = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[256, 256, 256, 256],
    short_cut=True,
    batch_norm=True,
    concat_hidden=True,
)
```

### 3. Define the task

```python
from torchdrug import tasks

task = tasks.PropertyPrediction(
    model,
    task=dataset.tasks,
    criterion="bce",
    metric=("auprc", "auroc"),
)
```

`task` means the target field name(s) or a mapping of target names to weights. It
does not mean `"node"`, `"edge"`, or `"graph"`.

Documented `PropertyPrediction` criteria are:

- `"mse"`
- `"bce"`
- `"ce"`

Documented metrics are:

- `"mae"`
- `"rmse"`
- `"auprc"`
- `"auroc"`

Other useful constructor options include `num_mlp_layer`, `normalization`,
`num_class`, `mlp_batch_norm`, `mlp_dropout`, and
`graph_construction_model`.

For large multi-label problems, inspect `tasks.MultipleBinaryClassification`,
which has its own task IDs, metrics, and reweighting behavior.

### 4. Train with Engine

```python
from torchdrug import core

optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(
    task,
    train_set,
    valid_set,
    test_set,
    optimizer,
    batch_size=1024,
)
solver.train(num_epoch=100)
solver.evaluate("valid")
```

Add `gpus=[0]` only for supported CUDA execution. Start with one epoch and a
smaller batch for a smoke test.

## Manual prediction

Use TorchDrug collation:

```python
from torch.nn import functional as F
from torchdrug import data

batch = data.graph_collate(valid_set[:8])
logits = task.predict(batch)
probabilities = F.sigmoid(logits)
targets = task.target(batch)
```

For binary classification, `predict()` returns logits and the tutorial applies
sigmoid. For normalized regression, TorchDrug 0.2.1 returns predictions on the
original target scale; this changed from earlier releases.

When predicting on CUDA manually, move the whole nested batch:

```python
from torchdrug import utils

batch = utils.cuda(batch)
```

## Self-supervised pretraining

The tutorial uses ClinTox only as a small illustration and recommends a larger
unlabeled corpus such as ZINC2m for real pretraining.

Use matching pretraining features:

```python
dataset = datasets.ClinTox(
    "~/molecule-datasets/",
    atom_feature="pretrain",
    bond_feature="pretrain",
)
```

### InfoGraph

```python
from torchdrug import core, models, tasks

gin_model = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[300, 300, 300, 300, 300],
    edge_input_dim=dataset.edge_feature_dim,
    batch_norm=True,
    readout="mean",
)
model = models.InfoGraph(gin_model, separate_model=False)
task = tasks.Unsupervised(model)

optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(
    task,
    dataset,
    None,
    None,
    optimizer,
    batch_size=256,
)
solver.train(num_epoch=100)
solver.save("gin-infograph.pth")
```

### Attribute masking

```python
model = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[300, 300, 300, 300, 300],
    edge_input_dim=dataset.edge_feature_dim,
    batch_norm=True,
    readout="mean",
)
task = tasks.AttributeMasking(model, mask_rate=0.15)

optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(
    task,
    dataset,
    None,
    None,
    optimizer,
    batch_size=256,
)
solver.train(num_epoch=100)
solver.save("gin-attribute-masking.pth")
```

### Fine-tune the encoder

Recreate the same GIN architecture and feature dimensions, then wrap it in the
supervised task:

```python
model = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[300, 300, 300, 300, 300],
    edge_input_dim=dataset.edge_feature_dim,
    batch_norm=True,
    readout="mean",
)
task = tasks.PropertyPrediction(
    model,
    task=dataset.tasks,
    criterion="bce",
    metric=("auprc", "auroc"),
)

checkpoint = torch.load("gin-attribute-masking.pth")["model"]
task.load_state_dict(checkpoint, strict=False)
```

Then construct a new optimizer and supervised `Engine`. `strict=False` is
intentional because the pretraining and supervised task heads differ. Review
missing and unexpected keys if changing the architecture.

## Experiment checks

- Confirm `dataset.tasks` names and label shapes.
- Confirm classification vs regression before choosing criterion and metrics.
- Record the exact split protocol; do not mislabel random splits as scaffold
  splits.
- Use AUPRC as well as AUROC for heavily imbalanced binary tasks.
- Keep feature arguments identical when loading pretrained weights.
- Fit preprocessing only on the training split.
- Reserve the test split until model selection is complete.

## Source links

- [Property tutorial](https://torchdrug.ai/docs/tutorials/property_prediction.html)
- [Pretraining tutorial](https://torchdrug.ai/docs/tutorials/pretrain.html)
- [Property task API](https://torchdrug.ai/docs/api/tasks.html#property-prediction-tasks)
- [Molecule dataset API](https://torchdrug.ai/docs/api/datasets.html#molecule-property-prediction-datasets)
- [0.2.1 release notes](https://github.com/DeepGraphLearning/torchdrug/releases/tag/v0.2.1)

# scEmbed

Verified against `geniml==0.8.4` release source, current Gtars
`0.9.2`, and official BEDbase documentation on 2026-07-23.

## Scope and evidence

scEmbed learns region embeddings from scATAC-seq accessibility and pools them
to represent cells. The primary paper reports that pre-trained region
embeddings can support clustering and transfer to unseen datasets. Do not turn
that result into a universal accuracy claim; performance depends on assay,
reference corpus, universe, filtering, cell types, and split design.

Primary source: LeRoy et al. (2024), *Fast clustering and cell-type annotation
of scATAC data with pre-trained embeddings*,
doi:[10.1093/nargab/lqae073](https://doi.org/10.1093/nargab/lqae073).

## Stable API and known drift

Use:

```python
from geniml.scembed.main import ScEmbed
from geniml.region2vec.utils import Region2VecDataset
from geniml.tokenization.utils import tokenize_anndata
from gtars.tokenizers import Tokenizer
```

Do not use `from geniml.scembed import ScEmbed`: the 0.8.4 package
`__init__` does not export it. The installed `geniml scembed` command parses
legacy MatrixMarket options but its 0.8.4 command body does no training or
encoding.

The source method `ScEmbed.encode(adata)` is public, but 0.8.4's nested token
handling does not match the current `tokenize_anndata` return shape observed
with modern Gtars. Require a pinned synthetic smoke test before relying on
that convenience method. For production, pre-tokenize explicitly, inspect the
shape, and keep the exact versions locked.

## AnnData contract

The AnnData object must satisfy:

- rows (`obs`) are cells;
- columns (`var`) are accessible regions/features;
- `var["chr"]`, `var["start"]`, and `var["end"]` describe each feature;
- coordinates are validated 0-based half-open BED coordinates;
- all features use one declared assembly and contig convention;
- `X` is sparse CSR for bounded tokenization performance;
- duplicate feature coordinates and duplicate barcodes have an explicit policy.

Confirm matrix orientation. A 10x peak-by-barcode MatrixMarket file is often
transposed when constructing AnnData; inspect dimensions instead of copying a
blind `.T`.

Do not expose barcodes, patient IDs, phenotypes, rare cell labels, or raw
intervals in logs. An `.h5ad` may contain identifying metadata in `obs`,
`uns`, embeddings, and file provenance. Output only bounded aggregate counts
unless the user explicitly approves disclosure.

## Leakage-safe split order

Split before fitting or selecting anything:

1. Group cells by patient/donor and biological replicate.
2. Assign complete groups to train/validation/test.
3. Fit QC thresholds, feature/universe selection, token vocabulary, model,
   annotation references, and hyperparameters on training data only.
4. Apply the frozen universe/tokenizer/model to validation and test.
5. Keep technical replicates and multiple samples from one patient together.

Randomly splitting cells from the same donor leaks donor- and batch-specific
accessibility. Building a consensus universe from all patients can also leak
test-set feature prevalence even when labels are hidden.

Audit a local manifest without printing metadata values:

```bash
python skills/geniml/scripts/corpus_auditor.py \
  --manifest data/cells.tsv \
  --group-column patient_id \
  --split-column split \
  --assembly-column assembly
```

## Build and validate the tokenizer

Use a local, checksummed universe from the training partition:

```python
from gtars.tokenizers import Tokenizer

tokenizer = Tokenizer.from_bed("refs/training_universe.bed")
```

Record:

- source cohort and split;
- assembly, chromosome sizes, coordinate/contig/strand policy;
- universe SHA-256, row order, and row count;
- Gtars version and special-token map/IDs;
- `len(tokenizer)`.

Do not use `Tokenizer.from_pretrained("organization/model")` unless the user
approves a network download and supplies a pinned revision and expected
hashes. A model and tokenizer are compatible only when the exact universe,
special-token IDs, and model vocabulary size agree.

## Pre-tokenize to one bounded Parquet file

```python
import pyarrow as pa
import pyarrow.parquet as pq
import scanpy as sc
from geniml.tokenization.utils import tokenize_anndata

adata = sc.read_h5ad("data/train.h5ad")
adata.X = adata.X.tocsr()

encoded_cells = tokenize_anndata(adata, tokenizer)
cells = [encoded["input_ids"] for encoded in encoded_cells]

table = pa.table({
    "tokens": pa.array(cells, type=pa.list_(pa.int32()))
})
pq.write_table(table, "work/train_tokens.parquet")
```

Before writing:

- verify `len(cells) == adata.n_obs`;
- check each token list is bounded and contains IDs in
  `[0, len(tokenizer))`;
- quantify empty cells and out-of-vocabulary/unmatched features;
- preserve row correspondence in a separate protected manifest;
- do not include barcodes or labels in the training Parquet unless required.

The upstream issue
[`databio/geniml#14`](https://github.com/databio/geniml/issues/14)
(opened 2025-09-05) proposes moving away from one `.gtok` file per cell.
Prefer the single Parquet corpus for current work; treat `.gtok` as legacy.

## Train

```python
from geniml.region2vec.utils import Region2VecDataset
from geniml.scembed.main import ScEmbed

dataset = Region2VecDataset(
    "work/train_tokens.parquet",
    shuffle=True,
)
model = ScEmbed(
    tokenizer=tokenizer,
    embedding_dim=100,
    pooling_method="mean",
    device="cpu",
)
model.train(
    dataset,
    window_size=5,
    epochs=10,
    min_count=10,
    num_cpus=4,
    seed=42,
)
```

Bound cells, nonzeros, tokens per cell, workers, epochs, checkpoint frequency,
RAM, and disk. `Region2VecDataset` loads the full Parquet token column into
memory. Training uses Gensim and Torch; Gensim checkpoint loading is unsafe for
untrusted `.model` files.

Generate a run plan first:

```bash
python skills/geniml/scripts/embedding_plan.py \
  --mode scembed \
  --data work/train_tokens.parquet \
  --universe refs/training_universe.bed \
  --output-dir work/scembed \
  --assembly GRCh38 \
  --embedding-dim 100 --epochs 10 --workers 4 --seed 42
```

## Export and local loading

```python
from pathlib import Path
import shutil

bundle = Path("models/scembed")
model.export(str(bundle))
shutil.copyfile(
    "refs/training_universe.bed",
    bundle / "universe.bed",
)
```

As in Region2Vec, the 0.8.4 export utility writes `checkpoint.pt` and
`config.yaml` but does not write the tokenizer universe. Add the exact
validated `universe.bed` yourself and generate checksums.

Inspect before loading:

```bash
python skills/geniml/scripts/model_artifact_inspector.py \
  --model-dir models/scembed

python skills/geniml/scripts/tokenizer_compatibility.py \
  --model-dir models/scembed \
  --universe refs/training_universe.bed \
  --assembly GRCh38
```

Then, for a trusted local bundle:

```python
from geniml.scembed.main import ScEmbed

model = ScEmbed.from_pretrained("models/scembed")
```

This classmethod is local. In contrast,
`ScEmbed(model_path="organization/model")` downloads three files through
Hugging Face Hub. Never trigger that constructor implicitly. Pin a revision,
cache path, expected size, and checksums when a download is explicitly
approved.

`checkpoint.pt` is loaded with Torch `weights_only=True`. Continue to treat it
as untrusted until verified and load in an isolated, resource-bounded
environment. Never inspect it using pickle.

## Generate and attach cell embeddings

After a pinned synthetic smoke test confirms the installed convenience API:

```python
embeddings = model.encode(adata, pooling="mean")
assert embeddings.shape[0] == adata.n_obs
adata.obsm["X_scembed"] = embeddings
```

If the smoke fails, do not patch around token nesting silently. Pin a known
compatible Geniml/Gtars pair or implement an explicit, tested projection using
the verified token IDs and model contract. Never substitute a different
universe to make shapes fit.

For Scanpy downstream analysis:

```python
import scanpy as sc

sc.pp.neighbors(adata, use_rep="X_scembed")
sc.tl.leiden(adata, resolution=0.5, random_state=42)
sc.tl.umap(adata, random_state=42)
```

UMAP and Leiden are exploratory unless validated on held-out donors. Store
software versions, seeds, neighborhood parameters, and the embedding checksum.

## Cell-type annotation

The release contains `geniml.scembed.annotation.Annotator`, which queries a
Qdrant collection and can use local or remote endpoints. That is a separate
network/data-disclosure decision: embeddings and metadata can be sensitive.
Do not create or contact an annotation server without explicit approval.

For any KNN annotation:

- reference and query embeddings must use the same model/tokenizer/universe;
- fit the reference index using training donors only;
- tune `k` and score thresholds on validation donors;
- include unknown/reject behavior;
- report per-class metrics and calibration on held-out donors;
- avoid claiming labels for absent reference cell types.

Never send raw barcodes, patient metadata, or interval lists to a hosted vector
store by default.

## Evaluation

Report:

- donor-grouped clustering metrics with confidence intervals;
- annotation macro/micro F1 and per-class support;
- unknown/reject rate;
- batch/donor association;
- runtime and peak memory;
- baselines fitted on the same training split.

Do not select clusters, labels, or universe parameters by inspecting the test
UMAP. If pre-trained public models were trained on overlapping donors or
datasets, document that possible leakage.

## Official sources

- [scEmbed training tutorial](https://docs.bedbase.org/geniml/tutorials/train-scembed-model)
  (undated; accessed 2026-07-23)
- [scEmbed API page](https://docs.bedbase.org/geniml/api-reference/scembed/)
  (undated; accessed 2026-07-23)
- [Geniml v0.8.4 source](https://github.com/databio/geniml/tree/v0.8.4/geniml/scembed)
  (released 2026-01-14; accessed 2026-07-23)
- [Gtars tokenizer documentation](https://docs.bedbase.org/gtars/tokenizers)
  (undated; accessed 2026-07-23)
- [Primary scEmbed paper](https://doi.org/10.1093/nargab/lqae073)
  (2024)

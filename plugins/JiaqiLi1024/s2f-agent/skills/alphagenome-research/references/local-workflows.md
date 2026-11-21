# Local Workflows

## Coordinate Conventions

- `genome.Interval(start, end)` is 0-based half-open.
- `genome.Variant(position=...)` uses a 1-based genomic position.
- Keep chromosome names consistent with the FASTA, typically `chr22` rather than `22`.

## Minimal Model Loading

```python
from alphagenome_research.model import dna_model

model = dna_model.create_from_kaggle("all_folds")
# or:
model = dna_model.create_from_huggingface("all_folds")
# or:
model = dna_model.create("/path/to/checkpoint")
```

Pass `organism_settings=...` when local FASTA or annotations are needed.

For downloaded `all_folds` checkpoints and `predict_sequence`, use both organism metadata entries even when predicting a human sequence:

```python
organism_settings = {
    dna_model.Organism.HOMO_SAPIENS: dna_model.OrganismSettings(),
    dna_model.Organism.MUS_MUSCULUS: dna_model.OrganismSettings(),
}
model = dna_model.create("/path/to/checkpoint", organism_settings=organism_settings)
```

This matches the two-organism embedding stored in the checkpoint.

## Accelerator Smoke Test

Use `predict_sequence` as the first real local model test. It exercises checkpoint restore and accelerator forward without requiring FASTA or annotation files.

```python
import jax
from alphagenome_research.model import dna_model

checkpoint_path = "/path/to/hf/snapshot"
device = next(
    d for d in jax.local_devices() if d.platform in {"gpu", "tpu"}
)
organism_settings = {
    dna_model.Organism.HOMO_SAPIENS: dna_model.OrganismSettings(),
    dna_model.Organism.MUS_MUSCULUS: dna_model.OrganismSettings(),
}
model = dna_model.create(
    checkpoint_path,
    organism_settings=organism_settings,
    device=device,
)
outputs = model.predict_sequence(
    "ACGT" * 512,
    organism=dna_model.Organism.HOMO_SAPIENS,
    requested_outputs=[dna_model.OutputType.RNA_SEQ],
    ontology_terms=["UBERON:0001157"],
)
print(outputs.rna_seq.values.shape, outputs.rna_seq.values.dtype, outputs.rna_seq.resolution)
```

A successful smoke test should record the JAX device, checkpoint path, requested output head, output shape, dtype, resolution, and timing. Timing is hardware-dependent. One observed discrete NVIDIA GPU run with `google/alphagenome-all-folds` produced:

- `model_create`: about 4 seconds
- `predict_sequence`: about 29 seconds for a 2048 bp synthetic sequence
- RNA-seq output shape: `(2048, 3)`
- dtype: `float32`
- resolution: `1`

## Interval Prediction

```python
from alphagenome.data import genome
from alphagenome_research.model import dna_model

model = dna_model.create_from_huggingface("all_folds")
interval = genome.Interval(chromosome="chr22", start=35677410, end=35693800)

outputs = model.predict_interval(
    interval=interval,
    requested_outputs=[dna_model.OutputType.RNA_SEQ],
    ontology_terms=["UBERON:0001157"],
)
rna = outputs.rna_seq
print(rna.values.shape, rna.resolution)
```

## Variant Prediction

```python
from alphagenome.data import genome
from alphagenome_research.model import dna_model

model = dna_model.create_from_kaggle("all_folds")
interval = genome.Interval(chromosome="chr22", start=35677410, end=36725986)
variant = genome.Variant(
    chromosome="chr22",
    position=36201698,
    reference_bases="A",
    alternate_bases="C",
)

outputs = model.predict_variant(
    interval=interval,
    variant=variant,
    requested_outputs=[dna_model.OutputType.RNA_SEQ],
    ontology_terms=["UBERON:0001157"],
)
ref_track = outputs.reference.rna_seq
alt_track = outputs.alternate.rna_seq
```

## Sequence Prediction

Use `predict_sequence` when a DNA sequence string is already available. This avoids FASTA lookup but cannot attach true genomic coordinates unless an `interval` is supplied.

```python
outputs = model.predict_sequence(
    "ACGT" * 4096,
    requested_outputs=[dna_model.OutputType.DNASE],
    ontology_terms=None,
)
```

Helper invocation:

```bash
export XLA_PYTHON_CLIENT_PREALLOCATE=false
python skills/alphagenome-research/scripts/run_local_alphagenome.py \
  --mode sequence \
  --model-source checkpoint \
  --checkpoint-path /path/to/hf/snapshot \
  --minimal-organism-settings \
  --output-head RNA_SEQ \
  --ontology-term UBERON:0001157 \
  --output-dir output/alphagenome_research_sequence_smoke
```

## Scoring

`score_variant` and `score_interval` return lists of `AnnData` objects. They may require GTF or polyadenylation annotation paths depending on scorer selection.

```python
scores = model.score_variant(interval, variant)
for i, adata in enumerate(scores):
    adata.write_h5ad(f"variant_score_{i}.h5ad")
```

For in silico mutagenesis:

```python
ism_interval = genome.Interval(chromosome="chr22", start=36201000, end=36201100)
ism_scores = model.score_ism_variants(interval, ism_interval)
```

## Output Pattern

For real agent runs, save:

- `*_result.json`: input parameters, package versions, device list, model source, output paths, status, and error.
- `*_prediction.npz`: raw track arrays when `predict_interval` or `predict_variant` is used.
- `*.h5ad` or `*.csv`: scorer outputs.
- `*.png`: only when plotting is requested.

Do not store credentials or access tokens in output JSON.

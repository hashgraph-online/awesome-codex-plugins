---
name: alphagenome-research
description: Build, run, and troubleshoot local AlphaGenome Research workflows from the `google-deepmind/alphagenome_research` JAX codebase with downloaded Kaggle, Hugging Face, or local checkpoint weights. Use when Codex needs local AlphaGenome model setup, `alphagenome_research.model.dna_model`, `create_from_kaggle`, `create_from_huggingface`, `dna_model.create`, local GPU/TPU/JAX checks, FASTA or annotation settings, `predict_sequence`, `predict_interval`, `predict_variant`, `score_variant`, `score_interval`, or in silico mutagenesis. For hosted API-key `dna_client` calls, use `alphagenome-api` instead.
---

# AlphaGenome Research

## Overview

Use this skill for the local JAX implementation of AlphaGenome Research, where the model runs in the user's Python environment with downloaded weights. Keep it separate from the hosted AlphaGenome API skill, which uses `alphagenome.models.dna_client` and an API key.

## Follow This Workflow

1. Choose the execution path.
- Use this skill when the user says local, research repo, downloaded weights, Kaggle weights, Hugging Face weights, checkpoint path, JAX, GPU, TPU, or `alphagenome_research`.
- Route hosted API-key workflows to `alphagenome-api`.
- If the user asks only for a quick feasibility check, use `scripts/run_local_alphagenome.py --mode check`.

2. Confirm runtime before writing a long workflow.
- Require Python `>=3.11`, because the research package declares `requires-python = >=3.11`.
- Check JAX devices with the bundled script; the model defaults to GPU/TPU and raises if only CPU is present unless a CPU device is explicitly passed.
- Treat upstream high-end accelerator guidance as a recommendation for practical full-model inference, not as a strict software requirement.
- Verify that JAX, not only the vendor CLI, sees the accelerator before model loading. Record driver, CUDA/runtime, JAX, `jaxlib`, plugin package versions, and `jax.local_devices()` as run context rather than assuming a fixed GPU model.
- If a CPU-only or no-GPU container has a tiny cgroup memory limit, do not attempt checkpoint loading on CPU; it can be OOM-killed before `model_loaded`.
- Do not install packages into the system Python when a virtual environment or conda env is available.

3. Install the local research package.
- Prefer an editable install from an existing clone:

```bash
python -m pip install -e /path/to/alphagenome_research
```

- The package depends on `alphagenome`, `jax`, `dm-haiku`, `orbax`, `pyfaidx`, `pyranges`, `tensorflow`, `kagglehub`, `huggingface_hub`, and related scientific Python packages.
- For NVIDIA GPU, follow the JAX CUDA installation path that matches the machine; verify with `python -c "import jax; print(jax.local_devices())"`.

4. Acquire weights and reference assets deliberately.
- Model factories:
  - `dna_model.create_from_kaggle('all_folds')`
  - `dna_model.create_from_huggingface('all_folds')`
  - `dna_model.create('/path/to/checkpoint')`
- Kaggle and Hugging Face weights require accepting AlphaGenome model terms and having the relevant CLI/token authentication available.
- Hugging Face `all_folds` maps to `google/alphagenome-all-folds`. If downloads stall behind a proxy or on cloud networks, set `HF_HUB_DISABLE_XET=1` and use `snapshot_download(..., max_workers=1)` into a persistent cache on whatever large storage the machine provides.
- Default organism settings point to remote reference FASTA and Feather annotation URLs. For reliable local runs, prefer explicit local paths through `dna_model.OrganismSettings`.
- When passing explicit `organism_settings` for an `all_folds` checkpoint, include both `HOMO_SAPIENS` and `MUS_MUSCULUS` metadata entries. A human-only metadata dict can load the checkpoint but fail during forward with `alphagenome/embed/embeddings` shape `(2, 1536)` versus `(1, 1536)`.

5. Build the smallest useful prediction.
- For a true local accelerator smoke test, run `predict_sequence` first. It validates checkpoint restore and model forward without requiring FASTA or annotation assets.
- Use `predict_sequence` when the user already has sequence text and does not need FASTA lookup.
- Use `predict_interval` for interval-only track prediction; interval coordinates are 0-based half-open.
- Use `predict_variant` for REF/ALT comparison; variant `position` is 1-based in `genome.Variant`.
- Use `score_variant`, `score_interval`, or `score_ism_variants` only when the user asks for scorer outputs rather than raw tracks.
- Request only needed output heads and ontology terms.

6. Save auditable outputs.
- For real runs, save a JSON summary with package versions, model source, organism, coordinates, requested output heads, ontology terms, status, and error if any.
- Save arrays as `.npz` or scorer tables as `.h5ad`/`.csv` when the task needs downstream analysis.
- Save plots only when the user asks to inspect signal tracks.

## Grounded Local API Surface

Treat these names as grounded by the bundled AlphaGenome Research README and source:

- `from alphagenome.data import genome`
- `from alphagenome_research.model import dna_model`
- `dna_model.create(checkpoint_path, organism_settings=None, model_settings=dna_model.ModelSettings(), device=None)`
- `dna_model.create_from_kaggle('all_folds', organism_settings=None, device=None)`
- `dna_model.create_from_huggingface('all_folds', organism_settings=None, device=None)`
- `dna_model.Organism.HOMO_SAPIENS`
- `dna_model.Organism.MUS_MUSCULUS`
- `dna_model.OutputType.RNA_SEQ`
- `dna_model.OutputType.DNASE`
- `dna_model.OutputType.ATAC`
- `dna_model.OutputType.CHIP_TF`
- `dna_model.OutputType.CHIP_HISTONE`
- `dna_model.OutputType.CONTACT_MAPS`
- `dna_model.OutputType.SPLICE_SITES`
- `dna_model.OutputType.SPLICE_SITE_USAGE`
- `dna_model.OutputType.SPLICE_JUNCTIONS`
- `dna_model.OrganismSettings(fasta_path=..., gtf_feather_path=..., pas_feather_path=..., splice_site_starts_feather_path=..., splice_site_ends_feather_path=...)`
- `model.predict_sequence(sequence, organism=..., requested_outputs=[...], ontology_terms=[...], interval=None)`
- `model.predict_interval(interval, organism=..., requested_outputs=[...], ontology_terms=[...])`
- `model.predict_variant(interval, variant, organism=..., requested_outputs=[...], ontology_terms=[...])`
- `model.score_interval(interval, interval_scorers=(), organism=...)`
- `model.score_variant(interval, variant, variant_scorers=(), organism=...)`
- `model.score_ism_variants(interval, ism_interval, variant_scorers=(), organism=..., interval_variant=None)`
- `genome.Interval(chromosome='chr22', start=..., end=...)`
- `genome.Variant(chromosome='chr22', position=..., reference_bases='A', alternate_bases='C')`

Verify any additional scorer enum, metadata field, or plotting helper against the installed package or the local source before using it.

## Common Commands

Environment/import check:

```bash
python skills/alphagenome-research/scripts/run_local_alphagenome.py --mode check
```

Real downloaded-checkpoint accelerator smoke test:

```bash
export HF_HOME=/path/to/persistent/hf-cache
export HF_HUB_CACHE="$HF_HOME/hub"
export HF_HUB_DISABLE_XET=1
python skills/alphagenome-research/scripts/run_local_alphagenome.py \
  --mode sequence \
  --model-source checkpoint \
  --checkpoint-path "$HF_HUB_CACHE/models--google--alphagenome-all-folds/snapshots/<sha>" \
  --minimal-organism-settings \
  --output-head RNA_SEQ \
  --ontology-term UBERON:0001157 \
  --output-dir output/alphagenome_research_gpu_smoke
```

Generate a runnable Python template without loading weights:

```bash
python skills/alphagenome-research/scripts/run_local_alphagenome.py \
  --mode template \
  --task variant \
  --model-source huggingface \
  --output-dir output/alphagenome_research
```

Run a local single-variant prediction:

```bash
python skills/alphagenome-research/scripts/run_local_alphagenome.py \
  --mode variant \
  --model-source kaggle \
  --model-version all_folds \
  --chrom chr22 \
  --position 36201698 \
  --ref A \
  --alt C \
  --interval-width 16384 \
  --output-head RNA_SEQ \
  --ontology-term UBERON:0001157 \
  --output-dir output/alphagenome_research
```

Run a local interval prediction:

```bash
python skills/alphagenome-research/scripts/run_local_alphagenome.py \
  --mode interval \
  --model-source checkpoint \
  --checkpoint-path /path/to/alphagenome/checkpoint \
  --interval chr22:35677410-35693800 \
  --output-head RNA_SEQ \
  --ontology-term UBERON:0001157 \
  --output-dir output/alphagenome_research
```

## Response Style

- State whether the workflow is local research code or hosted API before code.
- Surface hardware, Python, JAX, authentication, model terms, and reference-asset assumptions early.
- Use 0-based half-open language for intervals and 1-based language for variants every time coordinates are involved.
- Prefer local paths for FASTA and annotation assets when reproducibility matters.
- Never imply the weights are bundled with the repository; they must be downloaded or supplied by checkpoint path.

## References

- Read [references/setup-and-runtime.md](references/setup-and-runtime.md) for installation, authentication, hardware, and local asset guidance.
- Read [references/local-workflows.md](references/local-workflows.md) for minimal prediction, scoring, and output patterns.

## Scripts

- `scripts/run_local_alphagenome.py` checks the local runtime, writes runnable templates, and runs small local interval or variant prediction jobs when weights and references are available.

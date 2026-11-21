---
name: dnabert2
description: Use DNABERT-2 for DNA sequence embeddings, GUE benchmark evaluation, and supervised fine-tuning on custom classification datasets with the official Hugging Face + `finetune/train.py` workflow. Use when Codex needs to write, fix, explain, or review Python, shell, notebook, or `torchrun` code involving `zhihan1996/DNABERT-2-117M`, `AutoTokenizer`, `AutoModel`, `AutoModelForSequenceClassification`, `trust_remote_code=True`, DNABERT2 dataset formatting (`train.csv`/`dev.csv`/`test.csv`), or DNABERT2 training hyperparameters.
---

# DNABERT-2

## Overview

Use this skill for DNABERT-2 only. Prefer the official Hugging Face loading pattern for inference and the repository `finetune/train.py` path for training/evaluation.

## Follow This Decision Flow

1. Choose the task type first.
- Use embedding inference when the user needs sequence representations.
- Use coordinate-based embedding inference when users provide genomic loci (`species`, `assembly`, `chrom`, `start`, `end`) and need real-sequence embeddings or plots.
- Use GUE evaluation when the user asks to replicate paper-style benchmark scripts.
- Use custom fine-tuning when the user provides or plans `train/dev/test` CSV files.

2. Resolve sequence inputs explicitly for coordinate workflows.
- Confirm coordinate convention first: zero-based, half-open interval (`[start, end)`).
- Confirm interval width equals `end - start`, and report the fetched sequence length.
- Prefer local reference FASTA/2bit when available; otherwise use a reproducible remote source and report it.
- Preserve assembly/chromosome naming consistency (for example `hg38` with `chr19`).

3. Choose the Transformers loading path by version.
- For `transformers==4.28`, use direct `AutoModel.from_pretrained(..., trust_remote_code=True)`.
- For `transformers>4.28`, load `BertConfig` first, then pass it into `AutoModel.from_pretrained(..., trust_remote_code=True, config=config)`.

4. Validate data format before writing training commands.
- Require `train.csv`, `dev.csv`, and `test.csv` in one folder.
- Default single-sequence classification format: header `sequence,label`.
- Also support sequence-pair classification (`seq1,seq2,label`) because `train.py` supports 3-column rows.

5. Set DNABERT2-specific training defaults.
- Use `--model_name_or_path zhihan1996/DNABERT-2-117M`.
- Use `--kmer -1` for DNABERT-2 (no k-mer preprocessing).
- Start from official defaults (`learning_rate=3e-5`, `num_train_epochs=5`, mixed precision on GPU).
- Set `--model_max_length` to about `0.25 * sequence_length_bp` as documented.

6. Choose parallel training mode explicitly.
- Use plain `python train.py ...` for single process / DataParallel setups.
- Use `torchrun --nproc_per_node=<num_gpu> train.py ...` for DDP-style multi-GPU runs.
- Keep global batch-size reasoning explicit when adapting the official scripts.

7. Report outputs and metrics concretely.
- For embeddings, show shape expectations (`[seq_tokens, 768]` then pooled `768`).
- For coordinate-based embedding plots, report final interval, sequence source, sequence length, and output figure path.
- For fine-tuning, point to `output/.../results/<run_name>/eval_results.json` written by `train.py`.

## Grounded API Surface

Treat the following names and patterns as grounded:

- `AutoTokenizer.from_pretrained("zhihan1996/DNABERT-2-117M", trust_remote_code=True)`
- `AutoModel.from_pretrained("zhihan1996/DNABERT-2-117M", trust_remote_code=True)`
- `from transformers.models.bert.configuration_bert import BertConfig`
- `BertConfig.from_pretrained("zhihan1996/DNABERT-2-117M")`
- `AutoModel.from_pretrained(..., trust_remote_code=True, config=config)`
- `transformers.AutoModelForSequenceClassification.from_pretrained(..., trust_remote_code=True)`
- `python train.py ...`
- `torchrun --nproc_per_node=<N> train.py ...`
- `python scripts/embed_interval_plot.py --assembly hg38 --chrom chr19 --start 6700000 --end 6702768 ...`

Grounded model id:

- `zhihan1996/DNABERT-2-117M`

Do not invent alternate DNABERT2 wrappers, undocumented training entry points, or hidden preprocessing steps.

## Response Style

- Prefer runnable code snippets over architecture summaries.
- Surface version-compatibility (`4.28` vs `>4.28`) early.
- Call out `kmer=-1` explicitly for DNABERT2 training commands.
- For coordinate workflows, state coordinate convention and sequence provenance up front.
- When users provide dataset files, validate schema assumptions before giving long training commands.

## References

- Read [references/setup-and-compatibility.md](references/setup-and-compatibility.md) for environment setup and version matrix.
- Read [references/inference-quickstart.md](references/inference-quickstart.md) for minimal embedding examples.
- Read [references/finetune-workflows.md](references/finetune-workflows.md) for GUE and custom fine-tuning command patterns.
- Read [references/caveats.md](references/caveats.md) for common failure modes and constraints.
- Use [scripts/validate_dataset_csv.py](scripts/validate_dataset_csv.py) before fine-tuning custom data.
- Use [scripts/recommend_max_length.py](scripts/recommend_max_length.py) to suggest `model_max_length` from sequence lengths.
- Use [scripts/embed_interval_plot.py](scripts/embed_interval_plot.py) for real coordinate-based embedding extraction and PCA visualization.

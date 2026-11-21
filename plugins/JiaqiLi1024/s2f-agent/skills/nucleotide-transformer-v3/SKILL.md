---
name: nucleotide-transformer-v3
description: Use Nucleotide Transformer v3 for long-context multispecies workflows with Hugging Face Transformers as the primary path, with JAX helper APIs as secondary compatibility, including pre-trained MLM embeddings, post-trained species-conditioned track/annotation inference, dual-mode fine-tuning workflows (prep + full training), length-divisibility checks, and gated-repo troubleshooting. Use when Codex needs to write, fix, explain, or review code or notebooks involving `AutoTokenizer.from_pretrained(..., trust_remote_code=True)`, `AutoModelForMaskedLM`, `AutoModel`, `encode_species`, `num_downsamples`, `keep_target_center_fraction`, NTv3 model names, bigwig/bed outputs, NTv3 fine-tuning notebooks, or NTv3 install/auth issues.
---

# Nucleotide Transformer v3

## Overview

Use this skill for NTv3 only.

- Primary path: Hugging Face Transformers + PyTorch with `trust_remote_code=True`.
- Secondary path: legacy JAX helper APIs for projects that already depend on `nucleotide_transformer_v3.pretrained`.

## Follow This Decision Flow

1. Choose the backend first.
- Default to the HF backend: Transformers + PyTorch.
- Use the JAX helper backend only for existing code that already uses `nucleotide_transformer_v3.pretrained`.

2. Confirm gated-repo access early.
- NTv3 model repos are gated.
- Authenticate with `huggingface-cli login` or pass `token=...` in `from_pretrained(...)`.

3. Choose the NTv3 workflow family.
- Use pre-trained models for embeddings and masked-language-model style outputs.
- Use post-trained models for species-conditioned functional-track and genome-annotation prediction.
- Use dual-mode training workflows for NTv3 fine-tuning (`prep` planning mode or `train` full-training mode) and keep mode explicit.

4. Choose a model size or checkpoint family.
- Use the main production checkpoints first.
- Only surface ablation or intermediate checkpoints when the user explicitly needs them.

5. Validate sequence length before writing code.
- Sequence length must be divisible by `2^num_downsamples`.
- Main production models typically use `num_downsamples=7` (divisor `128`).
- 5-downsample ablations use divisor `32`.
- Prefer deriving divisor from config (`2 ** model.config.num_downsamples`) instead of hardcoding.
- For HF tokenization, use `pad_to_multiple_of=<divisor>`, or crop/pad with `N`.
- Use [scripts/check_valid_length.py](scripts/check_valid_length.py) when the user gives a concrete sequence length.

6. Handle conditioning and outputs correctly.
- For HF post-trained models, get species ids with `model.encode_species(...)`.
- Explain that functional-track and annotation outputs keep the model's center fraction (`model.config.keep_target_center_fraction`), while MLM logits stay full-length.
- For main post-trained checkpoints this center fraction is commonly 37.5%, but do not hardcode it.

7. Address install, version, and network issues explicitly.
- For installation failures, start with [references/setup-and-troubleshooting.md](references/setup-and-troubleshooting.md).
- Prefer pinned dependencies: `transformers>=4.55,<5`, `huggingface_hub>=0.23,<1`, and `numpy<2` with `torch 2.2.x`.
- If download transport is unstable, set `HF_HUB_DISABLE_XET=1`.
- If JAX-source install errors on `jax>=0.6.0` with Python 3.9, switch to Python >=3.10 or use the HF tutorial path.

8. Pick execution format by task.
- For region-level track prediction + plotting, prefer [scripts/run_track_prediction.py](scripts/run_track_prediction.py) instead of rewriting notebook cells.
- For BED batch workflows, use [scripts/run_track_prediction_bed_batch.py](scripts/run_track_prediction_bed_batch.py).
- For fine-tuning requests, use mode-aware guidance from [references/finetune-workflows.md](references/finetune-workflows.md), plus `case-study-playbooks/fine-tuning/run_fine_tuning_case.sh` for reproducible prep/train execution.
- For NTv3 full training, use [scripts/train_csv_binary_classification.py](scripts/train_csv_binary_classification.py) via the case-study wrapper; keep CPU-only and MPS fail-fast constraints explicit.

## Real Track Prediction Fastpath

Use this path when the user asks for one real NTv3 track prediction run and wants directly executable commands.

- Default model: `InstaDeepAI/NTv3_100M_post`.
- Default output directory: `output/ntv3_results`.
- CPU execution is acceptable when CUDA is unavailable.

Preflight order (do not skip):

1. `HF_TOKEN` availability from environment (for example via root `.env`).
2. Gated model access check (`InstaDeepAI/NTv3_100M_post`).
3. Runtime check with `conda run -n ntv3`.
4. Network checks for UCSC sequence API and Hugging Face model fetch.

Standard command template:

```bash
set -a; source .env; set +a
mkdir -p output/ntv3_results
conda run -n ntv3 python skills/nucleotide-transformer-v3/scripts/run_track_prediction.py \
  --model InstaDeepAI/NTv3_100M_post \
  --species human \
  --assembly hg38 \
  --chrom chr19 \
  --start 6700000 \
  --end 6732768 \
  --output-dir output/ntv3_results \
  2>&1 | tee output/ntv3_results/ntv3_run.log
```

Download-transport fallback (retry once):

```bash
set -a; source .env; set +a
conda run -n ntv3 python skills/nucleotide-transformer-v3/scripts/run_track_prediction.py \
  --model InstaDeepAI/NTv3_100M_post \
  --species human \
  --assembly hg38 \
  --chrom chr19 \
  --start 6700000 \
  --end 6732768 \
  --output-dir output/ntv3_results \
  --disable-xet \
  2>&1 | tee output/ntv3_results/ntv3_run.log
```

BED batch fastpath:

```bash
set -a; source .env; set +a
mkdir -p case-study/track_prediction/ntv3_results
conda run -n ntv3 python skills/nucleotide-transformer-v3/scripts/run_track_prediction_bed_batch.py \
  --bed case-study/track_prediction/bed/Test.interval.bed \
  --model InstaDeepAI/NTv3_100M_post \
  --species human \
  --assembly hg38 \
  --output-dir case-study/track_prediction/ntv3_results \
  2>&1 | tee case-study/track_prediction/ntv3_results/ntv3_bed_batch.log
```

Batch behavior:

- Each interval retries once with `--disable-xet` on failure.
- Batch continues even if some intervals fail.
- Batch always exits `0`; inspect `ntv3_bed_batch_summary.json` for `failed_count`.

Acceptance checklist:

- Log contains `loading config/tokenizer/model from HF`.
- Log contains `saved plot:` and `saved meta:`.
- `*_trackplot.png` exists.
- `*_result.json` exists with expected `species/assembly/chrom/start/end`.
- BED mode writes `ntv3_bed_batch_summary.json` with per-interval success/failure details.

## Mode-Aware Fine-Tuning Fastpath

Use this path when the user asks for NTv3 fine-tuning and wants explicit prep/train mode behavior.

- Primary source notebooks remain: `Readme/NTv3/02_fine_tuning_pretrained_model_biwig.ipynb`, `03_fine_tuning_posttrained_model_biwig.ipynb`, `04_fine_tuning_pretrained_model_annotation.ipynb`.
- Reproducible local execution entrypoint is `case-study-playbooks/fine-tuning/run_fine_tuning_case.sh`.
- `prep` mode produces planning artifacts only.
- `train` mode performs full CSV binary-classification training through `scripts/train_csv_binary_classification.py`.

Preflight order (do not skip):

1. Confirm `HF_TOKEN` and gated model access.
2. Confirm runtime dependencies (`pyfaidx`, `pyBigWig`, `torchmetrics`, `transformers`, `torch`) in `conda run -n ntv3`.
3. Confirm data schema (`sequence,label`) and intended objective.
4. Confirm sequence length divisibility with `2 ** num_downsamples`.
5. Confirm execution device policy:
   - train mode is CPU-only in this playbook
   - MPS is fail-fast (unsupported)

Execution guidance:

- Prep mode:
  - `bash case-study-playbooks/fine-tuning/run_fine_tuning_case.sh --skills ntv3 --ntv3-mode prep --data-dir case-study-playbooks/fine-tuning/data`
- Train mode:
  - `FINE_TUNING_NTV3_DEVICE=cpu bash case-study-playbooks/fine-tuning/run_fine_tuning_case.sh --skills ntv3 --ntv3-mode train --data-dir case-study-playbooks/fine-tuning/data`

Expected outputs to surface in responses:

- prep mode:
  - `train-command.sh`
  - `eval-metrics.json` (`status=not_executed`)
- train mode:
  - `eval-metrics.json`
  - `training_history.json`
  - `model_output/best_checkpoint.pt`
  - `train.log`

## Case-Study Fine-Tuning Execution Flow

Use this section when the user asks for reproducible NTv3 fine-tuning under `case-study-playbooks/fine-tuning`.

Recommended order:

1. Run prep mode first to validate schema and context-length assumptions.
2. Run train mode only after prep artifacts are valid and compute constraints are explicit.

Preflight checklist:

1. `HF_TOKEN` is set and gated NTv3 model access is available.
2. Runtime is available (`conda run -n ntv3`).
3. Input lengths are validated with `scripts/check_valid_length.py`.
4. Mode is explicit (`prep` or `train`).

Flow-level acceptance checkpoints (process-oriented):

- prep mode artifacts exist under `<run_root>/ntv3_results`:
  - `fine_tuning_plan.json`
  - `train-command.sh`
  - `eval-metrics.json`
  - `prep_report.json`
- train mode artifacts exist under `<run_root>/ntv3_results`:
  - `eval-metrics.json`
  - `training_history.json`
  - `model_output/best_checkpoint.pt`
  - `train.log`
- Do not treat one specific run's tensor shape values as hard assertions in this workflow section.

## Grounded API Surface

Treat the following HF tutorial names and patterns as grounded:

- `from transformers import AutoConfig, AutoModel, AutoModelForMaskedLM, AutoTokenizer`
- `AutoTokenizer.from_pretrained(..., trust_remote_code=True, token=...)`
- `AutoModelForMaskedLM.from_pretrained(..., trust_remote_code=True, token=...)`
- `AutoModel.from_pretrained(..., trust_remote_code=True, token=...)`
- `tokenizer(..., add_special_tokens=False, padding=True, pad_to_multiple_of=<divisor>, return_tensors="pt")`
- `model.encode_species(...)`
- `model(input_ids=..., species_ids=...)`
- `model.config.num_downsamples`
- `model.config.keep_target_center_fraction`
- `outs["logits"]`
- `outs["bigwig_tracks_logits"]`
- `outs["bed_tracks_logits"]`
- `torch.utils.data.DataLoader`
- `torch.optim.AdamW`
- `crop_center(...)`
- `poisson_loss(...)`
- `focal_loss(...)`

Legacy JAX helper names remain grounded for compatibility:

- `from nucleotide_transformer_v3.pretrained import get_pretrained_ntv3_model`
- `from nucleotide_transformer_v3.pretrained import get_posttrained_ntv3_model`
- `get_pretrained_ntv3_model(...)`
- `get_posttrained_ntv3_model(...)`
- `tokenizer.batch_np_tokenize(...)`
- `model(tokens)`
- `posttrained_model.encode_species(...)`
- `posttrained_model(tokens=tokens, species_tokens=species_tokens)`

Grounded main model names and HF repo ids:

- `NTv3_8M_pre`
- `NTv3_100M_pre`
- `NTv3_650M_pre`
- `NTv3_100M_post`
- `NTv3_650M_post`
- `InstaDeepAI/NTv3_8M_pre`
- `InstaDeepAI/NTv3_100M_pre`
- `InstaDeepAI/NTv3_650M_pre`
- `InstaDeepAI/NTv3_100M_post`
- `InstaDeepAI/NTv3_650M_post`

Grounded optional intermediate/ablation names:

- `NTv3_8M_pre_8kb`
- `NTv3_100M_pre_8kb`
- `NTv3_100M_post_131kb`
- `NTv3_650M_pre_8kb`
- `NTv3_650M_post_131kb`
- `NTv3_5downsample_pre_8kb`
- `NTv3_5downsample_pre`
- `NTv3_5downsample_post_131kb`
- `NTv3_5downsample_post`

Do not invent alternate wrappers or training code from this skill alone.

## Response Style

- Prefer concise Transformers examples first, with exact model names.
- Use JAX examples only when the user asks for the legacy API path.
- Surface divisibility and center-fraction rules before discussing large-context runs.
- State clearly whether a sequence should be cropped or padded with `N`.

## References

- Read [references/setup-and-troubleshooting.md](references/setup-and-troubleshooting.md) first for install, version, and import failures.
- Read [references/model-catalog.md](references/model-catalog.md) for checkpoint selection.
- Read [references/pre-vs-post.md](references/pre-vs-post.md) for code patterns and output differences.
- Read [references/finetune-workflows.md](references/finetune-workflows.md) for notebook-aligned NTv3 fine-tuning patterns.
- Read [references/length-and-memory.md](references/length-and-memory.md) for divisibility, padding, and precision guidance.
- Use [scripts/check_valid_length.py](scripts/check_valid_length.py) to validate concrete input lengths.
- Use [scripts/run_track_prediction.py](scripts/run_track_prediction.py) for region-level prediction and plotting.
- Use [scripts/run_track_prediction_bed_batch.py](scripts/run_track_prediction_bed_batch.py) for BED batch prediction.

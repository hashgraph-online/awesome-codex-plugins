# Fine-Tune Workflows

Use this file when the user asks for NTv3 fine-tuning, notebook-to-script conversion, or prep/train mode disambiguation.

Primary evidence source for this reference:

- `Readme/NTv3/02_fine_tuning_pretrained_model_biwig.ipynb`
- `Readme/NTv3/03_fine_tuning_posttrained_model_biwig.ipynb`
- `Readme/NTv3/04_fine_tuning_pretrained_model_annotation.ipynb`

## Scope and Execution Mode

- Notebook workflows remain the model-behavior source of truth.
- Reproducible local execution entrypoint for this repository is:
  - `case-study-playbooks/fine-tuning/run_fine_tuning_case.sh`
- NTv3 fine-tuning is mode-aware:
  - `prep`: planning artifacts only (`train-command.sh`, placeholder metrics)
  - `train`: full CSV binary-classification training (`eval-metrics.json`, `training_history.json`, `best_checkpoint.pt`)

## Shared Preflight Checklist

1. Gated model access is available (`HF_TOKEN` or `huggingface-cli login`).
2. Runtime dependencies are installed:
   - `transformers`, `torch`, `pyfaidx`, `pyBigWig`, `torchmetrics`
3. Sequence length is valid for the selected checkpoint:
   - divisor = `2 ** num_downsamples`
4. Target cropping behavior is explicit:
   - `keep_target_center_fraction` affects bigwig/annotation heads.
5. Hardware policy is explicit:
   - this playbook supports CPU-only full training currently
   - MPS is fail-fast and should be rejected early

## Workflow A: Pretrained -> BigWig Tracks

Notebook source: `02_fine_tuning_pretrained_model_biwig.ipynb`

Typical config keys:

- `model_name`
- `hf_repo_id`
- `species`
- `sequence_length`
- `keep_target_center_fraction`
- `bigwig_file_ids`
- `batch_size`
- `num_steps_training`
- `learning_rate`
- `weight_decay`

Typical training pattern:

- build genomic window dataset
- tokenize DNA inputs with `AutoTokenizer(..., trust_remote_code=True)`
- center-crop targets for track heads
- optimize with Poisson-style track loss
- report correlation metrics on validation/test sets

## Workflow B: Posttrained -> BigWig Tracks

Notebook source: `03_fine_tuning_posttrained_model_biwig.ipynb`

Typical config keys:

- `model_name`
- `species_name`
- `sequence_length`
- `keep_target_center_fraction`
- `mini_batch_size`
- `num_accumulation_gradient`
- `num_steps_training`
- `initial_learning_rate`
- `end_learning_rate`
- `num_steps_warmup`

Typical training pattern:

- post-trained model path with species-conditioned head behavior
- gradient accumulation for memory control
- warmup + decay learning-rate schedule
- track-wise correlation metrics for validation/test

## Workflow C: Pretrained -> Annotation Heads

Notebook source: `04_fine_tuning_pretrained_model_annotation.ipynb`

Typical config keys:

- `model_name`
- `species_name`
- `sequence_length`
- `keep_target_center_fraction`
- `batch_size`
- `num_steps_training`
- `learning_rate`
- `weight_decay`

Typical training pattern:

- annotation target construction and center-crop alignment
- classification-style objective (for example focal-loss family)
- per-label metrics tracking during train/val/test

## Mode-Aware Case Study Commands

Prep mode:

```bash
bash case-study-playbooks/fine-tuning/run_fine_tuning_case.sh \
  --skills ntv3 \
  --ntv3-mode prep \
  --data-dir case-study-playbooks/fine-tuning/data
```

Train mode:

```bash
FINE_TUNING_NTV3_DEVICE=cpu \
bash case-study-playbooks/fine-tuning/run_fine_tuning_case.sh \
  --skills ntv3 \
  --ntv3-mode train \
  --data-dir case-study-playbooks/fine-tuning/data
```

## Artifact Acceptance (Prep vs Train)

Prep mode artifacts under `<run_root>/ntv3_results`:

- `fine_tuning_plan.json`
- `train-command.sh`
- `eval-metrics.json` (`status=not_executed`)
- `prep_report.json`

Train mode artifacts under `<run_root>/ntv3_results`:

- `eval-metrics.json` (`status=completed` expected on success)
- `training_history.json`
- `model_output/best_checkpoint.pt`
- `train.log`

Flow-level summary:

- `<run_root>/fine_tuning_case_summary.json` must exist in both modes.
- Treat artifact presence and mode-correct status fields as pass criteria.

## Failure Recovery Paths

1. Length invalid (`check_valid_length.py` fails):
   - round context length to nearest valid multiple (`2 ** num_downsamples`) and rerun.
2. Dataset schema invalid (`validate_dataset.log` fails):
   - repair headers/columns/types to `sequence,label` and rerun.
3. Token missing or gated model auth failure:
   - export valid `HF_TOKEN` (or run `huggingface-cli login`) and rerun.
4. Unsupported train device:
   - if MPS/GPU mode is requested for this playbook, switch to CPU and rerun.

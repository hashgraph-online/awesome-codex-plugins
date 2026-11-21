---
name: borzoi-workflows
description: Use Calico Borzoi workflows for RNA-seq coverage prediction from DNA, including environment setup, model download, data processing, mini-model training, variant scoring, sequence-interpretation gradients, and SV/STR analysis. Use when Codex needs to write, fix, explain, or review Borzoi commands, scripts, or notebooks from the official `borzoi` tutorials (`make_data`, `train_model`, `score_variants`, `interpret_sequence`, `analyze_sv`) or example QTL notebooks. Prefer this skill for Borzoi repository workflows; use `segment-nt` only for SegmentBorzoi JAX segmentation APIs from Nucleotide Transformer docs.
---

# Borzoi Workflows

## Overview

Use this skill for the TensorFlow-based `calico/borzoi` repository workflows and tutorials. Keep repository-level Borzoi usage separate from SegmentBorzoi JAX segmentation helper APIs.

## Follow This Decision Flow

1. Choose the objective first.
- Use pretrained Borzoi when the user wants published-model inference or variant interpretation quickly.
- Use tutorial Mini/Micro Borzoi when the user wants an end-to-end toy pipeline on sample data.
- Use training workflows only when the user explicitly asks for training or data processing.

2. Choose tutorial generation deliberately.
- Default to `tutorials/latest/*`.
- Use `tutorials/legacy/*` only for manuscript-style transforms or when reproducing older published settings.

3. Set up environment and dependencies before writing long scripts.
- Use Python `3.10` and TensorFlow `2.15.x` for the grounded path.
- Install `baskerville` and `borzoi` for core workflows.
- Install `westminster` when training/data-prep scripts require it.
- If notebooks are requested, include `jupyter`/`notebook` installation.

4. Pick an inference tier explicitly for real-world prediction requests.
- `full`: published pretrained Borzoi + local genome/annotation assets via `download_models.sh`. Use when users request paper-grade published weights and can afford larger downloads/runtime.
- `fast`: Mini Borzoi + task-local sequence retrieval and minimal assets. Use when users need real prediction output but have runtime/bandwidth constraints.
- `offline`: reuse already-downloaded local model/FASTA assets without network access.

5. Align data and model assets to the selected tier.
- For `full` published-model workflows, run `download_models.sh` first.
- For `fast` human workflows, prefer `mini/human_gtex` (or `mini/human_all`) by default; use `k562_*` only when user explicitly asks for K562-focused outputs.
- For training-data requests, call out that the full data bucket is multi-TB and requester-pays.
- Keep organism/build explicit (`hg38` vs `mm10`) and verify targets files used by scripts.

6. Use the tutorial script entry points directly.
- Data processing: `tutorials/latest/make_data`.
- Training: `tutorials/latest/train_model`.
- Variant scoring: `tutorials/latest/score_variants` (or `legacy` with published model).
- Interpretation gradients: `tutorials/latest/interpret_sequence` (or `legacy` variants).
- Indel/SV/STR analysis: `tutorials/latest/analyze_sv`.

7. Explain score semantics precisely.
- Expression: `logSED`, `logD2`.
- Polyadenylation: `COVR`.
- Splicing: `nDi`.
- Distinguish gene-specific vs gene-agnostic outputs when summarizing results.

8. Surface operational caveats early.
- Some scripts assume SLURM/multiprocess environments.
- Tutorial scripts are minimal examples and not full benchmark pipelines.
- Legacy scripts may require old-transform flags (`-u` or `--untransform_old`).
- Sequence-window and output-window coordinates can differ after model cropping; include both in outputs.

9. For s2f track-prediction case-study runs, prefer BED batch wrappers.
- Use `case-study-playbooks/track_prediction/run_borzoi_track_case.sh` for runnable batch execution.
- Default output root should be `case-study-playbooks/track_prediction/<run_id>/borzoi_results`.
- Treat `borzoi_bed_batch_summary.json` as the execution source of truth, with per-interval artifacts (`*_trackplot.png`, `*_result.json`, `*_track_prediction.npz`, `*_top_tracks.tsv`, interval logs).

## Grounded Command Surface

Treat the following commands and paths as grounded:

- `git clone https://github.com/calico/baskerville.git`
- `git clone https://github.com/calico/borzoi.git`
- `git clone https://github.com/calico/westminster.git`
- `pip install -e .`
- `conda create -n borzoi_py310 python=3.10`
- `./env_vars.sh`
- `./download_models.sh`
- `tutorials/latest/make_data/download_dependencies.sh`
- `tutorials/latest/make_data/download_bw.sh`
- `tutorials/latest/make_data/process_w5.sh`
- `tutorials/latest/make_data/Makefile`
- `tutorials/latest/train_model/train_mini.sh`
- `tutorials/latest/train_model/train_micro.sh`
- `tutorials/latest/score_variants/score_expr_sed.sh`
- `tutorials/latest/score_variants/score_expr_sad.sh`
- `tutorials/latest/score_variants/score_polya.sh`
- `tutorials/latest/score_variants/score_splice.sh`
- `tutorials/latest/interpret_sequence/run_gradients_expr_HBE1.sh`
- `tutorials/latest/analyze_sv/download_dependencies_SV.sh`
- `tutorials/latest/analyze_sv/analyze_indel.sh`
- `tutorials/latest/analyze_sv/download_dependencies_STR.sh`
- `tutorials/latest/analyze_sv/score_STRs.sh`

Do not invent alternate Borzoi wrappers, hidden APIs, or unsupported benchmark claims.

## Response Style

- Prefer the smallest runnable script sequence first.
- State whether the path is `latest` or `legacy`.
- Label clearly when examples use tutorial Mini/Micro models instead of the published pretrained model.
- For constrained runtime paths, label explicitly as `fast` tier and include the model chosen.
- If users ask for SegmentBorzoi segmentation APIs, route them to `segment-nt`.

## References

- Read [references/setup-and-env.md](references/setup-and-env.md) for installation, versions, and environment variables.
- Read [references/tutorial-playbooks.md](references/tutorial-playbooks.md) for end-to-end latest tutorial command flow.
- Read [references/variant-and-interpretation.md](references/variant-and-interpretation.md) for score semantics and legacy-vs-latest behavior.
- Read [references/real-inference-fastpath.md](references/real-inference-fastpath.md) for low-overhead real prediction and single-site variant execution patterns.

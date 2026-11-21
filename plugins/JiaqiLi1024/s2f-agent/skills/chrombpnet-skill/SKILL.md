---
name: chrombpnet-skill
description: Build, validate, run, and troubleshoot ChromBPNet workflows for bias-factorized base-resolution ATAC-seq or DNase-seq modeling. Use when Codex needs ChromBPNet installation, BAM/fragment/tagAlign preprocessing, chromosome splits, GC-matched nonpeaks, bias-model training, full model training or QC, prediction BigWigs, contribution scores, TF-MoDISco-lite motif discovery, marginal footprints, or interpretation of ChromBPNet outputs and failures.
---

# ChromBPNet

## Overview

Use this skill for the `kundajelab/chrombpnet` command-line package and its bias-factorized accessibility workflow. Keep assay bias modeling, the full ChromBPNet model, and the no-bias TF model distinct in commands and output interpretation.

## Follow This Workflow

1. Identify the objective.
- Use `prep splits` to create a train/validation/test chromosome JSON.
- Use `prep nonpeaks` to build GC-matched background regions.
- Use `bias pipeline` to train and evaluate a custom enzyme-bias model.
- Use `pipeline` with a pretrained or custom bias model for end-to-end ChromBPNet training, QC, contribution scoring, motif discovery, and reports.
- Use `train` when the user wants model fitting without the downstream QC and interpretation stages.
- Use `qc`, `bias qc`, `pred_bw`, `contribs_bw`, or `footprints` for an isolated downstream task.

2. Confirm the runtime before preparing a long command.
- Prefer the repository-grounded Python 3.8 conda path because the bundled requirements pin TensorFlow 2.8.0 and NumPy 1.23.4.
- Require an NVIDIA GPU for practical training; verify both `nvidia-smi` and TensorFlow GPU visibility.
- Install `samtools`, `bedtools`, `ucsc-bedgraphtobigwig`, `pybigwig`, and MEME through conda before the Python package.
- Use the Docker image when the host can provide NVIDIA Container Toolkit and sufficient memory.
- Verify the installed CLI with `chrombpnet --help`; the source snapshot contains inconsistent version labels across `setup.py`, `CHANGELOG.md`, and `CITATION.cff`.

3. Validate all coordinate-bearing inputs together.
- Require exactly one of BAM, fragment TSV, or tagAlign.
- Require one assembly-consistent reference FASTA and two-column chromosome sizes file.
- Require peaks and nonpeaks as exactly 10-column narrowPeak-like files. Treat column 10 as a 0-based summit offset and center each example at `start + summit`.
- Require fold JSON keys `train`, `valid`, and `test`; keep chromosome lists nonempty and disjoint.
- Use the same chromosome naming convention in reads, FASTA, chromosome sizes, narrowPeak files, and folds.
- Run `scripts/validate_chrombpnet_inputs.py` before training when local inputs are available.

4. Choose the bias strategy deliberately.
- Prefer a validated pretrained bias model when the assay protocol is compatible.
- Train a custom bias model when protocol bias differs or pretrained-model QC fails.
- Start `--bias-threshold-factor` at `0.5` for ATAC and `0.8` for DNase, then review bias QC rather than treating those values as universal.
- Do not proceed with a bias model that has strongly negative peak count correlation; the pipeline asserts that Pearson correlation is greater than `-0.5`.

5. Choose training depth.
- Use `chrombpnet pipeline` for the standard complete run.
- Use `chrombpnet train` only when downstream QC, marginal footprints, DeepSHAP contribution scores, TF-MoDISco-lite, and the final report will be run separately.
- Keep the defaults `inputlen=2114`, `outputlen=1000`, `filters=512`, `n_dilation_layers=8`, `max_jitter=500`, and `batch_size=64` unless the dataset or hardware justifies changing them.
- Treat the output directory as a new run location. The CLI creates `logs`, `auxiliary`, `models`, and `evaluation` with `exist_ok=False` and fails if those children already exist.

6. Interpret the correct artifact.
- Use `models/chrombpnet.h5` for total predicted accessibility, including the learned bias contribution.
- Use `models/chrombpnet_nobias.h5` as the bias-corrected TF model for regulatory syntax, contribution scores, motifs, and footprints.
- Use `models/bias_model_scaled.h5` as the bias model rescaled during full-model preparation.
- Use `models/bias.h5` as the custom bias-model output from `bias pipeline`.
- Inspect `evaluation/*_metrics.json`, training logs, prediction BigWigs, contribution HDF5/BigWigs, motif reports, and `overall_report.html` together.

7. Preserve provenance.
- Record the ChromBPNet version or commit, container digest when applicable, assembly, FASTA checksum, input-read type, assay, fold JSON, bias-model source, random seed, and full command.
- Keep train/validation/test chromosomes separate across model selection and reporting.
- Report filtered peak/nonpeak counts and any edge filtering caused by the sequence window.

## Grounded CLI Surface

Treat these commands as exposed by the bundled `chrombpnet` parser:

- `chrombpnet pipeline`
- `chrombpnet train`
- `chrombpnet qc`
- `chrombpnet bias pipeline`
- `chrombpnet bias train`
- `chrombpnet bias qc`
- `chrombpnet prep nonpeaks`
- `chrombpnet prep splits`
- `chrombpnet pred_bw`
- `chrombpnet contribs_bw`
- `chrombpnet footprints`
- `print_meme_motif_file`

Do not emit `chrombpnet snp_score` or `chrombpnet modisco_motifs`: their implementation branches remain in the snapshot, but their parser definitions are commented out. Use `modisco motifs` and `modisco report` directly after `contribs_bw` when motif discovery is requested. Do not assume legacy `chrombpnet_*` helper commands from old workflow shell scripts are installed by the current `setup.py`.

## Minimal Training Pattern

Validate and render the command first:

```bash
python skills/chrombpnet-skill/scripts/validate_chrombpnet_inputs.py \
  --mode chrombpnet \
  --assay ATAC \
  --genome /path/to/hg38.fa \
  --chrom-sizes /path/to/hg38.chrom.sizes \
  --peaks /path/to/peaks.narrowPeak \
  --nonpeaks /path/to/nonpeaks.narrowPeak \
  --fold /path/to/fold_0.json \
  --bam /path/to/filtered.bam \
  --bias-model /path/to/bias.h5 \
  --output-dir /path/to/run
```

Run only after reviewing the emitted command and warnings. Never launch a long GPU training job unless the user asked for execution rather than planning or validation.

## Response Style

- State the assay, assembly, read-input format, bias strategy, and execution path before the command.
- Give the smallest runnable stage first, then optional downstream stages.
- Distinguish `chrombpnet.h5`, `chrombpnet_nobias.h5`, `bias_model_scaled.h5`, and `bias.h5` explicitly.
- Call coordinates 0-based half-open and summit values 0-based offsets.
- Surface version conflicts, missing system tools, and existing output subdirectories early.
- Route generic BPNet requests without ChromBPNet or enzyme-bias context to the separate BPNet skill when available.

## References

- Read [references/setup-and-inputs.md](references/setup-and-inputs.md) for installation, runtime checks, input formats, and preprocessing commands.
- Read [references/training-and-qc.md](references/training-and-qc.md) for bias/full-model commands, defaults, outputs, and QC interpretation.
- Read [references/prediction-and-interpretation.md](references/prediction-and-interpretation.md) for prediction BigWigs, contribution scores, motif discovery, and footprints.

## Scripts

- Run `scripts/validate_chrombpnet_inputs.py` to statically validate a training input bundle, detect output collisions, inspect required executables, and emit the corresponding official `chrombpnet` command as JSON.

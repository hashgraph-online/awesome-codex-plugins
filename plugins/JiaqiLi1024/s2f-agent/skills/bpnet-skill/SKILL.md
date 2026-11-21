---
name: bpnet-skill
description: Use Kundaje Lab BPNet 2.x workflows for base-resolution transcription-factor binding models, including legacy environment setup, ChIP-seq or ChIP-nexus preprocessing, `input_data.json`/`bpnet_params.json`/`splits.json` validation, model training, prediction, DeepSHAP attribution, TF-MoDISco motif discovery, and Fi-NeMo hit calling. Use when Codex needs to write, run, debug, explain, or review `bpnet-train`, `bpnet-predict`, `bpnet-shap`, `bpnet-counts-loss-weight`, `bpnet-outliers`, `bpnet-gc-reference`, `bpnet-gc-background`, BPNet JSON configuration, prediction bigWigs, contribution-score HDF5 files, or BPNet-derived motif workflows.
---

# BPNet Workflows

## Use The Grounded Path

Treat the bundled `Readme/bpnet-master` checkout as BPNet 2.0.0, not as the original paper repository or ChromBPNet. Inspect the user's installed `bpnet --help` surface or checkout when it differs from this snapshot; do not silently translate commands from another BPNet implementation.

1. Identify the requested stage: setup, preprocessing, config validation, training, prediction, SHAP attribution, motif discovery, or hit calling.
2. Confirm the runtime before proposing execution. Prefer the upstream-pinned Python 3.7 and TensorFlow 2.4.1 environment or the documented Docker image. Treat newer Python/TensorFlow combinations as unverified ports.
3. Confirm the assay, genome assembly, reference FASTA, chromosome sizes, strandedness, task count, peak files, signal bigWigs, and optional control bigWigs.
4. Validate configuration files before GPU work:

```bash
python skills/bpnet-skill/scripts/validate_bpnet_inputs.py \
  --input-data input_data.json \
  --model-params bpnet_params.json \
  --splits splits.json \
  --chrom-sizes hg38.chrom.sizes \
  --reference-genome hg38.genome.fa \
  --command train \
  --check-paths
```

5. Create output directories explicitly before calling train, predict, or SHAP unless using that command's timestamped-output option.
6. Start with a small chromosome or region subset. Scale only after the environment, schemas, sequence lengths, output lengths, and generated artifacts pass inspection.
7. Record the exact command, package version, genome build, split, model path, and output paths in the result.

## Respect These Boundaries

- Use only the console scripts exposed by `setup.py`: `bpnet-train`, `bpnet-predict`, `bpnet-shap`, `bpnet-counts-loss-weight`, `bpnet-outliers`, `bpnet-gc-reference`, and `bpnet-gc-background`.
- Do not claim that `bpnet-motif` or `bpnet-embeddings` is installed; both entry points are commented out in BPNet 2.0.0.
- Always include `bias.source` and `bias.smoothing` for every task, even with no controls. Use two empty lists when bias is absent; generator code indexes both keys despite README language calling bias optional.
- Keep top-level task IDs and split IDs contiguous string integers starting at `"0"`; BPNet iterates `range(n)` and indexes those keys.
- Use ENCODE narrowPeak BED6+4 input for loci. Its summit column is an offset from the interval start.
- Keep `bpnet_params.json` `input_len` and `output_profile_len` aligned with CLI `--input-seq-len` and `--output-len`.
- For `bpnet-predict`, keep `--output-window-size <= --output-len` and restrict the current implementation to one or two total signal tracks.
- For `bpnet-shap`, use `--output-directory`, not the outdated README spelling `--output-dir`. Use at most one of `--chroms` and `--sample`; provide `--chrom-sizes` when exporting SHAP bigWigs.
- Run TF-MoDISco and Fi-NeMo as separate external tools after SHAP generation.

## Choose The Reference

- Read [references/setup.md](references/setup.md) for Docker, local installation, version constraints, and external tools.
- Read [references/input-configs.md](references/input-configs.md) when preparing or debugging input data, architecture parameters, splits, peaks, controls, outliers, or GC-matched background.
- Read [references/cli-workflows.md](references/cli-workflows.md) for grounded train, predict, and SHAP commands plus expected artifacts.
- Read [references/motif-workflows.md](references/motif-workflows.md) only after contribution scores exist and the request involves TF-MoDISco or Fi-NeMo.
- Read [references/troubleshooting.md](references/troubleshooting.md) for source-grounded incompatibilities and common failure checks.

## Return Actionable Results

Provide the smallest runnable command block for the requested stage. State assumptions and unresolved inputs before the command. For executed work, report validation status and concrete artifact paths; for planned work, distinguish source-grounded defaults from user-selected parameters.

---
name: alphagenome-api
description: Build and debug AlphaGenome Python API workflows for variant-effect and track-prediction tasks, including API key setup, package installation, `dna_client` creation, selecting `requested_outputs`, adding `ontology_terms`, plotting results, and troubleshooting environment or response issues. Use when Codex needs to write, fix, explain, or review code and notebooks that use `alphagenome`, `dna_client`, `genome.Interval`, `genome.Variant`, `predict_variant`, `predict_interval`, AlphaGenome plotting helpers, or AlphaGenome API prediction workflows.
---

# AlphaGenome API

## Overview

Use this skill to produce conservative AlphaGenome Python snippets and notebook cells. Prefer the smallest runnable example that satisfies the request, and verify any symbol not grounded by the bundled references before relying on it.

## Follow This Workflow

1. Confirm setup.
- Confirm whether the user already has an AlphaGenome API key.
- Confirm the active Python version is `>=3.10` before installing `alphagenome`.
- Prefer a virtual environment before installing packages.
- Keep API credentials out of code and logs; prefer `ALPHAGENOME_API_KEY` from environment variables.
- Use the install flow in [references/quickstart.md](references/quickstart.md).

2. Build the client.
- Import `genome` from `alphagenome.data` and `dna_client` from `alphagenome.models`.
- Prefer resolving a valid conda env prefix first (`conda run -p <prefix>`); fall back to env name (`conda run -n alphagenome-py310`) only when no usable prefix is found.
- Create the client with `dna_client.create(API_KEY, timeout=...)` to avoid indefinite hangs.
- If `dna_client.create(...)` times out (`grpc.FutureTimeoutError`), retry with local proxy variables:
  - `grpc_proxy=http://127.0.0.1:7890`
  - `http_proxy=http://127.0.0.1:7890`
  - `https_proxy=http://127.0.0.1:7890`

3. Choose the prediction path.
- Use `genome.Variant` plus `model.predict_variant(...)` when the task compares reference and alternate alleles.
- Use `model.predict_interval(...)` for interval-only track prediction requests.
- For `model.predict_variant(...)`, use a supported interval width (currently `16384`, `131072`, `524288`, or `1048576` bp), then verify this list against the installed package when needed.
- For `model.predict_interval(...)`, keep each requested inference interval at supported widths and within 1,000,000 bp.
- Keep each interval at or below 1,000,000 base pairs.

4. Limit the request.
- Request only the output modalities the user needs.
- Add `ontology_terms` only when the selected assay depends on tissue or anatomical context.
- Surface every assumption about tissues, cell types, coordinates, and output types.

5. Present the result.
- Return a short runnable snippet first.
- Add plotting only when the user asks to inspect predictions or compare reference and alternate tracks.
- For real runs, persist a machine-readable summary (status, coordinates, REF/ALT, output paths, error if any) so agent retries are auditable.
- Use [references/workflows.md](references/workflows.md) for code patterns and [references/caveats.md](references/caveats.md) for limits and troubleshooting.

## Grounded API Surface

Treat the following names as grounded by the bundled AlphaGenome README:

- `genome.Interval`
- `genome.Variant`
- `dna_client.create`
- `model.predict_interval`
- `model.predict_variant`
- `dna_client.OutputType.RNA_SEQ`
- `plot_components.plot`
- `plot_components.OverlaidTracks`
- `plot_components.VariantAnnotation`

Verify any other method, output enum, or helper against the installed package or official docs before using it. Do not invent modality names or helper functions.

## Response Style

- Prefer code the user can run immediately.
- Explain genomic assumptions in plain language.
- Call out when you are inferring a coordinate window, assay, or ontology term.
- Push back on large-batch workloads that exceed the README guidance.
- Redact secrets in examples and transcripts; never echo API keys.

## Track Prediction (BED / Single Interval)

Use `scripts/run_alphagenome_track_prediction_bed_batch.py` for real `predict_interval` workflows.

**Input modes:**
- `--bed`: run interval track prediction for every BED row (BED uses 0-based half-open intervals)
- `--interval chr:start-end`: run one interval with the same output schema

**Key behaviours:**
- Supports `--species human|mouse` and maps to AlphaGenome organism enums
- Uses `model.predict_interval(...)` directly
- Supports head selection via `--output-head` (default `RNA_SEQ`)
- Supports ontology context via repeatable `--ontology-term` (default `UBERON:0001157`)
- Auto-selects nearest supported inference width (`16384/131072/524288/1048576`) unless `--interval-width` is given
- Crops back to requested interval before saving outputs
- Retries client create with proxy env vars if first attempt times out

**Output contract (per interval):**
- `*_result.json`
- `*_trackplot.png`
- `*_track_prediction.npz`
- batch/summary file: `*_bed_batch_summary.json`

**Invocation (BED batch):**
```bash
python skills/alphagenome-api/scripts/run_alphagenome_track_prediction_bed_batch.py \
  --bed case-study-playbooks/track_prediction/bed/Test.interval.bed \
  --species human \
  --assembly hg38 \
  --output-head RNA_SEQ \
  --ontology-term UBERON:0001157 \
  --output-dir case-study-playbooks/track_prediction/alphagenome_results
```

**Invocation (single interval):**
```bash
python skills/alphagenome-api/scripts/run_alphagenome_track_prediction_bed_batch.py \
  --interval chr19:6700000-6732768 \
  --species human \
  --assembly hg38 \
  --output-head RNA_SEQ \
  --output-dir output/alphagenome_track
```

## Batch VCF Prediction

Use `scripts/run_alphagenome_vcf_batch.py` for multi-variant, multi-tissue batch prediction from a standard VCF file.

**Key behaviours:**
- Accepts any standard VCF (CHROM with or without `chr` prefix; POS is 1-based)
- Supports SNP, INS, DEL, and MNP; multi-allelic ALT uses the first allele
- Transparently passes through all VCF INFO fields as output columns (two-pass collection)
- Adds `variant_type` column (SNP / INS / DEL / MNP)
- Outputs per-tissue `{tissue}_mean_diff` and `{tissue}_log2fc` for all 8 tissues in `TISSUE_DICT`
- `--non-interactive` now always uses default 8 tissues without prompting
- Automatically retries once with proxy vars when `dna_client.create` times out (`grpc_proxy/http_proxy/https_proxy`)
- Supports `--resume` (skip already-completed variants), `--limit N` (debug subset), `--interval-width` (16384 / 131072 / 524288 / 1048576)

**Invocation:**
```bash
python skills/alphagenome-api/scripts/run_alphagenome_vcf_batch.py \
  --input path/to/variants.vcf \
  --assembly hg38 \
  --output-dir output/alphagenome \
  [--tissues path/to/tissues.json]  # or inline JSON, or omit for interactive prompt
  [--non-interactive]               # no prompt, force default 8 tissues
  [--proxy-url http://127.0.0.1:7890]  # retry proxy for client-create timeout
  [--interval-width 16384]          # 16384 / 131072 / 524288 / 1048576
  [--limit 10] \
  [--resume]
```

**Tissue config format** (`--tissues`):
```json
{
  "Neuronal_stem_cell": "CL:0000047",
  "Whole_Blood": "UBERON:0013756"
}
```
Omit `--tissues` to get an interactive prompt listing defaults; user can confirm or supply a JSON path.
Set `--proxy-url ''` to disable automatic proxy retry.

**Output columns:** `vid, chrom, position, ref, alt, variant_type, assembly, interval_start, interval_end` + all INFO keys (sorted) + `{tissue}_mean_diff / {tissue}_log2fc` × 8 tissues + `status, error, run_time_utc`

## References

- Read [references/quickstart.md](references/quickstart.md) for installation and minimal setup.
- Read [references/workflows.md](references/workflows.md) for variant analysis patterns, plotting, and parameter selection.
- Read [references/caveats.md](references/caveats.md) for limits, licensing, and troubleshooting.

---
name: segment-nt
description: Use SegmentNT, SegmentEnformer, and SegmentBorzoi for JAX-based genomic segmentation at nucleotide resolution, including model-family selection, `pmap` inference setup, SegmentNT Yarn rescaling, feature-probability extraction, and sequence/token-length troubleshooting. Use when Codex needs to write, fix, explain, or review code or notebooks involving `get_pretrained_segment_nt_model`, `get_pretrained_segment_enformer_model`, `get_pretrained_segment_borzoi_model`, `rescaling_factor`, `hk.transform_with_state`, segmentation logits, or sequence constraints for nucleotide-resolution annotation.
---

# SegmentNT Family

## Overview

Use this skill for segmentation models built around the NT ecosystem. Prefer the family-specific inference path shown in the local docs and notebooks.

## Follow This Decision Flow

1. Choose the segmentation family.
- Use `SegmentNT` for NT-backbone segmentation on sequences up to 30 kb, with documented generalization to 50 kb.
- Use `SegmentEnformer` when you want the Enformer backbone workflow shown at `196_608` bp.
- Use `SegmentBorzoi` when you want the Borzoi backbone workflow shown at `524_288` bp.

2. Set up the grounded JAX inference pattern.
- Initialize JAX device selection explicitly.
- Load the pretrained model with the matching helper function.
- For SegmentNT, use `hk.transform(...)`.
- For SegmentEnformer and SegmentBorzoi, use `hk.transform_with_state(...)`.
- Replicate parameters/keys (and state for transform-with-state models) across devices when using `jax.pmap(...)`.

3. Handle family-specific constraints.
- `SegmentNT` does not handle any `N` in the sequence.
- SegmentNT tokenizer uses 6-mers with a prepended CLS token.
- Use the same token-count naming as `$nucleotide-transformer`:
  - `num_tokens_inference`: includes CLS.
  - `num_dna_tokens_excluding_cls`: excludes CLS.
- For no-`N` inputs, compute tokens exactly with:
  - `num_dna_tokens_excluding_cls = floor(bp / 6) + (bp % 6)`
  - `num_tokens_inference = num_dna_tokens_excluding_cls + 1`
- For SegmentNT, `num_dna_tokens_excluding_cls` must be divisible by 4.
- Practical input-length shortcut: choose `bp % 24 == 0` to satisfy divisibility cleanly.
- For `SegmentNT` inference above 30 kb, compute the rescaling factor with [scripts/compute_rescaling_factor.py](scripts/compute_rescaling_factor.py).
- The practical docs formula is `rescaling_factor = num_tokens_inference / 2048`, where inference token count includes CLS.

4. Read outputs correctly.
- Convert logits to probabilities with `jax.nn.softmax(..., axis=-1)[..., -1]`.
- For `SegmentNT`, use `config.features`.
- `segment_nt_multi_species` is a checkpoint family choice, not a runtime species token input.
- Do not assume output length always equals input bp length; align coordinates from returned tensor length.
- For `SegmentEnformer` and `SegmentBorzoi`, use `FEATURES`.
- For `hk.transform_with_state(...)` paths, handle `(outs, state)` returned by apply.

5. Prefer the reusable interval script for real-region runs.
- For UCSC interval fetch + SegmentNT inference + track plotting, use [scripts/run_segment_nt_region.py](scripts/run_segment_nt_region.py).

6. For s2f track-prediction case-study runs, prefer BED batch wrappers.
- Use `case-study-playbooks/track_prediction/run_segment_nt_track_case.sh` for batch execution.
- Default output root should be `case-study-playbooks/track_prediction/<run_id>/segmentnt_results`.
- Treat `segmentnt_bed_batch_summary.json` as the batch execution contract, with per-interval artifacts (`*_trackplot.png`, `*_result.json`, `*_probs.npz`, interval logs).

## Grounded API Surface

Treat the following names and patterns as grounded by the bundled docs:

- `from nucleotide_transformer.pretrained import get_pretrained_segment_nt_model`
- `from nucleotide_transformer.enformer.pretrained import get_pretrained_segment_enformer_model`
- `from nucleotide_transformer.borzoi.pretrained import get_pretrained_segment_borzoi_model`
- `rescaling_factor=...`
- `tokenizer.batch_tokenize(...)`
- `hk.transform(...)`
- `hk.transform_with_state(...)`
- `jax.pmap(...)`
- `jax.nn.softmax(...)`
- `config.features`
- `FEATURES.index(...)`
- `outs["logits"]`

Grounded SegmentNT model names:

- `segment_nt`
- `segment_nt_multi_species`

Do not invent alternate segmentation wrappers or hidden post-processing functions unless the user provides another grounded source.

## Response Style

- Choose the family before writing code.
- Call out `N` handling and length assumptions early for SegmentNT.
- Make the tokenization difference explicit: SegmentNT uses 6-mer style tokenization, while SegmentEnformer/Borzoi workflows use 1-mer tokenization.
- Keep probability extraction examples explicit and runnable.

## References

- Read [references/family-selection.md](references/family-selection.md) for model-family choice.
- Read [references/inference-patterns.md](references/inference-patterns.md) for grounded code snippets.
- Read [references/constraints.md](references/constraints.md) for `N` handling, rescaling, and token divisibility.
- Read [references/setup-and-troubleshooting.md](references/setup-and-troubleshooting.md) for setup, cache, and device/runtime failures.
- Use [scripts/compute_rescaling_factor.py](scripts/compute_rescaling_factor.py) when SegmentNT runs exceed the training length.
- Use [scripts/run_segment_nt_region.py](scripts/run_segment_nt_region.py) for real genomic-interval prediction and plotting.

---
name: sei-workflows
description: Use the Sei Selene workflows for 21,907 chromatin-profile predictions, 40 sequence-class scores, and nucleosome-adjusted variant effects from BED, FASTA, or VCF inputs. Use when Codex needs Sei setup, `1_*` prediction scripts, `2_*` score scripts, HDF5/NPY/TSV outputs, or hg19/hg38 troubleshooting; do not use for generic sequence classification.
---

# Sei Workflows

## Grounded workflow

1. Use the Sei repository with Python 3.6+, PyTorch, Selene >=0.5.0, and `docopt`. Run `download_data.sh` first so the trained model and `resources` FASTA files exist. Prediction is intended for a GPU node.
2. For sequence prediction, use a BED or FASTA input and the documented script:

```bash
sh 1_sequence_prediction.sh input.bed hg19 output_dir --cuda
```

FASTA inputs can use either build label for logging; BED inputs require `hg19` or `hg38` so the bundled UCSC FASTA can be used.
3. For VCF variant effects, run `1_variant_effect_prediction.sh variants.vcf hg19 output_dir --cuda`. Both prediction paths write HDF5 files under `chromatin-profiles-hdf5`.
4. Post-process the HDF5 predictions with `2_raw_sc_score.py` for sequence-only projection scores or `2_varianteffect_sc_score.py ref.h5 alt.h5 output_dir`. The latter computes alt-ref sequence-class scores with histone/nucleosome normalization and writes NPY plus sorted TSVs unless `--no-tsv` is used.
5. Match rows to the generated `*_row_labels.txt` and columns to `model/target.names` / `model/seqclass.names`; never infer ordering from a sorted TSV.

## Hard boundaries

- Sei's primary output is 21,907 chromatin profiles and a 40-class projection, not a single scalar activity score.
- The variant workflow is a two-stage ref/alt computation. Do not call the raw sequence score script on variant-effect files or treat raw scores as nucleosome-adjusted effects.
- The repository's training path uses Selene and multi-GPU hardware; only propose training when the user has training data and appropriate GPUs.
- Keep hg19/hg38 explicit and preserve the VCF/reference coordinate assumptions.

## References

- Read [references/cli-and-outputs.md](references/cli-and-outputs.md) for setup, script arguments, output names, score semantics, and training caveats.

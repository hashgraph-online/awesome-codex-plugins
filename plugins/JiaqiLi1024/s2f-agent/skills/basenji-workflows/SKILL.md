---
name: basenji-workflows
description: Use the Basenji TensorFlow workflows for sequential regulatory activity prediction, training, BigWig export, SAD/SED variant scoring, saturated mutagenesis, and motif analysis. Use when Codex needs Basenji's `basenji_*` commands, params JSON, model files, HDF5/FASTA data, VCF analysis, or legacy environment setup; do not route Akita, Saluki, or Borzoi commands from the same checkout here unless the user names Basenji.
---

# Basenji Workflows

## Choose the Basenji stage

1. Treat `Readme/basenji-master` as the source of truth. It is an older TensorFlow codebase containing Basenji plus separate Akita, Saluki, and Borzoi programs; select the executable by the named model and objective.
2. Set up the documented conda/pip environment, install TensorFlow separately, install the checkout with `python setup.py develop`, and export `BASENJIDIR`, `PATH`, and `PYTHONPATH` as needed. Read [references/cli-workflows.md](references/cli-workflows.md) before proposing a full run.
3. Use the smallest grounded entry point:
   - `basenji_train.py params.json data_dir ...` for training.
   - `basenji_predict.py params.json model_file data_dir` for predictions; add `-b` and a genome-size file only when BigWig tracks are required.
   - `basenji_sad.py params.json model_file variants.vcf` for SNP Activity Difference.
   - `basenji_sed.py params.json model_file variants.vcf tss.bed` for SNP Expression Difference.
   - `basenji_sat_vcf.py params.json model_file variants.vcf` for VCF-centered saturated mutagenesis.
   - `basenji_motifs.py params.json model_file data_dir` or `basenji_sat.py`/`basenji_map.py` for interpretation.
4. Keep the parameter file, TensorFlow Saver/checkpoint, target metadata, genome FASTA, and data format explicit. Start with a small data or chromosome subset and verify `preds.h5`, normalization, tracks, or score files before scaling.

## Hard boundaries

- Basenji predicts quantitative binned activity along long sequences; it is not BPNet's base-resolution profile model.
- SAD expects a bi-allelic VCF; SED additionally needs a TSS BED. Do not omit these assets or silently substitute a different variant-score definition.
- `params_file`, `model_file`, and data/VCF arguments are positional in the upstream scripts. Preserve option names such as `--rc`, `--shifts`, `-t`, and `-o` from the actual script.
- The checkout is active research code with legacy TensorFlow assumptions. State the tested Python/TensorFlow environment and avoid claiming modern package compatibility without a local check.

## References

- Read [references/cli-workflows.md](references/cli-workflows.md) for grounded commands, required files, outputs, and Basenji-vs-Akita/Saluki routing.

# Prediction And Interpretation

## Contents

- Prediction BigWigs
- Contribution scores
- TF-MoDISco-lite
- Marginal footprints
- Interpretation rules
- Unsupported surfaces

## Prediction BigWigs

Select at least one model:

```bash
chrombpnet pred_bw \
  --chrombpnet-model /path/to/chrombpnet.h5 \
  --chrombpnet-model-nb /path/to/chrombpnet_nobias.h5 \
  --regions /path/to/regions.narrowPeak \
  --genome /path/to/genome.fa \
  --chrom-sizes /path/to/genome.chrom.sizes \
  --output-prefix /path/to/predictions/sample
```

Add `--bias-model /path/to/bias.h5` to predict bias alone. Add `--bigwig observed.bw` to emit prediction HDF5 and metrics against observed signal. Use `--debug-chr chr1` for a small diagnostic run.

Depending on selected models, expect suffixes such as:

- `_chrombpnet.bw`
- `_chrombpnet_nobias.bw`
- `_bias.bw`
- corresponding `*_preds.bed`
- optional `*_predictions.h5` and `*_metrics.json`

Use 10-column regions and interpret the summit as the center. Do not treat overlapping-window BigWig values as independent examples.

## Contribution Scores

Run DeepSHAP contribution scoring with the no-bias TF model for regulatory syntax:

```bash
chrombpnet contribs_bw \
  --model-h5 /path/to/chrombpnet_nobias.h5 \
  --regions /path/to/regions.narrowPeak \
  --genome /path/to/genome.fa \
  --chrom-sizes /path/to/genome.chrom.sizes \
  --profile-or-counts profile counts \
  --output-prefix /path/to/contribs/sample
```

The command writes `.profile_scores.h5` and/or `.counts_scores.h5`, an `.interpreted_regions.bed`, and corresponding contribution BigWigs. Prefer profile scores for base-resolution motif syntax; use counts scores when total accessibility contribution is the biological target.

## TF-MoDISco-Lite

The current `chrombpnet` parser does not expose `modisco_motifs`. Run modisco-lite directly on contribution HDF5:

```bash
modisco motifs \
  -i /path/to/sample.profile_scores.h5 \
  -n 50000 \
  -o /path/to/modisco_results_profile_scores.h5 \
  -w 500

print_meme_motif_file > /path/to/chrombpnet_motifs.meme

modisco report \
  -i /path/to/modisco_results_profile_scores.h5 \
  -o /path/to/modisco_report \
  -m /path/to/chrombpnet_motifs.meme
```

Use a task-appropriate seqlet cap and window rather than assuming the pipeline's `50000` and `500` fit every dataset. Record the score type, model, region set, modisco-lite version, motif database, and parameters.

## Marginal Footprints

Provide a two-column tab-separated motif file containing motif name and DNA sequence:

```text
CTCF\tCCACCAGGGGGCGCTA
```

Run footprints against background regions and the no-bias model:

```bash
chrombpnet footprints \
  --model-h5 /path/to/chrombpnet_nobias.h5 \
  --regions /path/to/nonpeaks.narrowPeak \
  --genome /path/to/genome.fa \
  --chr-fold-path /path/to/fold_0.json \
  --motifs-to-pwm /path/to/motif_to_pwm.tsv \
  --output-prefix /path/to/footprints/sample
```

The CLI parser declares `--ylim` as a Python tuple type, which is awkward from a shell. Prefer automatic limits unless the installed version documents a reliable syntax.

## Interpretation Rules

- Attribute TF syntax using `chrombpnet_nobias.h5`, not the total model, unless the question explicitly concerns total predicted accessibility.
- Compare bias-model motifs with no-bias TF-model motifs to detect residual enzyme preference.
- Treat DeepSHAP scores as model attributions, not causal biochemical measurements.
- Treat marginal footprints as model-derived aggregate predictions, not direct cleavage observations.
- Keep profile and counts contribution tracks separate.
- Use held-out chromosomes or independent data for claims about predictive performance.
- Preserve strand and reverse-complement handling when extracting motif instances.

## Unsupported Surfaces

Do not generate `chrombpnet snp_score`: the parser block is commented out even though an unreachable dispatch branch remains. For regulatory variants, use a separately verified method or implement an explicitly reviewed REF/ALT sequence comparison against installed model APIs; label it as custom analysis rather than an official ChromBPNet CLI command.

Do not assume legacy workflow entry points such as `chrombpnet_makebigwig`, `chrombpnet_hyperparams`, or `chrombpnet_train` exist. The current snapshot's `setup.py` exposes only `chrombpnet` and `print_meme_motif_file` as console scripts.

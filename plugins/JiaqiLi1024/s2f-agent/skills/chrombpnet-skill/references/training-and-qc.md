# Training And QC

## Contents

- Bias model
- Full model
- Train versus pipeline
- Output contract
- QC checks
- Failure triage

## Bias Model

Train and evaluate a custom bias model with the end-to-end command:

```bash
chrombpnet bias pipeline \
  --input-bam-file /path/to/filtered.bam \
  --data-type ATAC \
  --genome /path/to/genome.fa \
  --chrom-sizes /path/to/genome.chrom.sizes \
  --peaks /path/to/peaks.narrowPeak \
  --nonpeaks /path/to/nonpeaks.narrowPeak \
  --chr-fold-path /path/to/fold_0.json \
  --bias-threshold-factor 0.5 \
  --output-dir /path/to/bias_run
```

Use `0.5` as an ATAC starting value and `0.8` as a DNase starting value. Reassess the threshold using bias metrics and the number of retained training regions. Use `chrombpnet bias train` to stop after training and `chrombpnet bias qc` to evaluate an existing bias model.

The bias defaults are `filters=128`, `n_dilation_layers=4`, `max_jitter=0`, and `batch_size=64`. The resulting model is `models/bias.h5`.

## Full Model

Train and evaluate a bias-factorized model:

```bash
chrombpnet pipeline \
  --input-bam-file /path/to/filtered.bam \
  --data-type ATAC \
  --genome /path/to/genome.fa \
  --chrom-sizes /path/to/genome.chrom.sizes \
  --peaks /path/to/peaks.narrowPeak \
  --nonpeaks /path/to/nonpeaks.narrowPeak \
  --chr-fold-path /path/to/fold_0.json \
  --bias-model-path /path/to/bias.h5 \
  --output-dir /path/to/chrombpnet_run
```

Replace `--input-bam-file` with exactly one of `--input-fragment-file` or `--input-tagalign-file` when appropriate. The full-model defaults are:

| Parameter | Default |
|---|---:|
| `--inputlen` | 2114 |
| `--outputlen` | 1000 |
| `--negative-sampling-ratio` | 0.1 |
| `--filters` | 512 |
| `--n-dilation-layers` | 8 |
| `--max-jitter` | 500 |
| `--batch-size` | 64 |
| `--epochs` | 50 |
| `--early-stop` | 5 |
| `--learning-rate` | 0.001 |
| `--seed` | 1234 |

Change batch size for memory pressure before changing the model architecture. Keep input and output lengths even; verify any nondefault length against model cropping and edge filtering.

## Train Versus Pipeline

Both commands run preprocessing, bias scaling, hyperparameter derivation, and model fitting. `chrombpnet train` returns after fitting and report generation. `chrombpnet pipeline` continues with test predictions, marginal footprints, contribution scoring on up to 30,000 peaks, TF-MoDISco-lite, and final reports.

Use the isolated QC command only with all required models and original data assets:

```bash
chrombpnet qc \
  --bigwig /path/to/observed_unstranded.bw \
  --chrombpnet-model /path/to/chrombpnet.h5 \
  --chrombpnet-model-nb /path/to/chrombpnet_nobias.h5 \
  --genome /path/to/genome.fa \
  --chrom-sizes /path/to/genome.chrom.sizes \
  --peaks /path/to/peaks.narrowPeak \
  --nonpeaks /path/to/nonpeaks.narrowPeak \
  --chr-fold-path /path/to/fold_0.json \
  --data-type ATAC \
  --output-dir /path/to/qc_run
```

## Output Contract

Expect these top-level directories:

- `models/`: trained and scaled HDF5 models.
- `logs/`: epoch/batch logs, arguments, and model/data parameter TSV files.
- `auxiliary/`: shifted BigWig, filtered regions, interpretation subsets, and intermediate HDF5 files.
- `evaluation/`: metrics, plots, motif reports, footprints, and overall HTML/PDF reports.

Key full-model artifacts:

- `models/chrombpnet.h5`: total accessibility model with bias contribution.
- `models/chrombpnet_nobias.h5`: bias-corrected TF model.
- `models/bias_model_scaled.h5`: input bias model rescaled to the dataset.
- `evaluation/chrombpnet_metrics.json`: test-set metrics.
- `evaluation/overall_report.html` and commonly `overall_report.pdf`: consolidated report.

Key bias artifacts:

- `models/bias.h5`: trained bias model.
- `evaluation/bias_metrics.json`: counts/profile evaluation.
- `evaluation/pwm_from_input.png`: shift and enzyme-bias diagnostic.

Use actual directory contents as the run source of truth. Older workflow scripts in the snapshot use `chrombpnet_wo_bias.h5`, while the current pipeline code and README use `chrombpnet_nobias.h5`.

## QC Checks

- Confirm the shifted BigWig and PWM match the expected Tn5 or DNase-I pattern.
- Confirm sufficient peaks and nonpeaks remain after edge and count-outlier filtering.
- Review training and validation losses for divergence or premature early stopping.
- Review counts Pearson/Spearman metrics and profile Jensen-Shannon divergence on held-out chromosomes.
- Reject or retrain a bias model when peak counts correlation is strongly negative; the full pipeline enforces Pearson `> -0.5`.
- Inspect bias-only and no-bias motifs to ensure enzyme sequence preference is concentrated in the bias model rather than the TF model.
- Compare replicate or fold-level results before interpreting a single motif or footprint biologically.

## Failure Triage

- `FileExistsError`: choose a new output directory or move prior `logs`, `auxiliary`, `models`, and `evaluation` children aside explicitly.
- Missing chromosomes or empty generators: reconcile `chr` prefixes and fold membership across all inputs.
- Excessive edge filtering: inspect contig sizes, summit offsets, and `inputlen`.
- Shift inconsistency: verify whether upstream preprocessing already shifted reads and avoid double shifting.
- CUDA or TensorFlow import errors: restore the pinned Python/TensorFlow environment before changing model code.
- TF-MoDISco/report failure after successful training: preserve trained models and logs, then rerun downstream interpretation separately rather than retraining immediately.

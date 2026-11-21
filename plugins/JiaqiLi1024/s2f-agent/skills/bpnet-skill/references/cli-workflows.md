# Train, Predict, And SHAP

Use these templates only after validating configs and creating output directories.

## Train

```bash
mkdir -p models
bpnet-train \
  --input-data input_data.json \
  --output-dir models \
  --reference-genome hg38.genome.fa \
  --chroms chr1 chr2 chr3 chr4 chr5 chr6 chr7 chr8 chr9 chr10 chr11 chr12 chr13 chr14 chr15 chr16 chr17 chr18 chr19 chr20 chr21 chr22 chrX chrY \
  --chrom-sizes hg38.chrom.sizes \
  --splits splits.json \
  --model-arch-name BPNet \
  --model-arch-params-json bpnet_params.json \
  --sequence-generator-name BPNet \
  --model-output-filename model \
  --input-seq-len 2114 \
  --output-len 1000 \
  --shuffle \
  --threads 10 \
  --epochs 100 \
  --batch-size 64 \
  --reverse-complement-augmentation \
  --early-stopping-patience 10 \
  --reduce-lr-on-plateau-patience 5 \
  --learning-rate 0.001
```

Treat chromosome lists as dataset decisions. Do not reuse the example split without checking leakage, sex chromosomes, alternate contigs, and the reference build. A model path typically includes a split suffix such as `models/model_split000`.

## Predict

```bash
mkdir -p predictions_and_metrics
bpnet-predict \
  --model models/model_split000 \
  --chrom-sizes hg38.chrom.sizes \
  --chroms chr7 chr13 chr17 chr19 chr21 chrX \
  --test-indices-file None \
  --reference-genome hg38.genome.fa \
  --output-dir predictions_and_metrics \
  --input-data input_data.json \
  --sequence-generator-name BPNet \
  --input-seq-len 2114 \
  --output-len 1000 \
  --output-window-size 1000 \
  --batch-size 64 \
  --reverse-complement-average \
  --threads 2 \
  --generate-predicted-profile-bigWigs
```

Expected outputs include:

- `<model-tag>_predictions.h5` with `coords` and `predictions` groups
- `<model-tag>_predictions_track_<i>.bw` and stats files when bigWig export is enabled
- true/predicted log-count arrays and metric arrays/text summaries
- `config.json`

The current source asserts `1 <= total_signal_tracks <= 2` during prediction. It also pads examples internally for batching and deduplicates output coordinates.

## SHAP Attribution

The README example uses `--output-dir`, but the shipped parser requires `--output-directory`:

```bash
mkdir -p shap
bpnet-shap \
  --reference-genome hg38.genome.fa \
  --model models/model_split000 \
  --bed-file data/peaks_inliers.bed \
  --output-directory shap \
  --input-seq-len 2114 \
  --control-len 1000 \
  --task-id 0 \
  --input-data input_data.json \
  --chrom-sizes hg38.chrom.sizes \
  --generate-shap-bigWigs
```

Use `--chroms chr1 ...` or `--sample N`, never both. Expected outputs include:

- `counts_scores.h5`
- `profile_scores.h5`
- `peaks_valid_scores.bed`
- `counts_scores.bw` and `profile_scores.bw` when bigWig generation succeeds

Match `--control-len` to the model's bias-profile input length, normally the output profile length in the upstream example. SHAP disables TensorFlow eager execution and can be memory intensive; start with `--sample` or one chromosome.

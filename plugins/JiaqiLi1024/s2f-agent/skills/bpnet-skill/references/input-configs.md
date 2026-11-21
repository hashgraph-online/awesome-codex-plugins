# Input And Configuration

Use this reference for preprocessing and the three JSON files consumed by BPNet training.

## Signal And Peak Inputs

Generate 5-prime strand-specific signal tracks from aligned reads when the assay requires stranded profiles:

```bash
samtools merge -f merged.bam rep1.bam rep2.bam
samtools index merged.bam
bedtools genomecov -5 -bg -strand + -g hg38.chrom.sizes -ibam merged.bam \
  | sort -k1,1 -k2,2n > plus.bedGraph
bedtools genomecov -5 -bg -strand - -g hg38.chrom.sizes -ibam merged.bam \
  | sort -k1,1 -k2,2n > minus.bedGraph
bedGraphToBigWig plus.bedGraph hg38.chrom.sizes plus.bw
bedGraphToBigWig minus.bedGraph hg38.chrom.sizes minus.bw
```

Use ENCODE narrowPeak BED6+4 loci. BPNet computes the modeled center as `chromStart + peak`, where `peak` is column 10's 0-based summit offset.

## `input_data.json`

Use contiguous string task IDs beginning at `"0"`:

```json
{
  "0": {
    "signal": {"source": ["data/plus.bw", "data/minus.bw"]},
    "loci": {"source": ["data/peaks_inliers.bed"]},
    "background_loci": {
      "source": ["data/gc_negatives.bed"],
      "ratio": [0.33]
    },
    "bias": {
      "source": ["data/control_plus.bw", "data/control_minus.bw"],
      "smoothing": [null, null]
    }
  }
}
```

Apply these invariants:

- Give every task at least one `signal.source` and one `loci.source`.
- Give every task a `bias` object. For a no-control model, use `"bias": {"source": [], "smoothing": []}`.
- Match the lengths of `bias.source` and `bias.smoothing`. Each smoothing value is either `null` or `[sigma, window_width]`.
- Match the lengths of `background_loci.source` and `background_loci.ratio`.
- Interpret each background ratio as `number_selected = int(number_foreground * ratio)` for the corresponding background file. Despite wording in the upstream README, this is background divided by foreground in generator behavior.
- Resolve relative paths from the working directory used to launch BPNet.

## `bpnet_params.json`

Start from the upstream single-task, two-track configuration:

```json
{
  "input_len": 2114,
  "output_profile_len": 1000,
  "motif_module_params": {
    "filters": [64],
    "kernel_sizes": [21],
    "padding": "valid"
  },
  "syntax_module_params": {
    "num_dilation_layers": 8,
    "filters": 64,
    "kernel_size": 3,
    "padding": "valid",
    "pre_activation_residual_unit": true
  },
  "profile_head_params": {
    "filters": 1,
    "kernel_size": 75,
    "padding": "valid"
  },
  "counts_head_params": {
    "units": [1],
    "dropouts": [0.0],
    "activations": ["linear"]
  },
  "profile_bias_module_params": {"kernel_sizes": [1]},
  "counts_bias_module_params": {},
  "use_attribution_prior": false,
  "attribution_prior_params": {
    "frequency_limit": 150,
    "limit_softness": 0.2,
    "grad_smooth_sigma": 3,
    "profile_grad_loss_weight": 200,
    "counts_grad_loss_weight": 100
  },
  "loss_weights": [1, 42],
  "counts_loss": "MSE"
}
```

Compute the second loss weight from the data rather than copying `42` blindly:

```bash
bpnet-counts-loss-weight --input-data input_data.json
```

Although architecture loading has defaults, `training.py` directly indexes `loss_weights` and `counts_loss`; include both keys. For standard multi-task loss, set the last `counts_head_params.units` value to the number of tasks or `-1`. If any bias tracks are present, give `profile_bias_module_params.kernel_sizes` one value per task.

## `splits.json`

Use contiguous string split IDs. A chromosome split must include `val`; include `train` explicitly or let BPNet derive it from the master chromosome list after excluding `val` and optional `test`:

```json
{
  "0": {
    "test": ["chr7", "chr13", "chr17", "chr19", "chr21", "chrX"],
    "val": ["chr10", "chr18"],
    "train": ["chr1", "chr2", "chr3", "chr4", "chr5", "chr6", "chr8"]
  }
}
```

Alternatively use paired `loci_train_indices_file` and `loci_val_indices_file` values. If background index files are used, supply both `background_train_indices_file` and `background_val_indices_file`.

## Optional Peak Cleanup And Background

Remove extreme-signal or blacklisted peaks:

```bash
bpnet-outliers \
  --input-data input_data.json \
  --task 0 \
  --chrom-sizes hg38.chrom.sizes \
  --chroms chr1 chr2 chr3 \
  --sequence-len 1000 \
  --output-bed data/peaks_inliers.bed
```

Create genome-wide GC bins and matched negatives:

```bash
bpnet-gc-reference \
  --ref_fasta hg38.genome.fa \
  --chrom_sizes hg38.chrom.sizes \
  --output_prefix data/hg38_gc_bins \
  --inputlen 2114 \
  --stride 50

bpnet-gc-background \
  --out_dir data \
  --peaks_bed data/peaks_inliers.bed \
  --ref_fasta hg38.genome.fa \
  --ref_gc_bed data/hg38_gc_bins.bed \
  --flank_size 1057 \
  --neg_to_pos_ratio_train 1 \
  --output_prefix gc_negatives
```

This writes `data/gc_negatives.bed` and a GC-comparison plot. The GC-background wrapper invokes `bedtools intersect` through a shell command. Use trusted, space-free paths with this legacy implementation and inspect its outputs before training.

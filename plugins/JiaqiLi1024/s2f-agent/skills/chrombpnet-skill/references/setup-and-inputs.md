# Setup And Inputs

## Contents

- Runtime paths
- Installation
- Input contracts
- Preprocessing
- Preflight
- Reproducibility notes

## Runtime Paths

Choose one path and state it explicitly.

### Docker

Use the upstream image only on a host with Docker, NVIDIA drivers, and NVIDIA Container Toolkit:

```bash
docker run -it --rm --memory=100g --gpus device=0 \
  kundajelab/chrombpnet:latest
```

Mount input and output volumes for real work. Pin an image digest for reproducible runs instead of relying indefinitely on `latest`.

### Local Conda

Prefer the repository-documented Python 3.8 path:

```bash
conda create -n chrombpnet python=3.8
conda activate chrombpnet
conda install -y -c conda-forge -c bioconda \
  samtools bedtools ucsc-bedgraphtobigwig pybigwig meme
python -m pip install chrombpnet
```

For source development:

```bash
git clone https://github.com/kundajelab/chrombpnet.git
python -m pip install -e chrombpnet
```

The bundled source snapshot declares Python `>=3.8`, TensorFlow `2.8.0`, TensorFlow Probability `0.15.0`, NumPy `1.23.4`, protobuf `3.20`, modisco-lite `2.0.7`, and other legacy-era dependencies. Avoid silently substituting a modern TensorFlow stack. Build a separate environment and test the CLI before use.

Verify the environment:

```bash
chrombpnet --help
samtools --version
bedtools --version
bedGraphToBigWig 2>&1 | head
modisco --help
nvidia-smi
python - <<'PY'
import tensorflow as tf
print(tf.__version__)
print(tf.config.list_physical_devices("GPU"))
PY
```

## Input Contracts

### Read Input

Supply exactly one input:

- BAM: filtered alignments; inspect sorting, flags, duplicates, and reference contigs before use.
- Fragment TSV: at least chromosome, start, and end; each row represents a fragment with Tn5 events at both ends.
- tagAlign: at least chromosome, start, end, and strand in column 6.

The preprocessing code accepts plain or gzipped fragment/tagAlign input and estimates enzyme shifts. It produces an unstranded BigWig after applying the ChromBPNet conventions: `+4/-4` for ATAC and `0/+1` for DNase. Do not manually apply another shift unless the existing data processing is known and documented.

### Reference Assets

- FASTA: use the exact assembly represented by the reads and BED files.
- Chromosome sizes: use two tab-separated columns, chromosome and positive length.
- Keep names identical, including the `chr` prefix and mitochondrial chromosome spelling.

### Peaks And Nonpeaks

Use exactly 10 tab-separated columns. ChromBPNet assigns the schema:

```text
chrom  start  end  name  score  strand  signalValue  pValue  qValue  summit
```

Interpret `start`/`end` as a 0-based half-open interval and `summit` as a 0-based offset from `start`. The model centers the input at `start + summit`. Do not pass a generic 3-column BED to training, prediction, contribution, or footprint commands that request 10-column regions.

### Fold JSON

Provide nonempty, disjoint chromosome lists:

```json
{
  "train": ["chr1", "chr2", "chr3"],
  "valid": ["chr4"],
  "test": ["chr5"]
}
```

Ensure every fold chromosome exists in the chromosome sizes and FASTA. The pipeline uses the first validation chromosome for shift-QC PWM construction.

## Preprocessing

Create a split explicitly:

```bash
chrombpnet prep splits \
  --output_prefix /path/to/splits/fold_0 \
  --chrom-sizes /path/to/genome.chrom.sizes \
  --test-chroms chr1 chr2 \
  --valid-chroms chr3 chr4
```

The command appends `.json` and assigns all remaining chromosomes to training.

Generate GC-matched nonpeaks:

```bash
chrombpnet prep nonpeaks \
  --genome /path/to/genome.fa \
  --chrom-sizes /path/to/genome.chrom.sizes \
  --peaks /path/to/peaks.narrowPeak \
  --chr-fold-path /path/to/fold_0.json \
  --blacklist-regions /path/to/blacklist.bed \
  --inputlen 2114 \
  --stride 1000 \
  --neg-to-pos-ratio-train 2 \
  --seed 1234 \
  --output-prefix /path/to/background/sample
```

The command creates `<prefix>_auxiliary/` with intermediate GC files and `<prefix>_negatives.bed` as the 10-column training input. Choose a new prefix because the auxiliary directory is created with `exist_ok=False`.

## Preflight

Run the bundled validator before composing or launching training:

```bash
python skills/chrombpnet-skill/scripts/validate_chrombpnet_inputs.py --help
```

Treat errors as blockers. Review warnings about missing executables, FASTA/chromosome-size disagreement, BAM indexing, edge-filtered regions, and existing output children.

## Reproducibility Notes

- Record the exact package version and source commit. The bundled snapshot reports divergent version values in `setup.py`, `CHANGELOG.md`, and `CITATION.cff`.
- Record input checksums and fold JSON rather than only filenames.
- Use one output directory per assay, biosample, fold, seed, and bias-model choice.
- Preserve raw data separately; ChromBPNet output directories contain generated intermediates and reports.

# Pangolin CLI and Semantics

Source: `Readme/Pangolin-main/README.md` and `setup.py` (package 1.0.2).

## Setup

Use Python 3.6+ and conda. Install PyTorch first, then `pyvcf`, `gffutils`, `biopython`, `pandas`, and `pyfastx`; install the source checkout with `pip install .`. The console entry point is `pangolin=pangolin.pangolin:main`.

Create a transcript annotation database before scoring:

```bash
python scripts/create_db.py gencode.annotation.gtf.gz
```

The script defaults to the `Ensembl_canonical` tag. The database is a gffutils `.db` file, not a raw GTF.

## CLI contract

```text
pangolin [-h] [-c COLUMN_IDS] [-m {False,True}] [-s SCORE_CUTOFF] [-d DISTANCE]
         variant_file reference_file annotation_file output_file
```

`variant_file` is VCF or CSV with a header. `--column_ids` supplies CSV column names for chromosome, position, REF, and ALT (default `CHROM,POS,REF,ALT`). `--mask` defaults to `True`; `--score_cutoff` emits all sites above an absolute change threshold instead of only maximum loss/gain sites; `--distance` defaults to 50 bases on each side.

Example:

```bash
pangolin examples/brca.vcf GRCh37.primary_assembly.genome.fa.gz \
  gencode.v38lift37.annotation.db brca_pangolin
```

The output keeps the VCF/CSV type and uses an output prefix. Default summaries report `gene|pos:largest_increase|pos:largest_decrease|`.

## Skip and mask semantics

Only substitutions and simple insertions/deletions with either REF or ALT a single base are supported. Variants outside genes, within 5 kb of chromosome ends, with deletions larger than twice `-d`, or mismatching the reference FASTA are skipped. Masking zeros annotated-site gains and unannotated-site losses; turn it off only when raw splice-score changes are wanted.

For arbitrary sequence inputs, use the repository's `scripts/custom_usage.py` rather than assuming the VCF/CSV CLI accepts FASTA.


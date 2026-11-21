# Basenji CLI Workflows

Source: `Readme/basenji-master/README.md`, `docs/train.md`, `docs/variants.md`, `docs/regulatory.md`, and the `bin/` scripts.

## Environment and data

The source documents conda installation from `environment.yml` or `prespecified.yml`, TensorFlow installed separately, and `python setup.py develop --no-deps`. The recommended shell variables are:

```bash
export BASENJIDIR=/path/to/Basenji
export PATH=$BASENJIDIR/bin:$PATH
export PYTHONPATH=$BASENJIDIR/bin:$PYTHONPATH
```

The package can be imported with `import basenji`. Data directories generally contain HDF5/TFR sequence examples and `targets.txt`; the exact `params.json` controls sequence length, bins, targets, and normalization.

## Grounded commands

```text
basenji_train.py [options] <params_file> <data1_dir> ...
basenji_predict.py [options] <params_file> <model_file> <data_dir>
basenji_sad.py [options] <params_file> <model_file> <vcf_file>
basenji_sed.py [options] <params_file> <model_file> <vcf_file> <tss_bed_file>
basenji_sat_vcf.py [options] <params_file> <model_file> <vcf_file>
basenji_motifs.py [options] <params_file> <model_file> <data_dir>
basenji_sat.py [options] <params_file> <model_file> <input_file>
basenji_map.py [options] <params_file> <model_file> <genes_hdf5_file>
```

`basenji_train.py` supports `-o`, `--restore`, `--trunk`, TFR patterns, and optional mixed precision/Keras fit. `basenji_predict.py` writes `preds.h5` and `normalization.txt`; `-b` plus `-g` can write per-target BigWigs. Variant scripts support target selection (`-t`), reverse-complement ensembles (`--rc`), shifts (`--shifts`), output directories (`-o`), and optional parallel workers.

SAD is SNP Activity Difference over selected activity targets and expects a bi-allelic VCF. SED compares gene-expression predictions and additionally requires a TSS BED. SAT VCF produces per-position mutation scores in an HDF5 output. Motif analysis uses first-layer filters and can write MEME/logos/heatmaps.

## Routing note

The same checkout contains `akita_*`, `saluki_*`, and `borzoi_*` scripts. Use this skill only when the user names Basenji or a `basenji_*` command; route those other families to their own documented workflow.


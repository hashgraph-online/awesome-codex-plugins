# Sei CLI and Outputs

Source: `Readme/sei-framework-main/README.md` and the four numbered Python scripts.

## Setup

Create a dedicated conda environment with Python 3.6+, PyTorch (>=1.0), Selene (>=0.5.0), and `docopt`. Run `sh download_data.sh` to obtain the trained model and `resources` directory containing the bundled hg19/hg38 FASTA files.

## Prediction commands

```bash
sh 1_sequence_prediction.sh input.bed hg19 output_dir --cuda
sh 1_sequence_prediction.sh input.fa hg19 output_dir --cuda
sh 1_variant_effect_prediction.sh variants.vcf hg19 output_dir --cuda
```

The Python entry points expose the same positional arguments. BED inputs require `--genome` to be `hg19` or `hg38`; FASTA is accepted directly and the genome label is logging metadata. Both scripts create `output_dir/chromatin-profiles-hdf5` and write HDF5 predictions plus a row-label file.

## Sequence-class postprocessing

```bash
python 2_raw_sc_score.py input_predictions.h5 output_dir
python 2_varianteffect_sc_score.py ref_predictions.h5 alt_predictions.h5 output_dir
python 2_varianteffect_sc_score.py ref_predictions.h5 alt_predictions.h5 output_dir --no-tsv
```

Raw sequence scores project chromatin profiles onto `model/projvec_targets.npy` and write `<prefix>.raw_sequence_class_scores.npy`. Variant scores compute alt-ref projections with histone indices (`histone_inds.npy`) for nucleosome-occupancy normalization, write `<prefix>.sequence_class_scores.npy`, and optionally sorted chromatin-profile and sequence-class TSVs. Rows must match `*_row_labels.txt`; columns use `model/target.names` and `model/seqclass.names`.

## Training

The README places training under `train/`, uses Selene, and recommends four V100 GPUs with NVLink. Training data is downloaded separately and has Cistrome terms of use. Do not present the prediction scripts as a training API.


# Motif Discovery And Hit Calling

Use this reference after `bpnet-shap` has produced `profile_scores.h5` and/or `counts_scores.h5`.

## TF-MoDISco

Install the separately maintained `modisco-lite` package in a compatible environment:

```bash
conda create --name tfmodisco python=3.10
conda activate tfmodisco
pip install modisco-lite
mkdir -p modisco/profile modisco/counts
```

Run profile and counts attribution analyses separately:

```bash
modisco motifs \
  --max_seqlets 50000 \
  --h5py shap/profile_scores.h5 \
  -o modisco/profile/profile_modisco_scores.h5 \
  --trim_size 20 \
  --initial_flank_to_add 5 \
  --final_flank_to_add 10

modisco motifs \
  --max_seqlets 50000 \
  --h5py shap/counts_scores.h5 \
  -o modisco/counts/counts_modisco_scores.h5 \
  --trim_size 20 \
  --initial_flank_to_add 5 \
  --final_flank_to_add 10
```

Inspect the installed `modisco motifs --help` when using a newer release because this command belongs to an external package, not BPNet 2.0.0.

## Fi-NeMo

The upstream README points to the separate Fi-NeMo repository:

```bash
git clone https://github.com/austintwang/finemo_gpu.git
cd finemo_gpu
conda env create -f environment.yml -n finemo
conda activate finemo
pip install --editable .
cd ..
```

Extract regions, call motif hits, and generate a report:

```bash
mkdir -p hits/counts
finemo extract-regions-bpnet-h5 \
  -c shap/counts_scores.h5 \
  -o hits/counts/regions_bw.npz \
  -w 400 \
  -p data/peaks_inliers.bed

finemo call-hits \
  -l "${FINEMO_LAMBDA}" \
  -r hits/counts/regions_bw.npz \
  -m modisco/counts/counts_modisco_scores.h5 \
  -p data/peaks_inliers.bed \
  -C hg38.chrom.sizes \
  -o hits/counts \
  -t 0.7 \
  --compile

finemo report \
  -H hits/counts/hits.tsv \
  -r hits/counts/regions_bw.npz \
  -m modisco/counts/counts_modisco_scores.h5 \
  -p data/peaks_inliers.bed \
  -o hits/counts \
  -t 0.7 \
  -W 400
```

Treat the lambda value, window size, and threshold as analysis parameters, not BPNet defaults. Preserve the peak BED and chromosome-size files used for hit calling with the output provenance.

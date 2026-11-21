# Setup and Environment

Use this file when the user needs reproducible Borzoi installation and environment setup.

## Core dependency stack

Grounded major requirements from Borzoi docs:

- Python `3.10` (recommended tutorial path)
- TensorFlow `2.15.x`
- `baskerville` repository install
- `borzoi` repository install
- `westminster` repository install for training/data processing flows

Minimal installation order:

```bash
git clone https://github.com/calico/baskerville.git
cd baskerville
pip install -e .

git clone https://github.com/calico/borzoi.git
cd borzoi
pip install -e .
```

Training-oriented add-on:

```bash
git clone https://github.com/calico/westminster.git
cd westminster
pip install -e .
```

## Conda baseline

```bash
conda create -n borzoi_py310 python=3.10
conda activate borzoi_py310
```

Notebook users should install Jupyter:

```bash
pip install notebook
```

## Environment preflight (run before long jobs)

Use these checks to fail fast before model downloads or long inference:

```bash
python -V
python -c "import tensorflow as tf; print(tf.__version__)"
python -c "import borzoi, baskerville, pysam; print('imports_ok')"
```

If these fail, fix environment consistency first.

## Multi-conda safety notes

When multiple conda installations exist, avoid ambiguous interpreter resolution:

- Prefer invoking the target environment python with absolute path (for example, `<env>/bin/python script.py`).
- If `conda run -n <env> ...` behaves inconsistently, validate `CONDA_EXE`, `CONDA_PREFIX`, and env ownership.
- Keep one active Borzoi environment (`borzoi_py310`) as the source of truth for all runtime commands.

## Environment variables

Borzoi docs provide an `env_vars.sh` script in each repository. It configures:

- `BORZOI_DIR`
- `BORZOI_HG38`
- `BORZOI_MM10`
- `BORZOI_CONDA`
- `PATH`/`PYTHONPATH` entries for Borzoi scripts

`baskerville` and `westminster` variables are only required for workflows that use those repositories (especially training/data processing).

## Model and annotation download

For published-model workflows, run:

```bash
cd borzoi
./download_models.sh
```

This script downloads:

- pre-trained replicate `.h5` models
- hg38 gene annotations (GTF/BED/GFF)
- helper annotation tables
- hg38 FASTA plus indexing

For fast-tier real inference with lower download overhead, use mini model assets and task-local sequence retrieval (see `references/real-inference-fastpath.md`).

## Data and compute caveats

- Full training-data bucket is multi-terabyte and requester-pays on GCP.
- Some scripts in the Borzoi repository launch multi-process jobs and assume SLURM-style environments.

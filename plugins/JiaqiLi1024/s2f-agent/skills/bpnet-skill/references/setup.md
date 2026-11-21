# Setup

Use this reference for BPNet 2.0.0 installation and runtime selection.

## Runtime Choice

Prefer the documented Docker image when reproducibility matters more than editing the package:

```bash
docker pull vivekramalingam/tf-atlas:gcp-modeling_v2.1.0-rc.1
docker run -it --rm --cpus=10 --memory=32g --gpus device=1 \
  --mount src=/mnt/bpnet-models/,target=/mydata,type=bind \
  vivekramalingam/tf-atlas:gcp-modeling_v2.1.0-rc.1
```

Use a dedicated legacy environment for local work:

```bash
conda create --name bpnet python=3.7
conda activate bpnet
pip install git+https://github.com/kundajelab/bpnet.git
# The upstream README also documents: pip install bpnet
```

The bundled `setup.py` identifies version `2.0.0` and pins:

- `tensorflow==2.4.1`
- `tensorflow-probability==0.12.2`
- `pysam==0.18.0`
- `py2bit==0.3.0`
- `kundajelab-shap==1`

Do not present a modern Python/TensorFlow environment as source-supported without testing it. Use a separate environment for `modisco-lite` because its README example uses Python 3.10.

## External Tools

Install command-line tools used by preprocessing and bigWig generation separately:

```bash
conda install -y -c bioconda samtools=1.1 bedtools ucsc-bedgraphtobigwig
```

Install `bamtools` if the selected preprocessing workflow calls it.

## Preflight

Run these checks before a long job:

```bash
nvidia-smi
python --version
python -c 'import bpnet, tensorflow as tf; print(tf.__version__)'
bpnet-train --help
bpnet-predict --help
bpnet-shap --help
```

Keep GPU, CUDA, and driver compatibility separate from Python-package validation. Training is GPU-oriented; the bundled configuration validator is CPU-only and requires only the Python standard library.

## Published Alternatives

The upstream README points to AnVIL/Terra workspaces for managed BPNet and chromatin-accessibility training. Keep AnVIL advice high level unless the user supplies a specific workspace, billing project, and data layout.

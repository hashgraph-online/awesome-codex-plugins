# Setup And Runtime

## Package Source

AlphaGenome Research is the local JAX implementation from `google-deepmind/alphagenome_research`.
Install it from a clone in editable mode:

```bash
python -m pip install -e /path/to/alphagenome_research
```

The repository `pyproject.toml` declares Python `>=3.11` and dependencies including `alphagenome`, `jax`, `dm-haiku`, `orbax`, `pyfaidx`, `pyranges`, `tensorflow`, `kagglehub`, and `huggingface_hub`.

## JAX Device Expectations

The local model constructor selects `jax.default_device.value` or `jax.local_devices()[0]`. If no GPU or TPU is found, it raises unless a CPU `jax.Device` is explicitly passed.

Use CPU only for import checks, metadata exploration, or very small debugging. Full model inference is expected to need a capable accelerator; the README recommends at least an NVIDIA H100 GPU.

Check devices:

```bash
python - <<'PY'
import jax
print(jax.__version__)
print(jax.local_devices())
PY
```

For accelerator systems, install the JAX backend package that matches the machine and driver stack. Do not assume plain `pip install jax` gives GPU/TPU support.

Portable accelerator check:

```bash
python - <<'PY'
from importlib import metadata
import json
import jax

packages = {}
for name in (
    "jax",
    "jaxlib",
    "jax-cuda12-plugin",
    "jax-cuda12-pjrt",
    "jax-cuda13-plugin",
    "jax-cuda13-pjrt",
):
    try:
        packages[name] = metadata.version(name)
    except metadata.PackageNotFoundError:
        packages[name] = None

print(json.dumps({
    "packages": packages,
    "default_backend": jax.default_backend(),
    "devices": [
        {
            "platform": d.platform,
            "device_kind": d.device_kind,
            "description": str(d),
        }
        for d in jax.local_devices()
    ],
}, indent=2))
PY
```

Treat exact hardware details as run context, not requirements. Vendor tools, driver-reported CUDA versions, and JAX plugin package names can look inconsistent across machines; the portable decision point is whether JAX reports a usable accelerator device for the installed backend.

For smoke tests, prefer:

```bash
export XLA_PYTHON_CLIENT_PREALLOCATE=false
```

This avoids JAX preallocating most GPU memory before the first small forward pass.

CPU-only or no-GPU containers can be misleading. A no-card boot may still have CUDA paths and a JAX CUDA plugin installed, but `nvidia-smi` can fail and JAX may log `cuInit(0) failed`. Treat that as a hardware-mode check, not a package failure, if CPU import checks still pass. Also inspect cgroup memory:

```bash
cat /sys/fs/cgroup/memory.max
```

Very small memory limits are not enough for real checkpoint restore; in practice a 2 GiB no-card container was killed before `model_loaded`.

## Weights

Weights are not bundled with the source tree. Use one of:

- Kaggle: `dna_model.create_from_kaggle('all_folds')`
- Hugging Face: `dna_model.create_from_huggingface('all_folds')`
- Existing checkpoint: `dna_model.create('/path/to/checkpoint')`

Kaggle and Hugging Face downloads require accepting AlphaGenome model terms and authenticating with the corresponding service. Avoid echoing tokens in logs.

Hugging Face repo names used by the local helper:

- `all_folds` -> `google/alphagenome-all-folds`
- `fold_0` -> `google/alphagenome-fold-0`

For cloud servers, put the cache on persistent large storage rather than a small root overlay. Choose the mount that exists on the current machine:

```bash
export HF_HOME=/path/to/persistent/hf-cache
export HF_HUB_CACHE="$HF_HOME/hub"
export HF_HUB_DISABLE_XET=1
export HF_HUB_ENABLE_HF_TRANSFER=0
```

If the default `snapshot_download` stalls after small files, disable Xet and use a single worker:

```python
import os
from pathlib import Path
from huggingface_hub import snapshot_download

os.environ["HF_HUB_DISABLE_XET"] = "1"
checkpoint_path = snapshot_download(
    repo_id="google/alphagenome-all-folds",
    token=os.environ["HF_TOKEN"],
    max_workers=1,
)
Path("hf_snapshot_path.txt").write_text(checkpoint_path + "\n")
```

## Reference Assets

`dna_model.default_organism_settings()` points to remote reference FASTA and Feather annotation URLs:

- Human FASTA: `hg38/GRCh38.p13.genome.fa`
- Human GENCODE Feather: `gencode.v46.annotation.gtf.gz.feather`
- Human polyadenylation Feather
- Human splice-site Feather tables
- Mouse FASTA: `mm10/GRCm38.p6.genome.fa`
- Mouse GENCODE and splice-site Feather tables

For reproducible local runs, define explicit local paths:

```python
from alphagenome_research.model import dna_model

organism_settings = {
    dna_model.Organism.HOMO_SAPIENS: dna_model.OrganismSettings(
        fasta_path="/data/genomes/hg38/GRCh38.p13.genome.fa",
        gtf_feather_path="/data/alphagenome/gencode.v46.annotation.gtf.gz.feather",
        pas_feather_path="/data/alphagenome/polyadb_human_v3_exon3_contiguous_gtfv46.feather",
        splice_site_starts_feather_path="/data/alphagenome/gencode.v46.splice_sites_starts.feather",
        splice_site_ends_feather_path="/data/alphagenome/gencode.v46.splice_sites_ends.feather",
    )
}
model = dna_model.create_from_huggingface(
    "all_folds",
    organism_settings=organism_settings,
)
```

`predict_interval` and `predict_variant` need FASTA extraction. Scorers that use gene or polyadenylation masks need the corresponding Feather annotations.

For a `predict_sequence` smoke test, avoid remote reference asset loading by providing metadata-only organism settings. Include both organisms for `all_folds` checkpoints:

```python
from alphagenome_research.model import dna_model

organism_settings = {
    dna_model.Organism.HOMO_SAPIENS: dna_model.OrganismSettings(),
    dna_model.Organism.MUS_MUSCULUS: dna_model.OrganismSettings(),
}
model = dna_model.create(
    "/path/to/hf/snapshot",
    organism_settings=organism_settings,
)
```

Do not pass only the human entry for `all_folds`; that can restore successfully but fail during prediction with an organism embedding shape mismatch.

## Common Failures

- `ModuleNotFoundError: alphagenome_research`: install the research clone with `python -m pip install -e`.
- Python version error: use Python 3.11, 3.12, or 3.13.
- CPU-only error: confirm `jax.local_devices()` and install accelerator-enabled JAX, or explicitly pass a CPU device for debugging only.
- Kaggle or Hugging Face prompt/hang: authenticate first and confirm model terms were accepted.
- Hugging Face stalls after several files: set `HF_HUB_DISABLE_XET=1` and retry `snapshot_download(..., max_workers=1)`.
- Forward fails with `alphagenome/embed/embeddings` shape `(2, 1536)` versus `(1, 1536)`: include both human and mouse metadata-only `OrganismSettings` when using an `all_folds` checkpoint.
- Process is killed during CPU checkpoint loading: check cgroup memory; no-GPU containers may expose only 2 GiB even when host memory is large.
- Chromosome not found: match FASTA chromosome names, usually `chr1` style for the default examples.
- Remote reference fetch fails: download assets locally and pass `OrganismSettings`.

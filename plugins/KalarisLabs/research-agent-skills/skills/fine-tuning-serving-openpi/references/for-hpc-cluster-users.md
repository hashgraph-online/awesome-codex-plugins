# For HPC/cluster users

On Slurm-managed clusters, wrap commands with resource allocation:

```bash
srun --partition=gpu --gpus-per-node=1 --mem=64G --cpus-per-task=8 --pty bash
```

Route caches to scratch to avoid filling `/home`:

```bash
export HF_HOME=/scratch/$USER/.cache/huggingface
export XDG_CACHE_HOME=/scratch/$USER/.cache
export PIP_CACHE_DIR=/scratch/$USER/.cache/pip
export UV_CACHE_DIR=/scratch/$USER/.cache/uv
```

Avoid stacking cluster Python modules when using uv-managed environments. Typically `module load cuda` is sufficient.

---

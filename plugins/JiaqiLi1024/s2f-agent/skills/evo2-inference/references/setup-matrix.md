# Setup Matrix

Use this file to choose a supported Evo 2 setup before writing commands.

## Baseline requirements

- OS: Linux officially, or WSL2 with limited support
- Python: 3.11 or 3.12
- CUDA: 12.1 or newer
- cuDNN: 9.3 or newer
- Compiler: GCC 9+ or Clang 10+ with C++17 support
- Torch: prefer 2.6.x or 2.7.x

If the user is on macOS or lacks NVIDIA GPUs, steer them toward the hosted API instead of local inference.

## Checkpoint compatibility

Use this table when recommending a model:

| Checkpoint | Context | Notes |
| --- | --- | --- |
| `evo2_7b` | 1M | Best default local starting point |
| `evo2_7b_262k` | 262K | Lower context alternative to 1M |
| `evo2_7b_base` | 8K | Base 7B model |
| `evo2_20b` | 1M | Requires FP8 and Transformer Engine |
| `evo2_40b` | 1M | Requires FP8, Transformer Engine, and multiple H100 GPUs |
| `evo2_40b_base` | 8K | Requires FP8 and Transformer Engine |
| `evo2_1b_base` | 8K | Requires FP8 and Transformer Engine |
| `evo2_7b_microviridae` | not stated in README table | Fine-tuned Microviridae model |

## Hosted API operational matrix

Use this matrix for hosted workflows:

| Task | Primary endpoint | Fallback endpoint | Notes |
| --- | --- | --- | --- |
| Forward logits | `/v1/biology/arc/evo2-7b/forward` | none in this skill | `forward` returns encoded array payloads; decode before plotting. |
| Embeddings | `/v1/biology/arc/evo2-7b/forward` with `output_layers=["embedding_layer"]` | none in this skill | Extract per-position embedding tracks from decoded arrays. |
| Generation | `/v1/biology/arc/evo2-7b/generate` | `/v1/biology/arc/evo2-40b/generate` | Retry and fallback when 7B generation is temporarily degraded. |

Common hosted API transient failures:

- `400 ... DEGRADED function cannot be invoked`
- `422 ... Instance is restarting`
- `504` timeouts on large requests

Use short retries with backoff before failing a run.

## FP8 and hardware rules

- `evo2_7b`, `evo2_7b_262k`, and `evo2_7b_base` do not require Transformer Engine.
- `evo2_20b`, `evo2_40b`, `evo2_40b_base`, and `evo2_1b_base` require FP8 via Transformer Engine and a Hopper GPU.
- `evo2_40b` requires multiple H100 GPUs. Vortex handles device placement across available CUDA devices.

## Hosted forward payload shape

- Hosted `forward` commonly returns a base64 string.
- Decoded payload is a ZIP archive containing one or more `.npy` arrays.
- Typical layer names used in this skill:
  - `unembed` for logits-style tracks
  - `embedding_layer` for representation tracks

## Installation choices

Use full install when the target model requires Transformer Engine:

```bash
conda install -c nvidia cuda-nvcc cuda-cudart-dev
conda install -c conda-forge transformer-engine-torch=2.3.0
pip install flash-attn==2.8.0.post2 --no-build-isolation
pip install evo2
```

Use light install only for 7B-class local workflows:

```bash
pip install flash-attn==2.8.0.post2 --no-build-isolation
pip install evo2
```

Install from source when the user wants to work from a checkout:

```bash
git clone https://github.com/arcinstitute/evo2
cd evo2
pip install -e .
```

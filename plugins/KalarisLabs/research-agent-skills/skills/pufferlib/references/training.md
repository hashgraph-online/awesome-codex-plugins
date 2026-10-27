# Training, Evaluation, Configuration, and Logging

Research snapshot: **2026-07-23**.

## Choose a version profile first

### Published stable package

PyPI's latest stable `pufferlib` release is **3.0.0**, published
**2025-06-23**. It declares Python `>=3.9` and is distributed only as a
60.7 MB source archive:

```text
pufferlib-3.0.0.tar.gz
sha256: 7df3a3e3f5f894d78d2a1f5374097890aec01473183e748abefe4f3faa10eaa9
```

The uploaded metadata depends on NumPy `<2.0`, Gym `<=0.23`, Gymnasium
`<=0.29.1`, PettingZoo `<=1.24.1`, Shimmy, Torch, Neptune, W&B, and other
packages without a complete transitive lock. It does not declare a CUDA
version or a minimum Torch version. Do not invent compatibility guarantees.

### Current source line

The upstream default branch is `4.0`; its `pyproject.toml` says version `4.0.0`,
Python `>=3.10`, and Torch `>=2.9`. As of the research date, this source line
is not the latest stable PyPI artifact.

The current PufferTank Dockerfile uses:

- Ubuntu 24.04
- NVIDIA CUDA `13.0.2` cuDNN development image
- Python 3.12
- the CUDA 13.0 PyTorch wheel index
- Nsight Systems `2025.6.3`

The Dockerfile does **not** pin an exact Torch wheel, uv version, PufferLib
commit, or every apt package. It is an upstream convenience environment, not a
complete reproducibility lock.

## Reproducible uv workflow

Do not use an unpinned `uv pip install pufferlib`. Work in a disposable,
project-specific environment and commit `pyproject.toml` plus `uv.lock`.

For the published profile, after reviewing the source archive and build:

```bash
uv venv --python 3.11
uv add --exact --no-sync "pufferlib==3.0.0"
uv lock
uv sync --frozen
```

Confirm the lock records the published SHA-256 above and review every resolved
dependency. The 3.0.0 source build can compile native code and may fetch build
assets. Resolve and build in a sandbox with no credentials or sensitive mounts.
Do not treat a successful resolver run as a security review.

For 4.0 source work, pin an immutable revision rather than branch `4.0`:

```bash
uv add --no-sync \
  "pufferlib @ git+https://github.com/PufferAI/PufferLib.git@25647630e1b15330bb3153a5a0d3ff8d234c3acf"
uv lock
```

The commit above is the reviewed 4.0 branch head on 2026-07-23. Re-review before
updating it. Native training still requires an audited build of a specific
environment; uv locking does not lock compilers, CUDA, NCCL, cuDNN, Raylib, or
system libraries.

Never run remote install scripts directly from a pipe. Download, inspect, pin,
verify, and execute only in an appropriate sandbox.

## Published 3.0.0 training

### CLI

The 3.0 console entry point is `puffer = pufferlib.pufferl:main`:

```bash
puffer train ENV_NAME [OPTIONS]
puffer eval ENV_NAME [OPTIONS]
puffer sweep ENV_NAME [OPTIONS]
puffer autotune ENV_NAME [OPTIONS]
puffer profile ENV_NAME [OPTIONS]
puffer export ENV_NAME [OPTIONS]
```

Environment, vector, policy, recurrent, training, and sweep values come from
INI sections. Overrides use section-qualified flags:

```bash
puffer train puffer_breakout \
  --train.device cpu \
  --train.total-timesteps 100000 \
  --vec.backend Serial \
  --vec.num-envs 2
```

Run `puffer train ENV_NAME --help` against the exact locked environment because
available options are generated from merged INI files.

### Python API

The stable trainer is `pufferlib.pufferl.PuffeRL`, not a top-level
`pufferlib.PuffeRL`:

```python
from pufferlib import pufferl

args = pufferl.load_config("puffer_breakout")
vecenv = pufferl.load_env("puffer_breakout", args)
policy = pufferl.load_policy(args, vecenv, "puffer_breakout")
trainer = pufferl.PuffeRL(args["train"], vecenv, policy)

try:
    while trainer.epoch < trainer.total_epochs:
        trainer.evaluate()
        trainer.train()
        trainer.mean_and_log()
finally:
    trainer.close()
```

The exact public methods include `evaluate`, `train`, `mean_and_log`,
`save_checkpoint`, `print_dashboard`, and `close`. Use the CLI when possible;
the Python trainer is a relatively low-level implementation surface.

### Stable configuration checks

- Make rollout/batch relationships explicit; do not rely on `auto` in a
  published experiment.
- Record environment, vector, policy, recurrent, and train sections verbatim.
- Fix `seed` in both `[vec]` and `[train]`, then run multiple independent seeds.
- Record `torch_deterministic`, precision, compile settings, optimizer, horizon,
  minibatch, and total timesteps.
- Keep evaluation seeds, instances, and metrics separate from training.

## Current 4.0 training

Build one audited environment, then use:

```bash
puffer train breakout
puffer eval breakout --load-model-path checkpoints/.../weights.bin
puffer sweep breakout
puffer match breakout \
  --load-model-path trusted-a.bin \
  --load-enemy-model-path trusted-b.bin
```

Current modes are `train`, `eval`, `sweep`, `paretosweep`, and `match`.
Native training is the default. `--slowly` selects the Torch fallback.
Configuration uses sections such as:

```ini
[vec]
total_agents = 4096
num_buffers = 2
num_threads = 16

[train]
total_timesteps = 10_000_000
minibatch_size = 8192
horizon = 64

[torch]
network = MinGRU
encoder = DefaultEncoder
decoder = DefaultDecoder
```

Current source validates that `minibatch_size` is divisible by `horizon` and
does not exceed `horizon * total_agents`. Multi-GPU launch uses spawn. Do a
small CPU/local build and contract test before CUDA training.

## Held-out evaluation

Training rollouts are not evaluation. For every reported result:

1. Freeze one checkpoint-selection rule before inspecting held-out scores.
2. Construct fresh evaluation environment instances.
3. Use evaluation seeds disjoint from training seeds.
4. Disable optimizer updates, exploration noise unless explicitly measuring it,
   curriculum updates, normalization-stat updates, and reward shaping used only
   for training.
5. Report deterministic and stochastic policy protocols separately.
6. Run enough episodes for uncertainty; report per-seed results and aggregate
   intervals, not only a best run.
7. Preserve terminated versus truncated semantics in return/length accounting.
8. Record wrappers, frame skip, autoreset mode, opponent pool, policy state
   reset, and rendering state.

Generate a starting plan:

```bash
python3 scripts/repro_plan.py --environment synthetic
```

## Checkpoints

PufferLib 3.0 saves a policy `state_dict` with `torch.save` and a separate
trainer state containing optimizer state, global step, epoch, and run ID. Its
loading paths call `torch.load`. The 4.0 native backend writes `.bin` weight
files; the 4.0 Torch fallback also uses `torch.save`/`torch.load`.

Rules:

- Never load an untrusted checkpoint, even to “inspect” it.
- Record SHA-256, size, source URL, immutable revision, license, environment,
  policy architecture, package lock, and training config in a strict JSON
  sidecar.
- Do not use `latest` in a reproducible run; resolve and record the exact path
  and digest.
- Do not auto-download a run artifact by ID.
- Test restore and evaluation in a disposable environment before a long resume.
- A model-only checkpoint is not a bitwise resume; optimizer, scheduler,
  normalizer, RNG, environment, and recurrent state may also matter.

Safe metadata inspection:

```bash
python3 scripts/inspect_checkpoint.py trusted/model.pt \
  --expected-sha256 EXPECTED_DIGEST
```

The helper hashes and classifies bytes only. It never imports Torch, invokes
pickle, opens archive members, or extracts files.

## External logging

Local logging is the default. W&B and Neptune are optional network services
that may transmit configuration, metrics, source metadata, hardware telemetry,
stdout/stderr, and explicitly uploaded checkpoints/artifacts. They can create
storage, seat, compute, or retention costs and are subject to vendor privacy,
access, and retention policies.

Credential rules:

- W&B: use the named environment variable `WANDB_API_KEY` or an approved secret
  manager.
- Neptune: use `NEPTUNE_API_TOKEN` or an approved secret manager.
- Never pass either secret as a CLI argument, INI/JSON value, logger config,
  tag, run name, or chat/tool input.
- Never print the value or include it in a broad environment dump.
- Do not recursively search for `.env` files. If policy permits a local secret
  file, read only the explicitly named key from the explicitly named file.
- Sanitize configuration before logging; reject keys containing token, secret,
  password, credential, authorization, private key, or API key.
- Disable checkpoint/source upload unless separately approved.

PufferLib 3.0 supports both `--wandb` and `--neptune`; its sweep mode requires
one. Current 4.0 source exposes W&B but no Neptune CLI integration. In either
profile, require explicit logging opt-in and disclosure acknowledgment. The
bundled training planner enforces this without reading credential values:

```bash
python3 scripts/train_template.py \
  --logger wandb \
  --enable-external-logging \
  --acknowledge-external-disclosure
```

## Sources

- [PyPI: pufferlib 3.0.0](https://pypi.org/project/pufferlib/3.0.0/) —
  released 2025-06-23; accessed 2026-07-23.
- [PyPI 3.0.0 JSON metadata](https://pypi.org/pypi/pufferlib/3.0.0/json) —
  package requirements and digest; accessed 2026-07-23.
- [PufferLib 3.0 trainer](https://github.com/PufferAI/PufferLib/blob/3.0/pufferlib/pufferl.py)
  — stable CLI, logger, and checkpoint source; accessed 2026-07-23.
- [PufferLib 3.0 default config](https://github.com/PufferAI/PufferLib/blob/3.0/pufferlib/config/default.ini)
  — stable parameters; accessed 2026-07-23.
- [PufferLib 4.0 docs](https://puffer.ai/docs.html) — current CLI and
  architecture; accessed 2026-07-23.
- [PufferLib 4.0 trainer](https://github.com/PufferAI/PufferLib/blob/4.0/pufferlib/pufferl.py)
  — current modes/config/checkpoints; accessed 2026-07-23.
- [PufferLib 4.0 package metadata](https://github.com/PufferAI/PufferLib/blob/4.0/pyproject.toml)
  — current Python/Torch requirements; accessed 2026-07-23.
- [PufferTank 4.0 Dockerfile](https://github.com/PufferAI/PufferTank/blob/4.0/puffertank.dockerfile)
  — CUDA/Python reference environment; accessed 2026-07-23.
- [Neptune Run API](https://docs.neptune.ai/run) — token and offline-mode
  guidance; accessed 2026-07-23.
- [W&B documentation](https://docs.wandb.ai/) — logging and credential
  guidance; accessed 2026-07-23.

# Setup And Troubleshooting

Use this file first when NTv3 code fails to install, import, or run.

## Recommended install path (tutorial-aligned)

Use a pinned Transformers 4.x stack to avoid accidental upgrades to 5.x:

```bash
pip install "transformers>=4.55,<5" "huggingface_hub>=0.23,<1" safetensors torch "numpy<2"
```

Optional notebook dependencies for track plotting and sequence download:

```bash
pip install pyfaidx requests seaborn matplotlib
```

Notebook dependencies for NTv3 fine-tuning workflows:

```bash
pip install pyfaidx pyBigWig torchmetrics
```

## Authentication for gated repos (required)

NTv3 repos are gated. Authenticate before loading models.

Option 1: CLI login

```bash
huggingface-cli login
```

Option 2: Python login

```python
from huggingface_hub import login

login()
```

Option 3: pass token directly in code

```python
AutoModel.from_pretrained(..., token=HF_TOKEN, trust_remote_code=True)
```

Practical pattern:

- Prefer setting `HF_TOKEN` in the environment and reading it in scripts.
- Do not hardcode tokens in notebooks or committed files.

## Minimal import smoke check

```python
from transformers import AutoModel, AutoModelForMaskedLM, AutoTokenizer
import torch
import numpy
```

Minimal gated-model smoke check (HF path):

```python
import os
from transformers import AutoModel

token = os.environ["HF_TOKEN"]
model = AutoModel.from_pretrained(
    "InstaDeepAI/NTv3_100M_post",
    trust_remote_code=True,
    token=token,
)
print(model.config.num_downsamples)
print(model.config.keep_target_center_fraction)
```

## Common failure modes

1. `No module named transformers`
- Install the packages above in the same environment used for inference.

2. Hugging Face auth / 401 / gated model error
- Ensure account access to the NTv3 repo and authenticate (`huggingface-cli login`), or pass `token=...`.
- Verify the token is visible in the current process (`HF_TOKEN`) and has accepted gated-model terms.

3. Slow or unstable weight download
- Set `HF_HUB_DISABLE_XET=1` as a fallback when default transport is unreliable.

4. NumPy / PyTorch compatibility warnings
- If using `torch 2.2.x`, prefer `numpy<2`.
- Reinstall with pinned versions from the command above.

5. Legacy JAX-source install fails with `No matching distribution found for jax>=0.6.0`
- This usually means the environment is too old (for example Python 3.9).
- Switch to Python >=3.10 for source install, or use the Transformers tutorial path.

6. CUDA out-of-memory
- Use a smaller checkpoint first (`NTv3_8M_pre` or `NTv3_100M_post`).
- Use reduced precision (`bfloat16` or `float16`) on GPU.
- Reduce sequence length or batch size.
- Prefer single-example runs first for post-trained `32,768+` contexts before scaling batch size.

7. `No module named pyBigWig` / `No module named pyfaidx` / `No module named torchmetrics`
- Install notebook fine-tuning extras: `pip install pyfaidx pyBigWig torchmetrics`.
- Ensure installation is in the same environment used by notebook/script execution.

8. Fine-tuning labels and head mismatch
- Confirm whether the workflow is bigwig-track regression or annotation classification before training.
- Keep loss family aligned with the head type (for example Poisson-style for bigwig, focal/classification style for annotation).
- Verify center-crop handling is consistent between model outputs and training targets.

## Cold-start expectations

- First run may download hundreds of MB of model weights and remote code.
- Long-context CPU inference can be noticeably slower than GPU inference.
- Validate output structure from generated result JSON fields instead of hardcoding one run's tensor shape values.
- For post-trained heads, derive center-crop behavior from `keep_target_center_fraction` and active config.

## Case-Study (case-study/ntv3) Fast Triage Order

Use this shortest command set when case-study execution fails:

1. Token and environment check:

```bash
set -a; source .env; set +a; test -n "${HF_TOKEN:-}" && echo "HF_TOKEN=ok"
```

2. Runtime import check:

```bash
conda run -n ntv3 python -c "import transformers, torch; print(transformers.__version__)"
```

3. Length divisibility check:

```bash
python skills/nucleotide-transformer-v3/scripts/check_valid_length.py 670 --model InstaDeepAI/NTv3_100M_post
```

4. Case-study embedding flow:

```bash
bash case-study/ntv3/run_ntv3_embedding.sh
```

5. Case-study fine-tuning prep flow:

```bash
bash case-study/ntv3/run_ntv3_finetuning_prep.sh
```

6. Combined flow summary:

```bash
bash case-study/ntv3/run_ntv3_case_study.sh
```

Triage interpretation order:

- If step 1 fails: fix `HF_TOKEN` / gated access first.
- If step 2 fails: fix environment/dependency mismatch first.
- If step 3 fails: fix/crop/pad lengths before rerunning workflow commands.
- If step 4 or 5 fails: inspect corresponding log/JSON artifacts under `case-study/ntv3/output`.

## Backend selection guidance

- Default: HF Transformers path for reliability and parity with official tutorials.
- Use JAX helper APIs only when a project already depends on `nucleotide_transformer_v3.pretrained`.
- For NTv3 fine-tuning in this repo, prefer the notebook-first workflow references in `Readme/NTv3/02/03/04`.

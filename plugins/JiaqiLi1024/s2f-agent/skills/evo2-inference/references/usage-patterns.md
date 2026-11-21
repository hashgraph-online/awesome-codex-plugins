# Usage Patterns

Use this file for the smallest grounded Evo 2 examples.

## Verify installation

After installation or hardware configuration changes, run:

```bash
python -m evo2.test.test_evo2_generation --model_name evo2_7b
```

Swap in another grounded checkpoint name if needed.

## Forward pass

Use this when the user wants logits over a DNA sequence:

```python
import torch
from evo2 import Evo2

evo2_model = Evo2("evo2_7b")

sequence = "ACGT"
input_ids = torch.tensor(
    evo2_model.tokenizer.tokenize(sequence),
    dtype=torch.int,
).unsqueeze(0).to("cuda:0")

outputs, _ = evo2_model(input_ids)
logits = outputs[0]

print("Logits:", logits)
print("Shape:", logits.shape)
```

## Embeddings

Use intermediate embeddings for downstream tasks:

```python
import torch
from evo2 import Evo2

evo2_model = Evo2("evo2_7b")

sequence = "ACGT"
input_ids = torch.tensor(
    evo2_model.tokenizer.tokenize(sequence),
    dtype=torch.int,
).unsqueeze(0).to("cuda:0")

layer_name = "blocks.28.mlp.l3"

outputs, embeddings = evo2_model(
    input_ids,
    return_embeddings=True,
    layer_names=[layer_name],
)

print("Embeddings shape:", embeddings[layer_name].shape)
```

Do not invent alternate layer names. If the user needs a different layer, verify it from the installed model or official examples.

## Generation

Use this for prompt-conditioned DNA completion:

```python
from evo2 import Evo2

evo2_model = Evo2("evo2_7b")

output = evo2_model.generate(
    prompt_seqs=["ACGT"],
    n_tokens=400,
    temperature=1.0,
    top_k=4,
)

print(output.sequences[0])
```

## Hosted API pattern

Use this when the user cannot or does not want to install locally:

```python
import os
import requests

key = os.getenv("NVCF_RUN_KEY") or input("Paste the Run Key: ")

r = requests.post(
    url=os.getenv(
        "URL",
        "https://health.api.nvidia.com/v1/biology/arc/evo2-40b/generate",
    ),
    headers={"Authorization": f"Bearer {key}"},
    json={
        "sequence": "ACTGACTGACTGACTG",
        "num_tokens": 8,
        "top_k": 1,
        "enable_sampled_probs": True,
    },
)

print(r.status_code)
print(r.text[:200])
```

Add file handling only when the user needs to persist JSON or ZIP responses.

## Hosted forward and embedding decode

Use this when the user needs forward tracks or embedding tracks from hosted API:

```python
import base64
import io
import zipfile

import numpy as np
import requests

key = "..."
sequence = "ACGTACGTACGTACGT"
url = "https://health.api.nvidia.com/v1/biology/arc/evo2-7b/forward"

r = requests.post(
    url,
    headers={"Authorization": f"Bearer {key}"},
    json={"sequence": sequence, "output_layers": ["unembed"]},
    timeout=120,
)
r.raise_for_status()

raw = base64.b64decode(r.json()["data"])
with zipfile.ZipFile(io.BytesIO(raw)) as zf:
    name = zf.namelist()[0]
    arr = np.load(io.BytesIO(zf.read(name)))

print(arr.shape)  # example: [1, sequence_len, 512]
```

Switch `output_layers` to `["embedding_layer"]` for embedding tracks.

## Hosted generation with fallback

Generation endpoints can degrade temporarily. Use fallback:

```python
import requests

def generate_with_fallback(key: str, sequence: str) -> dict:
    models = ["evo2-7b", "evo2-40b"]
    payload = {
        "sequence": sequence,
        "num_tokens": 64,
        "top_k": 1,
        "enable_sampled_probs": True,
    }
    for model in models:
        url = f"https://health.api.nvidia.com/v1/biology/arc/{model}/generate"
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {key}"},
            json=payload,
            timeout=120,
        )
        if resp.status_code == 200:
            return {"model": model, "output": resp.json()}
    raise RuntimeError("all generation endpoints failed")
```

## Variant-effect proxy with Evo2

Evo2 in this skill does not expose AlphaGenome-style `predict_variant(...)`. Use REF-vs-ALT proxy:

```python
# 1) Build REF sequence window and ALT sequence window at the same locus.
# 2) Run hosted forward on both windows (for example output_layers=["unembed"]).
# 3) Compare tracks: delta = ALT_track - REF_track.
# 4) Optionally compare embeddings: ||ALT_embedding - REF_embedding|| per position.
```

Always label this output as a proxy score, not a native Evo2 variant endpoint.

## Reproducible workflow script

For a full hosted run with plots (interval forward/embedding/generation + variant proxy), use:

```bash
python evo2-inference/scripts/run_real_evo2_workflow.py
```

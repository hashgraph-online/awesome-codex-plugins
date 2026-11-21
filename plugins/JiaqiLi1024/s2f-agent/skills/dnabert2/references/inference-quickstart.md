# Inference Quickstart

Use this file for embedding extraction with DNABERT2.

## Minimal embedding example

```python
import torch
import transformers
from transformers import AutoTokenizer, AutoModel
from transformers.models.bert.configuration_bert import BertConfig

model_id = "zhihan1996/DNABERT-2-117M"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
if tuple(int(x) for x in transformers.__version__.split(".")[:2]) > (4, 28):
    config = BertConfig.from_pretrained(model_id)
    model = AutoModel.from_pretrained(model_id, trust_remote_code=True, config=config)
else:
    model = AutoModel.from_pretrained(model_id, trust_remote_code=True)

seq = "ACGTAGCATCGGATCTATCTATCGACACTTGGTTATCGATCTACGAGCATCTCGTTAGC"
input_ids = tokenizer(seq, return_tensors="pt")["input_ids"]

with torch.no_grad():
    hidden_states = model(input_ids)[0]  # [1, sequence_length, 768]

embedding_mean = hidden_states[0].mean(dim=0)
embedding_max = hidden_states[0].max(dim=0).values

print("hidden", tuple(hidden_states.shape))
print("mean", tuple(embedding_mean.shape))
print("max", tuple(embedding_max.shape))
```

## Coordinate-based real inference + PCA plot

```python
import subprocess

subprocess.run(
    [
        "python",
        "scripts/embed_interval_plot.py",
        "--species",
        "human",
        "--assembly",
        "hg38",
        "--chrom",
        "chr19",
        "--start",
        "6700000",
        "--end",
        "6702768",
        "--output-dir",
        "tmp/dnabert2_interval_demo",
    ],
    check=True,
)
```

Main outputs:

- `embedding_pca.png`
- `run_metadata.json`
- optional `token_embeddings.npy` (if `--save-token-embeddings` is set)

## Notes

- Keep `trust_remote_code=True` in grounded examples.
- DNABERT2 embeddings are `768`-dimensional in the published `117M` checkpoint.
- For coordinate workflows, report interval convention (`[start, end)`), sequence source, and fetched bp length.

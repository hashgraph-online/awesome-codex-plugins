---
name: hyenadna-inference
description: Use the HyenaDNA repository for long-context single-nucleotide DNA embeddings, Hugging Face checkpoint loading, downstream classification, pretraining, and fine-tuning. Use when Codex needs the `LongSafari/hyenadna-*` checkpoints, `CharacterTokenizer`, `huggingface.py`, `standalone_hyenadna.py`, Hydra `train.py`, or sequence-length/GPU planning.
---

# Hyenadna Inference

# HyenaDNA Inference

## Choose the path

1. Use the repository's Python 3.8+, PyTorch 1.13/CUDA 11.7, requirements, and Flash Attention setup. Clone with submodules when using the full training code; the standalone/Hugging Face path still needs the model dependencies.
2. For pretrained embeddings, select a checkpoint whose maximum length matches the request: `hyenadna-tiny-1k-seqlen`, `small-32k-seqlen`, `medium-160k-seqlen`, `medium-450k-seqlen`, or `large-1m-seqlen`. Read [references/inference-and-training.md](references/inference-and-training.md) before sizing memory or writing a loader.
3. The grounded standalone pattern is `HyenaDNAPreTrainedModel.from_pretrained(...)` plus `CharacterTokenizer` over `A,C,G,T,N`, left padding, and `model.eval()` under `torch.inference_mode()`. The model returns embedding tensors; a classification head requires `use_head=True` and an explicit class count.
4. For repository training/fine-tuning, use Hydra commands such as `python -m train wandb=null experiment=hg38/genomic_benchmark ...` or the documented `hg38/hg38_hyena` pretraining config. Keep dataset, max length, checkpoint, and device settings explicit.

## Hard boundaries

- Sequence length is a model/checkpoint constraint, not a cosmetic parameter. Do not feed 450k or 1M bases to a 1k/32k checkpoint without a deliberate windowing plan.
- The tokenizer adds/handles special-token accounting through `model_max_length=max_length + 2`; preserve the repository's left-padding behavior for causal HyenaDNA.
- Long-context inference is GPU- and memory-intensive; an embedding example on a short sequence is not evidence that the 1M model fits the user's hardware.
- HyenaDNA's training code uses PyTorch Lightning/Hydra and optional Flash Attention. Do not route Caduceus RC-equivariant or Hugging Face masked-LM requests here unless the user names HyenaDNA.

## References

- Read [references/inference-and-training.md](references/inference-and-training.md) for checkpoint limits, tokenizer/model-loading patterns, output expectations, and grounded training commands.

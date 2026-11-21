# HyenaDNA Inference and Training

Source: `Readme/hyena-dna-main/README.md`, `huggingface.py`, and `standalone_hyenadna.py`.

## Environment

The documented path clones with submodules, creates Python 3.8+, installs PyTorch 1.13 with CUDA 11.7, installs `requirements.txt`, and builds Flash Attention from the submodule. Docker images are also documented. The full Hydra training repository is heavier than the standalone embedding example.

## Checkpoint limits

```text
LongSafari/hyenadna-tiny-1k-seqlen       1,024
LongSafari/hyenadna-small-32k-seqlen    32,768
LongSafari/hyenadna-medium-160k-seqlen 160,000
LongSafari/hyenadna-medium-450k-seqlen 450,000
LongSafari/hyenadna-large-1m-seqlen   1,000,000
```

The source wrapper downloads a checkpoint into `./checkpoints/<model_name>` with Git LFS when `download=True`, reads `config.json` and `weights.ckpt`, and loads it with `HyenaDNAPreTrainedModel.from_pretrained(...)`.

## Tokenizer and embeddings

`CharacterTokenizer` uses `A,C,G,T,N`, `add_special_tokens=False`, `model_max_length=max_length + 2`, and left padding because HyenaDNA is causal. The README example builds token IDs, sends a batch tensor to the selected device, calls `model.eval()`, and runs `model(tok_seq)` under `torch.inference_mode()`. The result is the embedding tensor; a decoder head is optional through `use_head=True` and `n_classes`.

## Training and fine-tuning

The quick smoke command is:

```bash
python -m train wandb=null experiment=hg38/genomic_benchmark
```

Human-genome pretraining uses `experiment=hg38/hg38_hyena` plus explicit `model.d_model`, `model.n_layer`, `dataset.max_length`, batch size, optimizer, and trainer device overrides. The `data/hg38/` layout contains `hg38.ml.fa` and `human-sequences.bed`. Keep Hydra config names and checkpoint paths explicit; do not assume an arbitrary FASTA is accepted by every configured dataset without adding a dataloader.


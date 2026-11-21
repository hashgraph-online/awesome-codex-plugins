---
name: caduceus-inference
description: Use Caduceus bi-directional equivariant long-range DNA models for Hugging Face masked-language inference, reverse-complement-aware embeddings, pretraining, fine-tuning, and the Long Range Benchmark VEP embedding dump. Use when Codex needs Caduceus-Ph/PS model loading, `vep_embeddings.py`, Hydra `train.py`, `--rcps`, or 131k-token sequence handling.
---

# Caduceus Inference

## Choose the path

1. For direct masked-LM inference, load the published Hugging Face checkpoint with `AutoTokenizer` and `AutoModelForMaskedLM`. The documented checkpoints are Caduceus-Ph and Caduceus-PS at 131k sequence length; PS is reverse-complement (RC) equivariant, while Ph was trained with RC augmentation.
2. For Long Range Benchmark eQTL/SNP embeddings, use `vep_embeddings.py` with `torchrun` and a Hugging Face model path. The script loads `InstaDeepAI/genomics-long-range-benchmark`, tokenizes reference/alternate and RC sequences, extracts a local window around the variant, and saves `train_embeds_combined.pt` / `test_embeds_combined.pt`. Read [references/inference-and-training.md](references/inference-and-training.md) for the exact argument contract.
3. Set `--rcps` only for an RC-equivariant checkpoint such as Caduceus-PS; use `--no-rcps` for models without the property. Keep `--seq_len`, `--bp_per_token`, `--embed_dump_batch_size`, and the model path consistent with the checkpoint.
4. For pretraining or downstream fine-tuning, use the repository's Hydra entry point `python -m train ...`, explicit `model=caduceus`, dataset config, checkpoint path, and `wandb=null` for offline runs. Use the provided data layout and do not turn a VEP embedding dump into a training command.

## Hard boundaries

- The embedding script initializes NCCL distributed execution and assumes CUDA devices; a CPU-only dry run is not equivalent.
- `vep_embeddings.py` is a benchmark-specific pipeline and requires the benchmark's ref/alt sequence fields. For arbitrary FASTA embeddings, use the Hugging Face API instead.
- Preserve RC behavior: PS combines equivariant channels; non-RCPS models run explicit reverse-complement sequences. Do not average orientations without explaining the choice.
- Caduceus is distinct from HyenaDNA and Nucleotide Transformer even though the training entry point is Hydra-based.

## References

- Read [references/inference-and-training.md](references/inference-and-training.md) for checkpoint names, `torchrun` arguments, output tensors, data layout, and grounded training examples.

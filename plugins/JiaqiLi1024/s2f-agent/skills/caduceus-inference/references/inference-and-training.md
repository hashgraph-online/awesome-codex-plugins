# Caduceus Inference and Training

Source: `Readme/caduceus-main/README.md` and `vep_embeddings.py`.

## Published checkpoints

The documented Hugging Face checkpoints are:

```text
kuleshov-group/caduceus-ph_seqlen-131k_d_model-256_n_layer-16
kuleshov-group/caduceus-ps_seqlen-131k_d_model-256_n_layer-16
```

Both use 131k-token sequences, 256 model width, and 16 layers. Caduceus-Ph uses RC data augmentation; Caduceus-PS is RC equivariant. Direct masked-LM loading is:

```python
from transformers import AutoModelForMaskedLM, AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForMaskedLM.from_pretrained(model_name)
```

## VEP embedding dump

The source command is distributed over NCCL processes:

```bash
torchrun --standalone --nnodes=1 --nproc-per-node=8 vep_embeddings.py \
  --num_workers=2 --seq_len=131072 --bp_per_token=1 \
  --embed_dump_batch_size=1 \
  --name=caduceus-ps_downstream-seqlen=131k \
  --model_name_or_path=kuleshov-group/caduceus-ps_seqlen-131k_d_model-256_n_layer-16 \
  --rcps
```

Arguments include `--downstream_save_dir`, `--name`, `--seq_len`, `--bp_per_token`, `--embed_dump_batch_size`, `--num_workers`, and mutually opposite `--rcps` / `--no-rcps`. The script downloads/loads the `InstaDeepAI/genomics-long-range-benchmark` `variant_effect_gene_expression` task, filters high-N reference sequences, tokenizes ref/alt and reverse-complement sequences, then writes per-rank `.pt` files and combined `train_embeds_combined.pt` / `test_embeds_combined.pt`. The combined dictionaries contain `concat_avg_ws`, `rc_concat_avg_ws`, chromosome, labels, distance-to-TSS, and tissue encodings.

## Training data and command

Use the `data/hg38/hg38.ml.fa` and `human-sequences.bed` layout documented in the README. The source training entry point is Hydra:

```bash
python -m train experiment=hg38/hg38 dataset.max_length=1024 \
  dataset.batch_size=1024 dataset.mlm=true model=caduceus wandb=null
```

Fine-tuning adds an experiment such as `hg38/genomic_benchmark`, a saved `model.config_path`, `train.pretrained_model_path`, and explicit `dataset`/`decoder` RC conjoining options.


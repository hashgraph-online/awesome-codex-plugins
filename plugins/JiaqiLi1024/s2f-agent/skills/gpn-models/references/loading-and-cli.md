# Loading And CLI

Use this file for grounded installation, model loading, and single-sequence `GPN` command patterns.

## Install

Install directly from GitHub:

```bash
pip install git+https://github.com/songlab-cal/gpn.git
```

For editable development:

```bash
git clone https://github.com/songlab-cal/gpn.git
cd gpn
pip install -e .
```

Practical compatibility note (observed in real runs):

```bash
# Avoid NumPy 2.x ABI issues with torch-dependent GPN flows
pip install "numpy<2"
```

If Hugging Face downloads fail with Xet range/reconstruction errors, retry with:

```bash
HF_HUB_DISABLE_XET=1 python your_script.py
```

## Load `GPN`

```python
import gpn.model
from transformers import AutoModelForMaskedLM

model = AutoModelForMaskedLM.from_pretrained("songlab/gpn-brassicales")
```

## Load `GPN-MSA`

```python
import gpn.model
from transformers import AutoModelForMaskedLM

model = AutoModelForMaskedLM.from_pretrained("songlab/gpn-msa-sapiens")
```

## Load `PhyloGPN`

```python
from transformers import AutoModel

model = AutoModel.from_pretrained("songlab/PhyloGPN", trust_remote_code=True)
```

## Load `GPN-Star`

```python
import gpn.star.model
from transformers import AutoModelForMaskedLM

model = AutoModelForMaskedLM.from_pretrained("songlab/gpn-star-hg38-p243-200m")
```

## Build a single-sequence `GPN` dataset

Use the documented Snakemake workflow:

```bash
cd workflow/make_dataset
snakemake --cores all
```

The README says to configure `config/config.yaml` and `config/assemblies.tsv` first.

## Train single-sequence `GPN`

Use the documented `gpn.ss.run_mlm` entry point:

```bash
WANDB_PROJECT=your_project torchrun --nproc_per_node=$(echo $CUDA_VISIBLE_DEVICES | awk -F',' '{print NF}') -m gpn.ss.run_mlm --do_train --do_eval \
    --report_to wandb --prediction_loss_only True --remove_unused_columns False \
    --dataset_name results/dataset --tokenizer_name gonzalobenegas/tokenizer-dna-mlm \
    --soft_masked_loss_weight_train 0.1 --soft_masked_loss_weight_evaluation 0.0 \
    --weight_decay 0.01 --optim adamw_torch \
    --dataloader_num_workers 16 --seed 42 \
    --save_strategy steps --save_steps 10000 --evaluation_strategy steps \
    --eval_steps 10000 --logging_steps 10000 --max_steps 120000 --warmup_steps 1000 \
    --learning_rate 1e-3 --lr_scheduler_type constant_with_warmup \
    --run_name your_run --output_dir your_output_dir --model_type GPN \
    --per_device_train_batch_size 512 --per_device_eval_batch_size 512 --gradient_accumulation_steps 1 --total_batch_size 2048 \
    --torch_compile \
    --ddp_find_unused_parameters False \
    --bf16 --bf16_full_eval
```

## Extract embeddings

Input file must contain `chrom`, `start`, and `end` columns.

```bash
torchrun --nproc_per_node=$(echo $CUDA_VISIBLE_DEVICES | awk -F',' '{print NF}') -m gpn.ss.get_embeddings \
    windows.parquet genome.fa.gz 100 your_output_dir results.parquet \
    --per_device_batch_size 4000 --is_file --dataloader_num_workers 16
```

## Run variant effect prediction

Input file must contain `chrom`, `pos`, `ref`, and `alt` columns.

```bash
torchrun --nproc_per_node=$(echo $CUDA_VISIBLE_DEVICES | awk -F',' '{print NF}') -m gpn.ss.run_vep \
    variants.parquet genome.fa.gz 512 your_output_dir results.parquet \
    --per_device_batch_size 4000 --is_file --dataloader_num_workers 16
```

Keep these CLI patterns scoped to the single-sequence `GPN` path unless a separate grounded command is available for the other families.

## Single-site `predict_variant` example script

For one-off single-site scoring (without preparing a variants parquet), use:

```bash
python references/predict_variant_single_site.py \
    --genome hg38 \
    --chrom chr12 \
    --pos 1000000 \
    --model-id songlab/gpn-msa-sapiens \
    --alt-rule to_G_unless_ref_G_then_T \
    --output-json tmp/hg38/gpn_predict_variant_chr12_1000000.json
```

This script reports:
- `llr_fwd`
- `llr_rev`
- `llr_mean` (strand-averaged)

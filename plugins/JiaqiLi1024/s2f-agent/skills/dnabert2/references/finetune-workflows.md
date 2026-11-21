# Finetune Workflows

Use this file for GUE evaluation and custom-dataset fine-tuning.

## Evaluate on GUE

```bash
export DATA_PATH=/path/to/GUE_root
cd finetune

# DNABERT-2 on GUE
sh scripts/run_dnabert2.sh "$DATA_PATH"

# Optional baselines from the same repo
sh scripts/run_dnabert1.sh "$DATA_PATH" 3
sh scripts/run_nt.sh "$DATA_PATH" 0
```

## Custom dataset format

Prepare one folder with:

- `train.csv`
- `dev.csv`
- `test.csv`

Single-sequence format (default):

```csv
sequence,label
ACGTCAGTCAGCGTACGT,1
TTGCAAGTCCGTTAACGA,0
```

`train.py` also supports 3-column sequence-pair rows (`seq1,seq2,label`).

## Custom fine-tuning (single process / DataParallel style)

```bash
cd finetune
export DATA_PATH=/path/to/your_data
export MAX_LENGTH=100
export LR=3e-5

python train.py \
  --model_name_or_path zhihan1996/DNABERT-2-117M \
  --data_path "$DATA_PATH" \
  --kmer -1 \
  --run_name DNABERT2_custom \
  --model_max_length "$MAX_LENGTH" \
  --per_device_train_batch_size 8 \
  --per_device_eval_batch_size 16 \
  --gradient_accumulation_steps 1 \
  --learning_rate "$LR" \
  --num_train_epochs 5 \
  --fp16 \
  --save_steps 200 \
  --output_dir output/dnabert2 \
  --evaluation_strategy steps \
  --eval_steps 200 \
  --warmup_steps 50 \
  --logging_steps 100 \
  --overwrite_output_dir True \
  --log_level info \
  --find_unused_parameters False
```

## Custom fine-tuning (DDP)

```bash
cd finetune
export DATA_PATH=/path/to/your_data
export MAX_LENGTH=100
export LR=3e-5
export NUM_GPU=4

torchrun --nproc_per_node="$NUM_GPU" train.py \
  --model_name_or_path zhihan1996/DNABERT-2-117M \
  --data_path "$DATA_PATH" \
  --kmer -1 \
  --run_name DNABERT2_custom_ddp \
  --model_max_length "$MAX_LENGTH" \
  --per_device_train_batch_size 8 \
  --per_device_eval_batch_size 16 \
  --gradient_accumulation_steps 1 \
  --learning_rate "$LR" \
  --num_train_epochs 5 \
  --fp16 \
  --save_steps 200 \
  --output_dir output/dnabert2 \
  --evaluation_strategy steps \
  --eval_steps 200 \
  --warmup_steps 50 \
  --logging_steps 100 \
  --overwrite_output_dir True \
  --log_level info \
  --find_unused_parameters False
```

## Practical tuning notes

- Start with `model_max_length ~= 0.25 * input_bp_length` (README guidance).
- Keep `--kmer -1` for DNABERT2.
- The official GUE scripts assume a 4-GPU setup and tune per-device batch sizes accordingly.
- Evaluation outputs are saved to `output_dir/results/<run_name>/eval_results.json`.

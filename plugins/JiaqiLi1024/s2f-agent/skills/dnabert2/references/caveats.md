# Caveats

Use this file to handle DNABERT2 pitfalls quickly.

## 1) `kmer != -1` can trigger distributed-rank assumptions

The provided `train.py` calls `torch.distributed.get_rank()` inside the k-mer preprocessing branch.

- Safe DNABERT2 default: keep `--kmer -1`.
- If users intentionally enable k-mer mode, ensure distributed init assumptions are handled.

## 2) `trust_remote_code=True` is part of the grounded path

Both tokenizer/model loading and sequence-classification loading use remote code in official examples.

## 3) `model_max_length` is token length, not raw base-pair length

The README guidance uses an approximation (`~0.25 * bp_length`) because tokenization compresses sequence length.

## 4) CSV expectations

- `train.py` reads CSV and skips the first row as header.
- Rows must be consistent 2-column (`sequence,label`) or 3-column (`seq1,seq2,label`).
- Labels are cast to `int`.

## 5) Mixed precision is hardware-dependent

`--fp16` is common in official commands for GPU. Disable mixed precision for strict CPU environments.

## 6) Pre-training is not fully packaged in this repo

README points to MosaicBERT and HF `run_mlm.py` references for pre-training replication, not a one-command local script in this source tree.

## 7) Expected warnings during embedding-only inference

When loading `BertModel` from the DNABERT2 checkpoint, the following warnings are expected:

- MLM-head weights are unused (`cls.predictions.*`).
- Pooler weights may be newly initialized.
- ALiBi size may increase for longer sequences (`Increasing alibi size from 512 ...`).
- Missing Triton may trigger a throughput warning and fallback to PyTorch attention.

These warnings do not usually indicate failure for embedding extraction workflows.

## 8) Coordinate-to-sequence workflows need explicit provenance

- Always verify coordinate convention (`[start, end)`), assembly, and chromosome naming.
- Confirm fetched sequence length equals `end - start`.
- Record sequence source (local FASTA/2bit or remote API URL) in metadata for reproducibility.

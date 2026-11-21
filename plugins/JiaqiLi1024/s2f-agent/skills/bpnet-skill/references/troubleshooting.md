# Troubleshooting

Use these checks before changing model architecture or patching upstream code.

## CLI Mismatches

- Use `bpnet-shap --output-directory`; `--output-dir` in the README does not match the parser.
- Do not use `bpnet-motif` or `bpnet-embeddings`; their `setup.py` entry points are commented out.
- Pass a real `--splits` file to `bpnet-train` even though the parser does not mark it required; `bpnettrainer.py` calls `os.path.isfile(args.splits)`.
- Pass `--model-output-filename` unless `--automate-filenames` is selected. The legacy validation around an empty default is ineffective.

## Input Failures

- If a task raises `KeyError: 'bias'`, add `"bias": {"source": [], "smoothing": []}`.
- If a task ID or split ID raises a lookup error, renumber top-level keys contiguously from `"0"`.
- If bias smoothing fails, make `bias.smoothing` the same length as `bias.source`; use `null` for an unsmoothed control.
- If background sampling reports insufficient loci, lower the corresponding ratio or provide more GC-matched negatives.
- If peaks disappear at chromosome ends, account for half the input length and any training jitter on both sides of the summit.
- If relative input paths appear missing, run from the directory against which those paths were authored or rewrite them explicitly.

## Shape And Model Failures

- Match JSON `input_len` to CLI `--input-seq-len`.
- Match JSON `output_profile_len` to CLI `--output-len`.
- Keep prediction `--output-window-size` no larger than `--output-len`.
- Set the final standard-loss `counts_head_params.units` entry to the task count or `-1`.
- Give `profile_bias_module_params.kernel_sizes` one entry per task when any task has controls.
- Keep `loss_weights` as two numeric values and `counts_loss` as `MSE` or `POISSON`.

## Output Failures

- Create base output directories before train, predict, and SHAP.
- Supply `--chrom-sizes` with `--generate-shap-bigWigs`; otherwise the source warns and skips bigWig conversion.
- Restrict `bpnet-predict` to one or two total signal tracks; the source currently asserts this range.
- Use only `--chroms` or `--sample` for SHAP selection.

## Runtime Failures

- Reproduce under Python 3.7, TensorFlow 2.4.1, and TensorFlow Probability 0.12.2 before diagnosing a legacy BPNet bug on a newer stack.
- Check GPU visibility with `nvidia-smi`, then distinguish driver/CUDA failures from Python import failures.
- Reduce `--batch-size` for GPU memory errors and reduce `--threads` when a small dataset cannot fill `threads * batch_size` samples.
- Treat the Docker image as the closest upstream-documented reproducibility path when local dependency resolution fails.

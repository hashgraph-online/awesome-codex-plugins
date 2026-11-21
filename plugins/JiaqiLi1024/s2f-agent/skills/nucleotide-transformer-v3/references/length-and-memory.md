# Length And Memory

Use this file when the request depends on sequence geometry or memory pressure.

## Divisibility rule

NTv3 uses a U-Net-like architecture with downsampling and upsampling, so sequence length must be divisible by `2^num_downsamples`.

Grounded rules:

- 7 downsample models: length divisible by `128`
- 5 downsample models: length divisible by `32`
- General rule: `divisor = 2 ** model.config.num_downsamples`

## Tokenization and sequence handling

- In the HF path, use `pad_to_multiple_of=divisor` where `divisor` is derived from the loaded model config.
- Crop to nearest valid length when exact endpoints are not critical.
- If padding is necessary, pad with `N` tokens.
- Do not recommend `[PAD]` tokens for biological sequence padding.
- Use [scripts/check_valid_length.py](../scripts/check_valid_length.py) to validate a concrete length.

## Output-length rule for post-trained heads

- `outs["logits"]` remains full length.
- `outs["bigwig_tracks_logits"]` and `outs["bed_tracks_logits"]` keep center positions only.
- Compute cropped length via `int(input_len * model.config.keep_target_center_fraction)` instead of hardcoding `37.5%`.

## Memory and dtype

- GPU inference can use reduced precision to cut memory usage.
- Typical setup from the tutorial:
  - `torch.bfloat16` on Ampere+ GPUs (`compute capability >= 8`)
  - `torch.float16` on older CUDA GPUs
  - `torch.float32` on CPU
- Legacy JAX helper path supports `use_bfloat16=True` when available.

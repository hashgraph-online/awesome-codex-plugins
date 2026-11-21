# Setup And Troubleshooting

Use this file when SegmentNT-family code fails to install, import, or run.

## Recommended environment baseline

- Use Python `3.10+` for practical compatibility with current JAX stacks.
- For this repository deployment, prefer `./scripts/provision_stack.sh nt-jax`.

## Minimal import smoke check

```python
from nucleotide_transformer.pretrained import get_pretrained_segment_nt_model
from nucleotide_transformer.enformer.pretrained import get_pretrained_segment_enformer_model
from nucleotide_transformer.borzoi.pretrained import get_pretrained_segment_borzoi_model
```

## Runtime smoke checks

```bash
python segment-nt/scripts/compute_rescaling_factor.py --sequence-length-bp 40008
```

```bash
python segment-nt/scripts/run_segment_nt_region.py --species human --assembly hg38 --chrom chr19 --start 6700000 --end 6732768
```

```bash
bash scripts/smoke_test.sh
```

## Common failure modes

1. Apple Silicon + x86 Python (AVX / jaxlib crash)
- On arm64 Macs, running x86 Python/JAX often fails with AVX-related errors.
- Use an arm64 environment (`platform.machine() == "arm64"`), then reinstall JAX/JAXLIB there.

2. Sequence includes `N` for SegmentNT
- SegmentNT docs explicitly state this path does not handle `N`.
- Fix by selecting a sequence/window without `N`, or switch family if biological requirements permit.

3. SegmentNT length or token divisibility mismatch
- SegmentNT requires `num_dna_tokens_excluding_cls` divisible by `4`.
- For no-`N` inputs, compute tokens with `floor(bp / 6) + (bp % 6)` (not `ceil(bp / 6)`).
- Validate token assumptions early with:
  - `python segment-nt/scripts/compute_rescaling_factor.py --sequence-length-bp <bp>`

4. Long SegmentNT inference behaves poorly beyond training length
- For contexts beyond 30 kb, set `rescaling_factor=num_tokens_inference/2048`.
- Keep `max_positions` aligned to `num_tokens_inference` (includes CLS).

5. `pmap` shape mismatch on tokens
- For multi-device `pmap`, input tensors must include a leading device axis.
- Notebook pattern:
  - `tokens = jnp.stack([jnp.asarray(tokens_ids, dtype=jnp.int32)] * num_devices, axis=0)`

6. `transform_with_state` misuse for SegmentEnformer / SegmentBorzoi
- These paths require `hk.transform_with_state(...)`.
- `apply` returns `(outs, state)` and state must be threaded.

7. Download/cache issues while fetching checkpoints
- First run can download very large files (SegmentNT weights are multi-GB); this may take many minutes.
- Interrupted downloads may leave `.incomplete` blobs.
- If repeated checkpoint load failures occur, clear the NT cache and retry.
- Typical cache path:
  - `~/.cache/nucleotide_transformer/`

8. Memory pressure / device instability
- Start on CPU by setting `jax.config.update("jax_platform_name", "cpu")`.
- Reduce sequence length, batch size, or requested saved tensors (embeddings/attention maps).
- Expect first-run compilation overhead on JAX.

## Practical defaults for stable first run

- SegmentNT:
  - `model_name="segment_nt"`
  - one short sequence first
  - no `N`
  - no extra saved attention maps unless needed
- SegmentEnformer / SegmentBorzoi:
  - single-sequence dry run
  - confirm logits shape and one feature extraction before scaling up

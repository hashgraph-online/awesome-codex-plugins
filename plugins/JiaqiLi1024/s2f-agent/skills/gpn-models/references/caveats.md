# Caveats

Use this file when the request involves unclear model selection, alignment assumptions, or support questions.

## Alignment boundaries

- `GPN` uses unaligned genomes.
- `GPN-MSA` requires aligned genomes for both training and inference.
- `PhyloGPN` uses alignments during training, but does not require them for inference or fine-tuning.
- `GPN-Star` requires aligned genomes for both training and inference.

If the user does not have an alignment available at inference time, do not steer them to `GPN-MSA` or `GPN-Star`.

## Deprecation note

- The README says `GPN-MSA` is deprecated in favor of `GPN-Star`.
- Mention this when users ask for a new alignment-based workflow without naming a specific family.

## Grounding boundary

- The README gives explicit CLI training, embeddings, and VEP commands only for the single-sequence `GPN` path.
- For `GPN-MSA`, `PhyloGPN`, and `GPN-Star`, prefer grounded model-loading snippets and route detailed usage to the linked notebooks or analysis directories.
- Do not invent tokenizer calls, prediction wrappers, or hidden preprocessing steps for those families without verification.

## Runtime compatibility and download stability

- Some `torch` + `numpy` combinations fail with NumPy 2.x ABI warnings/errors in `gpn.ss` flows.
- If this appears, pin NumPy below 2 (`numpy<2`) in the active environment.
- If model downloads from Hugging Face fail with Xet-related range/reconstruction errors, retry with `HF_HUB_DISABLE_XET=1`.

## Tokenizer and checkpoint caveat

- Do not assume every checkpoint repo is self-contained for `AutoTokenizer.from_pretrained(model_id)`.
- In practice, some checkpoints (for example `songlab/gpn-msa-sapiens`) may need explicit tokenizer handling instead of loading tokenizer directly from the same repo id.
- Validate tokenizer vocabulary against model input expectations before running variant scoring.

## CLI execution caveat for `gpn.ss.run_vep`

- `gpn.ss.run_vep` uses `TrainingArguments` with `torch_compile=True` and `fp16=True`.
- On CPU-only or unsupported hardware/software stacks this can fail even when the command syntax is correct.
- If this happens, prefer a custom inference script that runs `model.eval()` without forced `fp16`/`torch_compile`, or run on a GPU stack known to support these settings.

## Training on other species

- For GPN-MSA training on other species, the README points to GitHub issues and discussions instead of a direct command recipe.
- Another source for plant alignments named in the README is PlantRegMap.
- Treat these as pointers, not as fully grounded workflows.

## Support links

- Direct usage questions to GitHub Discussions.
- Direct bugs or feature requests to GitHub Issues.

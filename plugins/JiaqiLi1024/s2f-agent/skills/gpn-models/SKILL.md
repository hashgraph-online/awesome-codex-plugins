---
name: gpn-models
description: Choose and use the Song Lab GPN model family, including GPN, GPN-MSA, PhyloGPN, and GPN-Star, for genomic language model loading, embeddings, training, and variant-effect workflows. Use when Codex needs to write, fix, explain, or review Python, Hugging Face, `torchrun`, Snakemake, notebook, or shell workflows involving `gpn`, `gpn.model`, `gpn.star.model`, `AutoModelForMaskedLM`, `AutoModel`, GPN single-sequence training, embeddings extraction, or GPN variant-effect prediction.
---

# GPN Models

## Overview

Use this skill to keep GPN-family responses aligned with the repo README. Start by choosing the model family, then use only the grounded load patterns and CLI workflows that the bundled source actually demonstrates.

## Follow This Decision Flow

1. Choose the model family.
- Use `GPN` for single-sequence modeling on unaligned genomes.
- Use `GPN-MSA` only when aligned genomes are available for inference, and note that the README marks it as deprecated in favor of `GPN-Star`.
- Use `PhyloGPN` when the user wants phylogenetic modeling that uses alignments during training but does not require them for inference or fine-tuning.
- Use `GPN-Star` when the user has aligned genomes for training and inference and wants the newer phylogeny-aware alignment model.

2. Choose the loading path.
- Use Hugging Face `AutoModelForMaskedLM` for `GPN`, `GPN-MSA`, and `GPN-Star`.
- Import the registration module first when the README does so, such as `import gpn.model` or `import gpn.star.model`.
- Use `AutoModel` with `trust_remote_code=True` for `PhyloGPN`.

3. Choose the task type.
- Use model loading snippets for quick experimentation or notebook setup.
- Use the single-sequence `GPN` CLI examples for training, embeddings extraction, and variant effect prediction.
- Route notebook-specific details to the linked examples rather than inventing hidden preprocessing steps.

4. Respect alignment and input requirements.
- Call out whether the method needs aligned genomes at inference time.
- For `gpn.ss.get_embeddings`, require input columns `chrom`, `start`, and `end`.
- For `gpn.ss.run_vep`, require input columns `chrom`, `pos`, `ref`, and `alt`.

5. Keep training guidance grounded.
- Present the documented Snakemake dataset workflow and `torchrun` commands when the user asks for training on their own data.
- Do not fabricate GPN-MSA or GPN-Star training commands beyond what the README links to.

6. For single-site `predict_variant` requests, use an explicit scoring workflow.
- Validate the reference base at the requested coordinate from the target genome sequence source before constructing `ref>alt`.
- For single-sequence `GPN` scoring, use a fixed window centered on the variant, mask the center token, and compute `LLR = logit(alt) - logit(ref)`.
- Report forward, reverse-complement, and mean score when both strands are evaluated.
- Do not route single-site requests to `GPN-MSA` or `GPN-Star` unless aligned inputs and species metadata are actually available.

## Grounded API Surface

Treat the following patterns as grounded by the bundled README:

- `pip install git+https://github.com/songlab-cal/gpn.git`
- `pip install -e .`
- `import gpn.model`
- `import gpn.star.model`
- `from transformers import AutoModelForMaskedLM`
- `from transformers import AutoModel`
- `AutoModelForMaskedLM.from_pretrained("songlab/gpn-brassicales")`
- `AutoModelForMaskedLM.from_pretrained("songlab/gpn-msa-sapiens")`
- `AutoModelForMaskedLM.from_pretrained("songlab/gpn-star-hg38-p243-200m")`
- `AutoModel.from_pretrained("songlab/PhyloGPN", trust_remote_code=True)`
- `snakemake --cores all`
- `python -m gpn.ss.run_mlm ...`
- `python -m gpn.ss.get_embeddings ...`
- `python -m gpn.ss.run_vep ...`

Verify any additional tokenizer API, preprocessing helper, or scoring function against the installed package or linked notebooks before using it.

## Execution Notes

- Prefer `numpy<2` when `torch`/ABI errors appear in real environments.
- If Hugging Face model downloads fail with Xet range errors, retry with `HF_HUB_DISABLE_XET=1`.
- Treat `gpn.ss.run_vep` defaults (`fp16`, `torch_compile`) as hardware-sensitive. For CPU-only contexts, consider a custom inference path without forced mixed precision/compile.

## Response Style

- Prefer a family-selection recommendation before giving code.
- State clearly when alignments are required for either training or inference.
- Mention that `GPN-MSA` is deprecated in favor of `GPN-Star` when relevant.
- Surface input schema requirements before suggesting embedding or VEP CLI runs.

## References

- Read [references/framework-selection.md](references/framework-selection.md) to choose between GPN, GPN-MSA, PhyloGPN, and GPN-Star.
- Read [references/loading-and-cli.md](references/loading-and-cli.md) for installation, model loading, and grounded `gpn.ss` commands.
- Read [references/caveats.md](references/caveats.md) for deprecation notes, alignment boundaries, and support links.
- Use [references/predict_variant_single_site.py](references/predict_variant_single_site.py) for reproducible one-site `predict_variant` scoring with forward/reverse LLR outputs.

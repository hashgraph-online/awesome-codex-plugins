---
name: spliceai-workflows
description: Use the Illumina SpliceAI 1.3.1 workflows to annotate splice-altering variants in VCF files or score custom DNA sequences. Use when Codex needs to install, run, interpret, or troubleshoot the `spliceai` CLI, delta scores, delta positions, reference FASTA, or GENCODE/custom annotations; do not use for Pangolin tissue-specific splice scores.
---

# SpliceAI Workflows

## Grounded workflow

1. Confirm the task is SpliceAI v1.3.1 from `Readme/SpliceAI-master`, not another splice predictor. Use the bundled `spliceai` console entry point or the documented Python ensemble path.
2. For VCF annotation, require a reference FASTA and an annotation source. Use the bundled `grch37`/`grch38` canonical annotation only when the requested build matches; otherwise pass a custom annotation file.
3. Run the smallest command for the requested stage:

```bash
spliceai -I input.vcf -O output.vcf -R genome.fa -A grch38
```

Use `-D` to change the maximum splice-site distance (default 50) and `-M 1` for masked scores. Read [references/cli-and-semantics.md](references/cli-and-semantics.md) before changing these defaults or explaining output fields.
4. Report the `ALLELE|SYMBOL|DS_AG|DS_AL|DS_DG|DS_DL|DP_AG|DP_AL|DP_DG|DP_DL` INFO fields. The maximum delta score is a 0-1 splice-altering score; delta positions are relative to the variant.
5. For custom sequence scoring, use the five packaged Keras models, 10,000 bp context, `one_hot_encode`, and mean predictions. Do not present this as VCF annotation because it has no gene/allele annotation layer.

## Hard boundaries

- Only SNVs and simple indels where REF or ALT is one base are annotated, and only variants inside genes in the annotation file are scored.
- Variants near chromosome ends, deletions longer than twice `-D`, or REF/FASTA mismatches are skipped by the upstream workflow; preserve and report that behavior.
- The trained models are CC BY-NC 4.0 and the source is PolyForm Strict; flag academic/non-commercial licensing before proposing redistribution or commercial use.
- Do not substitute Pangolin's tissue-specific predictions, bcftools normalization, or an invented Python wrapper for the documented CLI.

## References

- Read [references/cli-and-semantics.md](references/cli-and-semantics.md) for option semantics, output interpretation, custom-sequence inference, and failure checks.

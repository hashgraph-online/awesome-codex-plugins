---
name: pangolin-workflows
description: Use the Pangolin 1.0.2 workflows for tissue-specific splice-site strength and variant-effect prediction from VCF or CSV inputs. Use when Codex needs the `pangolin` CLI, gffutils annotation database creation, masking, score cutoffs, distance windows, or custom-sequence usage; do not use for SpliceAI's delta-score workflow.
---

# Pangolin Workflows

## Grounded workflow

1. Confirm a Python 3.6+ environment with PyTorch and the documented `pyvcf`, `gffutils`, `biopython`, `pandas`, and `pyfastx` dependencies. Install the checkout with `pip install .` after the dependencies are available.
2. Build or select a gffutils database before prediction. The upstream path is `python scripts/create_db.py annotation.gtf` and the result is an annotation `.db` file.
3. Run the positional CLI with a VCF or CSV, reference FASTA, annotation database, and output prefix:

```bash
pangolin variants.vcf reference.fa annotation.db result_prefix
```

For CSV, use `--column_ids CHROM,POS,REF,ALT` when the header differs. Use `--mask True|False`, `--score_cutoff`, and `--distance` only when the user specifies the desired semantics. Read [references/cli-and-semantics.md](references/cli-and-semantics.md) for exact output and defaults.
4. Explain whether the result reports only the largest increase/decrease in a 50 bp window (default) or all absolute score changes above a cutoff. Preserve the output format and output-file type of the input.
5. For custom sequences, inspect the repository's `scripts/custom_usage.py`; do not fabricate a different model API.

## Hard boundaries

- Current upstream support is substitutions and simple insertions/deletions with either REF or ALT a single base.
- Variants outside annotated genes, within 5,000 bases of chromosome ends, with deletions larger than twice `-d`, or inconsistent with the reference FASTA are skipped.
- Default masking is `True`; masked scores zero annotated-site gains and unannotated-site losses. Make this explicit when comparing with raw scores.
- Pangolin needs transcript/gene context from the annotation DB. Do not route a generic splice request here unless the user asks for Pangolin or tissue-specific splice strength.

## References

- Read [references/cli-and-semantics.md](references/cli-and-semantics.md) for database setup, CLI options, input restrictions, and output interpretation.

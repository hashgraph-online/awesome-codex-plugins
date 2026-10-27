---
name: gget
description: Queries 20+ bioinformatics databases and analysis services through the gget CLI and Python package, covering Ensembl gene search, info and sequences (ref, search, info, seq), BLAST, BLAT, MUSCLE, DIAMOND, PDB, AlphaFold, ELM, ARCHS4, CELLxGENE, Enrichr, Bgee, OpenTargets, cBioPortal, COSMIC, viral sequence downloads (virus), and 8cube mouse specificity and expression data. Use when looking up gene or transcript details, running a quick BLAST/BLAT search, fetching AlphaFold or PDB structures, running enrichment analysis on a gene list, downloading viral sequences with filters, or exploring disease and drug associations interactively. Not for batch processing or fine-grained BLAST control (use biopython) or multi-database Python pipelines (use bioservices).
license: BSD-2-Clause license
compatibility: Requires Python >=3.8 and gget 0.30.5-compatible APIs. Optional setup modules may install scientific dependencies that lag the newest Python releases; use Python 3.9 or 3.10 if `gget setup cellxgene` or `gget setup alphafold` fails.
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.5'
  category: scientific-databases
  maintainer: Kalaris Labs
  tags: bioinformatics databases, Ensembl, BLAST, AlphaFold, gene lookup
---

# gget

## Overview

gget is a command-line bioinformatics tool and Python package providing unified access to 20+ genomic databases and analysis methods. Query gene information, sequence analysis, protein structures, viral sequences, expression data, disease associations, and mouse tissue/cell specificity metrics through a consistent interface. Most gget modules work both as command-line tools and as Python functions.

**Important**: The databases queried by gget are continuously updated, which sometimes changes their structure. Guidance here targets gget 0.30.5 (PyPI current as of 2026-06-07). For reproducible work, pin `gget==0.30.5`; for broken upstream database adapters, update gget after checking release notes.

## Installation

Install gget in a clean virtual environment to avoid conflicts:

```bash
# Reproducible install targeting this skill
uv venv .venv
source .venv/bin/activate
uv pip install "gget==0.30.5"

# In Python/Jupyter
import gget
```

## Quick Start

Basic usage pattern for all modules:

```bash
# Command-line
gget <module> [arguments] [options]

# Python
gget.module(arguments, options)
```

Most modules return:
- **Command-line**: JSON (default) or CSV with `-csv` flag
- **Python**: DataFrame or dictionary

Common flags across modules:
- `-o/--out`: Save results to file
- `-q/--quiet`: Suppress progress information
- `-csv`: Return CSV format (command-line only)

Python argument names generally match long CLI options without leading dashes. For example, `--census_version` becomes `census_version=...`. Use `gget <module> --help` for the exact current signature.

## Module Categories

gget exposes 23 modules in six categories. Parameters, CLI and Python examples, and
return shapes for every one are in
[references/module_catalog.md](references/module_catalog.md); fuller per-parameter
documentation is in [references/module_reference.md](references/module_reference.md).

| Category | Modules |
| --- | --- |
| 1. Reference & gene information | `ref` (Ensembl reference downloads), `search` (gene search), `info` (gene/transcript detail), `seq` (nucleotide and protein sequences) |
| 2. Sequence analysis & alignment | `blast`, `blat`, `muscle` (multiple alignment), `diamond` (local alignment) |
| 3. Structural & protein analysis | `pdb` (structures and metadata), `alphafold` (structure prediction), `elm` (linear motifs) |
| 4. Expression & disease data | `archs4` (correlation, tissue expression), `cellxgene` (single-cell), `enrichr` (enrichment), `bgee` (orthology and expression), `opentargets` (disease and drug), `cbio` (cancer genomics), `cosmic` (mutations) |
| 5. Viral & mouse specificity | `virus` (viral sequences), `8cube` (mouse specificity and expression) |
| 6. Additional tools | `mutate` (mutated sequences), `gpt` (text generation), `setup` (install module dependencies) |

Several modules need a one-time `gget setup` before first use (`alphafold`, `elm`,
`cellxgene`), and `cosmic` prompts for COSMIC credentials to download its database.

## Common Workflows

Worked multi-module pipelines — gene characterization, structural comparison, expression
and enrichment analysis, disease and drug association, orthology comparison, and
reference-file preparation for kallisto or alignment — are in
[references/common_workflows.md](references/common_workflows.md), with longer versions in
[references/workflows.md](references/workflows.md).

## Best Practices

### Data Retrieval
- Use `--limit` to control result sizes for large queries
- Save results with `-o/--out` for reproducibility
- Check database versions/releases for consistency across analyses
- Use `--quiet` in production scripts to reduce output

### Sequence Analysis
- For BLAST/BLAT, start with default parameters, then adjust sensitivity
- Use `gget diamond` with `--threads` for faster local alignment
- Save DIAMOND databases with `--diamond_db` for repeated queries
- For multiple sequence alignment, use `-s5/--super5` for large datasets

### Expression and Disease Data
- Gene symbols are case-sensitive in cellxgene (e.g., 'PAX7' vs 'Pax7')
- Run `gget setup` before first use of alphafold, cellxgene, elm, gpt
- For enrichment analysis, use database shortcuts for convenience
- Cache cBioPortal data with `-dd` to avoid repeated downloads
- For OpenTargets, inspect returned column names before writing filters; gget 0.30.5 follows the newer OpenTargets API schema

### Structure Prediction
- AlphaFold multimer predictions: use `-mr 20` for higher accuracy
- Use `-r` flag for AMBER relaxation of final structures
- Visualize results in Python with `plot=True`
- Check PDB database first before running AlphaFold predictions

### Viral Data
- Use restrictive filters with `gget virus` before requesting broad viral datasets
- Keep `command_summary.txt` with downstream results for reproducibility and recovery after partial downloads
- Use `--baseline` and `--merge-results` to resume interrupted viral metadata/sequence downloads

### Error Handling
- Database structures change; when an adapter breaks, check upstream release notes and pin the newer fixed version explicitly
- Pin the known-good version for reproducible environments: `uv pip install "gget==0.30.5"`
- Process max ~1000 Ensembl IDs at once with gget info
- For large-scale analyses, implement rate limiting for API queries
- Use virtual environments to avoid dependency conflicts
- Keep COSMIC and OpenAI credentials in named environment variables or interactive prompts; do not write real credentials into examples, notebooks, or logs

## Output Formats

### Command-line
- Default: JSON
- CSV: Add `-csv` flag
- FASTA: gget seq, gget mutate
- PDB: gget pdb, gget alphafold
- PNG: gget cbio plot
- FASTA/CSV/JSONL folder: gget virus

### Python
- Default: DataFrame or dictionary
- JSON: Add `json=True` parameter
- Save to file: Add `save=True` or specify `out="filename"`
- AnnData: gget cellxgene
- DataFrame/JSON: gget 8cube specificity, psi_block, expression

## Resources

This skill includes reference documentation for detailed module information:

### references/
- `module_reference.md` - Comprehensive parameter reference for all modules
- `database_info.md` - Information about queried databases and their update frequencies
- `workflows.md` - Extended workflow examples and use cases

For additional help:
- Official documentation: https://pachterlab.github.io/gget/
- GitHub issues: https://github.com/pachterlab/gget/issues
- Citation: Luebbert, L. & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. https://doi.org/10.1093/bioinformatics/btac836

## Agent operating procedure

1. **Check the environment.** Confirm network access, API keys (if required) and the database's current API documentation and rate limits.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Fetch a single known record and check the response format before bulk queries.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Identifiers resolve, record counts are reported, and the database version or access date is recorded.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| HTTP 429 or 5xx errors | Respect rate limits with backoff, batch requests, and report partial results honestly. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Never invent accession numbers, IDs or records; report 'not found' instead.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `biopython`: Provides Biopython (Bio.Seq, Bio.SeqIO, Bio.Align, Bio.Entrez, Bio.Blast, Bio.PDB, Bio.Phylo, Bio.motifs, Bio.SeqUtils, Bio.Restriction) fo…
- `bioservices`: Unified Python interface to 40+ bioinformatics services.
- `pathway-enrichment`: Run pathway and gene-set enrichment analysis on gene lists or ranked gene data, then interpret the results.

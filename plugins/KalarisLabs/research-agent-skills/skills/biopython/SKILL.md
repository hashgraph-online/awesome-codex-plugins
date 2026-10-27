---
name: biopython
description: Provides Biopython (Bio.Seq, Bio.SeqIO, Bio.Align, Bio.Entrez, Bio.Blast, Bio.PDB, Bio.Phylo, Bio.motifs, Bio.SeqUtils, Bio.Restriction) for sequence handling, file parsing, NCBI access, BLAST, structures, and phylogenetic trees in Python. Reads, writes, and converts FASTA, GenBank, FASTQ, PDB, mmCIF, Newick, and NEXUS files. Use when manipulating or translating DNA, RNA, or protein sequences, converting sequence file formats, fetching records from NCBI via Entrez, running or parsing BLAST searches, doing pairwise or multiple sequence alignment, analyzing PDB structures, or building and editing phylogenetic trees. For quick lookups use gget; for multi-service integration use bioservices.
license: Biopython License Agreement
compatibility: Requires Python 3.10+, NumPy, and Biopython. Entrez and web BLAST examples require network access; local BLAST/MUSCLE examples require those command-line tools installed separately.
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.3'
  category: life-sciences
  maintainer: Kalaris Labs
  openclaw:
    envVars:
    - name: NCBI_EMAIL
      required: false
      description: Email for NCBI Entrez identification (required by NCBI policy for Entrez calls).
    - name: NCBI_API_KEY
      required: false
      description: NCBI API key to raise Entrez rate limits.
  tags: sequence analysis, bioinformatics, BLAST, NCBI, phylogenetics, Python
---

# Biopython: Computational Molecular Biology in Python

## Overview

Biopython is a comprehensive set of freely available Python tools for biological computation. It provides functionality for sequence manipulation, file I/O, database access, structural bioinformatics, phylogenetics, and many other bioinformatics tasks. The current version is **Biopython 1.87** (released 30 March 2026). It supports **Python 3.10-3.14** and PyPy3.10, and requires NumPy. Biopython 1.87 also addresses **CVE-2025-68463** in `Bio.Entrez.Parser` when parsing untrusted files, so prefer 1.87+ for workflows that parse externally supplied Entrez XML.

## When to Use This Skill

Use this skill when:

- Working with biological sequences (DNA, RNA, or protein)
- Reading, writing, or converting biological file formats (FASTA, GenBank, FASTQ, PDB, mmCIF, etc.)
- Accessing NCBI databases (GenBank, PubMed, Protein, Gene, etc.) via Entrez
- Running BLAST searches or parsing BLAST results
- Performing sequence alignments (pairwise or multiple sequence alignments)
- Analyzing protein structures from PDB files
- Creating, manipulating, or visualizing phylogenetic trees
- Finding sequence motifs or analyzing motif patterns
- Calculating sequence statistics (GC content, molecular weight, melting temperature, etc.)
- Performing structural bioinformatics tasks
- Working with population genetics data
- Any other computational molecular biology task

## Core Capabilities

Biopython is organized into modular sub-packages, each addressing specific bioinformatics domains:

1. **Sequence Handling** - Bio.Seq and Bio.SeqIO for sequence manipulation and file I/O
2. **Alignment Analysis** - Bio.Align and Bio.AlignIO for pairwise and multiple sequence alignments
3. **Database Access** - Bio.Entrez for programmatic access to NCBI databases
4. **BLAST Operations** - Bio.Blast for running and parsing BLAST searches
5. **Structural Bioinformatics** - Bio.PDB for working with 3D protein structures
6. **Phylogenetics** - Bio.Phylo for phylogenetic tree manipulation and visualization
7. **Advanced Features** - Motifs, population genetics, sequence utilities, and more

## Installation and Setup

Install the current stable Biopython release with an explicit version pin for reproducibility:

```bash
uv pip install "biopython==1.87"
```

For NCBI database access, always set your email address (required by NCBI). For reusable software, set a stable `Entrez.tool` value and register the tool/email with NCBI. For higher rate limits (10 req/s instead of 3 req/s), read only `NCBI_API_KEY` from the environment — do not hardcode keys or load unrelated environment variables:

```python
import os
from Bio import Entrez

Entrez.email = "your.email@example.com"  # required — use your real email
Entrez.tool = "your_tool_name"  # optional but recommended for reusable software

# Optional: register at https://www.ncbi.nlm.nih.gov/account/settings/
if api_key := os.environ.get("NCBI_API_KEY"):
    Entrez.api_key = api_key
```

## Using This Skill

Details, code examples and parameter tables: [references/using-this-skill.md](references/using-this-skill.md). Read it when this step applies.

## General Workflow Guidelines

### Reading Documentation

When a user asks about a specific Biopython task:

1. **Identify the relevant module** based on the task description
2. **Read the appropriate reference file** using the Read tool
3. **Extract relevant code patterns** and adapt them to the user's specific needs
4. **Combine multiple modules** when the task requires it

Example search patterns for reference files:
```bash
# Find information about specific functions
rg -n "SeqIO.parse" references/sequence_io.md

# Find examples of specific tasks
rg -n "BLAST" references/blast.md

# Find information about specific concepts
rg -n "alignment" references/alignment.md
```

### Writing Biopython Code

Follow these principles when writing Biopython code:

1. **Import modules explicitly**
   ```python
   from Bio import SeqIO, Entrez
   from Bio.Seq import Seq
   ```

2. **Set Entrez email** when using NCBI databases; load only `NCBI_API_KEY` from the environment if present
   ```python
   import os
   from Bio import Entrez

   Entrez.email = "your.email@example.com"
   Entrez.tool = "your_tool_name"
   if api_key := os.environ.get("NCBI_API_KEY"):
       Entrez.api_key = api_key
   ```

3. **Use appropriate file formats** - Check which format best suits the task
   ```python
   # Common formats: "fasta", "genbank", "fastq", "clustal", "phylip"
   ```

4. **Handle files properly** - Close handles after use or use context managers
   ```python
   with open("file.fasta") as handle:
       records = SeqIO.parse(handle, "fasta")
   ```

5. **Use iterators for large files** - Avoid loading everything into memory
   ```python
   for record in SeqIO.parse("large_file.fasta", "fasta"):
       # Process one record at a time
   ```

6. **Handle errors gracefully** - Network operations and file parsing can fail
   ```python
   from urllib.error import HTTPError

   try:
       handle = Entrez.efetch(db="nucleotide", id=accession)
   except HTTPError as e:
       print(f"Error: {e}")
   ```

## Common Patterns

### Pattern 1: Fetch Sequence from GenBank

```python
from Bio import Entrez, SeqIO

Entrez.email = "your.email@example.com"

# Fetch sequence
handle = Entrez.efetch(db="nucleotide", id="EU490707", rettype="gb", retmode="text")
record = SeqIO.read(handle, "genbank")
handle.close()

print(f"Description: {record.description}")
print(f"Sequence length: {len(record.seq)}")
```

### Pattern 2: Sequence Analysis Pipeline

```python
from Bio import SeqIO
from Bio.SeqUtils import gc_fraction

for record in SeqIO.parse("sequences.fasta", "fasta"):
    # Calculate statistics
    gc = gc_fraction(record.seq)
    length = len(record.seq)

    # Find ORFs, translate, etc.
    protein = record.seq.translate()

    print(f"{record.id}: {length} bp, GC={gc:.2%}")
```

### Pattern 3: BLAST and Fetch Top Hits

```python
from Bio.Blast import NCBIWWW, NCBIXML
from Bio import Entrez, SeqIO

Entrez.email = "your.email@example.com"

# Run BLAST
result_handle = NCBIWWW.qblast("blastn", "nt", sequence)
blast_record = NCBIXML.read(result_handle)

# Get top hit accessions
accessions = [aln.accession for aln in blast_record.alignments[:5]]

# Fetch sequences
for acc in accessions:
    handle = Entrez.efetch(db="nucleotide", id=acc, rettype="fasta", retmode="text")
    record = SeqIO.read(handle, "fasta")
    handle.close()
    print(f">{record.description}")
```

### Pattern 4: Build Phylogenetic Tree from Sequences

```python
from Bio import AlignIO, Phylo
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor

# Read alignment
alignment = AlignIO.read("alignment.fasta", "fasta")

# Calculate distances
calculator = DistanceCalculator("identity")
dm = calculator.get_distance(alignment)

# Build tree
constructor = DistanceTreeConstructor()
tree = constructor.nj(dm)

# Visualize
Phylo.draw_ascii(tree)
```

## Best Practices

1. **Always read relevant reference documentation** before writing code
2. **Use grep to search reference files** for specific functions or examples
3. **Validate file formats** before parsing
4. **Handle missing data gracefully** - Not all records have all fields
5. **Cache downloaded data** - Don't repeatedly download the same sequences
6. **Respect NCBI rate limits** - Use API keys, registered tool/email values for reusable software, and Entrez history/batching for large jobs
7. **Test with small datasets** before processing large files
8. **Keep Biopython updated** to get latest features and bug fixes
9. **Use appropriate genetic code tables** for translation
10. **Document analysis parameters** for reproducibility

## Troubleshooting Common Issues

### Issue: "No handlers could be found for logger 'Bio.Entrez'"
**Solution:** This is just a warning. Set Entrez.email to suppress it.

### Issue: "HTTP Error 400" from NCBI
**Solution:** Check that IDs/accessions are valid and properly formatted.

### Issue: "ValueError: EOF" when parsing files
**Solution:** Verify file format matches the specified format string.

### Issue: Alignment fails with "sequences are not the same length"
**Solution:** Ensure sequences are aligned before using AlignIO or MultipleSeqAlignment.

### Issue: BLAST searches are slow
**Solution:** Use local BLAST for large-scale searches, or cache results.

### Issue: PDB parser warnings
**Solution:** Use `PDBParser(QUIET=True)` to suppress warnings, or investigate structure quality.

### Issue: ImportError for Bio.HMM, Bio.MarkovModel, or Bio.Application
**Solution:** These modules were removed in Biopython 1.86. Use [hmmlearn](https://pypi.org/project/hmmlearn/) for HMMs and the standard library `subprocess` module instead of `Bio.Application` CLI wrappers.

### Issue: PairwiseAligner returns fewer alignments after upgrading to 1.86+
**Solution:** The default gap score changed from 0 to -1 in 1.86, eliminating trivial tie alignments. Set `aligner.gap_score = 0` to restore the old behavior if needed (see `references/alignment.md`).

## Additional Resources

- **Official Documentation**: https://biopython.org/docs/latest/
- **Tutorial**: https://biopython.org/docs/latest/Tutorial/
- **Cookbook**: https://biopython.org/docs/latest/Tutorial/ (advanced examples)
- **GitHub**: https://github.com/biopython/biopython
- **Release notes**: https://github.com/biopython/biopython/blob/master/NEWS.rst
- **Deprecated APIs**: https://github.com/biopython/biopython/blob/master/DEPRECATED.rst
- **Mailing List**: biopython@biopython.org

## Quick Reference

To locate information in reference files, use these search patterns:

```bash
# Search for specific functions
rg -n "function_name" references/*.md

# Find examples of specific tasks
rg -n "example" references/sequence_io.md

# Find all occurrences of a module
rg -n "Bio.Seq" references/*.md
```

## Summary

Biopython provides comprehensive tools for computational molecular biology. When using this skill:

1. **Identify the task domain** (sequences, alignments, databases, BLAST, structures, phylogenetics, or advanced)
2. **Consult the appropriate reference file** in the `references/` directory
3. **Adapt code examples** to the specific use case
4. **Combine multiple modules** when needed for complex workflows
5. **Follow best practices** for file handling, error checking, and data management

The modular reference documentation ensures detailed, searchable information for every major Biopython capability.

## Agent operating procedure

1. **Check the environment.** Confirm tool versions, the reference genome/annotation build and the input formats (FASTQ, BAM, VCF, h5ad).
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Run the pipeline on a small subset (one sample, one chromosome, a few thousand cells) first.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Check QC metrics, sample identities, genome build consistency and batch effects before interpreting results.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Genome builds or identifiers do not match between inputs | Stop and harmonize (liftover, ID mapping) before continuing. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Do not interpret biological significance beyond what the statistics support; report multiple-testing correction.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `scikit-bio`: Python library scikit-bio for biological sequence and community-ecology analysis: DNA/RNA/protein sequences, pair_align alignment, phylogen…
- `gget`: Queries 20+ bioinformatics databases and analysis services through the gget CLI and Python package, covering Ensembl gene search, info and…
- `etetoolkit`: Analyze, manipulate, compare, annotate, and visualize phylogenetic or other hierarchical trees with ETE 4.

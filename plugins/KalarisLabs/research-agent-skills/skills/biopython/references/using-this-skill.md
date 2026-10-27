# Using This Skill

This skill provides comprehensive documentation organized by functionality area. When working on a task, consult the relevant reference documentation:

### 1. Sequence Handling (Bio.Seq & Bio.SeqIO)

**Reference:** `references/sequence_io.md`

Use for:
- Creating and manipulating biological sequences
- Reading and writing sequence files (FASTA, GenBank, FASTQ, etc.)
- Converting between file formats
- Extracting sequences from large files
- Sequence translation, transcription, and reverse complement
- Working with SeqRecord objects

**Quick example:**
```python
from Bio import SeqIO

# Read sequences from FASTA file
for record in SeqIO.parse("sequences.fasta", "fasta"):
    print(f"{record.id}: {len(record.seq)} bp")

# Convert GenBank to FASTA
SeqIO.convert("input.gb", "genbank", "output.fasta", "fasta")
```

### 2. Alignment Analysis (Bio.Align & Bio.AlignIO)

**Reference:** `references/alignment.md`

Use for:
- Pairwise sequence alignment (global and local)
- Reading and writing multiple sequence alignments
- Using substitution matrices (BLOSUM, PAM)
- Calculating alignment statistics
- Customizing alignment parameters

**Quick example:**
```python
from Bio import Align

# Pairwise alignment
aligner = Align.PairwiseAligner()
aligner.mode = 'global'
alignments = aligner.align("ACCGGT", "ACGGT")
print(alignments[0])
```

### 3. Database Access (Bio.Entrez)

**Reference:** `references/databases.md`

Use for:
- Searching NCBI databases (PubMed, GenBank, Protein, Gene, etc.)
- Downloading sequences and records
- Fetching publication information
- Finding related records across databases
- Batch downloading with proper rate limiting

**Quick example:**
```python
from Bio import Entrez
Entrez.email = "your.email@example.com"

# Search PubMed
handle = Entrez.esearch(db="pubmed", term="biopython", retmax=10)
results = Entrez.read(handle)
handle.close()
print(f"Found {results['Count']} results")
```

### 4. BLAST Operations (Bio.Blast)

**Reference:** `references/blast.md`

Use for:
- Running BLAST searches via NCBI web services
- Running local BLAST searches
- Parsing BLAST XML output
- Filtering results by E-value or identity
- Extracting hit sequences

**Quick example:**
```python
from Bio.Blast import NCBIWWW, NCBIXML

# Run BLAST search
result_handle = NCBIWWW.qblast("blastn", "nt", "ATCGATCGATCG")
blast_record = NCBIXML.read(result_handle)

# Display top hits
for alignment in blast_record.alignments[:5]:
    print(f"{alignment.title}: E-value={alignment.hsps[0].expect}")
```

### 5. Structural Bioinformatics (Bio.PDB)

**Reference:** `references/structure.md`

Use for:
- Parsing PDB and mmCIF structure files
- Navigating protein structure hierarchy (SMCRA: Structure/Model/Chain/Residue/Atom)
- Calculating distances, angles, and dihedrals
- Secondary structure assignment (DSSP)
- Structure superimposition and RMSD calculation
- Extracting sequences from structures

**Quick example:**
```python
from Bio.PDB import PDBParser

# Parse structure
parser = PDBParser(QUIET=True)
structure = parser.get_structure("1crn", "1crn.pdb")

# Calculate distance between alpha carbons
chain = structure[0]["A"]
distance = chain[10]["CA"] - chain[20]["CA"]
print(f"Distance: {distance:.2f} Å")
```

### 6. Phylogenetics (Bio.Phylo)

**Reference:** `references/phylogenetics.md`

Use for:
- Reading and writing phylogenetic trees (Newick, NEXUS, phyloXML)
- Building trees from distance matrices or alignments
- Tree manipulation (pruning, rerooting, ladderizing)
- Calculating phylogenetic distances
- Creating consensus trees
- Visualizing trees

**Quick example:**
```python
from Bio import Phylo

# Read and visualize tree
tree = Phylo.read("tree.nwk", "newick")
Phylo.draw_ascii(tree)

# Calculate distance
distance = tree.distance("Species_A", "Species_B")
print(f"Distance: {distance:.3f}")
```

### 7. Advanced Features

**Reference:** `references/advanced.md`

Use for:
- **Sequence motifs** (Bio.motifs) - Finding and analyzing motif patterns
- **Population genetics** (Bio.PopGen) - GenePop files, Fst calculations, Hardy-Weinberg tests
- **Sequence utilities** (Bio.SeqUtils) - GC content, melting temperature, molecular weight, protein analysis
- **Restriction analysis** (Bio.Restriction) - Finding restriction enzyme sites
- **Clustering** (Bio.Cluster) - K-means and hierarchical clustering
- **Genome diagrams** (GenomeDiagram) - Visualizing genomic features

**Quick example:**
```python
from Bio.SeqUtils import gc_fraction, molecular_weight
from Bio.Seq import Seq

seq = Seq("ATCGATCGATCG")
print(f"GC content: {gc_fraction(seq):.2%}")
print(f"Molecular weight: {molecular_weight(seq, seq_type='DNA'):.2f} g/mol")
```

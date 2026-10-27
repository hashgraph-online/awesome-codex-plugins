# ARA Directory Schema — Complete Field-Level Reference

## Directory Structure

```
PAPER.md                            # Level 1: Root manifest + layer index
logic/
  problem.md                        # Why: observations → gaps → key insight
  claims.md                         # Falsifiable assertions
  concepts.md                       # All key technical terms (one ## per term)
  experiments.md                    # Declarative experiment plans (NOT scripts)
  solution/
    architecture.md                 # System design + component graph
    algorithm.md                    # Math formulation + pseudocode
    constraints.md                  # Boundary conditions + limitations
    heuristics.md                   # Convergence tricks + rationale
  related_work.md                   # Typed dependency graph (RDO)
src/
  configs/
    training.md                     # Training hyperparameters with rationale
    model.md                        # Architecture/model configs
  execution/
    {module}.py                     # Minimal code stubs (core algorithm only)
  environment.md                    # Dependencies, hardware, seeds
trace/
  exploration_tree.yaml             # Research DAG: nested YAML tree with typed nodes
evidence/
  README.md                         # Index mapping every evidence file to claims
  tables/                           # Raw result tables (exact cell values)
  figures/                          # Raw figure data (extracted data points)
rubric/                             # (Only if rubric provided)
  requirements.md                   # Leaf-level rubric requirements mapped to ARA files
```

Additional files or subdirectories may be created on demand when the source contains
content that does not fit the standard layers (for example, appendix-sourced worked
examples, prompt templates, or enumerated taxonomies). Place such content in the ARA
layer where it best belongs.

## Progressive Disclosure (3 Levels)

- **Level 1 — PAPER.md** (~200 tokens): Frontmatter + layer index. Agent reads ONLY this to decide relevance.
- **Level 2 — Layer files** (problem.md, claims.md, experiments.md, evidence/README.md): Loaded on demand.
- **Level 3 — Detail files** (algorithm.md, code stubs, individual evidence tables): Loaded when drilling in.

---

## PAPER.md

YAML frontmatter MUST include:
```yaml
---
title: "{full paper title}"
authors: [{author list}]
year: {year}
venue: "{venue}"
doi: "{DOI or arXiv ID}"
ara_version: "1.0"
domain: "{research domain}"
keywords: [{5-10 keywords}]
claims_summary:
  - "{one-line summary of main claim 1}"
  - "{one-line summary of main claim 2}"
  - "{one-line summary of main claim 3}"
abstract: "{paper abstract}"
---
```

Body MUST include a Layer Index — a table for each layer listing every file:

```markdown
# {Paper Title}

## Overview
{1-2 paragraph summary of the contribution}

## Layer Index

### Cognitive Layer (`/logic`)
| File | Description |
|------|-------------|
| [problem.md](logic/problem.md) | Observations → gaps → key insight |
| [claims.md](logic/claims.md) | {N} falsifiable claims (C01–C{NN}) |
| ...

### Physical Layer (`/src`)
| File | Description | Claims |
|------|-------------|--------|
| [execution/{module}.py](src/execution/{module}.py) | {what} | C{NN} |
| ...

### Exploration Graph (`/trace`)
| File | Description |
|------|-------------|
| [exploration_tree.yaml](trace/exploration_tree.yaml) | {N}-node research DAG |

### Evidence (`/evidence`)
| File | Description |
|------|-------------|
| [README.md](evidence/README.md) | Full index of {N} tables + {N} figures |
```

---

## Evidence Naming and Fidelity

The evidence layer has two different object types:

1. **Raw source evidence**
   - Faithful transcription of one source table or figure
   - Must preserve the original source identifier and caption
   - Example: `evidence/tables/table3_imagenet_validation.md`

2. **Derived subset evidence**
   - Filtered or recomposed view created for a specific claim
   - Must NOT masquerade as the original source object
   - Filename should include `derived_`, `subset_`, or equivalent
   - Must declare which raw source object it came from
   - Example: `evidence/tables/derived_from_table3_residual_depth_slice.md`

Rule: if a filename includes a source label such as `table3` or `figure4`, it should faithfully represent that exact source object rather than a curated subset.

---

## logic/problem.md

```markdown
# Problem Specification

## Observations

### O{N}: {title}
- **Statement**: {precise empirical fact with numbers}
- **Evidence**: {source — figure, table, measurement, citation}
- **Implication**: {what this means for the problem}

## Gaps

### G{N}: {title}
- **Statement**: {what's missing or broken}
- **Caused by**: {which observations, e.g., O1, O2}
- **Existing attempts**: {what's been tried}
- **Why they fail**: {specific failure mode}

## Key Insight
- **Insight**: {the creative leap, stated precisely}
- **Derived from**: {which observations}
- **Enables**: {what solution approach this unlocks}

## Assumptions
- A1: {assumption}
- A2: {assumption}
```

---

## logic/claims.md

Each claim MUST have ALL fields:
```markdown
## C{NN}: {Short title}
- **Statement**: {Precise, falsifiable assertion}
- **Status**: {hypothesis|supported|refuted}
- **Falsification criteria**: {What would disprove this}
- **Proof**: [{experiment IDs: E01, E02}]
- **Evidence basis**: {What the cited evidence directly shows}
- **Interpretation**: {Optional broader reading that should not be confused with the raw evidence}
- **Dependencies**: {other claim IDs, if any}
- **Tags**: {comma-separated keywords}
```

Proof MUST reference experiment IDs from experiments.md.
Each proofed experiment should in turn be backed by evidence files whose rows or measurements actually match the claim being asserted.
`Statement` should stay at the strongest level directly supported by the cited evidence. Use `Interpretation` for broader synthesis.

---

## logic/concepts.md

≥5 concepts. One section per concept:
```markdown
## {Term Name}
- **Notation**: {LaTeX or symbolic notation}
- **Definition**: {Formal definition}
- **Boundary conditions**: {When does this concept apply/not apply}
- **Related concepts**: {other concept names}
```

---

## logic/experiments.md

≥3 experiments. Declarative plans, NOT scripts. NO exact numerical results.

```markdown
## E{NN}: {Short title}
- **Verifies**: {claim IDs, e.g., C01, C02}
- **Setup**:
  - Model: {model name and size}
  - Hardware: {GPU type, count, memory}
  - Dataset: {dataset name, size, source}
  - System: {system configuration}
- **Procedure**:
  1. {Step 1}
  2. {Step 2}
- **Metrics**: {what to measure, with units}
- **Expected outcome**:
  - {directional/relative ONLY, e.g., "A outperforms B on metric X"}
  - NEVER exact numbers (those go in evidence/)
- **Baselines**: {methods to compare against}
- **Dependencies**: {other experiment IDs, or "none"}
```

---

## logic/solution/architecture.md

Component graph. For each component: name, purpose, inputs, outputs, interactions, key design choices.

## logic/solution/algorithm.md

- Mathematical formulation (LaTeX)
- Pseudocode
- Step-by-step explanation
- Complexity analysis

## logic/solution/constraints.md

- Boundary conditions
- Assumptions
- Known limitations

## logic/solution/heuristics.md

Each heuristic MUST have ALL fields:
```markdown
## H{NN}: {Short description}
- **Rationale**: {Why this trick is needed}
- **Sensitivity**: {low|medium|high}
- **Bounds**: {acceptable range or limits}
- **Code ref**: [{path to src/execution/ file}]
- **Source**: {Section/table in the paper}
```

---

## logic/related_work.md

```markdown
## RW{NN}: {Author et al., Year}
- **DOI**: {DOI or arXiv ID}
- **Type**: {imports|bounds|baseline|extends|refutes}
- **Delta**:
  - What changed: {specific technical delta}
  - Why: {motivation}
- **Claims affected**: {claim IDs}
- **Adopted elements**: {what was kept}
```

Works with a specific technical delta get full `RW` blocks as above. Additional citations
from the paper that do not have a technical delta (background, historical, infrastructure,
or inline-comparison references) should still be captured more briefly so the ARA preserves
the paper's full citation footprint.

---

## src/configs/training.md

```markdown
## {Parameter name}
- **Value**: {exact value}
- **Rationale**: {why this value}
- **Search range**: {if mentioned}
- **Sensitivity**: {low|medium|high}
- **Source**: {section/table}
```

## src/configs/model.md

Same format as training.md for model/architecture configs.

## src/execution/{module}.py

- Typed function signatures (input/output types, tensor shapes)
- Docstrings explaining what each function does
- Implementation logic for the NOVEL contribution
- NO scaffolding (no argparse, logging, distributed wrappers)
- Import only standard libraries + torch/numpy

## src/environment.md

```markdown
# Environment
- **Python**: {version}
- **Framework**: {PyTorch version, etc.}
- **Hardware**: {GPU type, count, memory}
- **Key dependencies**: {list with versions}
- **Random seeds**: {if specified}
```

---

## evidence/tables/{file}.md

Raw source-table transcription:

```markdown
# Table {N} - {Caption or short description}

**Source**: Table {N} in {paper/report title}
**Caption**: {verbatim or near-verbatim caption}
**Extraction type**: raw_table

| ... | ... |
| --- | --- |
| ... | ... |
```

Derived subset:

```markdown
# Derived subset - {Short description}

**Source**: Derived from Table {N} in {paper/report title}
**Caption**: {what part of the source table this subset preserves}
**Extraction type**: derived_subset
**Derived from**: `table{N}_{raw_file_name}.md`

| ... | ... |
| --- | --- |
| ... | ... |
```

Rules:
- Raw source-table files should reproduce the original row set relevant to that table, not a claim-specific slice
- If you drop rows, rename the file as a derived subset and declare the parent source
- Do not combine rows from multiple source tables while retaining a single original table number in the filename

---

## trace/exploration_tree.yaml

Each node should distinguish direct source support from reconstruction:

```yaml
tree:
  - id: N01
    type: question
    support_level: explicit | inferred
    source_refs: ["Table 2", "§4.1"]   # recommended for explicit nodes
    title: "{...}"
    description: "{...}"
```

Rules:
- `support_level: explicit` means the node is directly grounded in the provided source material
- `support_level: inferred` means the node is a reconstruction of the paper's logic, not a literal session record
- Explicit nodes should include `source_refs`
- Inferred nodes must not be presented as if they were directly observed historical events

---

## evidence/README.md

```markdown
# Evidence Index

## Tables
| File | Source | Claims | Description |
|------|--------|--------|-------------|
| [tables/{name}.md](tables/{name}.md) | Table N, §X.Y | C01, C02 | {one sentence} |

## Figures
| File | Source | Claims | Description |
|------|--------|--------|-------------|
| [figures/{name}.md](figures/{name}.md) | Figure N, §X.Y | C03 | {one sentence} |
```

## evidence/tables/{name}.md

ALL result tables, exact cell values:
```markdown
# Table N: {Title}
- **Source**: Table N, Section X.Y
- **Caption**: "{caption}"

| Column1 | Column2 | ... |
|---------|---------|-----|
| exact   | values  | ... |
```

## evidence/figures/{name}.md

ALL quantitative figures (not diagrams). Extract data points:
```markdown
# Figure N: {Title}
- **Source**: Figure N, Section X.Y
- **Caption**: "{caption}"
- **Axes**: X = {label, units}, Y = {label, units}

| X | Y (Series A) | Y (Series B) | ... |
|---|-------------|-------------|-----|
| v | v           | v           | ... |
```

Mark approximate readings with "≈".

---

## Appendix-sourced content

Appendix sections commonly carry worked examples, prompt templates, enumerated taxonomies,
annotation schemas, extended analyses, and prescriptive content. Route each into the ARA
layer where it best fits, preserving the granularity the source uses (for example, keep
per-entry descriptive fields for taxonomies rather than collapsing to names + frequencies).
The existing layer conventions above apply; create additional files only when no existing
file is a natural home.

---

## rubric/requirements.md (Only if rubric provided)

```markdown
# Rubric Requirements — {paper_id}

**Source**: PaperBench expert-authored reproduction rubric
**Total leaf requirements**: {N}

## {Category Group}

### R{NN}: {Short title}
- **Rubric ID**: {uuid}
- **Category**: {task_category} / {finegrained_task_category}
- **Weight**: {weight}
- **Requirement**: {verbatim from rubric}
- **ARA coverage**: {path to most specific ARA file, or "Not covered"}
- **Key detail**: {exact value from paper, or "Not specified in paper"}
```

# ARA Seal Level 1 — Validation Checklist

These are all checks the Seal validator runs. Fix ALL failures before reporting success.

## 1. Directory Existence

All must exist as directories:
- `logic/`
- `logic/solution/`
- `src/`
- `src/configs/`
- `trace/`
- `evidence/`

## 2. Mandatory File Existence (non-empty)

All must exist with >10 bytes:
- `PAPER.md`
- `logic/problem.md`
- `logic/claims.md`
- `logic/concepts.md`
- `logic/experiments.md`
- `logic/solution/architecture.md`
- `logic/solution/algorithm.md`
- `logic/solution/constraints.md`
- `logic/solution/heuristics.md`
- `logic/related_work.md`
- `src/configs/training.md`
- `src/configs/model.md`
- `src/environment.md`
- `trace/exploration_tree.yaml`
- `evidence/README.md`

## 3. PAPER.md Checks

- Starts with `---` (YAML frontmatter)
- Frontmatter is valid YAML mapping
- Contains keys: `title`, `authors`, `year`
- Body contains "Layer Index" section

## 4. Field-Level Checks (regex patterns)

### logic/claims.md
- Has `## C\d+` blocks (at least one claim)
- Contains `**Statement**`
- Contains `**Status**`
- Contains `**Falsification criteria**`
- Contains `**Proof**`
- Contains `**Evidence basis**`
- Contains `**Interpretation**`

### logic/problem.md
- Has `### O\d+` blocks (observations)
- Has `### G\d+` blocks (gaps)
- Has Key Insight section (`## Key Insight` or `**Insight**`)

### logic/experiments.md
- Has `## E\d+` blocks (at least 3)
- Contains `**Verifies**`
- Contains `**Setup**`
- Contains `**Procedure**`
- Contains `**Expected outcome**` or `**Expected results**`

### logic/solution/heuristics.md
- Has `## H\d+` blocks
- Contains `**Rationale**`
- Contains `**Sensitivity**`
- Contains `**Bounds**`

### logic/related_work.md
- Has `## RW\d+` blocks
- Contains `**Type**`
- Contains `**Delta**`
- Coverage should extend beyond the closest predecessors to reflect the paper's full
  citation footprint

### logic/concepts.md
- Has `## ` sections (at least 5)
- Contains `**Definition**`

## 5. Count Checks

- `logic/concepts.md`: ≥5 concept sections (`## ` headers)
- `logic/experiments.md`: ≥3 experiment blocks (`## E\d+`)
- `src/execution/`: ≥1 `.py` file
- `evidence/tables/` or `evidence/figures/`: ≥1 `.md` file

## 5b. Appendix Coverage

When the source has appendices, every appendix section should be traceable to at least
one ARA file, with the granularity of the source preserved.

## 6. Evidence Quality

For each file in `evidence/tables/*.md` and `evidence/figures/*.md`:
- Must contain a Markdown table (`|...|...|` pattern)
- Must contain `**Source**` field
- If the filename includes `table{N}` or `figure{N}`, the `**Source**` field must reference the same identifier
- If the file is a derived subset, it must say so explicitly via `**Extraction type**: derived_subset` or equivalent
- Raw source-table files should not silently omit rows while still presenting themselves as the original table

## 7. evidence/README.md

- Must contain a Markdown table (file index)
- Numbered tables and figures from the source (main text and appendices) should be
  reflected in the index

## 8. Exploration Tree (YAML)

- Parses as valid YAML
- Has top-level `tree` key
- ≥8 nodes total (counted recursively through children)
- All node types in {question, decision, experiment, dead_end, pivot}
- At least 1 `dead_end` node exists
- At least 1 `decision` node exists
- Every node has `id` and `type` fields
- Every node has `support_level` in {explicit, inferred}
- Type-specific required fields:
  - question: `description`
  - experiment: `result`
  - dead_end: `hypothesis`, `failure_mode`, `lesson`
  - decision: `choice`, `alternatives`
  - pivot: `from`, `to`, `trigger`
- All `also_depends_on` references resolve to existing node IDs
- Nodes with `support_level: explicit` should include `source_refs`

## 9. Cross-Layer Binding

### Claim Proof → Experiment Resolution
- Every `E\d+` in a claim's `**Proof**: [...]` must exist in experiments.md
- Proof-linked experiments should have evidence files whose labels and row contents actually match the compared systems or measurements
- Claim wording should be auditable against `Evidence basis`; broader language should be isolated to `Interpretation`

### Experiment Verifies → Claim Resolution
- Every `C\d+` in an experiment's `**Verifies**` must exist in claims.md

### Heuristic Code Ref → File Resolution
- Every `src/...` path in `**Code ref**: [...]` must be an existing file

### Architecture Components → Code Stubs (fuzzy)
- Significant words from `## ` headings in architecture.md should appear somewhere in src/execution/ code

### Tree Evidence → Claims (YAML)
- Any `C\d+` in a tree node's `evidence` field must exist in claims.md

### Trace Hygiene
- Do not add dead_end, decision, or experiment nodes that are unsupported by the provided source material
- If a node is reconstructed from partial evidence rather than stated explicitly, it should be marked as inferred or excluded from Seal Level 1 outputs

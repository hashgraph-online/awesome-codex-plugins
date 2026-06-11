---
name: design
description: "Run design."
---
# $design -- Product Validation Gate (Codex Native)

> **Quick Ref:** Validates that a proposed goal aligns with the product's strategic direction before discovery begins major work. Council-gated with `--preset=product`.

---

## Quick Start

```bash
$design "add caching layer for CLI"           # validate goal against PRODUCT.md
$design --quick "add caching layer"           # inline check, no judge spawning
$design --strict "redesign hook system"       # higher threshold (avg >= 2.5)
$design                                       # infers goal from recent context
```

---

## Execution Steps

### Step 0: Check for PRODUCT.md

Locate `PRODUCT.md` in the repo root.

```bash
ls PRODUCT.md 2>/dev/null
```

**If absent:** Output a warning and return PASS with note: "No PRODUCT.md found -- skipping product validation gate. Run `$product` to generate one."

**If present:** Continue to Step 1.

### Step 1: Load Product Context

Read `PRODUCT.md` and extract:
- **Mission** -- the product's core purpose
- **Personas** -- defined user types and their needs
- **Gaps** -- known product gaps or roadmap items
- **Competitive landscape** -- how the product differentiates

If any section is missing, note it as unavailable and score that dimension conservatively (1).

### Step 2: Score Alignment Matrix

Evaluate the proposed goal against five dimensions. Use the scoring rubric in [references/alignment-matrix.md](references/alignment-matrix.md).

| Dimension | Score (0-3) | Rationale |
|-----------|-------------|-----------|
| Gap Alignment | | Does this goal address a known product gap? |
| Persona Fit | | Does this serve defined personas? |
| Competitive Diff | | Does this strengthen competitive position? |
| Precedent | | Has similar work been done before? What can we learn? |
| Scope Fit | | Is this appropriately scoped for the current phase? |

Compute the average score across all five dimensions.

### Step 3: Run Council

Invoke council with the product preset. See [references/product-council-preset.md](references/product-council-preset.md) for judge configuration.

```
$council --preset=product validate design alignment for: <goal>
```

Pass the alignment matrix from Step 2 as context to the council judges.

If `--quick` flag is set, skip council spawning and perform inline assessment instead.

### Step 4: Write Design Artifact

Write the design artifact to `.agents/design/`:

```bash
mkdir -p .agents/design
```

Filename: `<date>-design-<goal-slug>.md` (e.g., `2026-03-30-design-add-caching-layer.md`)

Artifact contents:
- Goal statement
- Alignment matrix with scores and rationale
- Council verdict (or inline assessment if `--quick`)
- Final verdict and recommendation

### Step 5: Output Verdict

Determine the final verdict based on scores:

| Condition | Verdict |
|-----------|---------|
| Average score >= 2.0 AND no dimension at 0 | **PASS** -- goal aligns with product direction |
| Average score >= 1.5 OR one dimension at 0 with others strong | **WARN** -- goal has alignment concerns, review before proceeding |
| Average score < 1.5 OR multiple dimensions at 0 | **FAIL** -- goal does not align with product direction |

When `--strict` is set, raise the PASS threshold to average >= 2.5.

Output the verdict in this format:

```
DESIGN VERDICT: <PASS|WARN|FAIL>
  Gap Alignment:     <score>/3 -- <one-line rationale>
  Persona Fit:       <score>/3 -- <one-line rationale>
  Competitive Diff:  <score>/3 -- <one-line rationale>
  Precedent:         <score>/3 -- <one-line rationale>
  Scope Fit:         <score>/3 -- <one-line rationale>
  Average:           <avg>/3.0
  Artifact:          .agents/design/<filename>.md
```

---

## Flags

| Flag | Effect |
|------|--------|
| `--quick` | Inline check without multi-perspective spawning. Faster but less thorough. |
| `--strict` | Raise PASS threshold from avg >= 2.0 to avg >= 2.5. Use for high-stakes changes. |

---

## Reference Documents

- [references/alignment-matrix.md](references/alignment-matrix.md) -- Scoring rubric for the five alignment dimensions
- [references/project-reality-check.md](references/project-reality-check.md) -- Quick reality-check prompts before committing to a project direction
- [references/product-council-preset.md](references/product-council-preset.md) -- Council `--preset=product` judge configuration and verdict rules

---

## See Also

- `../council/SKILL.md` -- Multi-model consensus council
- `../product/SKILL.md` -- Generate PRODUCT.md
- `../discovery/SKILL.md` -- Discovery phase orchestrator
- `../pre-mortem/SKILL.md` -- Plan validation gate

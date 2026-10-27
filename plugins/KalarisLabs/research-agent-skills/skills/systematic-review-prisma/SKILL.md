---
name: systematic-review-prisma
description: Plan, run and report systematic reviews and meta-analyses to PRISMA 2020 standards. Use when writing a review protocol (PROSPERO/OSF), building reproducible database search strings (PubMed, Embase, Scopus, Web of Science), deduplicating exports, organizing title/abstract and full-text screening, assessing risk of bias, drawing the PRISMA flow diagram, or completing the PRISMA 2020 checklist. Includes a dedup tool and a checked PRISMA diagram generator.
license: MIT
compatibility: Python 3.9+ standard library for the bundled scripts; Graphviz optional for DOT rendering.
metadata:
  version: "1.0"
  category: literature-review
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: systematic review, PRISMA 2020, meta-analysis, PROSPERO, screening, risk of bias, evidence synthesis
---

# Systematic Reviews with PRISMA 2020

A systematic review is judged on transparency and reproducibility: another team
should be able to rerun your searches and reach the same included set. Work in
the phases below and keep an audit trail (dates, counts, decisions) as you go.
Retrofitting a trail at the end is how reviews fail peer review.

## Phase 1: Protocol (before searching)

1. Frame the question with **PICO** (Population, Intervention, Comparator, Outcome);
   use PECO for exposures, SPIDER for qualitative work, PCC for scoping reviews.
2. Pre-specify eligibility criteria, primary/secondary outcomes, databases, date
   limits, languages, risk-of-bias tool and synthesis method.
3. Register the protocol **before screening starts**: PROSPERO (health, human outcomes)
   or OSF Registries (everything else). Record the registration ID for the manuscript.
4. Use the PRISMA-P checklist to write the protocol. Scoping reviews follow PRISMA-ScR.

## Phase 2: Search

- Build one concept block per PICO element: controlled vocabulary (MeSH in PubMed,
  Emtree in Embase) **OR** free-text synonyms, then **AND** the blocks.
- Translate the syntax per database (field tags differ: `[tiab]` PubMed, `:ti,ab` Embase,
  `TITLE-ABS-KEY()` Scopus, `TS=` Web of Science). Never paste one string everywhere.
- Validate sensitivity: the search must retrieve a pre-assembled set of known relevant papers.
- Search at least two bibliographic databases, plus trial registers, and do forward and backward
  citation searching of included studies.
- Record, per database: platform, exact string, date run, and hit count. These go in the
  supplement verbatim (PRISMA item 7), and PRISMA-S covers search reporting in detail.

Example PubMed block structure:

```text
("Diabetes Mellitus, Type 2"[Mesh] OR "type 2 diabetes"[tiab] OR T2DM[tiab])
AND ("Metformin"[Mesh] OR metformin[tiab])
AND (randomized controlled trial[pt] OR randomi*[tiab] OR placebo[tiab])
```

## Phase 3: Deduplicate and screen

```bash
python scripts/dedupe_records.py pubmed.ris embase.ris scopus.csv wos.bib \
  -o screening.csv --summary dedup-counts.json
```

The output CSV has `screen_title_abstract`, `screen_full_text` and `exclusion_reason`
columns for screening in a spreadsheet, or import it into Rayyan, Covidence or ASReview.

- Two independent reviewers screen titles/abstracts, then full texts. Report agreement
  (Cohen's kappa) and how conflicts were resolved.
- Full-text exclusions need **one primary reason each**, drawn from a fixed list. These
  become the "Reports excluded" box in the flow diagram.
- AI-assisted screening (active learning, LLM triage) must be described, validated against
  human decisions, and never used as the sole reviewer for exclusions.

## Phase 4: Extraction and risk of bias

- Pilot a data-extraction form on 3-5 studies. Extract in duplicate where feasible.
- Risk-of-bias tool by design: **RoB 2** (randomized trials), **ROBINS-I** (non-randomized
  interventions), **ROBINS-E** (exposures), **QUADAS-2** (diagnostic accuracy),
  **Newcastle-Ottawa** (observational, commonly used), **CASP/JBI** (qualitative).
- Rate certainty of evidence per outcome with **GRADE** and present a Summary of Findings table.

## Phase 5: Synthesis

- Meta-analysis only when studies are sufficiently similar. Use random-effects by default
  for clinical and methodological heterogeneity. Report I², tau² and prediction intervals.
- Pre-specified subgroup and sensitivity analyses only. Label post hoc analyses as such.
- Small-study effects: funnel plot + Egger's test when there are ≥10 studies.
- Without meta-analysis, follow SWiM (Synthesis Without Meta-analysis) guidance.
- R `metafor`/`meta` or Python `statsmodels` (see the `statistical-analysis` skill) for computation.

## Phase 6: Report

Generate the flow diagram from your recorded counts; the script refuses inconsistent arithmetic:

```bash
python scripts/prisma_flow.py --template > prisma-counts.json   # fill in
python scripts/prisma_flow.py prisma-counts.json > prisma.mmd    # Mermaid for Markdown/Quarto
python scripts/prisma_flow.py prisma-counts.json --format dot -o prisma.dot && dot -Tsvg prisma.dot -o prisma.svg
```

Complete the 27-item PRISMA 2020 checklist ([references/prisma-2020-checklist.md](references/prisma-2020-checklist.md))
with the page/section where each item is reported, and submit it with the manuscript.
The abstract must follow the PRISMA 2020 for Abstracts checklist (12 items).

## Integrity rules

- Never fabricate search counts, studies or screening decisions. Every number in the flow diagram must come from the recorded logs.
- Verify each included study's bibliographic record (`citation-verification`) and report exact search dates.

## Common reasons reviews are rejected

- Protocol not registered, or registered after screening began without explanation.
- One database only, no grey literature or register search.
- Search strings not reported in full or not reproducible.
- Single-reviewer screening with no justification.
- Flow-diagram numbers that do not add up (the script prevents this).
- Pooling clinically heterogeneous studies; ignoring risk of bias in the synthesis.
- Conclusions stronger than the GRADE certainty supports.

## Related skills

`literature-review` (narrative and scoping searches), `citation-verification`,
`statistical-analysis`, `scientific-writing`, `peer-review`.

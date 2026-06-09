---
name: curriculum-crosswalk
description: Compares two or more band-tagged frameworks and produces a framework-neutral topic matrix showing coverage and gaps across all inputs, plus an optional reference-centric PLC crosswalk document when a reference framework is supplied.
disable-model-invocation: false
user-invocable: true
effort: high
skill_id: curriculum-alignment/curriculum-crosswalk
skill_name: Curriculum Crosswalk
domain: curriculum-alignment
version: "2.0"
evidence_strength: moderate
evidence_sources:
  - "Webb, N. L. (1997) — Criteria for Alignment of Expectations and Assessments in Mathematics and Science Education, CCSSO Research Monograph No. 6: the canonical four-dimension alignment framework (categorical concurrence, depth-of-knowledge consistency, range-of-knowledge correspondence, balance of representation); this skill operationalises categorical concurrence and range at the school-band level."
  - "Porter, A. C. (2002) — Measuring the content of instruction: Uses in research and practice, Educational Researcher 31(7), 3–14: the Surveys of Enacted Curriculum methodology for comparing intended vs enacted curricula across frameworks via common content taxonomies."
  - "Porter, A. C., Smithson, J., Blank, R. & Zeidner, T. (2007) — Alignment as a teacher variable, Applied Measurement in Education 20(1), 27–51: alignment indices and content-matrix methodology applied across standards documents."
  - "Case, B. J., Jorgensen, M. A. & Zucker, S. (2004) — Alignment in Educational Assessment, Pearson Assessment Report: practical alignment procedures that surface rather than hide framework differences — the rationale for the divergence and unique-content tables in this skill's output."
  - "Martone, A. & Sireci, S. G. (2009) — Evaluating alignment between curriculum, assessment, and instruction, Review of Educational Research 79(4), 1332–1361: literature review establishing that alignment studies should preserve framework distinctiveness rather than collapse to a lowest-common-denominator schema — the design principle behind this skill's refusal to produce a merged mega-framework."
input_schema:
  required:
    - field: comparison_frameworks_band_tagged
      type: string
      description: Array of two or more frameworks, each produced by the Developmental Band Translator. Each entry must include source_metadata, band_tagged_kud (or equivalent content-bearing items), and band_tagged_lts. All frameworks are treated as equals in the primary matrix output.
  optional:
    - field: reference_framework_band_tagged
      type: string
      description: An optional designated reference framework, already band-tagged using the Developmental Band Translator. If supplied, the skill produces both the framework-neutral matrix AND the secondary reference-centric crosswalk document. If omitted, only the framework-neutral matrix outputs are produced.
    - field: reference_framework_name
      type: string
      description: Human-readable name of the reference framework for output labelling. Defaults to source_name from reference_framework_band_tagged metadata if omitted.
    - field: theme_taxonomy
      type: string
      description: An optional pre-defined list of theme labels. If supplied, the skill maps all framework content to these themes rather than deriving themes from the input. Overrides model-derived theme grouping. Use when running the skill repeatedly on changing inputs and needing consistent row labels across runs.
    - field: focus_bands
      type: string
      description: Restrict the crosswalk to a subset of school bands (e.g. "D,E" for secondary-focused PLC). If omitted, all bands are covered.
    - field: focus_themes
      type: string
      description: Restrict to specific thematic areas (e.g. "consent, relationships"). If omitted, all content is compared.
    - field: plc_context
      type: string
      description: A short description of the PLC context (e.g. "Band D/E wellbeing team preparing for September 2026 planning"). Used to tune the Questions for PLC section in the secondary crosswalk_document when a reference framework is supplied.
output_schema:
  type: object
  fields:
    - field: framework_neutral_matrix
      type: string
      description: Primary output. A Markdown matrix with one row per theme × band. Rows are derived by scanning ALL input frameworks — no theme is excluded because one framework lacks it. Columns are one per framework (all on equal footing). Empty cells are marked "—" explicitly; an empty cell for any framework is a visible gap, not an omission.
    - field: framework_neutral_matrix_csv
      type: string
      description: Primary CSV at band level. Columns — theme, band, then for each framework one content column and one band_confidence column, plus gap_count (number of frameworks with empty cell for that theme × band), notes. One row per theme × band combination.
    - field: framework_neutral_summary_matrix
      type: string
      description: Summary-grain CSV. One row per theme (not per band), showing which frameworks cover it and at which band range. Designed for a scannable overview of cross-framework coverage.
    - field: theme_grouping_flags
      type: array
      description: Array of ambiguous theme groupings flagged for human review. Each entry includes — theme label, source topics grouped under it, rationale for the grouping decision. Surfaces interpretive uncertainty rather than hiding it in Known Limitations.
    - field: crosswalk_document
      type: string
      description: Secondary output — only produced if reference_framework_band_tagged was supplied. A Markdown document for direct use by a teacher or PLC facilitator. Contains the five required sections (Convergence, Divergence, Unique Content, Sequencing Differences, Questions for PLC) plus a short preamble identifying the frameworks and scope.
    - field: crosswalk_convergence_csv
      type: string
      description: Secondary output — only produced if reference_framework_band_tagged was supplied. Flat CSV with one row per LT × band × comparison framework pairing. Columns — lt_id, lt_name, band, reference_content, comparison_framework, comparison_content, comparison_source_label, confidence, issue_type, notes. Empty comparison_content means no equivalent found.
    - field: skill_flags
      type: array
      description: Skill-level warnings (insufficient overlap to produce meaningful convergence, framework with >50% ambiguity upstream, focus_bands exclude all content in one framework, too many frameworks for readable output, etc.).
    - field: internal_trace
      type: object
      description: Non-prose metadata retained for debugging and for skill chaining — framework ids compared, item counts per section, band-coverage matrix, theme derivation log. Not included in primary or secondary output documents.
chains_well_with:
  - developmental-band-translator
  - learning-progression-builder
  - scope-and-sequence-designer
  - curriculum-knowledge-architecture-designer
  - gap-analysis-from-student-work
teacher_time: 30 minutes
tags:
  - curriculum-alignment
  - crosswalk
  - framework-comparison
  - Webb-alignment
  - Porter-content-analysis
  - PLC
  - source-voice-preservation
---

# What This Skill Does

This skill compares two or more band-tagged frameworks and produces a framework-neutral topic matrix as its primary output. Its input is the output of the Developmental Band Translator skill — one output per framework. Every framework is treated as an equal participant: topics present in any framework appear as rows in the matrix, and a framework's absence at a given theme × band is shown as an explicit "—" gap, not an omission. This makes the primary output useful for identifying what any framework lacks, not just where frameworks agree.

If a reference framework is also supplied, the skill additionally produces a secondary reference-centric crosswalk document — a Markdown document that a teacher or PLC facilitator can open and use directly for a professional discussion, organised under five required sections: Convergence, Divergence, Unique Content, Sequencing Differences, and Questions for PLC. The secondary document and its associated CSV are only produced when a reference framework is supplied.

The skill is deliberately additive, not reductive. It does not merge the frameworks into a single synthesised schema. It does not rewrite statements into a common voice. Each framework's content appears in the output in the original words the framework used, attributed by name. This is a design decision grounded in Martone & Sireci (2009): alignment work that hides framework distinctiveness loses the very information a PLC needs to make a planning decision.

The skill is opinionated about the distinction between "cross-framework agreement" and "cross-framework coincidence". Two frameworks addressing the same topic at the same band is convergence only if they also treat the topic at comparable depth and intent. Where that is unclear, the skill flags the pairing as *apparent convergence, teacher confirmation needed* rather than silently counting it as agreement.

# Evidence Foundation

**Webb (1997)** — The four-dimension alignment framework (categorical concurrence, depth-of-knowledge consistency, range-of-knowledge correspondence, balance of representation) is the canonical reference point for alignment work in curriculum and assessment. This skill operationalises categorical concurrence (do the frameworks address the same topics?) and range (do the ages match?) at the school-band level. Depth-of-knowledge and balance are deliberately not assessed automatically; the Questions for PLC section surfaces them for human discussion.

**Porter (2002) and Porter et al. (2007)** — The Surveys of Enacted Curriculum methodology established that framework comparison requires a common content taxonomy. The theme taxonomy — whether supplied via `theme_taxonomy` or derived from all input frameworks — serves this role. The skill inherits the Porter methodology's commitment to making the comparison visible and defensible: every cell in every table traces back to specific items in specific frameworks.

**Case, Jorgensen & Zucker (2004)** — Practical alignment procedures in assessment explicitly recommend that alignment studies preserve framework differences rather than suppress them. The framework-neutral matrix exists for exactly this reason: a theme row where the reference framework cell is "—" is as informative as a row where it matches others. A crosswalk that showed only overlap would erase the most important planning signal.

**Martone & Sireci (2009)** — This review article establishes that alignment studies should preserve framework distinctiveness rather than collapse to a lowest-common-denominator schema. The skill's refusal to produce a merged mega-framework, and its commitment to showing each framework's content in its own voice, follow directly from this finding.

# Input Schema

**Required inputs.** The skill needs one required input:

- **`comparison_frameworks_band_tagged`** — An array (two or more) of Developmental Band Translator outputs. All frameworks in this array are treated as equals in the primary matrix output. Beyond four frameworks the Convergence table in the secondary document becomes unwieldy and the skill emits a `too_many_frameworks_for_readable_output` flag.

**Optional inputs.**

- **`reference_framework_band_tagged`** — If supplied, the skill produces both the framework-neutral matrix AND the secondary reference-centric crosswalk_document and crosswalk_convergence_csv. The reference framework is included in the primary matrix as one column among equals. If omitted, only the framework-neutral matrix outputs are produced.
- **`reference_framework_name`** — A human-readable label for the reference framework used in output headings and table columns.
- **`theme_taxonomy`** — A pre-defined list of theme labels. If supplied, all framework content is mapped to these labels rather than themes being derived from the input. Use this when running the skill repeatedly across changing inputs to keep row labels consistent across runs.
- **`focus_bands`** — A comma-separated list of school bands to restrict the output to (e.g. `"D,E"` for a secondary PLC). Content outside these bands is excluded from all tables but acknowledged in preambles.
- **`focus_themes`** — Free-text theme restriction (e.g. `"consent, relationships"`). The skill filters items using keyword and semantic-similarity matching; a match log is retained in `internal_trace`.
- **`plc_context`** — One or two sentences describing the PLC audience and purpose. Used to tune the Questions for PLC section of the secondary crosswalk_document when a reference framework is supplied.

**Worked example (reference framework supplied).** A REAL School Budapest Band D/E wellbeing PLC preparing for September 2026 planning might pass: `reference_framework_band_tagged` = the REAL School Wellbeing Framework band-tagged output; `comparison_frameworks_band_tagged` = [band-tagged UK DfE Statutory RSHE, band-tagged Welsh CfW Health & Wellbeing]; `reference_framework_name = "REAL School Budapest Wellbeing Framework"`; `focus_bands = "D,E"`; `plc_context = "Band D/E wellbeing team reviewing coverage gaps for 2026-27 planning"`. All three frameworks appear as equal columns in the primary matrix, with any REAL School gap cells shown as "—".

**Worked example (no reference framework).** A curriculum team comparing three published frameworks before designing a new scope and sequence might pass only `comparison_frameworks_band_tagged` = [band-tagged IB MYP Health, band-tagged UK RSHE, band-tagged Welsh CfW H&W]. The primary matrix shows all three on equal footing; no secondary crosswalk document is produced.

# Prompt

You are a curriculum crosswalk assistant. You compare multiple band-tagged frameworks and produce a framework-neutral topic matrix as your primary output, and optionally a reference-centric crosswalk document as a secondary output.

## Step 1 — Read all frameworks and extract all topics

For each framework in `comparison_frameworks_band_tagged` (and `reference_framework_band_tagged` if supplied), list every band-tagged item: school band(s), content statement, source-band label, and knowledge type if present. Produce a combined topic list spanning all frameworks. No topic is excluded at this step.

## Step 2 — Group topics into coherent themes

If `theme_taxonomy` is supplied, map every topic from Step 1 to the nearest theme in that taxonomy. Do not invent new themes; flag unplaceable topics in `theme_grouping_flags`.

If `theme_taxonomy` is not supplied, derive themes from the full combined topic list. Group by semantic similarity and disciplinary coherence. Apply `focus_themes` filter (if supplied) after grouping.

For any grouping decision that is genuinely ambiguous — two frameworks addressing a topic at very different grain sizes, or content that plausibly belongs in two themes — add an entry to `theme_grouping_flags`. Each entry must include: the theme label, the source topics grouped under it, and the rationale for the grouping decision. Do not silently collapse ambiguous cases.

## Step 3 — Build the theme × band × framework matrix

For each theme × band combination in scope (all bands, or `focus_bands` if supplied), find the relevant content statement from each framework. If a framework has no content for that theme × band, the cell is "—". An empty cell for the reference framework is a visible gap — do not omit it.

Record for each non-empty cell: the verbatim content statement, the source-band label (e.g. "End of Secondary", "Progression Step 4"), and a band_confidence value (high / medium / low) reflecting upstream ambiguity from the Developmental Band Translator.

## Step 4 — Produce the matrix outputs

Produce three outputs:

**`framework_neutral_matrix`** — A Markdown table. Rows: theme × band. Columns: Theme, Band, then one column per framework (all on equal footing, including reference framework if supplied). Cells: verbatim content with source-band label in parentheses, or "—". Each "—" in any column is a visible gap.

**`framework_neutral_matrix_csv`** — A flat CSV at band level. One row per theme × band. Columns: theme, band, then for each framework: `[framework_name]_content` and `[framework_name]_band_confidence`, plus `gap_count` (integer: number of frameworks with "—" for this row), `notes`.

**`framework_neutral_summary_matrix`** — A summary CSV at theme level (one row per theme, not per band). Columns: theme, then for each framework: `[framework_name]_covers` (yes/no/partial) and `[framework_name]_band_range` (e.g. "D–E", "A–C", or "—").

Also produce **`theme_grouping_flags`** — the array of ambiguous grouping entries from Step 2.

## Step 5 — Produce secondary outputs (only if reference framework supplied)

If `reference_framework_band_tagged` was supplied, produce the secondary reference-centric outputs using the following logic:

**`crosswalk_document`** — A Markdown document for direct use by a PLC facilitator. Contains a short preamble and these five sections:

1. **Convergence table** — content that the reference framework and at least one comparison framework address at the same school band. Columns: Band; Reference content (verbatim); Comparison framework; Comparison content (verbatim); Confidence (high / medium / apparent-only).
2. **Divergence table** — content that the reference framework and at least one comparison framework *both* address but at *different* school bands. Columns: Topic; Reference band; Reference content (verbatim); Comparison framework; Comparison band; Comparison content (verbatim); Source label; Band-gap (in band units).
3. **Unique-content table** — content present in only one framework. One subsection per framework.
4. **Sequencing-difference notes** — prose description of meaningful differences in how the frameworks sequence related content. Focus on differences with planning implications.
5. **Questions for PLC** — 6–10 numbered questions grounded in specific cells from the tables above. Do NOT answer them.

**`crosswalk_convergence_csv`** — A flat CSV. One row per LT × band × comparison framework pairing. Columns: lt_id, lt_name, band, reference_content, comparison_framework, comparison_content, comparison_source_label, confidence, issue_type, notes. Every convergence, divergence, and unique-content row appears. Empty comparison_content is data, not an omission.

If `reference_framework_band_tagged` was not supplied, omit both `crosswalk_document` and `crosswalk_convergence_csv` entirely.

## Step 6 — Produce skill_flags and internal_trace

**`skill_flags`** — Emit warnings for: insufficient overlap to produce meaningful convergence; framework with >50% upstream ambiguity; `focus_bands` excluding all content in one framework; more than four frameworks producing unwieldy secondary output; fewer than 3 items remaining after filtering in any framework.

**`internal_trace`** — Framework ids compared, item counts per section, band-coverage matrix, theme derivation log (or taxonomy mapping log if `theme_taxonomy` was supplied), focus filter match log.

## Output format (hard constraints)

- `framework_neutral_matrix` and `crosswalk_document`: Markdown only. No JSON, no YAML, no field names, no `{variable}` placeholders.
- All framework content quoted verbatim. Do not paraphrase, shorten, or translate content statements. Quote marks around exact source text.
- Attribute every content statement to its source framework by name.
- Preserve source-band labels alongside school bands in every table row.
- If an item's band assignment was ambiguous upstream (multi-band), list every relevant band, not just one.

## Source-voice preservation (hard constraint)

Every content statement you reproduce must appear exactly as it did in the band-tagged input. Quote it. Attribute it. Do not rewrite it to match another framework's style. This is not stylistic — it is the crosswalk's core integrity property.

## Inputs

- `reference_framework_band_tagged`: {{reference_framework_band_tagged}}
- `reference_framework_name`: {{reference_framework_name}}
- `comparison_frameworks_band_tagged`: {{comparison_frameworks_band_tagged}}
- `theme_taxonomy`: {{theme_taxonomy}}
- `focus_bands`: {{focus_bands}}
- `focus_themes`: {{focus_themes}}
- `plc_context`: {{plc_context}}

Produce `framework_neutral_matrix`, `framework_neutral_matrix_csv`, `framework_neutral_summary_matrix`, and `theme_grouping_flags` in all cases. Produce `crosswalk_document` and `crosswalk_convergence_csv` only if `reference_framework_band_tagged` was supplied. Always produce `skill_flags` and `internal_trace`.

# Example Output

**Context**: Band D/E wellbeing PLC, comparing REAL School Budapest Wellbeing Framework (reference, supplied via `reference_framework_band_tagged`) against UK DfE Statutory RSHE and Welsh CfW Health & Wellbeing (in `comparison_frameworks_band_tagged`). `focus_bands = "D,E"`.

---

## (a) `framework_neutral_matrix_csv` — 5-row sample

Note: the REAL School cell is "—" in row 4 (STI/Contraception), making the gap explicit.

```csv
theme,band,REAL_School_Wellbeing_content,REAL_School_Wellbeing_band_confidence,UK_RSHE_content,UK_RSHE_band_confidence,Welsh_CfW_content,Welsh_CfW_band_confidence,gap_count,notes
Consent Understanding,D,"Students understand consent as an ongoing, reversible, affirmative process.",high,"the concepts of, and laws relating to, sexual consent, sexual exploitation, abuse, grooming, coercion",medium (End of Secondary spans C–E),—,—,1,Welsh CfW has no direct consent content at PS3/PS4
Mental-health Help-seeking,D,"Students can identify when to seek help for themselves or a peer and know at least two trusted routes.",high,"where to get advice e.g. family, school and/or other sources",low (End of Primary — band D is out of RSHE's intended range),—,—,1,RSHE places this 2 bands earlier; placed here for nearest-band comparison
Digital Wellbeing,E,"Students can evaluate the wellbeing effects of their own technology use and adjust it.",high,—,—,"I can make informed decisions about how to use digital technologies… to enhance my physical health and well-being",medium (PS3 spans C–D),1,Welsh CfW places this 1–2 bands earlier; no RSHE coverage at E
STI and Contraception,E,—,—,"the facts about the full range of contraceptive choices, efficacy and options available",high (End of Secondary),—,—,2,Reference framework gap — REAL School has no content matching this theme at Band E
Natural Environment and Wellbeing,D,—,—,—,—,"I can explain the benefits of spending time in the natural environment for my health and well-being",high (PS3),2,Reference framework gap — theme absent in both REAL School and UK RSHE at Band D
```

---

## (b) `framework_neutral_summary_matrix` — 3-row sample

```csv
theme,REAL_School_Wellbeing_covers,REAL_School_Wellbeing_band_range,UK_RSHE_covers,UK_RSHE_band_range,Welsh_CfW_covers,Welsh_CfW_band_range
Consent Understanding,yes,D,yes,C–E (End of Secondary),no,—
STI and Contraception,no,—,yes,C–E (End of Secondary),no,—
Natural Environment and Wellbeing,no,—,no,—,yes,C–D (PS3)
```

---

## (c) `theme_grouping_flags` — 2-entry sample

```json
[
  {
    "theme": "Consent Understanding",
    "source_topics_grouped": [
      "REAL School: 'Students understand consent as an ongoing, reversible, affirmative process.'",
      "UK RSHE: 'the concepts of, and laws relating to, sexual consent, sexual exploitation, abuse, grooming, coercion, harassment, rape'"
    ],
    "rationale": "Both address consent but at different epistemic grains and framing — REAL School frames consent developmentally; UK RSHE frames it propositionally and in law. Grouped under one theme for matrix comparability, but these may represent genuinely distinct learning goals. Flagged for human review."
  },
  {
    "theme": "Digital Wellbeing",
    "source_topics_grouped": [
      "REAL School: 'Students can evaluate the wellbeing effects of their own technology use and adjust it.'",
      "Welsh CfW: 'I can make informed decisions about how to use digital technologies… to enhance my physical health and well-being'"
    ],
    "rationale": "Both concern technology and wellbeing, but REAL School frames this as a self-regulation competency while Welsh CfW frames it as a health-literacy decision skill. Grouped under one theme but the pedagogical intent differs. A school treating these as one topic may be collapsing a meaningful distinction."
  }
]
```

---

## (d) Secondary output note

`crosswalk_document` is the secondary PLC-ready Markdown document, produced only when `reference_framework_band_tagged` is supplied. When produced, it follows the same five-section structure as in version 1.0 (Convergence, Divergence, Unique Content, Sequencing Differences, Questions for PLC), using REAL School as the reference column. Example content for that document follows the same format as the version 1.0 example — see that section's sample tables for illustration. The key difference is that the document is now secondary: the framework-neutral matrix is always produced first and is the primary analytical artefact.

# Known Limitations

**The skill does not assess depth-of-knowledge alignment.** Webb's depth-of-knowledge dimension is out of scope for automated comparison. The skill can see that two frameworks both address "consent" at the same band, but it cannot reliably judge whether they do so at the same cognitive depth. The Questions for PLC section is where depth-of-knowledge discussions belong. Convergence at apparent-only confidence is explicitly flagged for this reason.

**Theme derivation is the most judgement-dependent step.** Grouping topics from multiple frameworks into coherent themes is interpretive, not mechanical. Two frameworks addressing "self-regulation" at very different grains may or may not belong in the same theme row — the skill makes an interpretive proposal, not an authoritative classification. `theme_grouping_flags` surfaces uncertain cases for human review rather than hiding them. Use the `theme_taxonomy` input for consistent row labels across repeated runs on changing inputs.

**The skill inherits upstream ambiguity.** Where the Developmental Band Translator tagged items with multiple candidate school bands (common for UK RSHE's 2-band structure), the matrix carries that ambiguity into every cell. A framework with high upstream ambiguity produces a matrix with many multi-band rows, which is honest but can be harder to read. The skill emits a skill flag when >50% of upstream items are multi-band.

**The skill does not merge frameworks.** This is intentional (Martone & Sireci, 2009). The skill will not produce a synthesised unified framework, nor a single recommended topic order. Those are planning decisions informed by this output but made by humans.

**Thematic matching is not perfect.** The skill pairs items by semantic similarity in content statements. False negatives (genuine matches missed because the language is very different) and false positives (superficial lexical overlap with different pedagogical intent) are both possible. The `apparent-only` confidence tier surfaces false-positive risk; `theme_grouping_flags` and the Questions for PLC section backstop false-negative risk. The skill is a scaffold for the teacher's reading of the source documents, not a substitute for it.

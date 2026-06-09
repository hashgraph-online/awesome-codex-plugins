---
name: coverage-audit
description: Takes a curriculum framework and a statutory or accreditation requirement list; produces a coverage table, gap summary, and CSV showing which framework content covers each requirement and where gaps exist.
disable-model-invocation: false
user-invocable: true
effort: medium
skill_id: curriculum-alignment/coverage-audit
skill_name: Coverage Audit
domain: curriculum-alignment
version: "1.0"
evidence_strength: moderate
evidence_sources:
  - "Webb, N. L. (1997) — Criteria for Alignment of Expectations and Assessments in Mathematics and Science Education, CCSSO Research Monograph No. 6: canonical alignment framework defining coverage dimensions (categorical concurrence, depth-of-knowledge, range, balance) used in this skill's classification of match strength."
  - "Porter, A. C. et al. (2002) — Measuring the content of instruction: Uses in research and practice, Educational Researcher 31(7), 3–14: curriculum mapping methodology for comparing intended vs enacted curricula across frameworks — the basis for this skill's row-per-requirement approach."
input_schema:
  required:
    - field: framework
      type: string
      description: The curriculum framework being audited. Accepts band-tagged JSON from Developmental Band Translator, or plain markdown/text with competencies and learning targets identified.
    - field: requirements
      type: string
      description: The statutory or accreditation requirement list. Accepts markdown, CSV, or plain text. Each requirement should be identifiable by number or label.
  optional:
    - field: framework_name
      type: string
      description: Human-readable name of the framework being audited.
    - field: requirements_source
      type: string
      description: Name of the statutory or accreditation body.
    - field: band_filter
      type: string
      description: Restrict audit to specific bands only.
output_schema:
  type: object
  fields:
    - field: coverage_table
      type: string
      description: Markdown table — columns are Requirement ID, Requirement text, Covered by (framework LT or competency), Band(s), Evidence strength (direct/partial/indirect/none), Notes.
    - field: coverage_csv
      type: string
      description: Same data as coverage_table in flat CSV format for Google Sheets use.
    - field: gap_summary
      type: string
      description: Prose paragraph summarising requirements with no or only indirect coverage.
    - field: coverage_statistics
      type: object
      description: Counts — total requirements, directly covered, partially covered, not covered.
chains_well_with:
  - curriculum-crosswalk
  - developmental-band-translator
  - scope-and-sequence-designer
teacher_time: 15 minutes
tags:
  - coverage-audit
  - accreditation
  - statutory-compliance
  - curriculum-alignment
  - gap-analysis
---

# What This Skill Does

This skill audits a curriculum framework against a statutory or accreditation requirement list and produces a structured coverage table showing which framework content addresses each requirement and how strongly. It is framework-agnostic: the framework being audited can be any school's curriculum, any programme of study, or any competency framework. The requirement list can be a statutory mandate, an accreditation standard, or any external checklist that the school is expected to meet. Neither input is assumed to be REAL School, UK, or any other specific context.

The skill classifies each requirement match as direct (the framework explicitly addresses the requirement), partial (the framework addresses related content but not the specific requirement), indirect (tangentially related content is present), or none (no framework content touches the requirement). This four-tier scale follows Webb's (1997) categorical-concurrence logic, operationalised at the requirement level rather than the item level. The skill is transparent about what "coverage" means in this context: topical presence in the framework documentation. A framework item that touches a requirement topic does not necessarily mean the requirement is fully taught, assessed, or enacted at the intended cognitive depth.

The skill produces three outputs: a Markdown coverage table for PLC or accreditation preparation, a matching CSV for spreadsheet filtering, and a prose gap summary for narrative reporting. The coverage_statistics object gives a headline count for quick scanning. These outputs are scaffolds for human professional judgement — they are designed to reduce the time a curriculum coordinator spends locating evidence, not to replace the judgement required to confirm it.

# Evidence Foundation

**Webb (1997)** — The canonical four-dimension alignment framework establishes categorical concurrence as the foundational coverage dimension: do the framework and the requirement list address the same topics at all? The skill uses Webb's logic to classify match strength, stopping at categorical concurrence and range. Depth-of-knowledge alignment — whether the framework addresses a requirement at the required cognitive depth — is explicitly out of scope and flagged as a human judgement task in Known Limitations.

**Porter et al. (2002)** — The Surveys of Enacted Curriculum methodology establishes the row-per-requirement approach used in this skill's coverage table: each requirement gets its own row, and framework content is mapped to it rather than the reverse. This ensures that requirements with no framework coverage (the gap rows) are as visible as those with strong coverage, and prevents the natural tendency to organise the output around what the framework *does* cover rather than what the requirement list *asks for*.

# Input Schema

**Required inputs.**

- **`framework`** — The curriculum framework being audited. Accepts band-tagged JSON from the Developmental Band Translator (for band-level filtering), or plain markdown or text with competencies and learning targets. If band-tagged, the skill can restrict the audit to specific bands via `band_filter`. If plain text, all framework content is audited without band distinction.
- **`requirements`** — The statutory or accreditation requirement list. Accepts markdown, CSV, or plain text. Each requirement should carry an identifier (number, code, or label) for the Requirement ID column. If identifiers are absent, the skill assigns stable sequential IDs (R001, R002, …) and notes this in the preamble.

**Optional inputs.**

- **`framework_name`** — Human-readable label used in output headings.
- **`requirements_source`** — Name of the statutory or accreditation body, used in output headings.
- **`band_filter`** — Restrict the audit to specific bands (e.g. `"D,E"`). Only relevant when `framework` is band-tagged JSON. If omitted, all framework content is searched.

**Worked example of required inputs.** REAL School Budapest auditing its wellbeing curriculum against the UK RSHE statutory requirements (July 2025): `framework` = the REAL School Wellbeing Framework (band-tagged or markdown); `requirements` = the UK DfE statutory RSHE requirement list; `framework_name = "REAL School Budapest Wellbeing Framework"`; `requirements_source = "UK DfE Statutory RSHE, July 2025"`. The output would show each RSHE statutory bullet as a row, with REAL framework content (if any) mapped to it, classified by evidence strength.

# Prompt

You are a curriculum coverage-audit assistant. Your task is to audit a curriculum framework against a requirement list and produce a structured coverage table, a gap summary, and coverage statistics.

## Procedure

1. **Read the requirements list.** For each requirement, confirm it has a stable identifier. If identifiers are absent, assign sequential IDs (R001, R002, …) and note in your output preamble. Record every requirement before searching the framework — do not skip any.
2. **Read the framework.** If band-tagged, note the band labels and apply `band_filter` if supplied. If plain text, treat all content as a single pool.
3. **For each requirement, search the framework** for content that addresses it:
   - **Direct** — the framework explicitly and substantively addresses the requirement. The framework item's topic, framing, and intent match the requirement's topic, framing, and intent closely. A teacher could point to this item as evidence of coverage without qualification.
   - **Partial** — the framework addresses related content but not the specific requirement. The topic overlaps but the framing, depth, or scope differs. A teacher could point to this item as partial evidence but would need to add context.
   - **Indirect** — the framework contains content tangentially related to the requirement. The topic is adjacent but not the same. Evidence is inferential, not direct.
   - **None** — no framework content touches the requirement. This is a gap row.
4. **Produce `coverage_table`** — one row per requirement, with columns: Requirement ID | Requirement text | Covered by | Band(s) | Evidence strength | Notes.
5. **Produce `coverage_csv`** — the same data as coverage_table in flat CSV format. Column names exactly: requirement_id, requirement_text, covered_by, bands, evidence_strength, notes.
6. **Write `gap_summary`** — one prose paragraph summarising the requirements in the none and indirect rows. Group related gaps thematically if possible. State total count of none and indirect rows.
7. **Produce `coverage_statistics`** — counts: total_requirements, directly_covered, partially_covered, not_covered (none rows only). Include indirectly_covered as a separate count.

## Classification discipline

When classifying evidence strength, err toward conservatism. A match that requires the auditor to make an inferential leap beyond what the framework text directly states should be classified as partial or indirect, not direct. The skill's job is to give an honest starting point for professional review, not to maximise the apparent coverage score. A framework that looks fully covered by aggressive classification is not useful to an accreditor or a curriculum coordinator trying to find real gaps.

## Inputs

- `framework`: {{framework}}
- `requirements`: {{requirements}}
- `framework_name`: {{framework_name}}
- `requirements_source`: {{requirements_source}}
- `band_filter`: {{band_filter}}

Produce a JSON object with fields: coverage_table (markdown string), coverage_csv (CSV string), gap_summary (string), coverage_statistics (object).

# Example Output

**Context**: REAL School Budapest Wellbeing Framework audited against UK RSHE statutory requirements, `band_filter = "D,E"`.

**`coverage_table`** (8 rows shown):

| Req ID | Requirement text | Covered by | Band(s) | Evidence strength | Notes |
|---|---|---|---|---|---|
| RSHE-D-01 | "the characteristics of positive and healthy friendships… respect, honesty, trust, loyalty, kindness, generosity, boundaries, privacy, consent and the management of conflict" | "Students can identify healthy and unhealthy relationship patterns and articulate why each is so." | D | direct | Strong topical and intent match. |
| RSHE-D-02 | "the concepts of, and laws relating to, sexual consent, sexual exploitation, abuse, grooming, coercion, harassment" | "Students understand consent as an ongoing, reversible, affirmative process." | D | partial | Framework addresses consent developmentally; statutory requirement includes legal framing and broader harm categories not explicitly present. |
| RSHE-D-03 | "the facts about the full range of contraceptive choices, efficacy and options available" | — | — | none | No framework content addresses contraception at Bands D or E. |
| RSHE-D-04 | "the impact of pornography on attitudes to sex, relationships and gender" | — | — | none | No direct equivalent in framework. Digital wellbeing content at Band E touches media influence but not pornography specifically. |
| RSHE-D-05 | "how the different sexually transmitted infections (STIs), including HIV/AIDs, are transmitted, how risk can be reduced" | — | — | none | No STI content identified at Band D or E. |
| RSHE-E-01 | "how to seek, and recognise, support for mental health and wellbeing" | "Students can identify when to seek help for themselves or a peer and know at least two trusted routes." | D | partial | Framework addresses this at Band D; statutory requirement is placed at End of Secondary. Band E has no equivalent item — partial coverage at wrong band. |
| RSHE-E-02 | "the impact of viewing harmful content" | — | — | indirect | Digital wellbeing content at Band E covers technology use and wellbeing effects generally; harmful content is not specifically addressed. |
| RSHE-E-03 | "I can analyse and evaluate how my identity, values and sense of self-worth affect the way I interact with others" | "Students can analyse how identity, values, and context shape their decisions about relationships." | E | direct | Close topical and intent match at the correct band. |

**`coverage_csv`** (matching rows):

```csv
requirement_id,requirement_text,covered_by,bands,evidence_strength,notes
RSHE-D-01,"the characteristics of positive and healthy friendships… respect, honesty, trust, loyalty, kindness, generosity, boundaries, privacy, consent and the management of conflict","Students can identify healthy and unhealthy relationship patterns and articulate why each is so.",D,direct,Strong topical and intent match.
RSHE-D-02,"the concepts of, and laws relating to, sexual consent, sexual exploitation, abuse, grooming, coercion, harassment","Students understand consent as an ongoing, reversible, affirmative process.",D,partial,Framework addresses consent developmentally; statutory requirement includes legal framing not present.
RSHE-D-03,"the facts about the full range of contraceptive choices, efficacy and options available",,, none,No framework content addresses contraception at Bands D or E.
RSHE-D-04,"the impact of pornography on attitudes to sex, relationships and gender",,,none,No direct equivalent. Digital wellbeing content is adjacent but not specific.
RSHE-D-05,"how the different sexually transmitted infections (STIs), including HIV/AIDs, are transmitted",,, none,No STI content identified at Band D or E.
RSHE-E-01,"how to seek, and recognise, support for mental health and wellbeing","Students can identify when to seek help for themselves or a peer and know at least two trusted routes.",D,partial,Addressed at Band D not E; partial coverage at wrong band.
RSHE-E-02,"the impact of viewing harmful content",,,indirect,Digital wellbeing content is adjacent; harmful content not specifically addressed.
RSHE-E-03,"I can analyse and evaluate how my identity, values and sense of self-worth affect the way I interact with others","Students can analyse how identity, values, and context shape their decisions about relationships.",E,direct,Close topical and intent match.
```

**`gap_summary`**: Of 8 requirements sampled, 3 have no coverage (none) and 1 has only indirect coverage at Bands D and E. The none rows cluster around sexual health content: contraception options (RSHE-D-03), STI transmission and prevention (RSHE-D-05), and pornography and harmful content (RSHE-D-04 and RSHE-E-02, though the latter is indirect). These represent a substantive statutory gap at the secondary level. Additionally, the mental-health help-seeking requirement (RSHE-E-01) is partially met but at an earlier band than the statutory placement, meaning the Band E requirement is not addressed.

**`coverage_statistics`**:
```json
{
  "total_requirements": 8,
  "directly_covered": 2,
  "partially_covered": 2,
  "indirectly_covered": 1,
  "not_covered": 3
}
```

# Known Limitations

**Topical coverage is not depth equivalence.** A framework item that appears in the coverage_table as a "direct" match to a requirement is evidence that the topic is present in the framework documentation. It is not evidence that the topic is taught at the depth the requirement intends, assessed in the way the requirement expects, or enacted at the sophistication the accreditor would look for. Webb's (1997) depth-of-knowledge dimension — whether the cognitive demand of the framework content matches the cognitive demand of the requirement — is out of scope for this skill. A coverage_table row classified as direct is a starting point for professional review, not a conclusion.

**Human professional judgement is required before any accreditation submission.** This skill produces a scaffold for the curriculum coordinator's or accreditation reviewer's work. The coverage classifications are generated by pattern-matching against framework text; they have not been reviewed by a qualified professional in the relevant regulatory domain. Before using this output to support an accreditation claim, a competent professional must review each direct and partial row and confirm that the match holds under the accreditor's interpretation of the requirement. This skill explicitly does not substitute for that review.

**The skill cannot assess taught, assessed, or enacted curriculum.** The framework input describes the intended curriculum — what the school's documentation says will be taught. The skill audits documentation against documentation. It cannot determine whether the framework content is actually delivered in classrooms, whether it is assessed, or whether the enacted curriculum matches the written framework. Coverage in the table means coverage on paper. Accreditors and statutory inspectors typically require evidence of enacted curriculum, not just documented curriculum; this skill supports the documentation stage only.

# Outcome Mapping Matrix: {{program_name}}

**Course(s) mapped:** {{course_codes_and_titles}}
**Program:** {{program_name_and_degree}}
**Standard:** {{standard_body_and_name}} · **Version/year:** {{standard_version_year}}
· **Criteria text supplied by professor on:** {{date_text_supplied}}
**Strength scale:** {{strength_scale — I/R/M (Introduce/Reinforce/Master) unless the
institution mandates another; record the scale's definitions here}}
**Passport state verified against:** {{passport_path_and_date}}
**Matrix status:** {{draft | confirmed_by_professor on <date>}}

> This matrix is pinned to the standard version above. A revision of the standard
> invalidates it: cells must be re-confirmed against the new criteria text, not
> silently re-pointed.

## Matrix

| Course LO | {{criterion_id_1}} | {{criterion_id_2}} | {{criterion_id_3}} | {{…}} |
|-----------|--------------------|--------------------|--------------------|-------|
| {{LO_id: short statement}} | {{strength}} · {{evidence_status}} | | | |
| {{…rows for every mapped LO; empty cell = no claim, which is legitimate}} | | | | |

{{multi-course matrices: one row block per course, per-cell provenance retained —
"EVIDENCED (CS 201) / HOLLOW (CS 305)" is reported per course, never averaged}}

## Legend

| Label | Meaning |
|-------|---------|
| **CLAIMED** | Professor asserts the mapping; the assessment chain exists structurally (`assessed_by` non-empty) but no artifact yet backs it |
| **EVIDENCED** | The full chain holds: LO → assessment(s) → recorded artifact/results in the passport |
| **HOLLOW** | Claimed, but the evidence chain breaks (empty `assessed_by`, missing assessment, or the assessment does not actually target this LO) |

Strength ({{strength_scale}}) is the professor's claim; evidence status is computed by
`matrix_builder_agent` from the Course Passport. Neither substitutes for the other.

## Hollow-cell register

| Cell (LO × criterion) | Why hollow (specific ids) | Remediation owner | Routed to |
|-----------------------|---------------------------|-------------------|-----------|
| {{LO_id}} × {{criterion_id}} | {{e.g., "A3 listed in assessed_by but A3.outcomes_assessed omits LO4"}} | {{professor / department}} | {{course-designer redesign / new evidence next term / claim withdrawn}} |

## Over-mapping check

- Matrix density: {{claimed_cells}}/{{total_cells}} = {{percent}}%
- LOs claiming > {{threshold}} criteria: {{list with counts, or "none"}}
- {{flag_note — present once with counts if density suggests mapping theater; professor's
  response recorded here}}

## Change history

| Date | Change | By | Standard version at change |
|------|--------|----|----------------------------|
| {{date}} | {{e.g., "initial matrix confirmed" / "LO2×SO-3 upgraded to EVIDENCED — midterm results artifact added" / "claim LO5×SO-7 withdrawn at checkpoint"}} | {{professor / agent}} | {{version}} |

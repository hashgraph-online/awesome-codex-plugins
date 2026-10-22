---
name: accreditation-mapper
description: "Accreditation and program-assessment documentation for university professors. 4-agent team covering outcome mapping (course LO → program outcome → standard criterion), evidence package assembly, gap analysis, and self-study drafting that never overstates what the evidence shows. Triggers on: accreditation, ABET, AACSB, program outcomes, curriculum map, self-study, assessment report, learning outcomes assessment, continuous improvement report, 专业认证, 工程教育认证, 培养方案, 毕业要求, 课程目标达成, 自评报告, 持续改进, 课程矩阵."
metadata:
  version: "1.0.0"
  last_updated: "2026-06-10"
  status: active
  pipeline_stage: 1
  related_skills:
    - course-designer
    - teaching-pipeline
    - teaching-reflector
---

# Accreditation Mapper — Outcomes-to-Standards Documentation Team

Handles the compliance layer above the course: mapping course outcomes to program
outcomes to an accreditation standard's criteria, assembling the evidence behind each
mapping, finding the gaps, and drafting self-study prose that a review panel can trust.
This skill extends the suite's alignment idea one level up — the Alignment Gate checks
outcome ↔ assessment ↔ schedule *within* a course; this skill checks course ↔ program ↔
standard, with the same discipline: claims are verified against artifacts, not accepted
because they look complete.

> **Prime rule:** the mapping is the professor's claim; the evidence check is this
> skill's job. A matrix cell saying "LO2 supports Program Outcome 3" is asserted by the
> professor — the skill then verifies whether assessment evidence actually exists behind
> it and labels the cell honestly. A beautiful matrix with hollow cells is documentation
> theater, and review panels can smell it.

## Quick Start

```
Map my CS 201 outcomes to our ABET student outcomes
帮我把课程目标对应到毕业要求，做工程教育认证的课程矩阵
Assemble the evidence package for our program assessment report
Which of our program outcomes have weak assessment coverage?
Draft the continuous-improvement section of our self-study from last year's changes
```

## Modes

| Mode | Trigger intent | Output |
|------|---------------|--------|
| `map` | "Map my course to the program outcomes / standard"; building a curriculum map | Course-LO × program-outcome × criterion matrix with professor-claimed strength and per-cell evidence status (CLAIMED / EVIDENCED / HOLLOW) |
| `evidence` | "Assemble the evidence for…"; preparing for a review visit or assessment report | Evidence package index for a confirmed matrix: what exists (from passport `artifacts[]` + `iteration_history`), provenance per item, what's missing |
| `gap` | "Where is our coverage weak?"; pre-review self-check | Gap analysis: criteria with no or weak coverage across the mapped course(s), prioritized remediation suggestions routed to `course-designer` `redesign` |
| `self-study` | "Draft the self-study section…"; continuous-improvement narrative | Self-study / continuous-improvement section drafted FROM the confirmed matrix + evidence index — every claim footnoted to evidence; thin evidence becomes a hedged claim or an explicit gap statement, never inflation |

**Mode dispatch rule:** `evidence`, `gap`, and `self-study` all consume a confirmed
matrix. If none exists, run `map` first — drafting compliance prose from an unverified
mapping is exactly the failure mode this skill exists to prevent. Detect intent in any
language.

### Does NOT trigger

| Scenario | Use instead |
|----------|-------------|
| Designing or revising the learning outcomes themselves | `course-designer` |
| Analyzing student evaluations or teaching evidence for its own sake | `teaching-reflector` |
| Program-level curriculum redesign (re-sequencing courses, changing degree requirements) | Out of scope — a possible future skill; this skill documents and flags, it does not restructure programs |

## Agent Team (4)

| Agent | Role |
|-------|------|
| `standards_analyst_agent` | Normalizes professor-supplied standards and program outcomes into a criteria register: id, verbatim text, evidence type each criterion demands; flags vague criteria for the professor's interpretation |
| `matrix_builder_agent` | Builds the mapping matrix: LO rows × outcome/criterion columns, professor-claimed strength (I/R/M), per-cell evidence status computed from the passport; flags hollow cells and over-mapping |
| `evidence_assembler_agent` | Inventories what evidence actually exists per confirmed claim, with provenance; lists what's missing with the cheapest honest fix; never fabricates data |
| `selfstudy_writer_agent` | Drafts self-study / continuous-improvement prose from the confirmed matrix + evidence index; claim strength capped by evidence status |

## Workflow (`map` mode)

```
Phase 0  INTAKE      — professor supplies the program outcomes AND the standard's
                       criteria as actual current text (verbatim, with version/year).
                       The generic structures in references/accreditation_frameworks.md
                       are scaffolding for orientation only — never a substitute.
                       Missing standard text = [NEEDS PROFESSOR INPUT], full stop.
         🧑 checkpoint: standard version + text confirmed
Phase 1  REGISTER    — standards_analyst normalizes criteria into a register: ids,
                       verbatim text, evidence type demanded (direct / indirect /
                       process), measurability notes, vague-criterion flags
         🧑 checkpoint: register confirmed (incl. professor's reading of vague criteria)
Phase 2  MATRIX      — matrix_builder builds course-LO × program-outcome × criterion
                       matrix; professor claims each cell's strength (Introduce /
                       Reinforce / Master, or the institution's own scale)
Phase 3  VERIFY      — per-cell evidence status from the passport: LO.assessed_by →
                       assessment_plan → artifacts[] — does the evidence chain exist?
                       CLAIMED / EVIDENCED / HOLLOW per cell
         🧑 checkpoint: matrix + hollow-cell flags + over-mapping counts presented;
            professor confirms, revises claims, or accepts gaps knowingly
Phase 4  RECORD      — confirmed matrix saved from templates/outcome_matrix_template.md,
                       pinned to the standard version; this is the artifact the
                       `evidence`, `gap`, and `self-study` modes consume
```

`evidence` mode runs evidence_assembler over the confirmed matrix →
`ts/accreditation-mapper/templates/evidence_index_template.md`. `gap` mode reads the matrix column-wise
(criteria with no EVIDENCED cells across the mapped courses) and hands remediation
candidates to `course-designer` `redesign`. `self-study` mode requires both the matrix
and the evidence index and runs selfstudy_writer.

## Iron rules

1. **The standard's text comes from the professor — current and verbatim.** Bodies
   revise criteria; the reference file's generic structures are labeled
   possibly-outdated scaffolding. No current text from the professor → the mapping
   target is `[NEEDS PROFESSOR INPUT]`, and no matrix is built against a guess.
2. **Claims and evidence are separated.** The professor claims mappings; the skill
   verifies evidence existence. Every cell carries CLAIMED (asserted, chain not yet
   checked), EVIDENCED (assessment evidence chain exists in the passport), or HOLLOW
   (claimed, no evidence chain). The skill never upgrades a label as a courtesy.
3. **No compliance inflation.** Self-study prose strength is capped by evidence status:
   "students demonstrate X" requires an artifact showing it. HOLLOW cells cannot
   generate "students demonstrate" sentences — they generate gap statements with
   remediation plans, which is what honest continuous improvement looks like.
4. **Read-only on the course design.** Gaps route to `course-designer`; this skill
   never edits outcomes to fit a standard. An auditor that rewrites what it audits
   stops being an audit — same rule as Gate 1.5, one level up.
5. **Version pinning.** The matrix records which version/year of the standard it maps
   against. A standard revision invalidates the matrix loudly — the skill refuses to
   reuse a matrix pinned to a superseded version without re-confirmation — never
   silently.

## Outputs

- `outcome_matrix.md` — from `ts/accreditation-mapper/templates/outcome_matrix_template.md`; the mapping of
  record, version-pinned to the standard
- `evidence_index.md` — from `ts/accreditation-mapper/templates/evidence_index_template.md` (`evidence` mode)
- `gap_analysis.md` — prioritized coverage gaps with remediation routing (`gap` mode)
- `self_study_section.md` — footnoted draft, every factual sentence traceable
  (`self-study` mode)

## References

- `ts/accreditation-mapper/references/accreditation_frameworks.md` — generic shapes of ABET, AACSB,
  institutional review, and 工程教育认证; evidence-type taxonomy; mapping anti-patterns.
  Orientation only — carries its own version warning.
- `ts/accreditation-mapper/templates/outcome_matrix_template.md`
- `ts/accreditation-mapper/templates/evidence_index_template.md`
- Shared: `ts/shared/course_passport_schema.md`, `ts/shared/alignment_gate_protocol.md`,
  `ts/shared/checkpoint_protocol.md`

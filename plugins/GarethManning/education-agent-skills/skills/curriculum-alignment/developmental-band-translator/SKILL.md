---
name: developmental-band-translator
description: Tags harness-decomposed curriculum items (KUDs, LTs, criteria) with a school's developmental band metadata while preserving source voice and labels. Supply the band schema; the skill derives mapping rules from it.
disable-model-invocation: false
user-invocable: true
effort: medium
skill_id: curriculum-alignment/developmental-band-translator
skill_name: Developmental Band Translator
domain: curriculum-alignment
version: "1.0"
evidence_strength: moderate
evidence_sources:
  - "Wiggins, G. & McTighe, J. (2005) — Understanding by Design (2nd ed.), ASCD: backward design establishes the principle that curriculum alignment begins from stated outcomes and works backward through learning targets; band-tagging is an alignment operation on that model."
  - "Wiggins, G. & McTighe, J. (2011) — The Understanding by Design Guide to Creating High-Quality Units, ASCD: KUD as the canonical unit of translation between frameworks."
  - "Vygotsky, L. S. (1978) — Mind in Society: The Development of Higher Psychological Processes, Harvard University Press: the Zone of Proximal Development provides the theoretical basis for developmental banding as an age-and-readiness construct rather than a pure age construct."
  - "Heritage, M. (2008) — Learning Progressions: Supporting Instruction and Formative Assessment, CCSSO: progressions are developmental rather than age-deterministic; band mappings must preserve this."
  - "Webb, N. L. (1997) — Criteria for Alignment of Expectations and Assessments in Mathematics and Science Education, CCSSO Research Monograph No. 6: alignment is multi-dimensional (categorical concurrence, depth-of-knowledge, range, balance) — band translation addresses only the age-range dimension and must not be mistaken for full alignment."
input_schema:
  required:
    - field: band_schema
      type: string
      description: "The school or programme's developmental band definitions. Must include band labels, approximate age or grade ranges, and any named groupings. Example: REAL School Budapest uses Bands A-F — A (Water+Air Dragons, K-2, ages 5-7), B (Earth Dragons, G3-4, ages 7-9), C (Fire Dragons, G5-6, ages 9-11), D (Metal+Light Dragons, G7-8, ages 11-13), E (G9-10, ages 13-15), F (G11-12, ages 15-17)."
    - field: kud_json
      type: string
      description: The harness-produced KUD file (kud.json). Each item must include at minimum item_id, content_statement, knowledge_type, and source_block_id.
    - field: lts_json
      type: string
      description: The harness-produced LT file (lts.json). Each LT must include lt_id, lt_name, lt_definition, kud_item_ids, and knowledge_type.
    - field: progression_structure_json
      type: string
      description: The harness-produced progression_structure.json for the source. Must include band_labels, source_type, and age_range_hint (or per-band approximate_age_range). If both age-range fields are absent, the skill returns request_age_range_context in skill_flags and halts.
  optional:
    - field: criterion_bank_json
      type: string
      description: The harness-produced criterion_bank.json if criterion-level band tagging is also required. Optional — if omitted the skill tags only KUD items and LTs.
    - field: source_name
      type: string
      description: Human-readable source name (e.g. "UK DfE Statutory RSHE, July 2025") for output provenance. Defaults to progression_structure.source_slug if omitted.
    - field: user_age_range_override
      type: string
      description: Explicit age-range mapping supplied by the user when a source has no native band structure (flat list). Required only when the skill emits a request_age_range_context error.
output_schema:
  type: object
  fields:
    - field: source_metadata
      type: object
      description: Source name, source_type, source_band_labels (unchanged), and skill run provenance (version, timestamp, invoker).
    - field: band_tagged_kud
      type: array
      description: Every KUD item with school_band (string or array), band_confidence, source_band_preserved, source_voice_preserved (always true), ambiguity_flag, teacher_review_flag, and band_rationale.
    - field: band_tagged_lts
      type: array
      description: Every LT with school_band (string or array), band_confidence, source_band_preserved, source_voice_preserved (always true), ambiguity_flag, teacher_review_flag, and band_rationale. Band is assigned from the LT's constituent KUD items using the aggregation rule described in the prompt.
    - field: band_tagged_criteria
      type: array
      description: Present only if criterion_bank_json was supplied. Same field set as LTs. Inherit band from parent LT unless a criterion explicitly narrows the age range.
    - field: summary_counts
      type: object
      description: Counts of items per school band, ambiguity flags, teacher review flags, and low-confidence tags. For rapid quality scanning.
    - field: skill_flags
      type: array
      description: Any skill-level warnings (missing age range, CASEL-style frameworks requiring full teacher review, source-voice preservation warnings if any rewriting was detected).
chains_well_with:
  - curriculum-crosswalk
  - kud-knowledge-type-mapper
  - learning-progression-builder
  - competency-framework-translator
  - scope-and-sequence-designer
teacher_time: 10 minutes
tags:
  - developmental-bands
  - curriculum-alignment
  - band-mapping
  - source-voice-preservation
  - Wiggins-McTighe
  - Vygotsky
  - ZPD
  - framework-translation
---

# What This Skill Does

This skill tags an external curriculum — already decomposed by the curriculum harness into KUD items, learning targets, and (optionally) criteria — with a school's developmental band labels. The school's band schema is supplied as an input; the skill reads it, derives a mapping table from the source's age ranges to the school's band ranges, and applies that mapping across every item. Every item receives a `school_band` value, a confidence level, and diagnostic flags. The source's own band labels are preserved verbatim alongside the new school band tags, so the output can always be traced back to, and interpreted against, the original framework.

The skill is a metadata operation, not a content operation. It does not rewrite KUDs, LTs, or criteria, and it does not reinterpret the source's intent. Its only job is to answer the question: "If a teacher planning for a given school band opened this framework, which of its content is relevant to them?" The skill is deliberately conservative where a source band spans two school bands: it assigns both candidate bands, sets an ambiguity flag, and records a rationale. Downstream skills — especially the Curriculum Crosswalk skill and the human planning process — resolve these ambiguities with teacher judgement.

The skill handles three common source-structure scenarios. Most sources have an explicit band structure (Welsh CfW Progression Steps, NZ Curriculum Levels, IB PYP/MYP/DP phases) which maps cleanly with occasional boundary ambiguity. Some have a formal-but-compressed structure (UK RSHE has four Key Stage labels but only two actual age bands in the statutory document), where the skill applies the source's real 2-band structure first and records the formal label via `source_band_preserved`. A minority have no band structure at all (CASEL, some competency frameworks), where the skill maps by developmental descriptor rather than age and flags every item for teacher review.

# Evidence Foundation

**Wiggins & McTighe (2005, 2011)** — Understanding by Design establishes KUD (Know / Understand / Do) as the unit-level architecture through which framework content becomes teachable, and positions curriculum alignment as a backward-design operation from stated outcomes. The Developmental Band Translator operates on exactly the KUD layer that UbD specifies, and treats school-band assignment as one step in a backward-design pipeline whose final consumer is the classroom teacher.

**Vygotsky (1978)** — The Zone of Proximal Development grounds the concept that developmental banding is not a pure age-partition. A learner in a given band is defined by what they can do with support, not only by their chronological age. This justifies the skill's use of both age-range and developmental-descriptor evidence when tagging, and its willingness to assign a school band from descriptor-based reasoning alone when age evidence is absent.

**Heritage (2008)** — Learning progressions literature reinforces that progressions are developmental trajectories, not calendars. The skill treats school bands as trajectory-waypoints. Where a source's native progression is coarser than the school's (e.g. RSHE's 2-band structure vs a 6-band school schema), the skill preserves the coarseness honestly via ambiguity flags rather than forcing false precision.

**Webb (1997)** — The canonical alignment framework defines four alignment dimensions: categorical concurrence, depth-of-knowledge consistency, range-of-knowledge correspondence, balance of representation. Band translation addresses primarily the *range* dimension (do the age spans match?) with partial touch on *categorical concurrence*. The skill does not claim to assess depth or balance alignment; this limit is reported in `skill_flags` and in Known Limitations.

# Input Schema

**Required inputs.** The skill needs four inputs:

- **`band_schema`** — The school or programme's developmental band definitions. Must include band labels, approximate age or grade ranges, and any named groupings. The skill reads this to build the mapping table; it does not assume any particular band system. *Example*: "REAL School Budapest uses Bands A–F — A (Water+Air Dragons, K–2, ages 5–7), B (Earth Dragons, G3–4, ages 7–9), C (Fire Dragons, G5–6, ages 9–11), D (Metal+Light Dragons, G7–8, ages 11–13), E (G9–10, ages 13–15), F (G11–12, ages 15–17)."
- **`kud_json`** — The KUD file. Required fields per item: `item_id`, `content_statement`, `knowledge_type`, `source_block_id`. The skill uses `source_block_id` to look up the block's native band label in the progression structure.
- **`lts_json`** — The LT file. Required fields per LT: `lt_id`, `lt_name`, `lt_definition`, `kud_item_ids`, `knowledge_type`. LTs inherit their band from their constituent KUD items using a max-span rule (see Prompt).
- **`progression_structure_json`** — The progression structure. Required: `band_labels`, `source_type`, and either a top-level `age_range_hint` or per-band `approximate_age_range`. If both age-range fields are absent, the skill returns `request_age_range_context` in `skill_flags` and halts.

**Optional inputs.**

- **`criterion_bank_json`** — If supplied, criteria are also tagged. Criteria inherit their parent LT's band unless their content narrows to a more specific age-range signal.
- **`source_name`** — A friendly name for output metadata.
- **`user_age_range_override`** — A user-supplied age-range mapping, used when the source has no native band structure and the first invocation halted with `request_age_range_context`.

**Worked example of required inputs.** For a REAL School Budapest run against `uk-statutory-rshe`: `band_schema` = "REAL School Budapest uses Bands A–F — A (Water+Air Dragons, K–2, ages 5–7), B (Earth Dragons, G3–4, ages 7–9), C (Fire Dragons, G5–6, ages 9–11), D (Metal+Light Dragons, G7–8, ages 11–13), E (G9–10, ages 13–15), F (G11–12, ages 15–17)"; `kud_json` = the 279-item KUD file; `lts_json` = the 44-LT file; `progression_structure_json` = a structure declaring `band_labels: ["End of Primary (Year 6)", "End of Secondary (Year 11)"]`, `source_type: "national_statutory_curriculum"`, and age ranges 5–11 and 11–16 respectively.

# Prompt

You are a curriculum band-translation assistant. Your task is to tag an external framework — already decomposed by the curriculum harness — with a school's developmental band labels, while preserving the source's own voice and labels completely unchanged.

## School band schema

Read the supplied `band_schema` carefully. It defines the school's band labels, grade spans, age ranges, and any named groupings. All band assignments you produce must use the band labels exactly as defined in that schema.

## Procedure

1. **Read the progression structure.** Note `source_type`, `band_labels`, and age ranges. If both `age_range_hint` and per-band `approximate_age_range` are absent, emit `request_age_range_context` in `skill_flags`, do not tag anything, and stop.
2. **Build a band-mapping table for this source.** Using the `band_schema` and the source's per-band age ranges, identify which school bands overlap with each source band. Where a source band's age range spans multiple school bands, list all overlapping school bands as candidates and note the ambiguity. Where the source band maps cleanly to one school band, record low ambiguity. Record this mapping table in your reasoning before proceeding; every tagging decision in steps 3–5 must trace back to it.
3. **Tag every KUD item.**
   - Look up its `source_block_id` to find the source band.
   - Apply the band-mapping table to get candidate school bands.
   - `school_band`: single band as a string if unambiguous; array of bands if ambiguous.
   - `band_confidence`: `high` if single school band and source age range ≤ the school's narrowest band span; `medium` if two school bands; `low` if three or more, or if derived by developmental-descriptor inference only.
   - `source_band_preserved`: the exact native label from the source (e.g. "Key Stage 2", "End of Primary", "Progression Step 3").
   - `source_voice_preserved`: always `true`. If you would need to rewrite the content to make it fit a school band, do NOT rewrite — instead set this to `false` and add a skill flag. This field exists to prove no rewriting occurred.
   - `ambiguity_flag`: `true` if `school_band` is an array.
   - `teacher_review_flag`: `true` when (a) `school_band` spans three or more bands, (b) confidence is `low`, (c) `source_type` is a dispositional/competency framework with no age-banding (e.g. CASEL), or (d) the content statement contains developmental language that would narrow the band beyond what the source label allows.
   - `band_rationale`: one sentence explaining the assignment.
4. **Tag every LT.** An LT's school band is the union of its constituent KUD items' bands (max-span rule). If any constituent is ambiguous, the LT is ambiguous. `teacher_review_flag` fires if any constituent has it or if the LT aggregates across three or more school bands.
5. **Tag criteria** (if `criterion_bank_json` supplied). Each criterion inherits its parent LT's band unless its content narrows it. Same field set as LTs.
6. **Emit summary counts and skill flags.** Count items per school band, ambiguity flags, teacher-review flags, and low-confidence tags. Emit a skill flag for any source where >50% of items are ambiguous (signals a structural mismatch worth reviewing).

## Source-voice preservation rule (hard constraint)

You are **tagging** content, not rewriting it. Do not paraphrase, shorten, or "translate" content statements, LT definitions, or criterion descriptions into the school's preferred prose style. Keep source content exactly as written. The only new text you generate is `band_rationale`.

## CASEL / flat-framework handling

If `source_type` indicates a competency or dispositional framework with no age structure (e.g. CASEL), and no `user_age_range_override` was supplied:
- Set `teacher_review_flag: true` on every item.
- Set `band_confidence: low` on every item.
- Base `school_band` on the developmental sophistication of the descriptor, mapped to the school bands from the supplied `band_schema`: early-developmental content (emotion-labeling, basic self-regulation) → earliest bands in the schema; mid-developmental content (perspective-taking, collaborative problem-solving) → mid-range bands; late-developmental content (systems-level social awareness, abstract ethical reasoning) → later bands in the schema.
- Emit `skill_flag: casel_style_framework_full_teacher_review_required`.

## Inputs

- `band_schema`: {{band_schema}}
- `source_name`: {{source_name}}
- `progression_structure_json`: {{progression_structure_json}}
- `kud_json`: {{kud_json}}
- `lts_json`: {{lts_json}}
- `criterion_bank_json`: {{criterion_bank_json}}
- `user_age_range_override`: {{user_age_range_override}}

Produce the band-tagged output as a single JSON object conforming to the output schema. Do not rewrite source content. Do not invent bands the source cannot support.

# Example Output

**Context**: REAL School Budapest band schema supplied as `band_schema`. Source: UK DfE Statutory RSHE (July 2025), `progression_structure.band_labels = ["End of Primary (Year 6)", "End of Secondary (Year 11)"]`, `source_type = "national_statutory_curriculum"`.

**Inputs supplied**:

```json
{
  "band_schema": "REAL School Budapest uses Bands A–F — A (Water+Air Dragons, K–2, ages 5–7), B (Earth Dragons, G3–4, ages 7–9), C (Fire Dragons, G5–6, ages 9–11), D (Metal+Light Dragons, G7–8, ages 11–13), E (G9–10, ages 13–15), F (G11–12, ages 15–17). Bands are defined primarily by grade level; ages are approximate.",
  "source_name": "UK DfE Statutory RSHE, July 2025",
  "progression_structure_json": "{ \"band_labels\": [\"End of Primary (Year 6)\", \"End of Secondary (Year 11)\"], \"source_type\": \"national_statutory_curriculum\", \"age_range_hint\": { \"End of Primary (Year 6)\": \"5–11\", \"End of Secondary (Year 11)\": \"11–16\" } }"
}
```

**Output**:

```json
{
  "source_metadata": {
    "source_name": "UK DfE Statutory RSHE, July 2025",
    "source_type": "national_statutory_curriculum",
    "source_band_labels": ["End of Primary (Year 6)", "End of Secondary (Year 11)"],
    "skill_version": "1.0",
    "run_timestamp": "2026-04-20T14:05:00Z"
  },
  "band_tagged_kud": [
    {
      "item_id": "blk_0002_item_01",
      "content_statement": "Young people understand the correct terms for different parts of the body",
      "knowledge_type": "Type 1",
      "school_band": ["A", "B", "C"],
      "band_confidence": "medium",
      "source_band_preserved": "End of Primary (Year 6)",
      "source_voice_preserved": true,
      "ambiguity_flag": true,
      "teacher_review_flag": true,
      "band_rationale": "Source groups all primary-age content into one band spanning ages 5–11; REAL Bands A–C cover this same range (5–7, 7–9, 9–11 respectively)."
    },
    {
      "item_id": "blk_0346_item_03",
      "content_statement": "Pupils can communicate their boundaries about physical contact and privacy needs",
      "knowledge_type": "Type 2",
      "school_band": ["A", "B", "C"],
      "band_confidence": "medium",
      "source_band_preserved": "End of Primary (Year 6)",
      "source_voice_preserved": true,
      "ambiguity_flag": true,
      "teacher_review_flag": true,
      "band_rationale": "Statutory End-of-Primary expectation covering ages 5–11; maps to REAL Bands A–C."
    },
    {
      "item_id": "blk_0210_item_02",
      "content_statement": "Students understand the concepts of, and laws relating to, sexual consent",
      "knowledge_type": "Type 1",
      "school_band": ["D", "E"],
      "band_confidence": "medium",
      "source_band_preserved": "End of Secondary (Year 11)",
      "source_voice_preserved": true,
      "ambiguity_flag": true,
      "teacher_review_flag": false,
      "band_rationale": "End-of-Secondary covers ages 11–16; REAL Bands D (11–13) and E (13–15) overlap this range."
    }
  ],
  "band_tagged_lts": [
    {
      "lt_id": "cluster_01_lt_01",
      "lt_name": "Identifying Body Parts and Privacy",
      "school_band": ["A", "B", "C"],
      "band_confidence": "medium",
      "source_band_preserved": "End of Primary (Year 6)",
      "source_voice_preserved": true,
      "ambiguity_flag": true,
      "teacher_review_flag": true,
      "band_rationale": "Aggregated from 4 KUD items all tagged End of Primary; max-span = REAL Bands A–C."
    }
  ],
  "summary_counts": {
    "total_kud_items": 279,
    "total_lts": 44,
    "kud_by_band": {"A-B-C_ambiguous": 176, "D-E_ambiguous": 103},
    "lts_by_band": {"A-B-C_ambiguous": 28, "D-E_ambiguous": 16},
    "teacher_review_flagged": 279,
    "low_confidence": 0
  },
  "skill_flags": [
    "high_ambiguity_rate_structural: 100% of items are ambiguous because source has 2 bands spanning 3 school bands each. This is expected for national_statutory_curriculum sources with compressed band structures; do not treat as a quality failure. Downstream planning must resolve via teacher judgement."
  ]
}
```

# Known Limitations

**The skill does not do construct alignment.** Two items tagged to the same school band are not, by that fact alone, teaching the same thing. Webb's (1997) categorical-concurrence and depth-of-knowledge dimensions are out of scope. The skill answers "is this age-relevant?" not "does this match the school's learning intentions?" The Curriculum Crosswalk skill addresses relationships between frameworks but still requires human judgement for construct alignment.

**Ambiguity is not resolvable by this skill.** When a source's band structure is coarser than the school's — particularly UK RSHE's 2-band structure or any framework with fewer bands than the school schema — the skill deliberately preserves the ambiguity rather than guessing. High ambiguity rates (up to 100% for RSHE against a 6-band schema) are an honest report of the source's granularity, not a quality failure. They are resolved downstream by teacher judgement, which is why `teacher_review_flag` exists.

**Developmental-descriptor inference (CASEL case) is approximate.** When a framework has no age-banding, the skill maps by descriptor using the supplied `band_schema` as a guide — early-developmental descriptors → earliest bands in the schema; systems-level descriptors → later bands. These are defensible starting points drawn from developmental-psychology consensus, but they are not framework-specific determinations. Content tagged this way should be treated as a scaffold for teacher review, not a validated mapping.

**The skill assumes harness-validated input.** It does not re-validate the source decomposition. If the upstream harness produced a broken KUD or LT file (cycles in prerequisite graph, content_statement missing, etc.), the skill will pass those errors through as band-tagged nonsense. Run the harness's own validation gates before invoking this skill.

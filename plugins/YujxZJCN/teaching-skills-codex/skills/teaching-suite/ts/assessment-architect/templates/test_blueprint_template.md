# Test Blueprint: {{instrument_title}}

**Course:** {{course_code}} {{course_title}} · **Assessment ID:** {{assessment_id}}
**Type:** {{instrument_type}} · **Weight:** {{weight}}% · **Scheduled:** {{week}}
**Duration:** {{duration_minutes}} min · **Conditions:** {{conditions — closed/open book, calculator, formula sheet, platform}}
**Blueprint status:** {{draft | confirmed_by_professor + date}}

## Outcomes covered

| LO id | Outcome statement | Bloom level | Points on this instrument |
|-------|-------------------|-------------|---------------------------|
{{rows from assessment_plan.outcomes_assessed — every listed outcome appears; an
outcome with 0 points is a coverage flag, not an omission}}

## Content × Bloom matrix

Cells: `item count × format = points`. Empty cells are intentional, not oversights.

| Content area (taught in) | {{bloom_level_1}} | {{bloom_level_2}} | {{bloom_level_3}} | Points | % |
|--------------------------|-------------------|-------------------|-------------------|--------|---|
{{rows: one per content area, e.g. "Trees & balancing (W4–W6) | 4 × MC = 8 | 1 × problem = 12 | — | 20 | 25%"}}
| **Totals** | {{col_points}} | {{col_points}} | {{col_points}} | **{{total_points}}** | 100% |

**Emphasis check:** {{comparison of each row's % against its share of instructional
time; mismatches listed with rationale or flag}}
**Level-honesty flags:** {{outcomes whose bloom_level exceeds what their cells can
measure — Pedagogy Foundations §3 — or "none"}}

## Time budget

Heuristics (adjustable — challenge the constants, not just the total): MC ~1–1.5 min ·
short answer ~3–5 min · problem ~8–15 min · essay ~20–30 min.

| Item type | Count | Est. minutes each | Subtotal |
|-----------|-------|-------------------|----------|
{{rows per item type}}
| **Total** | | | **{{est_total_min}} / {{duration_minutes}} min** |

Target ≤90% of duration. Status: {{within budget | OVER — cut options listed at checkpoint}}

## Versions & accommodations

- **Parallel forms:** {{n_versions and variant strategy per references/item_writing_rules.md bank discipline, or "single form"}}
- **Extra-time variant (Quality Gate U3):** {{how derived — same instrument at {{multiplier}}× clock, or reduced-length variant; who arranges logistics}}
- **Other anticipated accommodations:** {{from learner_profile.accessibility_needs, or "none recorded — [NEEDS PROFESSOR INPUT if institution requires a plan]"}}

## Integrity tier

**Declared tier:** {{P | D | O}} — {{one-line rationale from assessment_plan}}
**Audit status:** {{ai_resilience value; the integrity audit runs after assembly — this
field is set only by integrity_auditor_agent}}

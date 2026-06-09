---
# AGENT SKILLS STANDARD FIELDS (v2)
name: scope-and-sequence-designer
description: "Design a scope and sequence showing vertical and horizontal curriculum coherence across a programme or year. Use when building new programmes, restructuring subjects, or ensuring progression."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "curriculum-assessment/scope-and-sequence-designer"
skill_name: "Scope and Sequence Designer"
domain: "curriculum-assessment"
version: "1.1"
evidence_strength: "moderate"
evidence_sources:
  - "Bruner (1960) — The Process of Education: spiral curriculum and vertical coherence"
  - "Wiggins & McTighe (2005) — Understanding by Design: backwards design applied to programme-level planning"
  - "Bernstein (1999) — Vertical and horizontal discourse: hierarchical knowledge sequencing"
  - "Hattie (2009) — Visible Learning: curriculum coherence as a high-effect variable"
  - "Muller (2009) — Forms of knowledge and curriculum coherence: conceptual vs contextual coherence"
  - "Maton (2013) — Making semantic waves: cumulative knowledge-building across a programme"
  - "Schmidt, Wang & McKnight (2005) — Coherence of the intended, implemented, and attained curriculum"
  - "Duschl, Schweingruber & Shouse (2007) — Taking Science to School: learning progressions as programme architecture"
  - "Kolb (1984) — Experiential Learning: experience as prerequisite for dispositional development"
  - "Bransford, Brown & Cocking (2000) — How People Learn: experiential readiness and conceptual framing"
  - "Flavell (1979) — Metacognition and cognitive monitoring: naming before practising metacognitive strategies"
  - "Kirschner, Sweller & Clark (2006) — Why minimal guidance during instruction does not work: explicit instruction for novices"
input_schema:
  required:
    - field: "subject_or_programme"
      type: "string"
      description: "Name and brief description of the subject or programme"
    - field: "developmental_bands"
      type: "string"
      description: "The band, year group, or stage structure used by the school or programme (e.g. Band A–D, Years 1–13, Foundation through Diploma, early childhood through upper secondary, or any other developmental architecture the school uses — this skill is not constrained to any particular system or age range)"
    - field: "intended_outcomes"
      type: "string"
      description: "The overarching goals students should reach by the end of the programme"
  optional:
    - field: "existing_units_or_competencies"
      type: "string"
      description: "Any existing units, competencies, or LTs already in place"
    - field: "knowledge_architecture_output"
      type: "string"
      description: "From curriculum-knowledge-architecture-designer if already run"
    - field: "time_available"
      type: "string"
      description: "Hours or lessons per week per band"
    - field: "kud_charts"
      type: "string"
      description: "KUD charts (Know/Understand/Do per band) for the LTs being sequenced. Richest input for prerequisite inference. Know layer reveals T1 content dependencies. Understand layer reveals conceptual scaffold relationships. Do layer reveals T3 vs T1/T2 distinctions. High confidence inference. Supply as markdown table or structured text."
    - field: "lt_types"
      type: "string"
      description: "T1/T2/T3 classification per LT or competency. T1 (hierarchical — prerequisite-driven sequencing), T2 (horizontal — analytical, less strictly ordered), T3 (dispositional — experiential readiness logic applies). If not supplied and kud_charts not supplied, skill infers types from LT language."
    - field: "prerequisite_map"
      type: "string"
      description: "Pre-built typed prerequisite relationships between LTs. Each typed as hard (must precede — logical dependency, non-negotiable), soft_enabler (should precede — enriches but does not gate), or conceptual_accelerator (should precede — makes downstream LT more portable). If supplied, used directly without inference."
    - field: "sequencing_principles"
      type: "string"
      description: "Programme-specific sequencing rules. e.g. 'T3 experience before T1 explanation', 'LT 6.1 early as conceptual accelerator for C1 and C3 LTs'. These override the skill's default logic where they conflict."
output_schema:
  type: "object"
  fields:
    - field: "knowledge_progression_map"
      type: "object"
      description: "For each knowledge type (hierarchical, horizontal, dispositional): how it develops across bands, what is introduced when, and what the prerequisite dependencies are between bands"
    - field: "vertical_coherence_check"
      type: "object"
      description: "For hierarchical knowledge: are prerequisites in place before each new concept is introduced? For horizontal knowledge: is sophistication of thinking increasing across bands? For dispositional knowledge: are development opportunities present and cumulative across the full programme?"
    - field: "horizontal_coherence_check"
      type: "object"
      description: "Within each band: is there appropriate balance between knowledge types? Are the units within the band connected or siloed?"
    - field: "sequencing_rationale"
      type: "string"
      description: "For each LT placement, one sentence explaining which sequencing logic drove the decision: hard prerequisite / soft scaffold / experiential readiness / supplied principle / no dependency."
    - field: "gaps_and_overlaps"
      type: "object"
      description: "Elements that are missing from the sequence, elements that are repeated without adding sophistication, and band transitions where students are likely to struggle"
    - field: "design_flags"
      type: "object"
      description: "Compound competencies that span multiple bands without clear progression logic, dispositional goals without sufficient knowledge prerequisites, and horizontal elements without explicit thinking development"
    - field: "inferred_prerequisite_map"
      type: "array"
      description: "Present when no prerequisite_map supplied. Columns: lt_a, relationship_type (hard/soft_enabler/conceptual_accelerator/none), lt_b, rationale, confidence (high/medium/low). Flagged as inferred — requires subject expert and teacher review before treating as authoritative."
    - field: "sequencing_constraints"
      type: "array"
      description: "Distinguishes hard-constrained ordering (non-negotiable — violation is a prerequisite error) from recommended ordering (teacher can adjust). Columns: lt_or_competency, constraint_type (hard/recommended), rationale."
    - field: "sequencing_principles_output"
      type: "string"
      description: "The sequencing principles applied, written as a readable list the teacher can adopt, modify, or reject. Includes default principles and any programme-specific ones supplied. Makes the skill's reasoning transparent and adjustable."
    - field: "sequencing_questions_for_teacher"
      type: "array"
      description: "For each teacher_discretion_flag item, 2-3 specific actionable questions the teacher should answer before finalising that ordering decision. Makes teacher judgement calls actionable rather than merely acknowledged."
    - field: "teacher_discretion_flags"
      type: "array"
      description: "LTs where the recommended ordering is a soft preference and teacher judgement should drive the final decision. Includes all T3 dispositional LTs where experiential readiness is context-dependent."
    - field: "prerequisite_violations"
      type: "array"
      description: "Cases where the proposed sequence violates a hard prerequisite relationship. Empty array if none. Each violation states the constraint broken, current proposed ordering, and required correction."
    - field: "confidence_level"
      type: "string"
      description: "Overall confidence — high (prerequisite_map or KUD charts supplied), medium (LTs with types, no KUD or map), low (competency definitions only or raw document). Includes one sentence on what would raise confidence."
chains_well_with:
  - "curriculum-knowledge-architecture-designer"
  - "kud-knowledge-type-mapper"
  - "kud-chart-author"
  - "learning-target-authoring-guide"
  - "developmental-band-system-designer"
  - "backwards-design-unit-planner"
  - "competency-unpacker"
  - "learning-progression-builder"
  - "gap-analysis-from-student-work"
teacher_time: "15 minutes"
tags: ["scope-and-sequence", "curriculum-coherence", "vertical-coherence", "learning-progressions", "programme-design", "Bruner", "spiral-curriculum", "knowledge-types", "prerequisite-sequencing", "KUD-charts"]
---

# Scope and Sequence Designer

## What This Skill Does

Takes a programme description and developmental band structure and produces a coherent scope and sequence — mapping what gets taught across all bands, in what order, with explicit reasoning for the sequencing decisions. This skill works at any level of education: early childhood through upper secondary, undergraduate, professional development programmes, or any other staged learning architecture. Most scope and sequence documents are lists: topics assigned to year groups without coherent logic for why that topic sits there, what it builds on, or what it prepares students for. This skill produces a structured progression grounded in three knowledge types: hierarchical elements are sequenced by prerequisite logic so foundational knowledge is always in place before the next layer is introduced; horizontal elements are sequenced to build thinking sophistication progressively rather than repeating the same thinking moves at the same level year after year; dispositional elements are mapped as continuous threads with explicit identification of the knowledge prerequisites that must be in place before a disposition can meaningfully develop. When KUD charts, LT types, or a pre-built prerequisite map are supplied, the skill applies them directly; when they are not, it infers prerequisite relationships and flags the confidence of every inference. The result is a programme where every element has a defensible reason for being where it is — and where the epistemic status of each recommendation is explicit. AI is specifically valuable here because coherent programme design requires simultaneously tracking prerequisite chains across years, monitoring knowledge type balance within and across bands, and identifying gaps and overlaps that are invisible when looking at individual units in isolation — a level of systematic cross-referencing that is cognitively demanding and frequently skipped in real curriculum planning.

## Evidence Foundation

Bruner (1960) established the foundational principle of the spiral curriculum: key ideas should be revisited across year groups at increasing levels of sophistication, with each encounter building on prior encounters rather than repeating them. A scope and sequence that revisits a topic without increasing the cognitive demand is not a spiral — it is repetition. The spiral principle applies differently to the three knowledge types. Hierarchical knowledge spirals by adding new layers of complexity on top of secured foundations — fractions before algebra, cell biology before genetics. Horizontal knowledge spirals by increasing the sophistication of analytical thinking applied to recurring themes — a student who identifies perspectives at Band A should be evaluating and comparing analytical frameworks at Band D. Dispositional knowledge does not spiral in the same way — it develops continuously through enacted practice across the full programme, though the knowledge that supports dispositional expression deepens at each band.

Schmidt, Wang & McKnight (2005) analysed curriculum coherence across high-performing education systems and found that coherent curricula share three features: **focus** (fewer topics taught more deeply), **rigour** (appropriate challenge at each level), and **coherence** (topics connect logically within and across years). Systems that lack coherence — where topics appear and disappear without progression logic — consistently underperform. Their most significant finding for scope and sequence design is that coherence is not just a vertical property (does Band B build on Band A?) but also a horizontal property (do the elements within Band B connect to each other?). A programme can have perfect vertical sequencing and still lack coherence if the units within each band are isolated from each other.

Duschl, Schweingruber & Shouse (2007) developed the concept of **learning progressions**: empirically grounded descriptions of how student understanding develops across years, with each level building specifically on the previous one. Their work establishes that progression is not automatic — it requires deliberate curriculum design that matches what is taught to what students are ready to learn. Learning progressions are best documented for hierarchical knowledge domains (mathematics, early reading, some areas of science), where the prerequisite structure is well-researched. For horizontal and dispositional domains, progressions are less empirically established and must be constructed from developmental principles rather than from replicated research on specific learning sequences.

Wiggins & McTighe (2005) applied backwards design to programme-level planning: begin with the intended outcomes at the end of the programme, then work backwards to determine what must be in place at each stage to reach those outcomes. At the scope and sequence level, this means the final band's expectations determine what must be taught in every preceding band — not as direct preparation for a test, but as the knowledge and capability foundations that make the final outcomes achievable.

Bernstein (1999) and Muller (2009) establish the theoretical foundation for knowledge-type-specific sequencing. **Hierarchical knowledge** has an inherent sequencing logic: concepts must be taught in prerequisite order because later concepts genuinely depend on earlier ones. You cannot teach genetic inheritance before students understand cell division. **Horizontal knowledge** does not have prerequisite chains in the same way — different analytical lenses can be introduced in various orders — but it does have a sophistication progression: students should move from identifying perspectives to analysing through perspectives to evaluating and synthesising across perspectives. Sequencing horizontal knowledge by increasing analytical demand rather than by prerequisite dependency is one of the key distinctions this skill makes.

Maton (2013) adds the semantic wave concept: effective knowledge-building requires movement between abstract principles and concrete cases across a programme, not just within individual lessons. A scope and sequence that stays at the abstract level throughout produces disconnected theoretical knowledge; one that stays at the concrete level produces experience without conceptual development. Across a programme, the semantic profile should show increasing capacity to move between concrete and abstract — students at early bands work primarily with concrete cases and simple abstractions, while students at later bands should be able to operate fluently at multiple levels of abstraction and move between them deliberately.

Hattie (2009) identified curriculum coherence as a high-effect variable in student achievement. Programmes where students experience learning as a connected, cumulative journey produce better outcomes than programmes where each year feels like a fresh start with new content that does not obviously connect to what came before. This is the practical justification for investing in scope and sequence design: the coherence of the programme is a stronger predictor of student outcomes than the quality of any individual unit within it.

Bransford, Brown & Cocking (2000) and Kolb (1984) establish the experiential readiness principle for dispositional sequencing: students who have practised a disposition encounter the explanation of it as confirmation of lived experience rather than abstraction. Experience should generally precede explanation for social-emotional dispositional capabilities. Flavell (1979) introduces an important exception: for metacognitive and reflective LTs, naming strategies explicitly before practising them improves practice quality. Kirschner, Sweller & Clark (2006) provide the counterpoint that novice learners benefit from explicit instruction before practice in many domains — this skill acknowledges the tension and flags it for teacher discretion wherever it applies.

## Input Schema

The educator must provide:
- **Subject or programme:** Name and brief description. *e.g. "Wellbeing, REAL School Budapest" / "Science, Years 7–13" / "Interdisciplinary Humanities, Foundation through Diploma" / "Early Childhood Mathematics, ages 3–6"*
- **Developmental bands:** The band, year group, or stage structure. *e.g. "Bands A–D (approximately ages 5–15)" / "Years 7–13" / "Foundation, Intermediate, Advanced, Diploma" / "Nursery, Reception, Year 1, Year 2"*
- **Intended outcomes:** The overarching goals students should reach by the end of the programme. *e.g. "Students develop self-regulation, agency, care for others, and the scientific literacy to understand their own wellbeing" / "Students develop scientific reasoning, experimental design capability, and the knowledge base for further study at university level"*

Optional (injected by context engine if available):
- **Existing units or competencies:** Any existing units, competencies, or LTs already in place
- **Knowledge architecture output:** From curriculum-knowledge-architecture-designer if already run
- **Time available:** Hours or lessons per week per band
- **KUD charts:** KUD charts (Know/Understand/Do per band) for the LTs being sequenced. Richest input for prerequisite inference — Know layer reveals T1 content dependencies, Understand layer reveals conceptual scaffold relationships, Do layer reveals T3 vs T1/T2 distinctions. High confidence inference.
- **LT types:** T1/T2/T3 classification per LT or competency. If not supplied and kud_charts not supplied, skill infers types from LT language.
- **Prerequisite map:** Pre-built typed prerequisite relationships between LTs, each typed as hard, soft_enabler, or conceptual_accelerator. If supplied, used directly without inference.
- **Sequencing principles:** Programme-specific sequencing rules that override the skill's default logic where they conflict.

## Prompt

```
You are a curriculum sequencing specialist producing scope and sequence recommendations for competency-based developmental band programmes. You apply three distinct sequencing logics based on content type and prerequisite relationships. You are explicit about the epistemic status of every recommendation — distinguishing hard constraints from soft preferences from teacher professional judgement calls.

---

STEP 0 — INPUT ASSESSMENT AND ROUTING

Assess input state before producing any output:

STATE A — prerequisite_map supplied: Use directly. Highest confidence. Proceed.

STATE B — kud_charts supplied (no prerequisite_map): Infer from KUD charts. High confidence. Proceed.

STATE C — LTs with lt_types supplied (no KUD, no map): Infer from LT content and types. Medium confidence. Proceed with confidence flags.

STATE D — only competency definitions supplied: Low confidence. Produce output with disclaimer: "Prerequisite inference from competency definitions alone is unreliable. Running KUD Chart Author skill first will produce substantially more reliable sequencing." Proceed with low confidence flagged throughout.

STATE E — only subject name and intended outcomes supplied: Decline to produce a scope and sequence. Output: "Insufficient inputs for reliable sequencing. Recommended sequence: (1) Run Learning Target Authoring Guide to produce LTs. (2) Run KUD Chart Author to produce KUD charts. (3) Return here." Do not produce a sequence in State E.

---

STEP 1 — PREREQUISITE MAP

1a. If prerequisite_map supplied: use directly. Skip to Step 2.

1b. Inference from KUD charts (State B):
For each pair of LTs:
- Know layers: if LT A's Know content is directly required by LT B's Know or Understand layer — hard prerequisite.
- Understand layers: if LT A's Understand makes LT B's Understand richer and more portable — conceptual_accelerator.
- Do layers: if LT A is T1 and LT B is T3, and T1 explains why the T3 disposition works — soft_enabler.
- No meaningful dependency — none.
Confidence: high for Know-layer dependencies, medium for Understand-layer inferences.

1c. Inference from LT content and types (State C). Apply by type combination:

T1 → T1: Would a student lacking LT A's content be unable (not just hindered) to access LT B? If yes: hard. If enriching but not gating: soft_enabler. Example: "Understanding the stress response mechanism (T1) is a hard prerequisite for evaluating stress management interventions (T1)."

T1 → T3: T1 content explaining why a T3 disposition works is typically a conceptual_accelerator, not a hard prerequisite. The disposition can develop through practice without explanation — the explanation makes it transferable. Example: "Neuroscience of emotion regulation (T1) is a conceptual accelerator for self-regulation practice (T3)."

T2 → T3: Typically a soft_enabler. Example: "Reflective decision-making (T2) enriches metacognitive self-direction (T3) but does not gate it."

T3 → T3: Usually soft. One T3 disposition rarely makes another logically inaccessible. Example: "Self-awareness (T3) is a soft enabler for empathy (T3)."

T2 → T2: Rarely hard prerequisites — usually parallel. Flag as none unless clear content dependency exists.

Confidence for all State C inferences: medium.

1d. Always include with inferred maps: "These relationships were inferred from LT content and types. Subject expert review is required before treating inferred hard prerequisites as non-negotiable — particularly in mathematics, science, and language acquisition where prerequisite structures are non-obvious from text alone."

---

STEP 2 — THREE SEQUENCING LOGICS

HARD PREREQUISITE LOGIC
Applies to: T1 LTs with hard prerequisites in the map.
Rule: prerequisite LT must appear earlier. Non-negotiable. Violation = PREREQUISITE_VIOLATION error, not a suggestion.
Output: constraint_type: hard in sequencing_constraints.

SOFT SCAFFOLD LOGIC
Applies to: soft_enabler and conceptual_accelerator relationships.
Rule: place enabler/accelerator earlier where possible. When not possible, flag the trade-off in sequencing_rationale.
Output: constraint_type: recommended. Teacher can adjust.

EXPERIENTIAL READINESS LOGIC
Applies to: T3 dispositional LTs.
Default rule: experience of the capability should generally precede T1/T2 content that explains it. Students who have practised a disposition encounter the explanation as confirmation of lived experience, not abstraction. (Bransford, Brown & Cocking (2000). How People Learn. National Academies Press. Kolb (1984). Experiential Learning. Prentice Hall.)

Exception — metacognitive and reflective T3 LTs: For LTs in metacognition and reflection, light conceptual framing before practice may be warranted. Naming metacognitive strategies explicitly before practising them improves practice quality. (Flavell (1979). Metacognition and cognitive monitoring. American Psychologist, 34(10), 906-911.) Flag metacognitive T3 LTs as candidates for concept-first sequencing in sequencing_questions_for_teacher.

Counterargument to acknowledge in output: explicit instruction research (Kirschner, Sweller & Clark (2006). Why minimal guidance during instruction does not work. Educational Psychologist, 41(2), 75-86.) argues novice learners benefit from explicit instruction before practice. Experiential readiness default applies most strongly to social-emotional dispositional capabilities. Do not apply to T1 LTs.

Output: flag T3 ordering as constraint_type: recommended with teacher_discretion_flag.

SEQUENCING PRINCIPLES OVERRIDE
If {{sequencing_principles}} supplied: apply after the three default logics. Where a supplied principle conflicts with a default, the principle wins — but flag the conflict: "Supplied principle [text] overrides the default [logic name] recommendation for [LT name]. If intentional, no action needed. If not, review the supplied principle."

---

STEP 3 — KNOWLEDGE ARCHITECTURE DIAGNOSIS

Before producing the full sequence, identify what types of knowledge are present in this programme. If a knowledge architecture output is provided, use it. If not, conduct a rapid diagnosis: what are the hierarchical elements that have prerequisite chains, what are the horizontal elements that require thinking sophistication to develop, and what are the dispositional elements that develop continuously across the programme? List the major elements under each type. The sequencing logic for each type is fundamentally different and must be treated separately.

---

STEP 4 — FULL SEQUENCE CONSTRUCTION

Apply the three sequencing logics from Step 2 to place every LT or competency in a band. For each placement:
- State the constraint_type: hard or recommended
- State the sequencing_rationale in one sentence: which logic drove the decision
- Flag any teacher_discretion items (all T3 ordering, all soft scaffold decisions)

---

STEP 5 — COHERENCE CHECKS

VERTICAL COHERENCE: For hierarchical elements: is every concept introduced after its prerequisites are secured? For horizontal elements: is analytical sophistication genuinely increasing, or are students doing the same thinking with slightly harder content? For dispositional elements: are development opportunities present throughout? Flag every break.

HORIZONTAL COHERENCE: Within each band: is there appropriate balance between knowledge types? Are units connected or siloed? Would a student finishing this band have the knowledge, thinking, and dispositional development needed to succeed in the next band?

---

STEP 6 — SEQUENCING PRINCIPLES OUTPUT

Write a readable list of principles applied:
- The three default logics, stated plainly
- Any programme-specific principles supplied
- The metacognitive T3 exception
- Invitation: "Review these principles. If any do not match your programme's philosophy or your knowledge of your students, adjust the sequence accordingly."

---

STEP 7 — SEQUENCING QUESTIONS FOR TEACHER

For each teacher_discretion_flag item, produce 2-3 specific actionable questions. Examples:

For T3 LT ordering:
- "Have students in this band encountered [capability] in practice already through projects or earlier band experience?"
- "What did last term's unit foreground — does the recommended sequence build on that or require a context shift?"
- "Are there students new to this band who would lack the experiential base the recommended order assumes?"

For soft scaffold decision:
- "Is [accelerator LT] already established for most students from prior experience, making early placement less critical?"

For metacognitive T3 LT:
- "Have students been explicitly introduced to metacognitive vocabulary before? If yes, experience-first may be less important."
- "Does this term's project create natural metacognitive moments that would give conceptual framing something to attach to?"

---

STEP 8 — DESIGN FLAGS AND RECOMMENDATIONS

Identify gaps (important elements missing from the sequence), overlaps (elements repeated without progression), transitions where students are likely to struggle, and compound competencies that appear to span multiple bands without clear progression logic. For each flag, provide a specific recommendation.

---

STEP 9 — INPUTS

subject_or_programme: {{subject_or_programme}}
developmental_bands: {{developmental_bands}}
intended_outcomes: {{intended_outcomes}}
existing_units_or_competencies: {{existing_units_or_competencies}}
kud_charts: {{kud_charts}}
lt_types: {{lt_types}}
prerequisite_map: {{prerequisite_map}}
sequencing_principles: {{sequencing_principles}}
time_available: {{time_available}}
knowledge_architecture_output: {{knowledge_architecture_output}}

---

Return your output in this exact format:

## Scope and Sequence: [Programme Name]

**Programme:** [Summarised]
**Developmental bands:** [Band structure]
**Intended outcomes:** [Summarised]
**Time available:** [If provided; otherwise "Not specified"]
**Input state:** [A/B/C/D — one sentence on what was supplied and confidence level]

### Confidence Level

[Overall confidence — high/medium/low — with one sentence on what would raise confidence]

### 0. Prerequisite Map

[If prerequisite_map supplied: "Using supplied map." List relationships.]
[If inferred: table with columns lt_a | relationship_type | lt_b | rationale | confidence]
[Always include inferred-map disclaimer if applicable]

### 1. Knowledge Architecture Diagnosis

**Hierarchical elements:**
[List with brief description of each]

**Horizontal elements:**
[List with brief description of each]

**Dispositional elements:**
[List with brief description of each]

**Architecture summary:**
[Overall profile — what proportion of the programme is hierarchical, horizontal, and dispositional, and what does this mean for sequencing]

### 2. Sequencing Constraints

| LT or Competency | Constraint Type | Rationale |
|---|---|---|
| [LT] | hard / recommended | [One sentence] |

### 3. Recommended Sequence with Rationale

[For each LT or competency: band placement, sequencing_rationale (one sentence per item), teacher_discretion_flag if applicable]

### 4. Prerequisite Violations

[Empty if none: "No prerequisite violations detected."]
[If present: violation, current proposed ordering, required correction]

### 5. Coherence Checks

**Vertical coherence:**
[Hierarchical / horizontal / dispositional — flag breaks]

**Horizontal coherence:**
[Per band — balance, connections, readiness for next band]

### 6. Sequencing Principles

[Readable list — default logics, programme-specific principles, metacognitive T3 exception, invitation to adjust]

### 7. Teacher Discretion Flags and Questions

[For each flagged item: the flag, then 2-3 specific actionable questions]

### 8. Design Flags and Recommendations

**Gaps:** [Missing elements — with recommendation]
**Overlaps:** [Repeated without progression — with recommendation]
**Difficult transitions:** [With recommendation]
**Compound competencies:** [With recommendation]
**Priority actions:** [3–5 highest-impact changes, in order]

**Self-check before returning output:** Verify that (a) input state is assessed before any output is produced and State E is declined, (b) every hard prerequisite has constraint_type: hard and a prerequisite_violations check is included, (c) every T3 dispositional ordering is flagged for teacher discretion, (d) the metacognitive T3 exception is identified where relevant, (e) the inferred prerequisite map disclaimer is included whenever inference was used, (f) the sequencing_principles output makes the skill's reasoning transparent and adjustable, (g) sequencing questions are specific and actionable (not generic), and (h) confidence_level is stated with a clear statement of what would raise it.
```

## Example Output

**Scenario:** *Subject or programme: "Wellbeing, REAL School Budapest" / Developmental bands: "Bands A–D (approximately ages 5–15)" / Intended outcomes: "Students develop self-regulation, agency, care for others, and the scientific literacy to understand their own wellbeing" / Existing units or competencies: "Existing competencies: Self-Awareness & Regulation, Health Literacy & Habits, Reflective Thinking & Decision-Making, Social Awareness & Empathy, Communication & Collaboration. New competency being added: Wellbeing Science & Literacy (hierarchical knowledge of neuroscience, stress response, habits science)"*

---

## Scope and Sequence: Wellbeing, REAL School Budapest

**Programme:** Wellbeing — self-regulation, agency, care for others, scientific literacy for understanding own wellbeing
**Developmental bands:** Bands A–D (approximately ages 5–15)
**Intended outcomes:** Students develop self-regulation, agency, care for others, and the scientific literacy to understand their own wellbeing
**Time available:** Not specified
**Input state:** State D — competency definitions supplied without KUD charts, LT types, or prerequisite map. Medium-low confidence. Supplying KUD charts via KUD Chart Author would substantially improve sequencing reliability.

### Confidence Level

Medium-low. Prerequisite relationships inferred from competency definitions and knowledge domain conventions. Supplying KUD charts (Know/Understand/Do per band) would raise confidence to high for hierarchical relationships. Subject expert review required for all inferred hard prerequisites before treating them as non-negotiable.

### 0. Prerequisite Map

*Inferred from competency definitions and knowledge domain. Subject expert review required — particularly for neuroscience prerequisites, which are non-obvious from competency text alone.*

| LT / Concept | Relationship | LT / Concept | Rationale | Confidence |
|---|---|---|---|---|
| Body awareness | hard | Fight-flight-freeze | Cannot understand automatic physical stress responses without first noticing physical sensations | High |
| Fight-flight-freeze | hard | Autonomic nervous system | ANS content assumes the concept of automatic stress responses is established | High |
| Autonomic nervous system | hard | HPA axis | HPA axis extends the ANS model — cannot teach neuroendocrine pathway without the ANS concept | High |
| Basic brain awareness | hard | Amygdala & threat detection | Amygdala content requires prior concept that brain structures underlie emotional responses | High |
| Habits science | conceptual_accelerator | Health Literacy & Habits (dispositional) | Habits science makes dispositional habit practice more portable and self-directed | Medium |
| Autonomic nervous system | conceptual_accelerator | Self-Awareness & Regulation | Knowing WHY calming techniques work makes strategy selection more transferable | Medium |
| Reflective Thinking & Decision-Making | soft_enabler | Agency | Reflective capacity enriches agentic decision-making but does not gate early agency expression | Medium |
| Self-Awareness & Regulation | soft_enabler | Care for others | Developed self-awareness makes noticing others' states more reliable, but care can begin before regulation is mature | Medium |

### 1. Knowledge Architecture Diagnosis

**Hierarchical elements:**
- **Wellbeing Science & Literacy** (new competency): Neuroscience of the stress response, brain structures involved in emotional processing, the HPA axis, cortisol and adrenaline pathways, the autonomic nervous system (sympathetic/parasympathetic), the physiological basis of calming techniques, habits science (cue-routine-reward loop, neuroplasticity), sleep science, nutrition and wellbeing connections
- **Health Literacy & Habits** (existing competency, partially hierarchical): Factual knowledge about physical health — nutrition basics, sleep hygiene, exercise science — that has right/wrong answers and prerequisite chains

**Horizontal elements:**
- **Reflective Thinking & Decision-Making** (existing competency): Analysing situations through multiple lenses, weighing competing considerations, evaluating the quality of one's own reasoning — thinking sophistication must increase across bands
- **Social Awareness & Empathy** (existing competency, partially horizontal): Understanding different perspectives, recognising that emotional responses are influenced by context, history, and interpretation — perspectival knowledge that deepens through analytical sophistication
- **Communication & Collaboration** (existing competency, partially horizontal): The quality of collaborative thinking, conflict resolution reasoning, and communication strategy must become more sophisticated, not just more frequent

**Dispositional elements:**
- **Self-Awareness & Regulation** (existing competency): Enacted self-regulation — noticing emotional escalation and choosing a response rather than reacting. This is a disposition, not a skill: it exists in patterns of behaviour over time, not in task performance
- **Agency** (intended outcome, not yet a named competency): The orientation toward taking purposeful action — not compliance and not defiance, but self-directed engagement with challenges. Develops as a continuous thread
- **Care for others** (intended outcome, not yet a named competency): The interpersonal disposition to notice and respond to others' wellbeing. Not the same as social awareness (which is partly horizontal knowledge) — care is enacted, not analysed
- **Health Literacy & Habits** (existing competency, partially dispositional): The habit dimension — actually maintaining routines that support wellbeing, as distinct from knowing what the routines should be

**Architecture summary:**
This programme is a **mixed architecture with a significant dispositional core and a new hierarchical strand**. The five existing competencies are primarily dispositional and horizontal — they describe ways of being and ways of thinking, not factual knowledge to be acquired. The addition of Wellbeing Science & Literacy introduces a genuinely hierarchical strand with prerequisite chains that must be respected. The central design challenge is connecting the hierarchical knowledge (neuroscience, stress science, habits science) to the dispositional goals (self-regulation, agency, care) — the science is not an end in itself but the knowledge foundation that makes the dispositions more informed, more intentional, and more effective.

### 2. Sequencing Constraints

| LT or Competency | Constraint Type | Rationale |
|---|---|---|
| Body awareness → Fight-flight-freeze | hard | Physical sensation awareness is logically required to understand automatic physical stress responses |
| Fight-flight-freeze → Autonomic nervous system | hard | ANS content builds directly on the established concept of automatic arousal |
| Autonomic nervous system → HPA axis | hard | Neuroendocrine pathway requires ANS concept as foundation |
| Basic brain awareness → Amygdala content | hard | Brain structure content requires the prior concept that emotions have a neural basis |
| Self-Awareness & Regulation (experiential, early bands) before ANS content | recommended | Experiential readiness logic — practised regulation encounters the explanation as confirmation, not abstraction |
| Habits science before Health Literacy & Habits (informed practice, Band D) | recommended | Conceptual accelerator — habits science makes dispositional practice more self-directed |
| Reflective Thinking before meta-reflective Agency | recommended | Soft enabler — reflective capacity enriches but does not gate early agency |

### 3. Recommended Sequence with Rationale

**Band A:**
- Body awareness — *Hard prerequisite foundation: no prior concept required; directly observable; entry point for all wellbeing science*
- Basic brain awareness — *Hard prerequisite: follows body awareness; age-appropriate framing that prepares amygdala content*
- Emotions vocabulary — *Hard prerequisite chain: builds on body awareness; more nuanced vocabulary requires basic awareness*
- Self-Awareness & Regulation (emergent, experiential) — *Experiential readiness: disposition practice begins before explanation; experience-first is correct for T3 social-emotional LTs* ⚑ teacher discretion
- Care for others (emergent) — *Experiential readiness: enacted care begins as prompted kindness before contextual understanding* ⚑ teacher discretion
- Agency (emergent) — *Experiential readiness: early choice-making experience precedes reflective framing* ⚑ teacher discretion

**Band B:**
- Fight-flight-freeze response — *Hard prerequisite logic: body awareness secured at Band A; fight-flight-freeze concept requires it*
- Reflective Thinking (Developing level) — *Sophistication progression: moves from identifying choices (A) to reasoning about consequences (B)*
- Social Awareness & Empathy (Developing level) — *Sophistication progression: from recognising emotions in others (A) to recognising others feel differently (B)*
- Self-Awareness & Regulation (understanding automatic reactions) — *Conceptual accelerator from fight-flight-freeze: practice becomes more informed; still recommended not hard* ⚑ teacher discretion

**Band C:**
- Amygdala & threat detection — *Hard prerequisite logic: fight-flight-freeze and basic brain awareness both secured; introduces specific neural structure*
- Autonomic nervous system — *Hard prerequisite logic: fight-flight-freeze secured; ANS content explains why techniques work — must precede informed regulation expectations*
- Habits science — *Hard prerequisite logic: basic brain awareness secured; neuroplasticity concept accessible at this band*
- Self-Awareness & Regulation (science-informed, strategy selection) — *Conceptual accelerator activated: ANS content must precede this expectation — teach ANS first in Band C, then move to informed strategy selection*
- Reflective Thinking (Competent level) — *Sophistication progression: weighing competing considerations*
- Social Awareness (Competent level) — *Sophistication progression: contextual analysis of emotional responses*

**Band D:**
- HPA axis and acute vs chronic stress — *Hard prerequisite logic: ANS and amygdala both secured; completes the neuroendocrine pathway*
- Sleep science — *Hard prerequisite logic: ANS concept required to explain sleep as active physiological process*
- Self-Awareness & Regulation (distinguishing acute from chronic stress) — *Hard prerequisite logic: HPA axis content must precede this capability*
- Agency (meta-reflective) — *Soft enabler activated: Reflective Thinking at Extending level enriches but does not fully gate this* ⚑ teacher discretion
- Reflective Thinking (Extending level — meta-reflective) — *Sophistication progression: thinking about thinking; explicit teaching required* ⚑ teacher discretion

### 4. Prerequisite Violations

No prerequisite violations detected in the recommended sequence above. **Risk to monitor:** If the autonomic nervous system content at Band C is scheduled after the regulation expectation for "informed strategy selection" — within the same band — this would constitute a hard prerequisite violation. Teach ANS content in Term 1 of Band C before moving to science-informed regulation expectations in Term 2.

### 5. Coherence Checks

**Vertical coherence:**

*Hierarchical:* The proposed Wellbeing Science & Literacy prerequisite chain is coherent: body awareness (A) → fight-flight-freeze (B) → amygdala, autonomic nervous system, habits science (C) → HPA axis, acute vs chronic stress, sleep science (D). Each concept builds on the previous. Risk: density at Band C — three new hierarchical concepts introduced simultaneously. If time is limited, prioritise autonomic nervous system (it is the prerequisite for the largest number of downstream capabilities).

*Horizontal:* Reflective Thinking, Social Awareness, and Communication & Collaboration show genuine sophistication increases. The critical transition to monitor is Band C → D: all three shift to meta-level thinking. Without explicit teaching of what meta-reflection looks like, students will stay at Band C sophistication with harder content — a plateau, not a spiral.

*Dispositional:* All four dispositional threads are present across all four bands with increasing expectations. Band B risk: dispositional threads develop through practice alone, without knowledge support. Self-Regulation at Band B is practice-based ("use these techniques because they work"), not science-informed. This is developmentally appropriate — the knowledge arrives at Band C — but teachers must understand that the transition to informed regulation happens at Band C, not before.

**Horizontal coherence:**

*Band A:* Primarily dispositional and concrete experiential. Hierarchical content minimal. Horizontal at Emerging level. Balance is developmentally appropriate. Internal connections are strong — body awareness, emotions vocabulary, noticing others' emotions, and simple regulation strategies are naturally linked through embodied experience.

*Band B:* Dispositional threads continue. One new hierarchical concept (fight-flight-freeze). Horizontal at Developing level. Balance appropriate but hierarchical strand is thin — one concept must be taught with sufficient depth to justify its placement. Connection between scientific concept and dispositional practice needs to be made explicit by teachers.

*Band C:* Most demanding band. Three new hierarchical concepts, horizontal at Competent level, dispositional expectations now science-informed. Risk of overload. Internal connections are potentially strong but span competencies — if competencies are taught in isolation, students will not see the connections. Recommend at least one cross-competency unit explicitly connecting ANS science to regulation practice.

*Band D:* All three types at maximum demand. Internal connections are strongest if made explicit: HPA axis → chronic stress → habits → agency → care for others with respect for autonomy forms a coherent synthesis. If taught as separate units, it fragments.

### 6. Sequencing Principles

The following principles were applied in producing this sequence. Review them. If any do not match your programme's philosophy or your knowledge of your students, adjust the sequence accordingly.

**Default principles applied:**

1. **Hard prerequisite logic (T1):** Where LT B genuinely cannot be accessed without LT A's content, LT A is placed earlier. These constraints are non-negotiable — reordering them produces prerequisite violations.

2. **Soft scaffold logic:** Where LT A enriches or makes LT B more transferable without fully gating it, LT A is placed earlier as a recommendation. Teachers can adjust soft scaffold ordering based on student readiness.

3. **Experiential readiness logic (T3):** For social-emotional dispositional capabilities, experience of the capability generally precedes the T1/T2 content that explains it. Students who have practised a disposition encounter the explanation as confirmation of lived experience, not abstraction.

**Exception applied:**

4. **Metacognitive T3 exception:** For metacognitive and reflective LTs, light conceptual framing before practice may improve practice quality (Flavell, 1979). These LTs are flagged for teacher discretion in Section 7.

**Note on the counterargument:** Explicit instruction research (Kirschner et al., 2006) argues novice learners benefit from explanation before practice in many domains. The experiential readiness default applies most strongly to social-emotional dispositions. For hierarchical knowledge LTs, explicit instruction first is assumed.

### 7. Teacher Discretion Flags and Questions

**Self-Awareness & Regulation — experiential practice beginning at Band A before ANS science**

This placement follows the experiential readiness default: students practise regulation before they can explain why techniques work. This is recommended, not hard-constrained.

- Have students in this band had previous school or home experience with regulation practice? If so, the experiential base is already established and science-first may be a reasonable alternative.
- Is there a programme-specific reason to introduce the neuroscience concept earlier (e.g. a schoolwide emphasis on body-based learning that would make ANS accessible at Band B)? If yes, supply this as a sequencing principle.
- Does this school's Band A population include students with significant trauma histories? If so, experience-first regulation practice may be more important, not less — the science can wait.

**Agency and Care for others — beginning at Band A**

Both are recommended to begin as emergent experiential practice at Band A before reflective framing is introduced.

- What does "agency" look like in this school's Band A context — structured choice? student-led projects? If the programme already foregrounds student choice, the experiential base is established.
- For Care for others: do Band A students already show prosocial behaviour in unstructured settings? If the disposition is already present, the focus is on naming and developing it, not on introducing it from scratch.

**Meta-reflective Reflective Thinking and Agency at Band D**

The shift to thinking-about-thinking is flagged as requiring explicit teaching rather than natural emergence.

- Have students in Band D been explicitly introduced to metacognitive vocabulary before? If yes, the transition to meta-reflection may require less scaffolding.
- Does this term's project create natural moments for students to observe their own reasoning processes? If so, concept-before-practice may be appropriate — introduce meta-reflection vocabulary before the project begins, then practise it in the project itself.
- Are there students entering Band D from outside this programme who lack the Band C experiential base? If so, the recommended sequence assumes continuity that may not be present for some students.

### 8. Design Flags and Recommendations

**Gaps:**
- **Scientific reasoning about evidence** is required at Band D (evaluating wellness claims) but is not included in the Wellbeing Science & Literacy strand. Students need to understand what counts as evidence for a health claim — controlled studies, sample size, correlation vs causation. Either add this to the wellbeing programme or verify it is covered in the science curriculum by Band D.
- **Agency is not currently a named competency.** The intended outcomes include agency, and it is mapped across all four bands, but it does not appear in the existing competency structure. **Recommendation:** Either add Agency as a sixth competency or ensure it is explicitly embedded within Self-Awareness & Regulation and Reflective Thinking — but if embedded, it must be named and tracked.
- **Care for others is not currently a named competency.** The Social Awareness & Empathy competency covers the horizontal knowledge dimension but not the dispositional dimension of enacted care. **Recommendation:** Either add Care as a competency or split Social Awareness & Empathy into an analytical strand (horizontal) and an enacted strand (dispositional).

**Overlaps:**
- **Self-Awareness & Regulation** and **Health Literacy & Habits** overlap in the area of "strategies for managing wellbeing." The distinction — regulation is about emotional responses in the moment, habits are about sustained routines — must be made explicit to teachers. **Recommendation:** Define the boundary clearly and where they overlap (e.g. a breathing technique used both in-the-moment and as a daily practice), name the overlap explicitly.
- **Reflective Thinking** and the meta-reflective dimension of **Self-Awareness & Regulation** at Band D overlap. **Recommendation:** At Band D, design assessment tasks that integrate both competencies — a reflective portfolio on personal regulation development would serve both.

**Difficult transitions:**
- **Band B → C** is the most significant transition: from experiential, practice-based learning to science-informed, analytically demanding content. Three new hierarchical concepts, a step up in horizontal sophistication, and informed rather than practised dispositional expectations. **Recommendation:** Begin Band C with a bridging unit connecting Band B experiential knowledge to new scientific content — "You already know deep breathing calms you down. Now we're going to learn WHY — and that understanding will help you choose the right technique for different situations."
- **Band C → D** for horizontal elements: the shift to meta-level thinking will not happen spontaneously for most students. **Recommendation:** Explicit modelling of meta-reflective thinking at the start of Band D.

**Compound competencies:**
- **Health Literacy & Habits** is compound across knowledge types: hierarchical knowledge (nutrition, sleep, exercise science), horizontal thinking (evaluating health claims), and dispositional practice (maintaining routines). The same competency is being sequenced by three different logics simultaneously. **Recommendation:** Consider splitting into Health Knowledge (hierarchical — assessed by structured responses) and Wellbeing Practice (dispositional — assessed through self-reflection and developmental conversation).

**Priority actions (in order of impact):**
1. **Ensure autonomic nervous system content is taught at the START of Band C** before regulation expectations assume students understand why techniques work. This is the highest-impact sequencing decision.
2. **Design a cross-competency bridging unit at the start of Band C** connecting experiential Band B learning to scientific Band C content.
3. **Add scientific reasoning about evidence** to the Wellbeing Science & Literacy strand at Band D, or verify it is covered in the science curriculum.
4. **Make Agency and Care for Others explicitly named and tracked** — unnamed intended outcomes are not assessed and tend to be neglected.
5. **Define the boundary between Self-Awareness & Regulation and Health Literacy & Habits** explicitly for teachers, so both competencies are taught with clear scope.

---

## Known Limitations

1. **The scope and sequence produced by this skill is a planning document, not an enacted curriculum.** A coherent written sequence does not guarantee coherent teaching — implementation depends on teachers understanding the sequencing logic and making consistent decisions across classrooms and year groups. The sequencing rationale output is designed to be shared with teachers precisely because implementation coherence requires them to understand why elements are placed where they are, not just what is to be taught.

2. **Learning progressions are empirically grounded for some domains (early mathematics, reading development, scientific reasoning) and much thinner for others (wellbeing, creative arts, interdisciplinary thinking).** Where the evidence base for a specific learning progression is thin, this skill produces a logical progression based on developmental principles — but the progression should be treated as a hypothesis to be tested through implementation and assessment data, not as a research-backed certainty.

3. **This skill produces a recommended sequence; it cannot enforce it.** In real schools, scope and sequence is subject to timetabling constraints, staff changes, resource availability, and contextual decisions that override the ideal sequence. The output should be treated as the design target — the curriculum team then determines how closely implementation can match it given real-world constraints.

4. **The three-type knowledge framework used for sequencing is a simplification.** Real knowledge elements often sit on boundaries between types, and the sequencing logic for boundary cases requires professional judgment that this skill can prompt but not replace. Where elements are classified as primarily one type for sequencing purposes, the classification should be made explicit so teachers understand the reasoning.

5. **Scope and sequence design is never finished.** As students move through the programme, assessment data will reveal where the sequence is working and where it is producing gaps or struggles. The scope and sequence designer produces the best available plan given current knowledge — it should be reviewed and revised at least annually using real student outcome data. The gap-analysis-from-student-work skill is the natural tool for feeding that data back into sequence revision.

6. **If no prerequisite_map is supplied, all prerequisite relationships are inferred from LT content and types.** Inference is most reliable for T1 content dependencies and least reliable for T3 dispositional relationships. For programmes with formally typed prerequisites, always supply the prerequisite_map — do not rely on inference for hard constraint decisions.

7. **T3 dispositional LT ordering is inherently a teacher professional judgement question that cannot be fully resolved from curriculum documents.** The skill provides principles and flags decisions for review. The experiential readiness default is well-supported for social-emotional dispositional LTs but contested in other domains. Use sequencing_principles to override.

8. **Subject expert review is required for inferred prerequisite maps in specialist domains.** In mathematics, science, and language acquisition, prerequisite structures are often non-obvious from LT text. The inferred map in these domains is a starting point for expert review, not an authoritative map.

9. **The skill declines to produce output from subject name and intended outcomes alone (State E).** A scope and sequence produced from insufficient inputs creates a false impression of structure that may be harder to revise than starting fresh. Run Learning Target Authoring Guide and KUD Chart Author first.

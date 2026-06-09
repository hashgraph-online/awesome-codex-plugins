---
# AGENT SKILLS STANDARD FIELDS (v2)
name: developmental-progression-synthesis
description: "Synthesise completed KUD charts into a developmental progression matrix and per-competency narrative sections. Use when you need a programme-level view of how knowledge, understanding, and performance develop across bands."
disable-model-invocation: true
user-invocable: true
effort: high

# EXISTING FIELDS

skill_id: "original-frameworks/developmental-progression-synthesis"
skill_name: "Developmental Progression Synthesis"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Wiggins & McTighe (2005) — Understanding by Design (backward design; desired results as the basis for programme coherence)"
  - "Vygotsky (1978) — Mind in society (ZPD; band statements describe the upper edge of capability with support)"
  - "Bruner (1960) — The Process of Education (spiral curriculum; concepts revisited with increasing sophistication across developmental stages)"
  - "Hattie & Donoghue (2016) — Learning strategies: a synthesis and conceptual model (surface to deep to transfer as a developmental progression model)"
  - "Biggs & Collis (1982) — Evaluating the Quality of Learning: the SOLO Taxonomy (structural complexity as a developmental progression lever)"
input_schema:
  required:
    - field: "kud_charts"
      type: "string"
      description: "The full set of KUD charts to synthesise. Provide all charts for the programme — each chart should include the LT name, knowledge type (T1/T2/T3), and the Know/Understand/Do content for each band. Paste all charts as a single input."
    - field: "competency_structure"
      type: "string"
      description: "The competency framework — list of competency names, their LT members, and the band range (e.g. \"Bands A–F, ages 5–17\"). Used to organise the matrix by competency grouping."
  optional:
    - field: "output_focus"
      type: "string"
      description: "\"matrix\" for Output 1 only, \"chapters\" for Output 2 only, or \"both\" (default). Use \"matrix\" for a quick programme overview; use \"chapters\" for programme guide chapter content."
    - field: "knowledge_type_filter"
      type: "string"
      description: "\"T1\", \"T2\", \"T3\", or \"all\" (default). Filter the synthesis to a specific knowledge type — e.g. \"T3\" to produce a disposition-only developmental view."
    - field: "audience"
      type: "string"
      description: "\"teachers\", \"parents\", \"researchers\", or \"AI-systems\". Adjusts the register and depth of the narrative synthesis. Default is \"teachers\"."
output_schema:
  type: "object"
  fields:
    - field: "developmental_matrix"
      type: "object"
      description: "Output 1 — a competency × band matrix showing the key developmental milestone per cell. Type 2 and Type 3 cells are visually distinguished. Suitable for a programme overview page."
    - field: "competency_chapters"
      type: "object"
      description: "Output 2 — per-competency narrative sections showing K/U/Do progression across bands. Structured for use as programme guide chapter content."
    - field: "design_notes"
      type: "object"
      description: "Flags, gaps, and coherence observations surfaced during synthesis — progression weaknesses, discontinuities, Type 3 underdifferentiation, and input gaps."
chains_well_with:
  - "kud-chart-author"
  - "learning-target-authoring-guide"
  - "scope-and-sequence-designer"
  - "coherent-rubric-logic-builder"
  - "dispositional-knowledge-assessment-designer"
tags: ["developmental-progression", "KUD", "programme-guide", "scope-and-sequence", "matrix", "competency", "bands", "synthesis", "curriculum-design"]
---

# Developmental Progression Synthesis

## What This Skill Does

This skill takes a completed set of KUD charts and synthesises them into two linked artefacts for a programme guide.

**Output 1 — Developmental matrix:** A competency × band grid showing the key developmental milestone for each LT at each band. The matrix gives any reader a single-page view of the full programme arc — what students are working toward at each developmental stage across every competency. Type 2 performance Do statements and Type 3 observation indicators are visually distinguished in the matrix because they represent different kinds of evidence and different assessment routes. Collapsing them into a uniform cell format misrepresents how the programme works.

**Output 2 — Per-competency developmental sections:** For each competency, a narrative section showing how Know, Understand, and Do develop across bands within that competency's LTs. This is the chapter content for a programme guide — written for teachers by default, adjustable for parents, researchers, or AI system documentation. Organising by competency rather than by individual LT is a deliberate design choice: competencies have internal coherence (a Type 2/Type 3 pair makes most sense read alongside each other) and a small number of competency sections is far more readable than a large number of individual LT sections.

**What this skill is not:** It is not a scope-and-sequence tool. The scope-and-sequence-designer produces a curriculum scheduling and prerequisite sequencing document — when to teach what, in what order. This skill produces a developmental progression document — what growth looks like across the full programme arc. Both are needed; they answer different questions.

**Critical design principle:** The synthesis must surface the progression logic explicitly, not just reproduce the band statements. For each competency chapter, the narrative should name the progression levers at work (complexity, precision, reasoning, scope, transfer, independence) and explain what the developmental arc means for a teacher or parent reading it. A reader who finishes a competency chapter should understand not just what students do at each band but why the progression is sequenced the way it is.

**Type 2 versus Type 3 in the matrix:** Type 2 Do statements describe task performance — what a student produces in a rubric-assessed task. Type 3 Do statements describe observation indicators — what a teacher notices over time. These must be visually distinct in the matrix. A unified cell format implies a unified assessment route, which is false for this framework.

## Evidence Foundation

Wiggins & McTighe (2005) provide the backwards design framework underpinning the synthesis structure: desired results — the end-of-programme developmental picture — must be articulated before curriculum decisions are made. This skill formalises the "desired results" column of backwards design into a programme-level matrix and narrative that any stakeholder can read. Vygotsky's (1978) zone of proximal development informs every band statement: each cell in the matrix describes what students can do with appropriate support at that developmental stage — the upper edge of the ZPD, not the independent floor. Bruner's (1960) spiral curriculum is the architectural principle behind multi-band synthesis: the same competencies appear at every band, revisited with increasing sophistication rather than replaced by different content. The synthesis must make the spiral visible — a reader should be able to trace a single LT across bands and see how the progression levers advance. Hattie & Donoghue (2016) provide the surface-to-deep-to-transfer model as a macro-level check: does the progression across the full band range move students from surface acquisition, through deep processing, toward transfer? Band statements that plateau at surface level for too many bands fail this check. Biggs & Collis's (1982) SOLO taxonomy provides a structural complexity lens — pre-structural through extended abstract — which is one of the progression lever systems (complexity) that the narrative synthesis should name explicitly where it operates.

## Input Schema

The designer must provide:
- **KUD charts:** The full set of completed KUD charts for the programme. Each chart should include the LT name, knowledge type (Type 1/Type 2/Type 3), and the Know/Understand/Do content for each developmental band. All charts pasted as a single input block.
- **Competency structure:** The list of competencies, their LT members, and the band range. This is the organising scaffold for both the matrix and the chapters.

Optional:
- **Output focus:** "matrix" for Output 1 only, "chapters" for Output 2 only, or "both" (default).
- **Knowledge type filter:** "T1", "T2", "T3", or "all" (default). Filters the synthesis to one knowledge type.
- **Audience:** "teachers" (default), "parents", "researchers", or "AI-systems". Adjusts register.

## Prompt

```
You are synthesising a set of completed KUD charts into two linked programme guide artefacts: a developmental matrix and per-competency narrative chapters. Follow these rules PRECISELY.

═══════════════════════════════════════════════════════════════
TWO-OUTPUT ARCHITECTURE
═══════════════════════════════════════════════════════════════

This skill produces two outputs from the same KUD chart inputs.

**Output 1 — Developmental matrix:** A competency × band grid. One key milestone sentence per cell. Suitable for a programme overview page.

**Output 2 — Per-competency narrative chapters:** One section per competency. Synthesised prose showing K/U/Do development across bands. Suitable for programme guide chapter content.

Both outputs are produced by default unless output_focus specifies otherwise. Read ALL KUD charts in full BEFORE beginning either output.

═══════════════════════════════════════════════════════════════
PRE-SYNTHESIS READING PROTOCOL (mandatory before any output)
═══════════════════════════════════════════════════════════════

Before generating any output, read all provided KUD charts and build an internal map:

1. **Competency membership:** Which LTs belong to which competency.
2. **Knowledge type inventory:** Which LTs are Type 1, Type 2, Type 3, or compound hybrid.
3. **Band coverage:** Which bands each LT covers. Note any bands explicitly marked N/A.
4. **Progression levers in use:** At each band transition, which lever(s) advance the progression — independence, complexity, scope, precision, reasoning, or transfer.
5. **Assessment route per LT:** Whether each LT uses performance Do statements (Type 1/Type 2) or observation indicators (Type 3).
6. **Internal flags:** Any inconsistencies, missing bands, underdifferentiated indicators, or gaps noticed during reading. These become design notes.

Do not begin Output 1 or Output 2 until this mapping is complete.

═══════════════════════════════════════════════════════════════
OUTPUT 1 — DEVELOPMENTAL MATRIX: CONSTRUCTION RULES
═══════════════════════════════════════════════════════════════

**Structure:**
- Rows: one row per LT, grouped by competency (competency name as a spanning header row above the group)
- Columns: the band range provided (e.g. Bands A through F)
- Each cell: one sentence capturing the key developmental milestone at that band for that LT — the most important thing a reader should understand about what the student is working toward at this stage

**Cell content by knowledge type:**

*Type 1 cells:* Draw the sentence from the Know or Understand element — the key concept or knowledge milestone at this band.

*Type 2 cells:* Draw the sentence from the Do statement — what the student performs or produces at this band.

*Type 3 cells:* Draw the sentence from the observation indicators — what the teacher notices at this band. Mark every Type 3 cell with an asterisk (*). Add a legend at the foot of the matrix: * = Observation indicator (multi-informant, not rubric-assessed).

*N/A cells:* Mark N/A. No further content. Do not leave blank.

*Compound hybrid LTs (Type 2 + Type 3 elements):* Produce two sub-rows — one labelled "Performance (T2)" and one labelled "Observation (T3)*". Both rows must appear for every band.

**Whole-matrix check:** After completing the matrix, read each row as a sequence. Does the progression within each row tell a coherent developmental story? Flag in design notes any row where the arc is discontinuous or where a band transition is not clearly justified by a lever advance.

═══════════════════════════════════════════════════════════════
OUTPUT 2 — PER-COMPETENCY CHAPTERS: CONSTRUCTION RULES
═══════════════════════════════════════════════════════════════

**Structure:** One section per competency, in the order provided in competency_structure.

**Each section opens with:**
- The competency name as a heading
- Its definition (one sentence)
- The number of LTs it contains and their knowledge types
- A one-paragraph orientation: what this competency is, why it matters developmentally, and what a reader should be watching for as they read the section

**For each LT within the competency:**

*Type 1 and Type 2 LTs — narrative progression account:*
Write a synthesised narrative of K/U/Do development across bands. Do not reproduce the KUD chart as a table. Describe what develops and why. Name the progression levers explicitly. A reader finishing this narrative should know not just what students do at each band but what is advancing from band to band and why the sequence is designed the way it is.

*Type 3 LTs — dispositional arc account:*
Instead of describing task performance development, describe the developmental arc of the observation indicators. What does this disposition look like in the earliest bands — how it shows up in simple, adult-scaffolded moments? What does it look like in the later bands — how it manifests independently and across diverse contexts? What does that mean for how a teacher or parent recognises growth? This prose is observational, not performative — it describes what is noticed over time, not what is scored on a task.

*Type 2/Type 3 pairs within a competency:*
Where two LTs within a competency are a Type 2/Type 3 pair (analytical capability + enacted disposition), show them together with explicit discussion of the relationship. Name the distinction plainly: the Type 2 LT describes what the student can reason about or produce when assessed; the Type 3 LT describes whether they enact it in real contexts. A student can be strong on Type 2 and weak on Type 3 simultaneously — name this possibility explicitly so teachers and parents understand the assessment distinction and what it means about a student's development.

**Each section closes with:**
- Key prerequisites from other competencies that teachers should be aware of
- The single most important progression observation for this competency: what a teacher should be watching for as the clearest sign of genuine development

═══════════════════════════════════════════════════════════════
AUDIENCE REGISTER
═══════════════════════════════════════════════════════════════

Apply the register consistently across both outputs.

**teachers (default):** Practical, grounded in classroom and observation language. Names what teachers will see students doing and what teachers will notice. Uses assessment terms as givens (rubric, observation indicators, developmental conversation). Does not over-explain the framework.

**parents:** Accessible language, no educational jargon. Focuses on what growth looks like from the outside — what a parent would notice at home or in conversation. Avoids unexplained terms (rubric, LT, KUD chart). Centres the student's visible behaviour and experience.

**researchers:** Includes progression lever terminology explicitly. References the knowledge type classification and names the theoretical warrants (SOLO, ZPD, spiral curriculum). Suitable for a programme evaluation or curriculum audit audience.

**AI-systems:** Structured, precise, complete. Names the assessment route for each LT explicitly. Identifies every progression lever at each band transition by name. Minimises interpretive prose; maximises structured labelling. Optimised for machine parsing of the developmental model.

═══════════════════════════════════════════════════════════════
DESIGN NOTES: CONSTRUCTION RULES
═══════════════════════════════════════════════════════════════

After completing both outputs, produce design notes. These are honest flags for the programme designer — not errors, but signals that further work may be needed.

Produce a note for each of the following where found:

1. **Weak or discontinuous progression arc:** Any LT where the band-to-band progression felt unclear, where the same lever repeated without advancing, or where a band transition introduced new content rather than advancing existing complexity.

2. **Delivery pressure:** Any band where multiple LTs converge in a way that may create pressure — e.g. a band where three LTs simultaneously advance on the reasoning lever for the first time.

3. **Underdifferentiated Type 3 indicators:** Any Type 3 LT where adjacent-band observation indicators are too similar — where Band C and Band D, for example, describe behaviours that would be difficult to distinguish in practice from a single observation event.

4. **Invisible Type 2/Type 3 relationship:** Any competency where the Type 2/Type 3 pair relationship is not clearly visible from the KUD chart inputs — where the analytical LT and the dispositional LT do not obviously complement each other.

5. **Input gaps:** Any LT or band where the KUD chart provided insufficient content to complete the matrix cell or narrative account. Name the specific gap: which LT, which band, which K/U/Do element is missing or underdeveloped.

If none of the above are found, state that explicitly. Do not omit the design notes section.

═══════════════════════════════════════════════════════════════
SELF-CHECK BEFORE RETURNING OUTPUT
═══════════════════════════════════════════════════════════════

Before returning any output, verify:

- [ ] Does the matrix visually distinguish Type 3 cells (asterisk marking on every Type 3 cell, legend at foot)?
- [ ] Does each competency chapter name at least one progression lever explicitly by name?
- [ ] Are Type 2/Type 3 pairs shown together with the T2/T3 distinction explained?
- [ ] Does the chapter narrative synthesise rather than reproduce the KUD chart content?
- [ ] Are design notes honest about gaps and discontinuities — specific, not reassuring?
- [ ] Is the register appropriate and consistent for the specified audience throughout both outputs?
- [ ] Are N/A cells marked N/A in the matrix (not left blank)?
- [ ] Are compound hybrid LTs shown as two labelled sub-rows in the matrix?

═══════════════════════════════════════════════════════════════

Your task is to synthesise:

**KUD charts:** {{kud_charts}}

**Competency structure:** {{competency_structure}}

The following optional parameters may or may not be provided. Use whatever is given; apply defaults for any not provided.

**Output focus:** {{output_focus}} — if "both" or not specified, produce both Output 1 and Output 2.

**Knowledge type filter:** {{knowledge_type_filter}} — if "all" or not specified, include all knowledge types in both outputs.

**Audience:** {{audience}} — if not specified, default to "teachers".

Return your output in this exact format:

## Developmental Progression Synthesis

### Output 1 — Developmental Matrix

[Competency × band matrix. Competency names as spanning header rows. One LT row per LT (or two sub-rows for compound hybrids). One milestone sentence per cell. Type 3 cells marked *. N/A cells marked N/A.]

* = Observation indicator (multi-informant, not rubric-assessed)

### Output 2 — Per-Competency Developmental Guide

#### [Competency Name]

**Competency definition:** [one sentence]
**LTs in this competency:** [LT names with knowledge types]

[Orientation paragraph — what this competency is, why it matters developmentally]

[LT-by-LT narrative — synthesised prose, not KUD chart reproduction. Progression levers named explicitly. Type 2/Type 3 pairs shown together with the distinction explained.]

**Prerequisites from other competencies:** [list, or "None identified"]
**Key progression observation:** [the single most important thing a teacher should watch for]

[Repeat #### section for each competency]

### Design Notes

**1. Progression arc flags:**
[LTs with weak or discontinuous progression, or "None identified"]

**2. Delivery pressure:**
[Bands with convergent demand, or "None identified"]

**3. Underdifferentiated Type 3 indicators:**
[Type 3 LTs where adjacent bands are difficult to distinguish in practice, or "None identified"]

**4. Invisible Type 2/Type 3 relationships:**
[Competencies where the T2/T3 pair relationship is not clear from the inputs, or "None identified"]

**5. Input gaps:**
[Specific LTs, bands, and K/U/Do elements where input was insufficient, or "None identified"]
```

## Example Output

**Scenario:** *Competency: "Analytical Reasoning" / LTs: LT-AR1 (Type 2 — reasoning quality) and LT-AR2 (Type 3 — dispositional) / Bands A–D only*

**KUD chart inputs used for this example:**

*LT-AR1: Evidence Analysis (Type 2)*
- Band A: Know — what a claim is and what it means to support one; Understand — claims require support to be credible; Do — identify a claim in a given text and say whether it is supported
- Band B: Know — difference between evidence and assertion; Understand — not all evidence is equally reliable; Do — compare two pieces of evidence and explain which better supports a claim
- Band C: Know — types of bias and how they affect evidence quality; Understand — analytical conclusions depend on the quality of evidence used; Do — evaluate a set of sources and justify which is most credible for a given purpose
- Band D: Know — how analytical frameworks work across disciplines; Understand — strong analysis requires naming the assumptions behind the evidence; Do — analyse competing evidence, name underlying assumptions, and construct a supported analytical position

*LT-AR2: Reasoning as Practice (Type 3)*
- Band A indicators: student asks "why?" when given a rule or claim; student accepts and connects an explanation when offered by the teacher
- Band B indicators: student independently questions a claim before accepting it; student notices when a peer's argument lacks evidence
- Band C indicators: student applies analytical questioning across subjects without prompting; student catches their own unsupported claims mid-argument
- Band D indicators: student names the analytical moves they are making as they reason; student seeks out counter-evidence before finalising a position

---

## Developmental Progression Synthesis

### Output 1 — Developmental Matrix

| LT | Band A | Band B | Band C | Band D |
|---|---|---|---|---|
| **Analytical Reasoning** | | | | |
| LT-AR1: Evidence Analysis (Type 2) | Identifies a claim in a given text and determines whether it is supported. | Compares two pieces of evidence and explains which better supports a claim. | Evaluates a source set and justifies which is most credible for a given purpose. | Analyses competing evidence, names underlying assumptions, and constructs a supported position. |
| LT-AR2: Reasoning as Practice (Type 3)* | Asks "why?" when given a rule; accepts and connects an explanation when offered.* | Independently questions a claim before accepting it; notices when peer arguments lack evidence.* | Applies analytical questioning across subjects unprompted; catches own unsupported claims mid-argument.* | Names the analytical moves they are making as they reason; seeks counter-evidence before finalising a position.* |

* = Observation indicator (multi-informant, not rubric-assessed)

---

### Output 2 — Per-Competency Developmental Guide

#### Analytical Reasoning

**Competency definition:** The ability to examine evidence, evaluate its quality, and construct well-supported positions.
**LTs in this competency:** 2 — LT-AR1 (Type 2, reasoning quality rubric) and LT-AR2 (Type 3, multi-informant observation)

Analytical Reasoning is the competency that anchors all evidence-based work across the programme. It is distinct from subject-specific content knowledge: a student can know a great deal about a topic and still reason poorly about it. This section describes both the analytical capability that can be assessed through rubric tasks (LT-AR1) and the reasoning disposition that must be observed over time across contexts (LT-AR2). Read them together — the relationship between the two LTs is where the most important developmental insight lives.

**LT-AR1: Evidence Analysis (Type 2)**

At Band A, students are working at the surface level of analytical reasoning: they can identify a claim and check whether it is backed by anything. The progression lever here is scope — students work with a single given text, with teacher support. By Band B, the lever advances to complexity: students must now hold two pieces of evidence simultaneously and reason comparatively about which is stronger. This is the first band where reasoning quality, rather than identification, is required. Band C introduces the reasoning lever in full: students must evaluate a whole source set and justify their judgement. The word "justify" is load-bearing at this band — it requires the student to name the reasoning, not just arrive at a conclusion. At Band D, the levers advance to transfer and precision simultaneously: students analyse competing evidence across contexts, surface the assumptions embedded in the evidence, and construct a position that can withstand challenge. The key developmental shift from Band C to Band D is the move from evaluating what is visible to naming what is hidden — assumptions, framing, and perspective.

**LT-AR2: Reasoning as Practice (Type 3)**

This LT describes whether analytical reasoning is a habit, not just a skill. At Band A, the teacher notices something modest but real: the student asks "why?" This is not sophisticated reasoning — it is the precondition for it. A student who accepts claims without question cannot develop analytical reasoning, however well they perform on evidence tasks. By Band B, the disposition begins to operate independently: the student questions a claim without a teacher prompting them to. This is the most important Band B transition for this LT — the shift from reactive to proactive questioning. At Band C, the teacher notices transfer: the student applies analytical questioning across subjects without prompting. This is Bruner's spiral made visible — the same reasoning capacity showing up in new contexts. At Band D, the disposition has become reflective: the student names the analytical moves they are making as they reason. This metacognitive narration is the highest observable form of the disposition in this band range.

**LT-AR1 and LT-AR2 together:** These two LTs describe the same developmental territory from different angles. LT-AR1 describes what a student can do when reasoning is required of them — in a task, scored on a rubric. LT-AR2 describes whether they reason when it is not required — spontaneously, across contexts, over time. A student can score well on LT-AR1 and show limited evidence on LT-AR2: they can analyse when asked but do not question habitually. This is not a contradiction — it is useful developmental information. It tells a teacher where the next work is: not more analytical tasks, but more contexts where questioning is valued and noticed.

**Prerequisites from other competencies:** Source literacy (understanding what counts as a source) should be in place before LT-AR1 Band C, when source credibility evaluation is introduced as a demand.

**Key progression observation:** The clearest sign of genuine development in Analytical Reasoning is the shift from analysis on demand to analysis by habit. When a student begins to catch their own unsupported claims before a teacher points them out (Band C for LT-AR2), the disposition has taken root.

---

### Design Notes

**1. Progression arc flags:**
LT-AR1 Band C to Band D is the sharpest lever advance in this set — from evaluating evidence quality to surfacing assumptions. Teachers should anticipate that this transition requires explicit instruction in assumption identification, not just more practice with evidence evaluation tasks. The leap is pedagogically intentional but will need scaffolding.

**2. Delivery pressure:**
No convergent delivery pressure identified in this two-LT competency. Note that both LTs reach their highest demand at Band D simultaneously, which requires Type 2 assessment infrastructure and Type 3 observation infrastructure both to be functioning by that band.

**3. Underdifferentiated Type 3 indicators:**
LT-AR2 Band C and Band D indicators are closely spaced. Band C: student catches own unsupported claims mid-argument. Band D: student names the analytical moves they are making and seeks counter-evidence. In practice, these behaviours may be difficult to distinguish in a single observation event. The distinction requires longitudinal evidence across multiple contexts and subjects — teachers should not draw Band D conclusions from a single incident.

**4. Invisible Type 2/Type 3 relationships:**
LT-AR1 and LT-AR2 are clearly paired and their relationship is visible in the KUD chart inputs. No flag needed.

**5. Input gaps:**
LT-AR1 Band A: the Know and Understand elements are present but minimal. A fuller Band A KUD chart would strengthen both the matrix cell and the chapter narrative at that stage. No content gaps identified for Bands B–D.

---

## Known Limitations

1. **This skill synthesises what the KUD charts provide.** If the input KUD charts have weak progression logic, underdeveloped band statements, or missing K/U/Do elements, the synthesis will surface those problems in design notes — but it cannot fix them. Use the kud-chart-author skill to strengthen inputs before synthesis.

2. **The matrix requires human formatting to publish.** The markdown table produced here is designed for a programme guide document, not a print-ready layout. The visual distinction between Type 2 and Type 3 cells (asterisk marking) may need to be adapted into colour coding, font styling, or shading for final publication.

3. **Narrative synthesis is not a substitute for curriculum delivery planning.** The chapter sections describe what develops and why — they articulate the intended arc. Whether the arc is being delivered in practice depends on unit plans, teaching sequences, and formative assessment loops that this skill does not produce. Use the scope-and-sequence-designer and three-part-lesson-designer skills for delivery planning.

4. **Type 3 observation distinctions at adjacent bands require longitudinal evidence.** The design notes flag where adjacent-band Type 3 indicators are closely spaced. This is not a design failure — developmental progression in dispositions is genuinely incremental. It does require that observation notes be stored over time and compared, rather than drawn from single-event impressions.

5. **Audience register is applied globally across both outputs.** The audience parameter applies uniformly to the matrix and to all chapter sections. If a programme guide requires different registers for different audiences (e.g. teacher-facing chapters alongside a parent-facing summary), run the skill twice with different audience settings and combine the outputs manually.

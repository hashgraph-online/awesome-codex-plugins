---
# AGENT SKILLS STANDARD FIELDS (v2)
name: learning-target-authoring-guide
description: "Author learning targets for a competency across developmental bands with precise, observable progression language. Use when writing 'I can' statements for competency-based programmes."
disable-model-invocation: true
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "original-frameworks/learning-target-authoring-guide"
skill_name: "Purpose-Driven Learning Target Authoring Guide"
domain: "original-frameworks"
version: "2.0"
evidence_strength: "emerging"
evidence_sources:
  - "Manning — Learning Target Authoring Guide v4.0 (2026, original methodology)"
  - "Black & Wiliam (1998) — Assessment and classroom learning (clear learning intentions as prerequisite for formative assessment)"
  - "Wiggins & McTighe (2005) — Understanding by Design (backwards design, extended with Manning's upstream 'why' layer)"
  - "Bloom et al. (1956) — Taxonomy of educational objectives (observable verb hierarchy)"
  - "Vygotsky (1978) — Mind in society (ZPD — band statements specify upper edge of capability with support)"
input_schema:
  required:
    - field: "competency_name"
      type: "string"
      description: "The broad capability being decomposed into learning targets"
    - field: "competency_definition"
      type: "string"
      description: "One sentence beginning 'The ability to...'"
    - field: "band_range"
      type: "string"
      description: "Which developmental bands this LT set covers — e.g. Bands A-D or Bands A-F"
    - field: "programme_purpose"
      type: "string"
      description: "Why this competency matters for this school's mission — the upstream 'why'"
  optional:
    - field: "existing_draft"
      type: "string"
      description: "Any existing LT wording to review and revise"
    - field: "subject_area"
      type: "string"
      description: "The curriculum domain"
    - field: "assessment_context"
      type: "string"
      description: "How LTs will be used — reporting, project assessment, or both"
output_schema:
  type: "object"
  fields:
    - field: "competency_review"
      type: "object"
      description: "Is this competency right? Does it serve the mission? Is it genuinely a capability or a topic list in disguise?"
    - field: "knowledge_type_classification"
      type: "object"
      description: "Step 0: classification of each emerging LT strand as Type 1 (hierarchical), Type 2 (horizontal/reasoning), or Type 3 (dispositional/enacted), with assessment route assignment and compound knowledge-type check"
    - field: "lt_decomposition"
      type: "object"
      description: "The 2-3 LTs that make the competency actionable, with rationale for each — including knowledge-type splits where required"
    - field: "lt_definitions"
      type: "object"
      description: "One-sentence 'I can...' definitions for each LT, with Knowledge Type, Assessment Route, and Prerequisites fields"
    - field: "band_statements_or_observation_indicators"
      type: "object"
      description: "Type 1 and Type 2: full A-F band statement progression. Type 3: observation indicator sets per band (no rubric)"
    - field: "quality_check"
      type: "object"
      description: "Full v4.0 checklist — single-construct, compound knowledge-type, no inline examples, observable verbs, vertical coherence, horizontal coherence, knowledge type checks, assessment route verification"
    - field: "known_limitations"
      type: "object"
      description: "Where the LT set is strongest; where teacher judgment will still be needed"
chains_well_with:
  - "developmental-band-system-designer"
  - "coherent-rubric-logic-builder"
  - "self-determined-project-design-protocol"
  - "curriculum-knowledge-architecture-designer"
  - "kud-knowledge-type-mapper"
  - "critical-thinking-task-designer"
  - "dispositional-knowledge-assessment-designer"
teacher_time: "5 minutes"
tags: ["learning-targets", "Manning", "competency", "authoring", "backwards-design", "observable-verbs", "band-statements", "progression", "knowledge-type", "observation-indicators", "Type-3", "multi-informant"]
---

# Purpose-Driven Learning Target Authoring Guide

## What This Skill Does

This skill encodes an original practitioner framework developed by Gareth Manning, educator, curriculum designer, and learning systems designer. Unlike skills in other domains, it is not drawn from peer-reviewed research traditions. It is grounded in serious engagement with learning science, original curriculum design work, and active classroom testing. It is included because the methodology is coherent, transferable, and genuinely useful — and because intellectual honesty requires distinguishing practitioner frameworks from research-validated approaches.

This skill guides an educator or curriculum designer through writing a complete, coherent set of learning targets (LTs) for a competency — from the upstream question of whether the competency is right, through knowledge type classification, decomposition into 2-3 LTs, to writing band-level statements (Type 1 and Type 2) or observation indicator sets (Type 3) that are developmental, precise, and assessable. Learning targets are the bridge between a broad competency ("Critical Thinking") and what a teacher can actually observe and assess in a student's work. Without well-written LTs, competency-based education degenerates into either vague impressions or checklist-style task completion. The v4.0 methodology introduces a mandatory classification step — Knowledge Type — that determines the assessment instrument BEFORE any band statements are written. This addresses the single most common failure mode in competency-based wellbeing and project curricula: dispositional goals assessed through rubrics, creating the illusion of measurement without the substance. The output is a complete LT set ready for use in planning and reporting, with quality checks built into the process. The methodology draws on Black & Wiliam (1998) — clear learning intentions are a prerequisite for effective formative assessment — and extends Wiggins & McTighe's (2005) backwards design with Manning's upstream "why" layer: before asking "What should students learn?" the process asks "Why does this competency matter for our mission?"

Critical distinction: LTs describe destinations, not content. A band statement describes what a student can do by the end of a developmental period — it does not prescribe what is taught to get there. Content specificity lives in KUD charts and unit plans. The LT constrains what is assessed; it does not constrain what is taught. An LT that appears to leave content unspecified is working correctly — the KUD chart is the right place to make content explicit.

## Evidence Foundation

Manning developed the Learning Target Authoring Guide through iterative curriculum design, documented in v4.0 (2026). The methodology addresses a specific problem: most competency-based curricula have poorly written learning targets. Common failure modes include: targets that use unobservable verbs ("Understands the water cycle" — how do you observe understanding?), targets that are topic lists disguised as competencies ("Knows the causes of WWI" — this is content, not capability), targets that lack developmental progression (the same statement at every band level with "simple" and "complex" bolted on), compound targets that assess multiple things simultaneously ("Analyses and evaluates sources to construct an argument" — which part is the student struggling with?), and — the most insidious — dispositional targets assessed through rubrics (a rubric scored on a scenario task does not tell you whether a student has developed the disposition; it tells you whether they can perform it when asked). Black & Wiliam (1998) established that effective formative assessment requires clear, shared learning intentions. If the teacher doesn't know precisely what they're looking for, they cannot provide useful feedback, and students cannot self-assess. LTs are the unit of clarity: specific enough to assess, broad enough to apply across multiple projects and contexts. Wiggins & McTighe (2005) provide the backwards design framework, which Manning extends by adding an upstream "why" layer. Standard UBD starts with given curriculum goals. Purpose-driven backwards design starts with the school's mission and asks: Why does this competency exist in our curriculum? What would we lose if we removed it? This upstream questioning prevents the accumulation of competencies that nobody can justify but nobody dares remove. Bloom's taxonomy (1956, revised 2001) provides the verb hierarchy that constrains LT writing: observable, assessable verbs (identify, describe, compare, explain, justify, analyse, evaluate, create) replace unobservable verbs (understand, know, appreciate, be aware of). Vygotsky's (1978) ZPD informs band-level specification: each band statement describes what students can do WITH APPROPRIATE SUPPORT at that developmental stage — the upper edge of the ZPD.

## Input Schema

The educator must provide:
- **Competency name:** The broad capability. *e.g. "Critical Thinking" / "Scientific Investigation" / "Collaborative Problem-Solving" / "Self-Regulation"*
- **Competency definition:** One sentence. *e.g. "The ability to analyse information, evaluate evidence, and construct well-reasoned arguments" / "The ability to monitor and adjust one's emotional and behavioural responses across different situations"*
- **Band range:** Which bands. *e.g. "Bands A-D (ages 5-14)" / "Bands B-D (ages 8-14)" / "Bands A-C (ages 5-12)"*
- **Programme purpose:** Why this competency matters. *e.g. "Our mission requires students who can contribute to a world that needs them — contribution requires the ability to think critically about complex problems, not just accept what they're told"*

Optional (injected by context engine if available):
- **Existing draft:** Any current LT wording to revise
- **Subject area:** The curriculum domain
- **Assessment context:** How LTs will be used

## Prompt

```
You are authoring learning targets using Gareth Manning's methodology (Learning Target Authoring Guide v4.0). You must follow these rules PRECISELY — they are the quality standard for every LT produced.

═══════════════════════════════════════════════════════════════
STEP 0: KNOWLEDGE TYPE CLASSIFICATION (mandatory first step)
═══════════════════════════════════════════════════════════════

Before decomposition. Before writing band statements. Before anything else.

Every LT must be classified as one of three knowledge types. The classification determines the assessment instrument. Writing the LT before classifying it produces the single most common failure mode in competency-based wellbeing and project curricula: dispositional goals assessed through rubrics, creating the illusion of measurement without the substance.

THE THREE TYPES:

**Type 1 — Hierarchical Knowledge.** Concepts build on each other in a fixed sequence. Missing a prerequisite makes later content inaccessible, not merely harder.
- Indicators: prerequisite chains exist; errors at lower levels propagate upward; canonical sequencing logic; content cannot be reordered without loss.
- Assessment route: rubric with clear criteria, explanation tasks, vocabulary checks, knowledge tests.

**Type 2 — Horizontal Knowledge.** Organised around a central question or situation, illuminated through multiple disciplinary lenses. No single correct answer, but better and worse analyses. What develops cumulatively is not content but thinking sophistication.
- Indicators: multiple valid interpretive frameworks exist; reasoning quality determines assessment outcome; content can be entered from different points; analytical depth increases with experience.
- Assessment route: reasoning-quality rubric, scenario analysis, roleplay with novel situations, case studies, written analytical tasks. Transfer is the test.

**Type 3 — Dispositional Knowledge.** Capacities that develop gradually through sustained experience and exist only in enactment. Cannot be assessed through a single task. A rubric scored on a scenario task does not tell you whether a student has developed the disposition — it tells you whether they can perform it when asked.
- Indicators: the quality exists only across time and contexts; observation of the real behaviour (not a simulation) is required for valid evidence.
- Assessment route: multi-informant, longitudinal — teacher observation notes, student self-reflection, optional parent input, Strive data where applicable. Synthesised in developmental conversation. NOT a summative grade. NO RUBRIC.

CLASSIFICATION DECISION TREE — apply to EVERY emerging LT strand:

1. Does this LT describe content with a hard prerequisite sequence?
   YES → Type 1. Assessment: rubric / knowledge test.

2. Does this LT describe analytical or reasoning capability across multiple lenses?
   YES → Type 2. Assessment: reasoning-quality rubric, scenario task.

3. Does this LT describe a quality that only exists as it is enacted over time?
   YES → Type 3. Assessment: multi-informant observation. NO RUBRIC.

4. Does the statement contain elements from more than one type?
   YES → COMPOUND. Split before proceeding. Type 3 elements always go to the multi-informant observation pathway. Type 1 and Type 2 elements go to the rubric pathway. Each pathway has a separate LT.

5. Is this Type 3 LT dependent on Type 1 or Type 2 knowledge being in place first?
   YES → Knowledge-contingent. Name the prerequisite LTs explicitly.

KNOWLEDGE-CONTINGENT DISPOSITIONS:
A Type 3 disposition is knowledge-contingent when the student cannot develop the capacity without first having the Type 1 or Type 2 knowledge base in place. This is a sequencing requirement, not a design flaw.

Example: Self-regulation is knowledge-contingent. A student cannot genuinely develop self-regulation strategies without first understanding what the stress response is (Type 1), and without having practised a repertoire of regulation strategies in structured situations (Type 2). The Type 3 observation is only valid evidence once the prerequisites are established.

Design rule: If an LT is Type 3 and knowledge-contingent, name the prerequisite LTs explicitly. Do not expect the disposition to develop before the prerequisites are taught.

═══════════════════════════════════════════════════════════════
LT WRITING RULES (non-negotiable)
═══════════════════════════════════════════════════════════════

1. **Every band statement begins "I can..."** — present tense, active voice, first person. **TYPE 3 EXCEPTION: Type 3 LTs do NOT use "I can..." band statements. They use observation indicator sets — see Mode 3 below.**
2. **No parentheses, no inline examples, no "such as" or "for example" anywhere.** Examples are provided separately in teaching guidance, never embedded in the LT statement itself. A statement with examples baked in becomes an implicit checklist.
3. **Single-construct rule.** Each statement describes ONE coherent capability. Test: "Could I assess these separately?" If yes, they must be separate LTs or separate statements. "Analyses sources and constructs arguments" violates this — analysis and argument construction are separately assessable.
4. **Compound knowledge-type rule.** If a statement contains elements from different knowledge types (e.g., one Type 2 and one Type 3 element), it MUST be split into separate LTs with separate assessment routes — REGARDLESS of whether each element passes the single-construct test on its own. This is the most common cause of assessment misrouting.
5. **Observable action verbs ONLY.** Use: identify, describe, compare, explain, justify, analyse, evaluate, create, design, plan, conduct, present, reflect. NEVER use: understand, know, appreciate, be aware of, effectively, sophisticated, well (without observable criteria).
6. **Progression uses LEVERS, not topic escalation.** The six progression levers: independence (how much support needed), complexity (how many variables or perspectives), scope (how broad the context), precision (how accurate or detailed), reasoning (how deep the justification), transfer (how far from the original context). Progression across bands is achieved by advancing one or more of these levers — NOT by changing the topic or adding content.
7. **2 LTs per competency is the default.** 3 only if the strands are genuinely distinct and cannot be collapsed without losing meaning. NOTE: If a competency contains both a Type 2 analytical strand and a Type 3 dispositional strand, these must become separate LTs with separate assessment routes. This may mean a competency that appeared to need 2 LTs actually needs 3. This is correct design, not inflation.
8. **The LT definition describes what ALL band levels do.** It is the generalised "I can..." statement that applies across every band. It is NOT a Band A statement. For Type 3 LTs, the definition must include a note that this LT is assessed through multi-informant observation.

═══════════════════════════════════════════════════════════════
REQUIRED FIELDS FOR EVERY LT
═══════════════════════════════════════════════════════════════

Every LT must include:
- **LT Name** (Title Case, noun-phrase style, stable across years)
- **LT Definition** (one sentence, "I can...")
- **Knowledge Type** (Type 1 / Type 2 / Type 3)
- **Assessment Route** (Rubric with clear criteria / Reasoning quality rubric / Multi-informant observation)
- **Prerequisites** (required for knowledge-contingent Type 3 LTs — name the Type 1/2 LTs that must be established first)
- **Band statements** (Type 1 and Type 2) OR **Observation indicator set** (Type 3)

═══════════════════════════════════════════════════════════════
THREE AUTHORING MODES
═══════════════════════════════════════════════════════════════

**Mode 1 — Plain-language decision targets**
Best for: judgement, choices, safety, credibility, reflection, ethics, communication, collaboration routines, and most Type 2 wellbeing LTs.
Default pattern: DO / CHECK / DECIDE
- DO: main action (one clear verb)
- CHECK: 1-3 simple checks (fit, risk, source, audience, constraints)
- DECIDE: outcome + short reason

**Mode 2 — Skill/proficiency targets**
Best for: academic disciplines, arts, performance, scientific practice. Also appropriate for Type 1 wellbeing science knowledge.
Defaults: one clear skill per band statement; complexity and independence increase across bands; avoid tool/menu lists.

Performance-based Do tasks — presentations, physical demonstrations, structured performances, observable skill execution — are a sub-type of Mode 2. They are assessed through performance rubrics applied to the observable execution, not through multi-informant observation (Mode 3, T3 only) and not through analytical reasoning rubrics (which assess reasoning quality, not execution quality). Use the criterion-referenced rubric generator for performance-based Do tasks. Common examples: oral presentations, debate performances, physical education demonstrations, practical science procedures, musical or artistic performances.

**Mode 3 — Observation indicator sets (Type 3 ONLY)**
Best for: ALL Type 3 dispositional LTs. This mode is mandatory for Type 3 — not optional.
Structure: a set of specific, observable, third-person indicators that describe what the disposition looks like when present, calibrated to each band. These are NOT assessed with a rubric — they inform the observation notes and the developmental conversation.

Format:
```
LT Name: [Dispositional quality]
Knowledge Type: Type 3
Assessment Route: Multi-informant observation

Band A indicators — the teacher notices:
- The student [specific observable behaviour at Band A level]
- The student [specific observable behaviour at Band A level]

Band B indicators — the teacher notices:
- The student [specific observable behaviour]
- The student [specific observable behaviour]

Band C indicators — the teacher notices:
- The student [specific observable behaviour]
- The student [specific observable behaviour]

Band D indicators — the teacher notices:
- The student [specific observable behaviour]
- The student [specific observable behaviour]

Band E indicators — the teacher notices:
- The student [specific observable behaviour]
- The student [specific observable behaviour]

Band F indicators — the teacher notices:
- The student [specific observable behaviour]
- The student [specific observable behaviour]

Knowledge-contingent prerequisites: [Name the Type 1/2 LTs, if applicable]
```

Type 3 developmental progression: Indicators at Band D describe more sophisticated, self-directed, and cross-context manifestations of the disposition. At Band A they describe simpler, more immediate, adult-scaffolded manifestations. The progression uses the same levers (independence, complexity, scope, reasoning, transfer) — but they describe what the teacher observes, not what the student performs for assessment.

Type 3 evidence pathway:
- Teacher observation notes: brief, dated, specific indicator. Third-person. Stored in a retrievable form. At least one counterexample observation per unit (an observation that surprised the teacher or contradicted their existing view of the student).
- Student self-reflection: open questions calibrated to developmental band — not self-grading.
  - Band A: name a moment when you tried something hard
  - Band B: describe one pattern you noticed in yourself this term
  - Band C: compare what you noticed with what your teacher observed
  - Band D: analyse a pattern across contexts and explain what shifted
  - Band E: evaluate how your capacity has developed over the past year — what has changed, what conditions made change possible, and what has remained resistant to change
  - Band F: construct an account of your development across high-stakes real-world contexts over an extended period — what patterns hold, what conditions still challenge you, and what remains unresolved
- Parent/caregiver noticing prompts (optional): three plain-language "what do you notice?" questions sent home two weeks before developmental conversations.
- Strive data (where applicable): behavioural record of actual habit enactment.
- Synthesised in the developmental conversation. NOT a summative grade.

Student-generated single-point rubric (Type 3 supplement): At the start of each unit, the student writes one sentence describing what "doing this well" looks like for them. This becomes the reference point for teacher observation and developmental conversations — not a school-wide criterion. Bands A-B generate this collaboratively with the teacher. Bands C-D write it independently. Band D students review and revise at mid-unit as a metacognitive act. The value of the student-generated single-point rubric is in the act of generation — the student articulating what doing this well looks like for them — not in scoring. It is never used for grading.

═══════════════════════════════════════════════════════════════
DECOMPOSITION LOGIC
═══════════════════════════════════════════════════════════════

A competency is too broad to assess directly. It must be decomposed into 2-3 LTs that together COVER the competency and are individually ASSESSABLE. The decomposition should feel natural — like cutting a diamond along its grain, not chopping it into arbitrary pieces.

Test the decomposition:
- **Coverage test:** Do the LTs together cover the full meaning of the competency? Is anything missing?
- **Distinctness test:** Are the LTs genuinely different capabilities, or are they different ways of saying the same thing?
- **Assessability test:** Can each LT be assessed through observable student work (Type 1/2) or multi-informant observation (Type 3)?
- **Knowledge-type test:** Does each LT contain only ONE knowledge type? If a single LT bundles Type 2 and Type 3 elements, split it — regardless of whether it passes the single-construct test.

═══════════════════════════════════════════════════════════════
QUALITY CHECKLIST (must pass before output)
═══════════════════════════════════════════════════════════════

Format checks:
- [ ] Every Type 1 and Type 2 band statement begins with "I can..."
- [ ] Every Learning Target Definition begins with "I can..."
- [ ] Every Competency Definition begins with "The ability to..."
- [ ] All statements are present tense, active voice
- [ ] Type 3 LTs use observation indicator format, not rubric band statements

Prohibition checks:
- [ ] No parentheses anywhere in the set
- [ ] No inline examples in band statements
- [ ] No inline examples in Learning Target Definitions
- [ ] No "such as" or "for example" anywhere
- [ ] No content inventories (lists of topics/tools/periods)
- [ ] No vague quality descriptors without observable criteria

Construct checks:
- [ ] Single-construct rule passes for all band statements
- [ ] Could pass the "assess separately?" test
- [ ] Compound knowledge-type check: no statement bundles Type 2 and Type 3 elements

Knowledge type checks:
- [ ] Every LT has a Knowledge Type field (Type 1 / Type 2 / Type 3)
- [ ] Every LT has an Assessment Route field that matches its knowledge type
- [ ] Type 3 LTs do not have rubric band statements
- [ ] Knowledge-contingent Type 3 LTs have prerequisite LTs named
- [ ] No Type 3 element is buried inside a Type 1 or Type 2 LT statement

Coherence checks:
- [ ] Vertical coherence: clear A-F progression for all LTs
- [ ] Horizontal coherence: each Learning Target Definition accurately describes what all its band levels do
- [ ] Progression uses appropriate levers (independence / complexity / scope / reasoning / transfer)

Language checks:
- [ ] Language is plain and assessable throughout
- [ ] Age-appropriate for all bands
- [ ] Consistent spelling convention (UK or US)
- [ ] Consistent terminology across the set
- [ ] Strong action verbs (avoid understand / know / appreciate)

Completeness checks:
- [ ] All cells filled (or explicitly marked N/A with rationale)
- [ ] Notes used only for teacher clarifications, not hidden examples
- [ ] Knowledge Type and Assessment Route fields completed for every LT

═══════════════════════════════════════════════════════════════
PRE-SUBMISSION SELF-CHECK PROTOCOL
═══════════════════════════════════════════════════════════════

Before returning output, complete this protocol:

1. Read all Learning Target Definitions aloud. Do any contain content lists? Flag and fix.
2. Apply the "such as" test. Could you insert "such as" naturally anywhere? If yes, you have an implicit list. Remove it.
3. Check for compound statements. Count the "and" conjunctions. Does each one join a single coherent capability, or two assessable actions? Fix any violations.
4. Apply the compound knowledge-type test. For every "and" in every statement: do the two elements belong to the same knowledge type? If one element is Type 2 (analysable in a scenario) and another is Type 3 (only evidenced through real enactment over time), the statement is a compound knowledge-type violation. Split it.
5. Verify horizontal alignment. For each LT, does the definition describe what ALL band levels do? If not, revise.
6. Quality descriptor audit. Highlight all quality adjectives. Are they tied to observable criteria? If not, replace them.
7. Assessment route verification. For each LT: is the named assessment route actually capable of producing valid evidence for this kind of knowledge? A multi-informant observation route for a Type 1 knowledge LT is as wrong as a rubric for a Type 3 disposition.

═══════════════════════════════════════════════════════════════

Your task is to author a complete LT set for:

**Competency name:** {{competency_name}}
**Competency definition:** {{competency_definition}}
**Band range:** {{band_range}}
**Programme purpose:** {{programme_purpose}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Existing draft:** {{existing_draft}} — if provided, review and revise against the quality rules. If not provided, author from scratch.
**Subject area:** {{subject_area}} — if not provided, design the LTs to work across subjects.
**Assessment context:** {{assessment_context}} — if not provided, design for use in both project assessment and reporting.

Return your output in this exact format:

## Learning Target Set: [Competency Name]

**Competency:** [Name]
**Definition:** [One sentence, "The ability to..."]
**Programme purpose:** [Why this matters for the mission]
**Number of LTs:** [2 or 3, with rationale — including knowledge-type split rationale if applicable]

### Competency Review

[Is this competency right? Does it serve the mission? Is it a genuine capability or a topic list in disguise? If the competency needs reframing, say so before proceeding.]

### Step 0: Knowledge Type Classification

[For each emerging LT strand, run the classification decision tree. State the knowledge type, the assessment route, and the reasoning. If any strand is compound, flag it and split before proceeding. If any Type 3 strand is knowledge-contingent, name the prerequisites.]

| LT Strand | Knowledge Type | Assessment Route | Reasoning |
|---|---|---|---|
| [Strand 1] | Type [1/2/3] | [Route] | [Why this classification] |
| [Strand 2] | Type [1/2/3] | [Route] | [Why this classification] |

### LT Decomposition

[The 2-3 LTs, with rationale for each and evidence that the decomposition passes the coverage, distinctness, assessability, and knowledge-type tests]

**LT1: [Name]**
- **Definition:** "I can [generalised statement that applies across all bands]"
- **Knowledge Type:** Type [1/2/3]
- **Assessment Route:** [Route]
- **Prerequisites:** [For knowledge-contingent Type 3 only; otherwise "N/A"]
- **Rationale:** [Why this strand exists as a separate LT]

**LT2: [Name]**
- **Definition:** "I can [generalised statement]"
- **Knowledge Type:** Type [1/2/3]
- **Assessment Route:** [Route]
- **Prerequisites:** [If applicable]
- **Rationale:** [Why this strand exists]

### Band Statements / Observation Indicators

[FOR TYPE 1 AND TYPE 2 LTs — use band statement table:]

**LT[n]: [Name]**
Knowledge Type: Type [1/2]
Assessment Route: [Route]
Authoring Mode: [Mode 1 or Mode 2]

| Band | Statement | Progression Lever(s) |
|---|---|---|
| A | I can [Band A statement] | [Which lever(s)] |
| B | I can [Band B statement] | [Which lever(s)] |
| C | I can [Band C statement] | [Which lever(s)] |
| D | I can [Band D statement] | [Which lever(s)] |

[FOR TYPE 3 LTs — use observation indicator format:]

**LT[n]: [Name]**
Knowledge Type: Type 3
Assessment Route: Multi-informant observation
Prerequisites: [Named Type 1/2 LTs, if knowledge-contingent]

Band A indicators — the teacher notices:
- The student [specific observable behaviour]
- The student [specific observable behaviour]

Band B indicators — the teacher notices:
- The student [specific observable behaviour]
- The student [specific observable behaviour]

Band C indicators — the teacher notices:
- The student [specific observable behaviour]
- The student [specific observable behaviour]

Band D indicators — the teacher notices:
- The student [specific observable behaviour]
- The student [specific observable behaviour]

Band E indicators — the teacher notices:
- The student [specific observable behaviour]
- The student [specific observable behaviour]

Band F indicators — the teacher notices:
- The student [specific observable behaviour]
- The student [specific observable behaviour]

Student self-reflection prompts:
- Band A: [prompt]
- Band B: [prompt]
- Band C: [prompt]
- Band D: [prompt]
- Band E: [prompt]
- Band F: [prompt]

### Quality Check

[Run every statement through the full v4.0 checklist. Flag any issues.]

**Format checks:**
- [ ] Every Type 1/2 band statement begins with "I can..."
- [ ] Every LT Definition begins with "I can..."
- [ ] Every Competency Definition begins with "The ability to..."
- [ ] All statements present tense, active voice
- [ ] Type 3 LTs use observation indicator format, not rubric band statements

**Prohibition checks:**
- [ ] No parentheses anywhere
- [ ] No inline examples in band statements or definitions
- [ ] No "such as" or "for example" anywhere
- [ ] No content inventories
- [ ] No vague quality descriptors without observable criteria

**Construct checks:**
- [ ] Single-construct rule passes
- [ ] Compound knowledge-type check passes: no statement bundles elements from different knowledge types

**Knowledge type checks:**
- [ ] Every LT has a Knowledge Type field
- [ ] Every LT has an Assessment Route that matches its knowledge type
- [ ] Type 3 LTs do not have rubric band statements
- [ ] Knowledge-contingent Type 3 LTs have prerequisites named
- [ ] No Type 3 element is buried inside a Type 1 or Type 2 LT

**Coherence checks:**
- [ ] Vertical coherence (clear A-F progression)
- [ ] Horizontal coherence (LT definition describes all band levels)
- [ ] Progression uses levers, not topic escalation

**Language checks:**
- [ ] Plain, assessable language throughout
- [ ] Consistent spelling convention
- [ ] Strong action verbs only

**Completeness checks:**
- [ ] All cells filled or marked N/A with rationale
- [ ] Knowledge Type and Assessment Route fields completed for every LT

### Known Limitations

[Where the LT set is strongest and where teacher judgment will still be needed]

**Self-check before returning output:** Run the full pre-submission protocol: (a) read all definitions aloud — any content lists? (b) "such as" test — could you insert it anywhere? (c) compound statement check — count the "and" conjunctions, (d) compound knowledge-type test — do elements on either side of "and" belong to the same knowledge type? (e) horizontal alignment — does the definition describe all band levels? (f) quality descriptor audit — all adjectives tied to observable criteria? (g) assessment route verification — is the named route capable of producing valid evidence for this knowledge type?
```

## Example Output

**Scenario 1 (Type 2):** *Competency name: "Critical Thinking" / Competency definition: "The ability to analyse information, evaluate evidence, and construct well-reasoned arguments" / Band range: "Bands A-D (ages 5-14)" / Programme purpose: "Our mission requires students who can contribute to a world that needs them. Contribution to complex real-world problems requires the ability to think critically — to distinguish strong evidence from weak, to identify assumptions, and to construct arguments that can withstand challenge. Without critical thinking, students become consumers of other people's conclusions rather than producers of their own"*

---

## Learning Target Set: Critical Thinking

**Competency:** Critical Thinking
**Definition:** The ability to analyse information, evaluate evidence, and construct well-reasoned arguments
**Programme purpose:** Contribution to a world that needs critical thinkers — people who produce their own conclusions, not consume others'
**Number of LTs:** 2 — Analysis and Argument are genuinely distinct capabilities (you can analyse without arguing, and argue without analysing well)

### Competency Review

This competency is well-framed. It describes a genuine capability (not a topic), it serves the mission directly (critical contribution requires critical thinking), and it is broad enough to apply across all subjects and projects. The definition contains three elements: analyse, evaluate, construct arguments. Analysis and evaluation are closely related (evaluating IS a form of analysis), so these collapse into one LT. Argument construction is distinct — it's a productive capability (making something) rather than an analytical capability (taking something apart). Two LTs.

### Step 0: Knowledge Type Classification

| LT Strand | Knowledge Type | Assessment Route | Reasoning |
|---|---|---|---|
| Analysis of Evidence | Type 2 | Reasoning quality rubric | Multiple valid analytical frameworks exist; reasoning quality determines outcome; no single correct answer; analytical depth increases with experience. Transfer to novel situations is the test. |
| Reasoned Argument | Type 2 | Reasoning quality rubric | Argument quality is assessed through reasoning sophistication, not correctness; multiple valid positions exist; what develops is the ability to construct and defend a position, not recall a right answer. |

No Type 3 elements detected. Critical thinking as a DISPOSITION (the habit of questioning spontaneously, not just when asked) is a real and important capacity — but it is not what this competency measures. If the programme wants to capture the disposition to think critically, that requires a separate Type 3 LT with its own observation pathway.

### LT Decomposition

**LT1: Analysis of Evidence**
- **Definition:** "I can examine information and evidence to identify what is relevant, reliable, and significant"
- **Knowledge Type:** Type 2
- **Assessment Route:** Reasoning quality rubric
- **Prerequisites:** N/A
- **Rationale:** This LT covers the ANALYTICAL dimension of critical thinking — the ability to take information apart, assess its quality, and determine what matters. It is the input side of critical thinking: processing what is given.

**LT2: Reasoned Argument**
- **Definition:** "I can construct a clear argument supported by evidence and reasoning"
- **Knowledge Type:** Type 2
- **Assessment Route:** Reasoning quality rubric
- **Prerequisites:** N/A
- **Rationale:** This LT covers the PRODUCTIVE dimension of critical thinking — the ability to build a case, support it with evidence, and present it in a way that can be examined and challenged. It is the output side of critical thinking: producing a position.

**Decomposition tests:**
- **Coverage:** Together, LT1 (analysis) and LT2 (argument) cover the full meaning of "Critical Thinking." A student who can analyse evidence AND construct reasoned arguments is a critical thinker.
- **Distinctness:** A student can be strong at analysis but weak at argument (they see the flaws but can't articulate their own position), or strong at argument but weak at analysis (they argue persuasively but from poor evidence). These are genuinely different capabilities.
- **Assessability:** Both LTs produce observable evidence in student work — analysis can be seen in how students evaluate sources, identify bias, and select evidence; argument can be seen in how students structure claims, support them, and address counter-positions.
- **Knowledge-type test:** Both LTs are Type 2. No compound knowledge-type issue.

### Band Statements

**LT1: Analysis of Evidence**
Knowledge Type: Type 2
Assessment Route: Reasoning quality rubric
Authoring Mode: Mode 2

| Band | Statement | Progression Lever(s) |
|---|---|---|
| A | I can identify relevant information from a given source | Scope: single source; Independence: given source |
| B | I can compare information from more than one source and identify differences | Complexity: multiple sources; Reasoning: comparison |
| C | I can evaluate the reliability of sources and explain why some evidence is stronger than others | Reasoning: evaluative judgment; Precision: explaining why |
| D | I can analyse competing evidence, identify assumptions and bias, and justify which evidence is most credible for a given purpose | Transfer: applying analysis to novel contexts; Complexity: competing evidence, multiple criteria |
| E | I can evaluate a body of evidence, identify systemic gaps or biases in what is available, and justify which interpretive framework best fits the purpose | Reasoning: evaluating the evidence base as a whole, not just individual sources; Scope: systemic pattern across a body, not a single comparison |
| F | I can construct a critical account of a body of evidence that accounts for the conditions under which it was produced, the interests it serves, and the limits of what it can show | Independence: self-directed critical construction; Reasoning: second-order analysis of the evidence base itself |

**LT2: Reasoned Argument**
Knowledge Type: Type 2
Assessment Route: Reasoning quality rubric
Authoring Mode: Mode 2

| Band | Statement | Progression Lever(s) |
|---|---|---|
| A | I can state my opinion and give a reason for it | Independence: single claim, single reason |
| B | I can present a claim supported by more than one piece of evidence | Complexity: multiple evidence points |
| C | I can construct an argument with a clear claim, supporting evidence, and acknowledgement of a different viewpoint | Scope: includes counter-position; Reasoning: structural awareness |
| D | I can build a sustained argument that integrates evidence, addresses counterarguments, and evaluates the strength of my own position | Transfer: self-evaluation of argument; Precision: sustained and integrated |
| E | I can construct a sustained argument that integrates competing perspectives, anticipates likely objections, and addresses the strongest version of the counter-position | Complexity: integrating competing perspectives; Reasoning: steelmanning the counter-position |
| F | I can evaluate the limits of my own argument — identifying where evidence is insufficient, where assumptions are load-bearing, and what it would take to shift my position | Independence: self-critical evaluation of own argument; Reasoning: identifying epistemic limits |

### Quality Check

- [x] **Single-construct rule:** Each statement assesses one coherent capability. LT1 is always about examining evidence; LT2 is always about building argument. No statement combines both.
- [x] **Compound knowledge-type check:** Both LTs are Type 2. No mixed-type elements.
- [x] **No parentheses or inline examples:** None present. No "such as" or "for example."
- [x] **Observable verbs only:** identify, compare, evaluate, explain, analyse, justify, state, present, construct, build, integrate, address. No "understand," "know," or "appreciate."
- [x] **Vertical coherence:** Within each LT, Band D is genuinely more advanced than Band A — the progression is clear and continuous through the levers.
- [x] **Horizontal coherence:** Band B across both LTs describes a similar developmental demand — comparing sources and presenting multi-evidence claims are both Band B level tasks.
- [x] **LT definition describes all band levels:** "I can examine information and evidence to identify what is relevant, reliable, and significant" applies to all bands — Band A does this simply (single source), Band D does this with sophistication (competing evidence with bias analysis).
- [x] **Knowledge Type fields:** Both LTs have Type 2 and Reasoning quality rubric specified.
- [x] **Assessment route verification:** Reasoning quality rubric is appropriate for Type 2 horizontal knowledge. Transfer to novel situations is the test.
- [x] **2 LTs:** Justified — analysis and argument are genuinely distinct.

### Known Limitations

1. **Critical thinking is domain-dependent as well as domain-general.** A student who thinks critically about science may not transfer that skill to history. These LTs are written as domain-general capabilities, but teachers should expect that critical thinking looks different in different subjects and that transfer across subjects requires explicit teaching.

2. **Band A is deliberately modest.** "I can state my opinion and give a reason" may seem too simple for critical thinking, but it accurately represents the developmental starting point for a 5-7-year-old. Pushing Band A toward "analyse multiple perspectives" would set an impossible expectation that produces either false compliance or teacher frustration.

3. **The LTs do not capture the DISPOSITION to think critically.** A student can have the CAPABILITY to analyse evidence (they can do it when asked) but not the DISPOSITION (they don't do it spontaneously). If the programme requires the disposition, author a separate Type 3 LT — "Critical Thinking as Practice" — assessed through multi-informant observation, not rubric.

---

**Scenario 2 (Type 3 — demonstrating observation indicator pathway):** *Competency name: "Self-Regulation" / Competency definition: "The ability to monitor and adjust one's emotional and behavioural responses across different situations" / Band range: "Bands A-D (ages 5-14)" / Programme purpose: "Our mission asks students to take increasing ownership of their learning and their impact on others. Self-regulation is the foundation — without it, autonomy becomes impulsivity and collaboration becomes conflict"*

---

## Learning Target Set: Self-Regulation

**Competency:** Self-Regulation
**Definition:** The ability to monitor and adjust one's emotional and behavioural responses across different situations
**Programme purpose:** Self-regulation is the foundation for autonomy and collaboration — without it, ownership of learning and impact on others cannot develop
**Number of LTs:** 3 — Knowledge-type analysis reveals three genuinely distinct strands that MUST be separated to avoid assessment misrouting

### Competency Review

This competency is well-framed but contains elements from all three knowledge types. "Monitor and adjust" appears to be a single capability, but it actually bundles: (a) understanding what the stress response is and how regulation works (Type 1 — teachable, testable knowledge), (b) analysing one's own patterns and selecting appropriate strategies in structured situations (Type 2 — reasoning about self-regulation), and (c) actually regulating in real situations over time (Type 3 — enacted disposition). If these are collapsed into a single rubric-assessed LT, only the Type 1 and Type 2 elements get captured. The Type 3 enactment — which is the whole point — disappears from the evidence. Three LTs are required. This is correct design, not inflation.

### Step 0: Knowledge Type Classification

| LT Strand | Knowledge Type | Assessment Route | Reasoning |
|---|---|---|---|
| Understanding the Stress Response | Type 1 | Rubric with clear criteria | Prerequisite chain exists: students must understand what happens physiologically and psychologically during stress before they can reason about strategies. Errors at lower levels propagate — a student who misunderstands the stress response will misapply regulation strategies. |
| Regulation Strategy Analysis | Type 2 | Reasoning quality rubric | Multiple valid strategies exist for any situation; reasoning quality determines whether the student selects an appropriate strategy; analytical depth increases with experience; transfer to novel situations is the test. |
| Self-Regulation as Practice | Type 3 | Multi-informant observation | This capacity exists only in enactment across time and contexts. A student who can analyse strategies in a scenario (Type 2) but does not regulate in real situations has not developed the disposition. Observation of real behaviour is required. Knowledge-contingent: requires both Type 1 and Type 2 prerequisites. |

COMPOUND KNOWLEDGE-TYPE FLAG: The original competency definition bundles all three types. The decomposition below separates them into distinct LTs with distinct assessment routes.

### LT Decomposition

**LT1: Understanding the Stress Response**
- **Definition:** "I can describe how the body and mind respond to stress and explain how regulation strategies work"
- **Knowledge Type:** Type 1
- **Assessment Route:** Rubric with clear criteria
- **Prerequisites:** N/A
- **Rationale:** This is the knowledge base. Without understanding what happens during a stress response, a student cannot reason about which strategies apply or why. This LT is assessed efficiently through explanation tasks and knowledge checks.

**LT2: Regulation Strategy Analysis**
- **Definition:** "I can analyse a situation and select a regulation strategy that fits the context"
- **Knowledge Type:** Type 2
- **Assessment Route:** Reasoning quality rubric
- **Prerequisites:** N/A (though LT1 knowledge deepens performance)
- **Rationale:** This is the reasoning capability. The student can examine a situation through multiple lenses and reason about which strategy fits. Assessed through scenario tasks requiring transfer to novel situations — not recall of a practised example.

**LT3: Self-Regulation as Practice**
- **Definition:** "I can regulate my responses to stress across different settings. [Assessed through multi-informant observation — see observation protocol.]"
- **Knowledge Type:** Type 3
- **Assessment Route:** Multi-informant observation — teacher notes, student self-reflection, parent input, Strive data. Synthesised in the developmental conversation. Not a summative grade.
- **Prerequisites:** LT1 (Understanding the Stress Response) and LT2 (Regulation Strategy Analysis) must be established. The Type 3 observation is only valid evidence once the student has the knowledge and analytical repertoire in place.
- **Rationale:** This is the enacted disposition. A student who can describe regulation (LT1) and analyse strategy selection (LT2) but does not regulate in real situations has not developed self-regulation. This LT captures what the others cannot — actual practice over time.

**Decomposition tests:**
- **Coverage:** Together, the three LTs cover the full meaning of Self-Regulation: knowing what regulation is (LT1), reasoning about when and how to apply it (LT2), and actually doing it (LT3).
- **Distinctness:** A student can know the science but not apply it (strong LT1, weak LT2/3). A student can reason about strategies in a scenario but not use them under real stress (strong LT2, weak LT3). These are genuinely separate.
- **Assessability:** LT1 through explanation tasks. LT2 through scenario analysis. LT3 through multi-informant observation.
- **Knowledge-type test:** Each LT contains one knowledge type only. No compound violations.

### Band Statements / Observation Indicators

**LT1: Understanding the Stress Response**
Knowledge Type: Type 1
Assessment Route: Rubric with clear criteria
Authoring Mode: Mode 2

| Band | Statement | Progression Lever(s) |
|---|---|---|
| A | I can identify when my body feels calm and when it feels stressed | Independence: recognising states with adult support; Scope: own body only |
| B | I can describe what happens in the body during a stress response and name strategies that help | Reasoning: describing mechanisms; Complexity: connecting response to strategy |
| C | I can explain how the stress response affects thinking and behaviour, and compare how different strategies target different aspects of the response | Reasoning: explaining cause-effect; Complexity: comparing strategies against mechanisms |
| D | I can analyse how individual and contextual factors influence the stress response and evaluate which regulation approaches are supported by evidence | Transfer: applying to varied contexts; Reasoning: evaluative judgment about evidence |
| E | I can critically evaluate explanations of the stress response, identify where the evidence is strong and where it is contested, and explain how individual and contextual variation affects which regulation principles apply | Transfer: applying critical evaluation to the evidence base itself; Reasoning: identifying limits of general principles |
| F | I can construct an account of the mechanisms underlying my own stress-regulation profile, drawing on the evidence base, and evaluate the conditions under which general regulation principles apply less reliably to me specifically | Independence: self-authored theoretical account; Transfer: generalising from evidence to personal profile |

**LT2: Regulation Strategy Analysis**
Knowledge Type: Type 2
Assessment Route: Reasoning quality rubric
Authoring Mode: Mode 1

| Band | Statement | Progression Lever(s) |
|---|---|---|
| A | I can choose a calming strategy from options offered when I am upset | Independence: supported choice; Scope: immediate situation |
| B | I can consider more than one strategy for a given situation and explain why I chose one | Complexity: multiple options; Reasoning: justifying choice |
| C | I can analyse a situation through more than one lens and select a strategy that fits the context and the people involved | Scope: considering context and others; Reasoning: multi-lens analysis |
| D | I can evaluate competing strategies for a complex situation, identify tensions between them, and justify my approach across more than one context | Transfer: cross-context application; Complexity: competing strategies with tensions |
| E | I can construct a regulation plan for a sustained high-stakes situation, anticipate the conditions under which my preferred strategies are likely to break down, and identify contingency approaches | Reasoning: anticipatory and contingency planning; Scope: sustained high-stakes situations |
| F | I can design a regulation approach for a novel high-stakes context, justify my design with reference to mechanism and evidence, and evaluate its effectiveness with reference to observed outcomes over time | Independence: self-designed approach; Transfer: applying principles to novel design problem; Reasoning: evaluating own design against evidence |

**LT3: Self-Regulation as Practice**
Knowledge Type: Type 3
Assessment Route: Multi-informant observation
Prerequisites: LT1 (Understanding the Stress Response), LT2 (Regulation Strategy Analysis)

Band A indicators — the teacher notices:
- The student accepts comfort or redirection from an adult when upset and begins to return to the activity
- The student uses a named calming strategy with adult prompting during an unstructured real situation

Band B indicators — the teacher notices:
- The student independently initiates a regulation strategy during a real moment of difficulty without adult prompting
- The student can name what they did to regulate after the event, with reasonable accuracy

Band C indicators — the teacher notices:
- The student selects different strategies in different contexts, showing awareness that what works in one situation may not work in another
- The student recovers from setbacks within a reasonable timeframe and re-engages with the task or interaction

Band D indicators — the teacher notices:
- The student maintains regulation across sustained periods of challenge without external scaffolding
- The student can name and explain their own regulation patterns when asked, including what has shifted over time

Band E indicators — the teacher notices:
- The student recognises early signs of dysregulation before full activation and initiates a strategy without adult prompting, including in high-stakes situations
- The student adjusts their strategy during a situation based on real-time assessment of what is and is not working
- The student reflects after an event with specificity about what shifted their state and what they would do differently

Band F indicators — the teacher notices:
- The student demonstrates consistent regulation across sustained high-stakes real-world contexts without scaffolding or post-hoc adult intervention
- The student can construct an account of their own regulation profile across multiple years, identifying what has changed and what conditions still challenge them
- The student takes responsibility for arranging conditions — environmental, social, or temporal — that support their own regulation ahead of demanding situations

Student self-reflection prompts:
- Band A: Tell me about a time this week when something was hard and what you did
- Band B: Describe one pattern you noticed about how you handle difficult moments this term
- Band C: Compare what you noticed about your regulation with what your teacher observed — where do you agree and disagree?
- Band D: Analyse how your regulation works across different settings and explain what has changed over the past term
- Band E: Evaluate how your regulation has changed over the past year — what has shifted, what conditions made the shift possible, and where you still lose hold
- Band F: Construct an account of how you regulate across different high-stakes contexts over time — what your profile looks like, what remains unresolved, and what you would need to work on next

### Quality Check

**Format checks:**
- [x] Every Type 1/2 band statement begins with "I can..."
- [x] Every LT Definition begins with "I can..."
- [x] Competency Definition begins with "The ability to..."
- [x] All statements present tense, active voice
- [x] Type 3 LT (LT3) uses observation indicator format, not rubric band statements

**Prohibition checks:**
- [x] No parentheses anywhere
- [x] No inline examples in band statements or definitions
- [x] No "such as" or "for example" anywhere
- [x] No content inventories
- [x] No vague quality descriptors without observable criteria

**Construct checks:**
- [x] Single-construct rule passes for all statements
- [x] Compound knowledge-type check passes: LT1 is purely Type 1, LT2 is purely Type 2, LT3 is purely Type 3. No mixed-type elements in any statement.

**Knowledge type checks:**
- [x] Every LT has a Knowledge Type field
- [x] Every LT has an Assessment Route that matches its knowledge type (rubric/reasoning rubric/multi-informant observation)
- [x] Type 3 LT does not have rubric band statements — uses observation indicators only
- [x] Knowledge-contingent Type 3 LT (LT3) has prerequisites named (LT1, LT2)
- [x] No Type 3 element is buried inside LT1 or LT2

**Coherence checks:**
- [x] Vertical coherence: clear A-D progression within each LT
- [x] Horizontal coherence: LT definitions describe what all band levels do
- [x] Progression uses levers (independence, complexity, scope, reasoning, transfer), not topic escalation

**Language checks:**
- [x] Plain, assessable language throughout
- [x] UK English spelling convention
- [x] Strong action verbs only — no "understand," "know," or "appreciate"

**Completeness checks:**
- [x] All cells filled
- [x] Knowledge Type and Assessment Route fields completed for every LT

### Known Limitations

1. **LT3 evidence depends on observation infrastructure.** Multi-informant observation requires teachers to store dated, retrievable notes. Until a dedicated observation app exists, the simplest sustainable system the teacher will actually use is the right system. Notes that cannot be retrieved and compared across a term are impressions, not evidence.

2. **LT3 is knowledge-contingent — timing matters.** The Type 3 observation pathway for LT3 should not begin until LT1 and LT2 prerequisites are reasonably established. Observing a student's self-regulation before they have the knowledge and strategy repertoire produces invalid evidence.

3. **Disagreement between sources is information, not error.** If a teacher's observation notes and a student's self-reflection diverge on LT3, this is developmental information to surface in the developmental conversation — not a problem to resolve before the conversation.

4. **The disposition is not the capability.** A student may score well on LT1 and LT2 (they know the science and can reason about strategies) but show limited evidence on LT3 (they don't regulate in practice). This is not an assessment failure — it is a genuine and important finding. The three LTs exist precisely to make this visible.

---

## Known Limitations

1. **This is a practitioner methodology, not a peer-reviewed framework.** The LT authoring rules have been developed and refined through classroom implementation, not through controlled experimental research. They are grounded in established assessment research (Black & Wiliam, Bloom, Wiggins & McTighe) but the specific rules (single-construct, no inline examples, progression levers, knowledge type classification) are Manning's original synthesis.

2. **LTs require professional judgment to apply.** A well-written LT set provides the structure, but assessing whether a specific piece of student work meets a specific band statement (Type 1/2) or whether an observation pattern constitutes evidence of a disposition (Type 3) still requires teacher professional judgment. The LTs reduce subjectivity — they do not eliminate it.

3. **The 2-LT default may not suit all competencies.** Some competencies decompose naturally into 2 strands; others resist clean decomposition. Knowledge-type splits may require 3 LTs where 2 seemed sufficient. The methodology provides the tests (coverage, distinctness, assessability, knowledge-type) but the designer must exercise judgment about when to follow the default and when to deviate.

4. **Type 3 assessment is harder to implement than Type 1 or Type 2.** Multi-informant observation requires infrastructure (retrievable notes, self-reflection protocols, developmental conversation scheduling) that most schools do not yet have in place. This is a real constraint. The answer is not to route Type 3 LTs through rubrics for convenience — that produces the illusion of measurement. The answer is to build the infrastructure incrementally.
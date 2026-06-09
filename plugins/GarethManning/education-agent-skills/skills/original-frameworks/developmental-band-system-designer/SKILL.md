---
# AGENT SKILLS STANDARD FIELDS (v2)
name: developmental-band-system-designer
description: "Design a developmental band system mapping student growth from early childhood through upper secondary. Use when building competency-based curriculum architecture for a school or programme."
disable-model-invocation: true
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "original-frameworks/developmental-band-system-designer"
skill_name: "Developmental Band System Designer"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Manning — Developmental band system (original, active implementation at REAL School Budapest)"
  - "Piaget (1952) — The origins of intelligence in children (developmental stages as rationale)"
  - "Vygotsky (1978) — Mind in society (ZPD applied to band-level specification)"
  - "Wiggins & McTighe (2005) — Understanding by Design (backwards design, extended with upstream 'why' layer)"
  - "Mixed-age grouping research (Lillard 2005, Montessori) — bands support rather than undermine mixed-age learning"
input_schema:
  required:
    - field: "school_mission"
      type: "string"
      description: "The core purpose and values of the school or programme — what the curriculum must serve"
    - field: "age_range"
      type: "string"
      description: "The full age range the band system needs to cover"
    - field: "programme_context"
      type: "string"
      description: "What kind of learning — project-based, subject-based, hybrid, or other"
  optional:
    - field: "existing_competency_framework"
      type: "string"
      description: "Any existing framework being mapped — EU frameworks (GreenComp, EntreComp, LifeComp, DigComp), UNESCO, national curriculum, or other"
    - field: "mixed_age_groupings"
      type: "string"
      description: "Whether the school uses mixed-age learning groups"
    - field: "subject_exceptions"
      type: "string"
      description: "Subjects that require finer granularity than broad bands — typically maths and language acquisition"
output_schema:
  type: "object"
  fields:
    - field: "band_architecture"
      type: "object"
      description: "Number of bands, age/grade mapping, developmental rationale for each band break"
    - field: "developmental_rationale"
      type: "object"
      description: "Why the bands are where they are — cognitive and social-emotional development reasoning"
    - field: "competent_definition_logic"
      type: "object"
      description: "How to determine what competent means at each band — not a list of topics but a developmental description of capability"
    - field: "exception_handling"
      type: "object"
      description: "Which subjects need finer granularity and why, with guidance on 9-level or similar precision systems"
    - field: "mixed_age_implications"
      type: "object"
      description: "How the band system supports rather than undermines mixed-age learning"
    - field: "known_limitations"
      type: "object"
      description: "Bands are broad — some students will be significantly ahead of or behind their band. How to handle this honestly"
chains_well_with:
  - "learning-target-authoring-guide"
  - "coherent-rubric-logic-builder"
  - "self-determined-project-design-protocol"
  - "curriculum-knowledge-architecture-designer"
  - "kud-knowledge-type-mapper"
  - "scope-and-sequence-designer"
teacher_time: "6 minutes"
tags: ["developmental-bands", "competency", "Manning", "curriculum-design", "Piaget", "backwards-design", "mixed-age", "band-system"]
---

# Developmental Band System Designer

## What This Skill Does

This skill encodes an original practitioner framework developed by Gareth Manning, educator, curriculum designer, and learning systems designer. Unlike skills in other domains, it is not drawn from peer-reviewed research traditions. It is grounded in serious engagement with learning science, original curriculum design work, and active classroom testing. It is included because the methodology is coherent, transferable, and genuinely useful — and because intellectual honesty requires distinguishing practitioner frameworks from research-validated approaches.

This skill designs a developmental band system for a competency-based curriculum — a framework that specifies what "competent" looks like at each broad developmental stage rather than at each individual grade level. It solves a problem that most competency frameworks ignore: the difference between what competent means for a 6-year-old versus a 12-year-old. UNESCO AI competency frameworks, most national curriculum documents, and frameworks like GreenComp and EntreComp list competencies without developmental specificity — leaving teachers to infer what "demonstrates critical thinking" means at age 7 versus age 14. The result is either impossibly vague expectations or arbitrary topic lists masquerading as developmental progression. The band system solves this by grouping ages into broad developmental bands (typically 4, mapping loosely to Piaget's stages) and specifying competent at EACH band — creating the developmental precision that flat competency lists lack, without the granularity overload of year-by-year standards. The output is a complete band architecture for a school or programme, including the number of bands, their developmental rationale, age/grade mapping, the logic for determining what competent means at each band, and guidance on subjects that require finer granularity than broad bands can provide.

## Evidence Foundation

Manning developed the band system through curriculum design work at REAL School Budapest, addressing a specific practical problem: when a school adopts a competency-based curriculum (particularly one that uses project-based learning and mixed-age groupings), it needs to know what competent looks like at different developmental stages — but existing competency frameworks don't provide this. A school using GreenComp, for example, finds that the framework specifies "Embracing complexity and sustainability" as a competency but says nothing about what this means for a 6-year-old versus a 14-year-old. The band system fills this gap. Piaget's (1952) stages of cognitive development provide the developmental anchoring, used as rationale rather than rigid prescription: Band A (approximately ages 5-7) aligns with late preoperational thinking — concrete, egocentric, perceptual; Band B (approximately ages 8-10) aligns with concrete operational thinking — logical operations on concrete objects, classification, seriation; Band C (approximately ages 10-12) aligns with early formal operational thinking — emerging abstract reasoning, hypothetical thinking; Band D (approximately ages 12-14) aligns with developing formal operational thinking — systematic reasoning, metacognition, abstract analysis. These are approximate alignments, not rigid prescriptions — developmental variability within any age group is large. Wiggins & McTighe (2005) provide the backwards design framework that Manning extends. Standard UBD begins with curriculum goals and works backwards: goals → assessment → instruction. Manning's extension adds an upstream "why" layer: mission → values → what the curriculum must prioritise → what it must NOT prioritise → competency selection → learning target decomposition → band specification. This "purpose-driven backwards design" means that every band statement can be traced back to the school's mission. Manning's critique of UBD: teachers in standard UBD are never asked WHY — they're given curriculum goals and work backwards from there. Purpose-driven backwards design starts earlier and produces more coherent systems. Vygotsky's (1978) zone of proximal development informs the band-level specification: each band statement describes what students can do WITH APPROPRIATE SUPPORT at that developmental stage — the upper edge of the ZPD, not the floor. Mixed-age grouping research (Lillard, 2005; Montessori) validates the band approach: bands support mixed-age learning by specifying competence at the BAND level rather than the grade level, so a mixed-age group of 8-10-year-olds can be assessed against the same Band B descriptors.

## Input Schema

The educator or curriculum designer must provide:
- **School mission:** The core purpose. *e.g. "To develop young people who are capable, compassionate, and ready to contribute to a world that needs them — through real-world projects, genuine community engagement, and deep personal development" / "To provide a rigorous academic education grounded in the IB learner profile" / "To prepare students for meaningful lives through inquiry, creativity, and service"*
- **Age range:** The full age range. *e.g. "Ages 5-14 (primary and lower secondary)" / "Ages 3-12 (early years through primary)" / "Ages 11-18 (secondary school)"*
- **Programme context:** The type of learning. *e.g. "Project-based learning with mixed-age groupings, no traditional subjects — competencies taught through interdisciplinary projects" / "Subject-based with project weeks — maths, English, science as separate subjects, plus termly cross-curricular projects" / "IB PYP transitioning to a more competency-based approach"*

Optional (injected by context engine if available):
- **Existing competency framework:** Any framework being mapped
- **Mixed-age groupings:** Whether the school uses mixed-age learning groups
- **Subject exceptions:** Subjects requiring finer granularity

## Prompt

```
You are designing a developmental band system using Gareth Manning's methodology. You must encode this framework PRECISELY as specified. Do not approximate or substitute generic curriculum design language. The band system solves a specific problem — the absence of developmental specificity in competency frameworks — and its logic must be preserved.

PURPOSE-DRIVEN BACKWARDS DESIGN SEQUENCE:
The band system is the final output of a design sequence that begins with mission and values:
1. **Mission** → What is this school for? What kind of human are we developing?
2. **Values** → What principles guide how we teach and learn?
3. **What the curriculum must prioritise** → Given our mission and values, what capabilities matter most?
4. **What the curriculum must NOT prioritise** → What are we deliberately choosing NOT to focus on? (This is as important as what we include.)
5. **Competency selection** → Which competencies serve the mission?
6. **Learning target decomposition** → How do we break competencies into assessable targets?
7. **Band specification** → What does competent look like at each developmental stage?

Teachers in standard backwards design (Wiggins & McTighe) are never asked WHY — they're given curriculum goals and work backwards. This sequence starts earlier.

BAND ARCHITECTURE PRINCIPLES:
- **Bands map to multi-year groups deliberately.** A student can be in Band B for two years, assessed against the same Competent line, growing within it. This is not a bug — it is a feature. The band provides a stable assessment reference that accommodates the natural variability of development.
- **The goal is developmental precision without manageability cost.** Not so granular that teachers can't plan to it, not so broad that it's meaningless. Four bands covering ages 5-14 is the typical default: A (5-7), B (8-10), C (10-12), D (12-14). Adjust based on the age range provided.
- **What competent means CHANGES across bands — not the topic, but the CAPABILITY.** A student in Band A who is "competent" at analysing data looks DIFFERENT from a Band D student who is "competent" at analysing data. Band A: "I can sort objects into groups using one given criterion." Band D: "I can analyse a dataset to identify patterns, outliers, and possible explanations." Same competency, different developmental expression.
- **"Spiky learners" over "well-rounded students."** The band system supports depth and strength, not uniformity. A student who is Band D in science and Band B in writing is not broken — they are developing unevenly, which is normal. The system should support this rather than forcing all dimensions to the same level.

CRITIQUE OF FLAT COMPETENCY LISTS:
Encode why this problem matters. UNESCO, GreenComp, EntreComp, LifeComp, DigComp — these frameworks list competencies without developmental specificity. A teacher reading "Demonstrates systems thinking" has no idea what this means for a 7-year-old. The cost: teachers either (a) set expectations too high (using the framework's adult-facing language), (b) set expectations too low (dumbing it down to be safe), or (c) ignore the competency entirely. The band system makes competencies usable by specifying what competent looks like at each developmental stage.

EXCEPTION HANDLING:
Some subjects require finer granularity than four broad bands:
- **Mathematics:** Mathematical progression is steep and sequential. A student who hasn't mastered place value cannot begin multiplication. Broad bands may be too imprecise for maths. Consider 9 levels (or more) for mathematical competencies.
- **Language acquisition (L1 and L2):** Reading and writing progression requires fine-grained tracking, especially in early years. Consider 9 levels for literacy and language.
- The rule: use broad bands for competencies where developmental progression is gradual and contextual (critical thinking, collaboration, creativity). Use finer granularity for competencies where progression is sequential and cumulative (maths, language).

Your task is to design a developmental band system for:

**School mission:** {{school_mission}}
**Age range:** {{age_range}}
**Programme context:** {{programme_context}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Existing competency framework:** {{existing_competency_framework}} — if not provided, the band system will be designed from mission and values rather than mapping an existing framework.
**Mixed-age groupings:** {{mixed_age_groupings}} — if not provided, design the bands to work with or without mixed-age groupings.
**Subject exceptions:** {{subject_exceptions}} — if not provided, identify which subjects likely need finer granularity and recommend accordingly.

Return your output in this exact format:

## Developmental Band System: [School/Programme Name]

**Mission:** [The school's core purpose]
**Age range:** [Full range covered]
**Number of bands:** [How many, and why this number]

### Purpose-Driven Design Sequence

[Walk through the full sequence: mission → values → priorities → non-priorities → competency logic → band rationale. This makes the design transparent and traceable.]

### Band Architecture

[The complete band structure: how many bands, what ages each covers, and the developmental rationale for each band break]

| Band | Age Range | Developmental Anchor | Key Cognitive Characteristics |
|---|---|---|---|
| [Band] | [Ages] | [Piaget stage or equivalent] | [What students can typically do at this stage] |

### Developmental Rationale

[Why the bands are where they are — the cognitive, social-emotional, and practical reasoning for each band break]

### Competent Definition Logic

[How to determine what competent means at each band — the general principles, with a worked example showing how ONE competency is expressed differently across all bands]

### Exception Handling

[Which subjects need finer granularity and why, with specific guidance on the finer-grained system]

### Mixed-Age Implications

[How the band system works with mixed-age learning groups — what it makes possible and what it complicates]

### Known Limitations

[Honest assessment — bands are broad, development is variable, and some students will be ahead of or behind their band]

**Self-check before returning output:** Verify that (a) the design sequence begins with mission not curriculum, (b) each band has a developmental rationale, (c) competent is defined developmentally not topically, (d) exception handling covers maths and language, (e) the critique of flat competency lists is included, and (f) "spiky learners" are supported not pathologised.
```

## Example Output

**Scenario:** *School mission: "To develop young people who are capable, compassionate, and ready to contribute to a world that needs them — through real-world projects, genuine community engagement, and deep personal development" / Age range: "Ages 5-14" / Programme context: "Project-based learning with mixed-age learning groups. No traditional subjects — competencies are taught through interdisciplinary projects. Maths and literacy have dedicated daily sessions but are also embedded in projects" / Existing competency framework: "Currently using a mix of GreenComp, EntreComp, and LifeComp with some school-developed competencies. These frameworks lack developmental specificity" / Mixed-age groupings: "Yes — four learning groups roughly corresponding to ages 5-7, 7-9, 9-11, 11-14"*

---

## Developmental Band System: REAL School

**Mission:** To develop young people who are capable, compassionate, and ready to contribute to a world that needs them
**Age range:** Ages 5-14
**Number of bands:** 4 (A, B, C, D) — aligning with the school's existing mixed-age learning groups and supported by developmental psychology

### Purpose-Driven Design Sequence

**1. Mission:** Capable, compassionate, ready to contribute. This is a DOING mission — it specifies agency (capable), ethics (compassionate), and orientation toward the world (contribute). The curriculum must produce people who can ACT in the world, not just know about it.

**2. Values:** Real-world learning. Community engagement. Personal development. These are not slogans — they are design constraints. "Real-world learning" means projects must have authentic audiences and genuine consequences. "Community engagement" means the community is a learning partner, not a backdrop. "Personal development" means the curriculum includes the inner life, not just academic skills.

**3. What the curriculum must prioritise:** Agency (the ability to initiate, plan, and complete meaningful work). Ecological thinking (understanding systems, consequences, interdependence). Communication (the ability to express ideas clearly and listen deeply). Craftsmanship (the commitment to quality in everything produced). Self-knowledge (understanding one's own strengths, limitations, and values).

**4. What the curriculum must NOT prioritise:** Content coverage for its own sake. Standardised test preparation. Competitive ranking. Uniform development across all dimensions. These are deliberate exclusions — every "no" makes the "yes" more powerful.

**5. Competency logic:** Competencies are selected because they serve the mission. "Demonstrates systems thinking" is included because it serves ecological thinking and real-world problem-solving. "Recites historical dates" is excluded because it serves content coverage, not capability.

**6. Band specification:** Each competency is expressed at four developmental levels, using the progression levers (independence, complexity, scope, precision, reasoning, transfer) rather than topic escalation.

### Band Architecture

| Band | Age Range | Developmental Anchor | Key Cognitive Characteristics |
|---|---|---|---|
| **A** | 5-7 | Late preoperational / early concrete operational | Concrete, sensory-based, egocentric perspective slowly expanding. Learning through doing and direct experience. Limited abstract reasoning. Can classify, sort, and compare with concrete objects. |
| **B** | 8-10 | Concrete operational | Logical thinking about concrete situations. Can seriate, classify, and conserve. Beginning to consider multiple perspectives. Can plan simple sequences. Increasingly independent in familiar contexts. |
| **C** | 10-12 | Early formal operational | Emerging abstract reasoning. Can hypothesise and test. Growing capacity for systematic thinking. Can consider multiple variables. Developing metacognition — awareness of own thinking. |
| **D** | 12-14 | Developing formal operational | Systematic abstract reasoning. Can construct and evaluate arguments. Sophisticated perspective-taking. Can design and execute complex plans. Metacognitive — can monitor and regulate own learning. |

### Developmental Rationale

**Band A → Band B break (approximately age 7-8):** The shift from preoperational to concrete operational thinking. Students move from perception-based reasoning ("This row has more because it's longer") to logic-based reasoning ("Both rows have the same number, they're just spread differently"). This is the most well-established developmental transition in Piaget's framework and the most consequential for curriculum design: Band A activities must be concrete and sensory; Band B activities can begin to introduce logical structures.

**Band B → Band C break (approximately age 10-11):** The emergence of abstract reasoning. Students begin to think about things they cannot see or touch — hypothetical scenarios, abstract principles, systems relationships. This opens up inquiry-based learning: Band C students can design investigations, form hypotheses, and consider variables in ways that Band B students cannot reliably do.

**Band C → Band D break (approximately age 12-13):** The development of systematic and metacognitive thinking. Students can not only think abstractly but can THINK ABOUT THEIR THINKING — planning, monitoring, and evaluating their own cognitive processes. This enables genuine self-directed learning: Band D students can design and manage their own projects with mentoring rather than instruction.

### Competent Definition Logic

**Worked example: "Demonstrates systems thinking"**

This competency serves the mission through ecological thinking — understanding that actions have consequences beyond the immediate and obvious.

| Band | "Competent" Statement | Progression Lever |
|---|---|---|
| **A** | I can describe what happens when one thing in a system changes | Scope: single cause-effect link |
| **B** | I can identify how parts of a system affect each other and predict what might happen if one part changes | Complexity: multiple connections, prediction |
| **C** | I can map the relationships within a system and explain how changes ripple through connected parts | Reasoning: explaining mechanisms, not just identifying connections |
| **D** | I can analyse a complex system, identify feedback loops and unintended consequences, and evaluate interventions | Transfer: applying systems analysis to novel situations, evaluating rather than just describing |

Notice: the TOPIC does not change (systems thinking throughout). The CAPABILITY changes — from describing a single link (Band A) to analysing feedback loops and evaluating interventions (Band D). This is developmental progression, not topic escalation.

### Exception Handling

**Mathematics:** Broad bands are insufficient for maths. Mathematical progression is steep and sequential: place value → addition → multiplication → fractions → algebra → each step requires mastery of the previous one. A student who is Band B for collaboration might be Band C for maths or Band A for maths — and the maths assessment needs to reflect this with precision. **Recommendation:** Use a 9-level system for mathematical competencies, with 2-3 levels per band. This provides the fine-grained tracking that maths progression requires while remaining compatible with the band architecture.

**Language acquisition (reading and writing):** Like maths, literacy progression requires fine-grained tracking — particularly in the early years where the difference between "recognises letters" and "reads simple sentences" is a matter of months, not years. **Recommendation:** Use a 9-level system for literacy competencies, aligned with but more granular than the broad bands.

**All other competencies:** Broad bands (A-D) provide sufficient granularity. Competencies like systems thinking, collaboration, craftsmanship, and self-regulation develop gradually and contextually — they do not require the sequential precision that maths and language demand.

### Mixed-Age Implications

**What the band system makes possible:**
- A mixed-age learning group of 8-10-year-olds (Band B) can be assessed against the SAME competency descriptors. The teacher does not need 3 separate sets of expectations for ages 8, 9, and 10 — Band B is the reference.
- Younger students in a mixed-age group can see what Band C looks like by watching older students. This creates natural ZPD scaffolding.
- Older students consolidate their Band B competencies by supporting younger students — the peer tutoring effect (Hattie, 2009: d = 0.55).

**What the band system complicates:**
- Students near band transitions (a 10-year-old moving from Band B to Band C) may exhibit characteristics of both bands. The teacher must exercise professional judgment about which band descriptor best fits.
- A "spiky" student who is Band D in one competency and Band B in another will be assessed at different band levels simultaneously. This is intentional (development IS uneven) but requires a reporting system that can represent multiple bands per student.

### Known Limitations

1. **Bands are deliberately broad — and some students will not fit neatly.** A 9-year-old who thinks abstractly (early for Band C) or a 13-year-old who struggles with abstract reasoning (late for Band C) will be assessed against a band that doesn't perfectly match their development. The band is a reference, not a diagnosis. Teacher professional judgment is always needed at the edges.

2. **The Piaget anchoring is approximate.** Piaget's stages are the most widely known developmental framework, but they are also the most criticised — development is more continuous and variable than stage theory suggests (Siegler, 2006). The band system uses Piaget as rationale, not as rigid prescription. Individual variation within any age group is large.

3. **The purpose-driven backwards design sequence requires a clear mission.** If the school's mission is vague ("We believe in excellence and opportunity"), the entire design sequence is weakened — there is nothing specific to work backwards from. The band system is strongest in schools with clear, distinctive missions; it is weaker in schools with generic statements of purpose.

4. **The band system is a DESIGN tool, not an assessment tool.** It specifies what competent looks like at each developmental stage, but it does not specify HOW to assess it. Assessment requires rubrics (see Skill 99: Coherent Rubric Logic Builder) and learning targets (see Skill 98: Learning Target Authoring Guide) built on top of the band architecture.

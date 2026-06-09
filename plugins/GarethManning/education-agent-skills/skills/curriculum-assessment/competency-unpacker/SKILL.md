---
# AGENT SKILLS STANDARD FIELDS (v2)
name: competency-unpacker
description: "Unpack a broad standard or competency descriptor into specific, assessable success criteria and sub-skills. Use when interpreting curriculum standards or writing learning objectives."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "curriculum-assessment/competency-unpacker"
skill_name: "Competency Unpacker"
domain: "curriculum-assessment"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Wiggins & McTighe (1998, 2005) — Understanding by Design: backward design from desired results"
  - "Marzano & Kendall (2007) — The New Taxonomy of Educational Objectives"
  - "Heritage (2008) — Learning progressions: supporting instruction and formative assessment"
  - "Popham (2007) — The lowdown on learning progressions"
  - "Hattie (2009) — Visible Learning: success criteria and learning intentions"
input_schema:
  required:
    - field: "competency_descriptor"
      type: "string"
      description: "The standard, learning objective, or competency descriptor to unpack"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: the specific curriculum or standards framework"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: prior attainment data, common gaps"
    - field: "assessment_purpose"
      type: "string"
      description: "Why the competency is being unpacked — for planning, for assessment design, for reporting"
output_schema:
  type: "object"
  fields:
    - field: "observable_indicators"
      type: "array"
      description: "Specific, observable behaviours that demonstrate the competency"
    - field: "prerequisite_knowledge"
      type: "array"
      description: "What students must already know or be able to do before attempting this"
    - field: "common_misconceptions"
      type: "array"
      description: "Typical misunderstandings that interfere with demonstrating this competency"
    - field: "success_criteria"
      type: "object"
      description: "Success criteria at multiple levels — beginning, developing, secure, extending"
chains_well_with:
  - "backwards-design-unit-planner"
  - "criterion-referenced-rubric-generator"
  - "learning-progression-builder"
  - "formative-assessment-technique-selector"
  - "curriculum-knowledge-architecture-designer"
  - "kud-knowledge-type-mapper"
  - "scope-and-sequence-designer"
teacher_time: "3 minutes"
tags: ["competency", "standards", "success-criteria", "unpacking", "curriculum"]
---

# Competency Unpacker

## What This Skill Does

Takes a standard, learning objective, or competency descriptor — often written in abstract, compressed language — and unpacks it into four actionable components: observable indicators (what a student who has achieved this actually DOES), prerequisite knowledge (what must be in place first), common misconceptions (what typically goes wrong), and success criteria at multiple levels (beginning through extending). The output transforms opaque curriculum language into concrete, assessable, teachable components. AI is specifically valuable here because competency descriptors are deliberately compressed — a single sentence like "analyse how writers use language and structure to achieve effects" contains multiple skills, knowledge domains, and levels of sophistication that must be unpacked before they can be taught or assessed.

## Evidence Foundation

Wiggins & McTighe (1998, 2005) established that effective curriculum design begins with clarity about desired results — and that most curriculum standards require significant "unpacking" before they can be translated into instruction and assessment. A standard that says "students will understand the causes of World War I" is not assessable until "understand" is defined in observable terms. Marzano & Kendall (2007) provided a taxonomy for classifying the cognitive demands of standards — distinguishing retrieval, comprehension, analysis, and knowledge utilisation — enabling teachers to identify what type of thinking a standard actually requires. Heritage (2008) and Popham (2007) demonstrated that unpacking standards into learning progressions — sequences of sub-skills from prerequisite to target — is essential for both instruction and formative assessment, because it reveals where students are and what they need next. Hattie (2009) found that clear success criteria (effect size 0.77) are among the highest-leverage instructional strategies, but only when they describe what success looks like in specific, observable terms — not when they restate the learning objective in different words.

## Input Schema

The teacher must provide:
- **Competency descriptor:** The standard or objective to unpack. *e.g. "Analyse how writers use language and structure to achieve effects and influence readers" / "Use ratio and proportion, including rates, to solve problems" / "Explain how changes in the environment may affect organisms"*
- **Student level:** Year group. *e.g. "Year 9"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Curriculum framework:** Specific standards framework (e.g., National Curriculum, IB, ACARA)
- **Student profiles:** Prior attainment data, common gaps
- **Assessment purpose:** Why the competency is being unpacked

## Prompt

```
You are an expert in curriculum design and standards-based instruction, with deep knowledge of Wiggins & McTighe's (1998, 2005) Understanding by Design framework, Marzano & Kendall's (2007) taxonomy of educational objectives, and Heritage's (2008) work on learning progressions. You understand that competency descriptors are compressed summaries of complex learning — they must be unpacked into observable, teachable, assessable components before they can guide instruction.

Your task is to unpack:

**Competency descriptor:** {{competency_descriptor}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the competency descriptor.
**Curriculum framework:** {{curriculum_framework}} — if not provided, unpack in general terms applicable across frameworks.
**Student profiles:** {{student_profiles}} — if not provided, assume a typical mixed-ability class at the stated year level.
**Assessment purpose:** {{assessment_purpose}} — if not provided, unpack for general instructional planning.

Apply these evidence-based principles:

1. **Observable indicators (Wiggins & McTighe, 2005; Hattie, 2009):**
   - Define what a student who has achieved the competency actually DOES — observable actions, not internal states.
   - "Understands" is not observable. "Identifies," "explains," "compares," "evaluates," "constructs" are observable.
   - Be specific to the competency: "identifies the effect of a writer's word choice on the reader" is more useful than "analyses language."
   - Include 4–6 specific indicators that collectively cover the competency.

2. **Prerequisite knowledge and skills (Heritage, 2008; Popham, 2007):**
   - What must a student already know or be able to do BEFORE they can work toward this competency?
   - Distinguish between content prerequisites (knowledge needed) and skill prerequisites (abilities needed).
   - These prerequisites become diagnostic checks — if a student can't demonstrate the competency, the prerequisite list helps identify WHERE the gap is.

3. **Common misconceptions (Marzano & Kendall, 2007):**
   - What typically goes wrong when students attempt this competency?
   - Include both conceptual misconceptions (misunderstandings of the content) and procedural errors (mistakes in the process).
   - These become assessment design priorities — good assessments surface these misconceptions.

4. **Multi-level success criteria (Hattie, 2009):**
   - Provide success criteria at four levels: Emerging, Developing, Competent, Extending.
   - Each level should describe what the student CAN do (not what they can't).
   - Levels should be qualitatively different, not just quantitatively different (Competent is not "more of" Developing — it's a different quality of response).
   - Use descriptive language, not evaluative labels.

Return your output in this exact format:

## Competency Unpacked: [Brief descriptor]

**Standard:** [Full competency descriptor]
**For:** [Student level]
**Subject:** [Subject area]

### Observable Indicators

[4–6 specific, observable behaviours that demonstrate this competency]

### Prerequisite Knowledge and Skills

**Content prerequisites (what students must know):**
[Specific knowledge required]

**Skill prerequisites (what students must be able to do):**
[Specific skills required]

### Common Misconceptions

[3–4 typical misconceptions or errors, with explanation of why they occur]

### Success Criteria

| Level | What the student does |
|-------|----------------------|
| **Emerging** | [Description of early, partial demonstration] |
| **Developing** | [Description of growing but inconsistent demonstration] |
| **Competent** | [Description of consistent, accurate demonstration] |
| **Extending** | [Description of sophisticated, independent application] |

### Implications for Teaching

[2–3 key teaching implications — what the unpacking reveals about how this competency should be taught]

**Self-check before returning output:** Verify that (a) all indicators are observable, not internal ("explains" not "understands"), (b) prerequisites are specific enough to be diagnostic, (c) misconceptions are based on common patterns, not hypothetical, (d) success criteria describe what students CAN do at each level, and (e) the four levels are qualitatively distinct.
```

## Example Output

**Scenario:** *Competency descriptor: "Analyse how writers use language and structure to achieve effects and influence readers" / Student level: "Year 9" / Subject area: "English Language"*

---

## Competency Unpacked: Analysing Writers' Language and Structure

**Standard:** Analyse how writers use language and structure to achieve effects and influence readers
**For:** Year 9
**Subject:** English Language

### Observable Indicators

A student who has achieved this competency:

1. **Identifies specific language choices** (individual words, phrases, figurative language, sentence types) and names the technique where applicable (metaphor, sibilance, short sentence for impact).
2. **Explains the effect of each language choice on the reader** — what it makes the reader think, feel, or picture — rather than simply identifying the technique.
3. **Identifies structural choices** (paragraph length, opening, ending, shift in tone, chronological vs. non-linear, sentence positioning) and explains how they shape the reader's experience across the whole text.
4. **Links language and structural choices to the writer's purpose** — explains WHY the writer made these choices, connecting technique to intention (to persuade, to create tension, to evoke sympathy, to shock).
5. **Uses appropriate analytical terminology** accurately — not just naming techniques but using the vocabulary of analysis: "suggests," "conveys," "implies," "positions the reader to."
6. **Supports analysis with embedded quotations** selected for their analytical potential, not just their availability.

### Prerequisite Knowledge and Skills

**Content prerequisites (what students must know):**
- A working vocabulary of literary and linguistic techniques (metaphor, simile, personification, alliteration, repetition, rhetorical question, short sentence, listing) — at minimum 10 techniques they can identify on sight
- Understanding that writers make deliberate choices — that language is crafted, not accidental
- Awareness that different genres have different purposes (persuade, inform, describe, argue, narrate) and that technique serves purpose

**Skill prerequisites (what students must be able to do):**
- Read a text extract and identify individual words or phrases that seem important or interesting (close reading at word level)
- Write in paragraphs with a clear point supported by evidence
- Distinguish between describing what happens in a text (summary) and explaining how the text is written (analysis)

### Common Misconceptions

1. **"Feature-spotting without analysis."** The most common error. Students identify a technique ("There is a metaphor") but don't explain its effect. They have been taught to NAME techniques but not to ANALYSE them. This produces responses like: "The writer uses alliteration in 'dark, dangerous, deathly.' This is effective." The identification is correct but the analysis is absent.

2. **"The writer uses this to make the reader want to read on."** A generic effect claim applied to every technique. Students use this phrase as a default when they don't know what the actual effect is. It signals that the student can identify that techniques have effects but cannot specify them.

3. **"Language analysis without structural analysis."** Students focus on individual words and phrases (language) but ignore how the text is organised (structure). They analyse the metaphor in paragraph 3 but don't notice that paragraph 3 is a single-sentence paragraph positioned after a long descriptive passage — a structural choice that creates impact.

4. **"Technique as the analysis."** Students write: "The writer uses a metaphor to show that..." as if naming the technique IS the analysis. The technique is the WHAT; the analysis is the HOW and WHY. Naming "metaphor" is identification; explaining how the metaphor creates a specific image or emotion is analysis.

### Success Criteria

| Level | What the student does |
|-------|----------------------|
| **Emerging** | Identifies some language features (e.g., "The writer uses a simile"). May attempt to describe effect but defaults to generic claims ("This is effective" / "This makes the reader want to read on"). Focuses on language only; structural analysis is absent or superficial. Quotations are included but not embedded in analysis. |
| **Developing** | Identifies language features AND begins to explain specific effects ("The simile 'cold as a gravestone' suggests death and creates an unsettling atmosphere"). Attempts structural analysis but may describe rather than analyse ("The text starts with a question"). Evidence is relevant but analysis is inconsistent — some points are developed, others stop at identification. |
| **Competent** | Analyses both language AND structure with specific, developed explanations of effect. Links techniques to the writer's purpose ("Priestley uses the short sentence 'We are responsible' at the end of the Inspector's speech to deliver his moral message with force — the simplicity contrasts with Birling's verbose speeches, positioning the reader to trust the Inspector's clarity over Birling's bluster"). Quotations are embedded and well-selected. Analysis is consistent across the response. |
| **Extending** | Produces perceptive, original analysis that considers multiple possible effects and evaluates which is most likely. Analyses how language and structure work TOGETHER ("The shift from long, flowing sentences to a single blunt statement at the paragraph's end mirrors the character's emotional shift from denial to realisation — the structure enacts what the language describes"). May consider alternative interpretations. Analytical vocabulary is precise and varied. |

### Implications for Teaching

1. **The biggest gap is between identification and analysis.** Most students can learn to spot techniques; far fewer can explain effects. Instruction should spend proportionally more time on "What effect does this create?" than on "What technique is this?" Model the difference explicitly: show a feature-spotted response and an analytical response side by side.

2. **Structural analysis must be taught separately from language analysis.** Students default to word/phrase-level analysis because it's concrete and visible. Structure (paragraph organisation, text-level patterns, positioning of key moments) is more abstract and requires a different analytical lens — looking at the text as a whole, not zooming into individual phrases.

3. **Success criteria should be shared with students BEFORE they write.** The four-level descriptions can be used as self-assessment tools: "Read your response. Are you at Developing (naming techniques but not always explaining effects) or Competent (consistently explaining HOW techniques create specific effects)? What would you need to add to move up?"

---

## Known Limitations

1. **The unpacking reflects general expectations for this competency at the stated level.** Specific exam boards, curricula, or school policies may define the competency differently or emphasise different components. Teachers should cross-reference the unpacking with their specific assessment framework and adjust where needed.

2. **Success criteria at four levels necessarily simplify a continuum.** Student work exists on a spectrum, not in neat categories. Some responses may demonstrate Competent analysis of language but Emerging analysis of structure. The levels are guides for feedback, not rigid classifications — the teacher must use professional judgement when a response spans multiple levels.

3. **The common misconceptions listed are the MOST common, not all possible ones.** Individual students may hold different misconceptions based on their prior instruction, first language, or conceptual framework. The listed misconceptions should be treated as starting points for diagnostic assessment, not as an exhaustive list.

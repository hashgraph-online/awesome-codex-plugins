---
# AGENT SKILLS STANDARD FIELDS (v2)
name: assessment-validity-checker
description: "Audit a proposed assessment for construct validity, reliability, and alignment to learning objectives. Use when reviewing or quality-assuring assessments before deployment."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "curriculum-assessment/assessment-validity-checker"
skill_name: "Assessment Validity Checker"
domain: "curriculum-assessment"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Wiliam (2011) — Embedded Formative Assessment"
  - "Messick (1989) — Validity in educational measurement: a unified validity framework"
  - "Kane (2006) — Validation as argument-based approach"
  - "Brookhart (2003) — Developing measurement theory for classroom assessment purposes and uses"
  - "Stobart (2008) — Testing Times: the uses and abuses of assessment"
input_schema:
  required:
    - field: "assessment_description"
      type: "string"
      description: "Description of the proposed assessment — what students do, how it is marked"
    - field: "intended_learning"
      type: "string"
      description: "What the assessment claims to measure"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "assessment_purpose"
      type: "string"
      description: "Formative, summative, diagnostic, or evaluative"
    - field: "marking_approach"
      type: "string"
      description: "How the assessment will be marked — rubric, mark scheme, holistic judgement"
    - field: "stakes"
      type: "string"
      description: "The consequences of the assessment — low stakes (informing teaching), high stakes (grading, reporting)"
output_schema:
  type: "object"
  fields:
    - field: "validity_analysis"
      type: "object"
      description: "Analysis of construct validity, content validity, and consequential validity"
    - field: "reliability_analysis"
      type: "string"
      description: "Analysis of inter-rater reliability and internal consistency"
    - field: "threats_identified"
      type: "array"
      description: "Specific threats to validity with explanations"
    - field: "recommendations"
      type: "array"
      description: "Specific modifications to address identified threats"
chains_well_with:
  - "criterion-referenced-rubric-generator"
  - "formative-assessment-technique-selector"
  - "competency-unpacker"
  - "backwards-design-unit-planner"
  - "curriculum-knowledge-architecture-designer"
  - "kud-knowledge-type-mapper"
teacher_time: "3 minutes"
tags: ["validity", "reliability", "assessment-design", "quality-assurance", "measurement"]
---

# Assessment Validity Checker

## What This Skill Does

Evaluates a proposed assessment against three dimensions: validity (does it measure what it claims to measure?), reliability (would different markers agree on the score?), and authenticity (is the task meaningful and does it require genuine demonstration of the intended learning?). The output identifies specific threats to validity — construct-irrelevant variance (the assessment measures something other than what it claims), construct underrepresentation (the assessment doesn't cover enough of what it claims to measure), and consequential validity problems (unintended negative effects of the assessment) — and provides specific, actionable recommendations for each threat. AI is specifically valuable here because most teacher-designed assessments contain validity threats that are invisible without explicit analytical frameworks — a teacher designing a "reading comprehension" test may inadvertently create a writing test, or a "science understanding" assessment may actually test literacy.

## Evidence Foundation

Messick (1989) unified the concept of validity into a single framework: validity is not a property of a test but of the interpretation and use of test scores. A test is not "valid" or "invalid" in the abstract — it is valid FOR a specific purpose with a specific population. This means every assessment must be evaluated against its intended use. Wiliam (2011) applied this framework to classroom assessment, showing that the most common validity threat in teacher-designed assessment is construct-irrelevant variance — where the assessment measures something other than the intended construct. For example, a group presentation assessed for "understanding of climate change" may actually measure public speaking confidence, group dynamics, and technology skills more than climate change understanding. Kane (2006) proposed a validation-as-argument approach: the validity of an assessment depends on the strength of the chain of reasoning from the task → the response → the score → the interpretation → the decision. Any weak link in this chain is a validity threat. Brookhart (2003) adapted measurement theory for classroom contexts, arguing that classroom assessments need not meet the same psychometric standards as standardised tests but must still demonstrate that they measure what they claim. Stobart (2008) highlighted consequential validity — the effects of assessment on learning. If an assessment drives students toward surface learning, test anxiety, or strategic behaviour rather than genuine engagement, its consequential validity is compromised.

## Input Schema

The teacher must provide:
- **Assessment description:** What students do and how it's marked. *e.g. "Students write a 500-word essay on the causes of WW1, marked against a rubric with four criteria: historical knowledge, analytical argument, use of evidence, and written communication" / "Students complete a 30-question multiple choice test on photosynthesis" / "Students create a poster about healthy eating and present it to the class"*
- **Intended learning:** What the assessment claims to measure. *e.g. "Understanding of the causes of WW1 and ability to construct a historical argument" / "Knowledge and understanding of photosynthesis" / "Understanding of nutrition and healthy eating"*
- **Student level:** Year group. *e.g. "Year 10"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Assessment purpose:** Formative, summative, diagnostic, or evaluative
- **Marking approach:** How it will be marked
- **Stakes:** Consequences of the assessment

## Prompt

```
You are an expert in educational assessment and measurement, with deep knowledge of Messick's (1989) unified validity framework, Wiliam's (2011) approach to classroom assessment validity, Kane's (2006) argument-based validation, and Stobart's (2008) work on consequential validity. You understand that validity is not a property of the test itself but of the interpretation and use of the scores — an assessment is valid FOR a specific purpose, and the same assessment may be valid for one purpose but invalid for another.

Your task is to evaluate the validity of:

**Assessment description:** {{assessment_description}}
**Intended learning:** {{intended_learning}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the assessment description.
**Assessment purpose:** {{assessment_purpose}} — if not provided, infer from the description and stakes.
**Marking approach:** {{marking_approach}} — if not provided, note that marking approach affects reliability and recommend one.
**Stakes:** {{stakes}} — if not provided, analyse for both low-stakes and high-stakes use.

Analyse across these dimensions:

1. **Construct validity (Messick, 1989):**
   - Does the assessment task actually require demonstration of the intended learning?
   - **Construct-irrelevant variance:** Does the assessment inadvertently measure something ELSE? (E.g., a science assessment that requires essay writing also measures literacy; a group project also measures collaboration and social dynamics.)
   - **Construct underrepresentation:** Does the assessment cover enough of the intended construct? (E.g., a test on "understanding photosynthesis" that only asks factual recall questions doesn't assess understanding — it assesses memorisation.)

2. **Content validity:**
   - Does the assessment sample appropriately from the domain of intended learning?
   - Are important aspects of the learning missing from the assessment?
   - Are there aspects of the assessment that go beyond the intended learning?

3. **Reliability (Brookhart, 2003):**
   - Would different markers give the same score? (Inter-rater reliability)
   - Would the same student get a similar score on a different day? (Test-retest)
   - Is the marking scheme clear enough to be applied consistently?

4. **Consequential validity (Stobart, 2008):**
   - What behaviours will this assessment drive? Will students engage in genuine learning or strategic/surface-level preparation?
   - Does the assessment create unfair barriers for specific groups (EAL students, students with learning differences)?
   - Does the assessment format match the learning it claims to measure?

5. **Authenticity:**
   - Does the task require genuine demonstration of the learning, or can a student perform well without actually having learned the intended content?
   - Can the task be completed through memorisation, copying, or procedural compliance without understanding?

Return your output in this exact format:

## Assessment Validity Analysis

**Assessment:** [Brief description]
**Claims to measure:** [Intended learning]
**For:** [Student level]

### Validity Analysis

**Construct validity:** [Analysis of whether the assessment measures what it claims]
**Construct-irrelevant variance:** [What ELSE the assessment measures that isn't intended]
**Construct underrepresentation:** [What aspects of the intended learning are NOT assessed]

### Reliability Analysis

[Analysis of marking consistency and specific reliability concerns]

### Consequential Validity

[What learning behaviours the assessment is likely to drive]

### Threats Identified

[Numbered list of specific validity threats, each with an explanation]

### Recommendations

[Specific, actionable modifications to address each identified threat]

### Overall Verdict

[Summary judgement: is this assessment fit for its stated purpose? What is the single most important modification?]

**Self-check before returning output:** Verify that (a) the analysis addresses construct validity, reliability, and consequential validity, (b) each threat is specific and explained, (c) each recommendation directly addresses an identified threat, (d) the analysis considers the assessment's purpose and stakes, and (e) the verdict is constructive — identifying what to fix, not just what's wrong.
```

## Example Output

**Scenario:** *Assessment description: "Students create a poster about the causes of climate change and present it to the class. The poster must include at least 3 causes, a visual element (graph or diagram), and be 'visually appealing.' Marked out of 20: content (8 marks), visual design (6 marks), presentation (6 marks)." / Intended learning: "Students understand the causes and effects of climate change." / Student level: "Year 9" / Subject area: "Geography"*

---

## Assessment Validity Analysis

**Assessment:** Poster presentation on climate change causes
**Claims to measure:** Understanding of the causes and effects of climate change
**For:** Year 9 Geography

### Validity Analysis

**Construct validity:** MODERATE CONCERN. The assessment claims to measure understanding of climate change causes and effects, but the task and marking scheme assess three constructs simultaneously: geography knowledge (8/20 = 40%), visual design skill (6/20 = 30%), and public speaking skill (6/20 = 30%). A student who deeply understands climate change but cannot draw or speak confidently will score lower than a student with superficial knowledge who presents a beautifully designed, confidently delivered poster. The assessment does not primarily measure what it claims to.

**Construct-irrelevant variance:**
- **Visual design (6 marks):** The ability to create a "visually appealing" poster is unrelated to understanding climate change. This measures art/design skills and access to coloured pens, printers, and craft materials — resources that correlate with socioeconomic background, not geographic understanding. A student who produces an aesthetically poor but scientifically accurate poster is penalised. This is the most significant validity threat.
- **Presentation skills (6 marks):** Public speaking confidence is a separate skill from geographic understanding. EAL students, students with speech difficulties, and students with social anxiety are disadvantaged by this component. The presentation may reveal understanding, but 6/20 marks for delivery means presentation manner is weighted as heavily as scientific accuracy.
- **Material access:** Students who can print colour images, use computers at home, or purchase poster materials have an advantage unrelated to learning.

**Construct underrepresentation:**
- The assessment requires "at least 3 causes" but the intended learning includes "effects" — effects are not assessed despite being part of the stated learning objective.
- The assessment doesn't require students to EXPLAIN causes — only to list them. A poster listing "burning fossil fuels, deforestation, agriculture" without explanation can score full content marks. Listing is recall; explaining is understanding. The assessment underrepresents the "understanding" component.
- No assessment of relationships between causes, relative significance, or evidence evaluation — which are the geographic thinking skills the objective implies.

### Reliability Analysis

- **"Visually appealing"** is subjective and unanchored. Two markers are likely to disagree significantly on what counts as visually appealing. This criterion will produce the lowest inter-rater reliability of any component.
- **Content marking (8 marks)** could be reliable if the mark scheme specifies what counts as a "cause" and what level of explanation earns each mark — but as described, "at least 3 causes" is a binary threshold, not a quality scale. A student listing 3 basic causes and a student providing detailed, evidenced explanations of 5 causes may receive similar scores.
- **Presentation (6 marks)** has no described criteria. Markers may weight fluency, confidence, eye contact, volume, or content accuracy differently. Without a rubric, reliability will be low.

### Consequential Validity

- **The assessment incentivises decoration over understanding.** Students who recognise that 12/20 marks (60%) depend on design and presentation will rationally invest more time on visuals and rehearsal than on learning the content. This drives surface-level learning behaviour.
- **The assessment disadvantages EAL students and shy students.** 6 marks for presentation creates a barrier that is unrelated to geography. Students who understand climate change deeply but are anxious about presenting will underperform relative to their actual understanding.
- **The assessment rewards socioeconomic advantage.** Access to printers, coloured paper, markers, and a computer for design gives some students a significant edge on 30% of the marks. This is inequitable.

### Threats Identified

1. **MAJOR: Construct-irrelevant variance from visual design.** 30% of marks assess design skill, not geography. This means the assessment score does not represent what it claims.
2. **MAJOR: Construct-irrelevant variance from presentation.** 30% of marks assess public speaking, disadvantaging EAL, anxious, and speech-difficulty students.
3. **MODERATE: Construct underrepresentation.** Effects of climate change are not assessed despite being in the intended learning. Explanation of causes is not required — listing is sufficient.
4. **MODERATE: Low reliability.** "Visually appealing" is subjective. Presentation marks lack a rubric. Content marks don't distinguish quality of explanation.
5. **MINOR: Consequential validity.** Mark weighting incentivises decoration over learning.

### Recommendations

1. **Restructure the mark allocation.** Content should be at least 70% of the total marks. Reduce visual design to 0 marks (remove it as a criterion entirely) or cap at 2 marks for "clarity of visual communication" (whether the diagram/graph communicates information effectively — not whether it looks pretty). Reduce presentation to 4 marks maximum, with a rubric focused on clarity of explanation, not confidence of delivery.

2. **Require explanation, not just listing.** Change "at least 3 causes" to "explain 3 causes of climate change, including HOW each cause contributes to increased greenhouse gas concentrations." This requires understanding, not recall.

3. **Add the missing construct.** Add a requirement to address effects as well as causes — or change the intended learning to match the assessment. Alignment must go both ways.

4. **Replace "visually appealing" with "clear and communicative."** If visual elements remain, assess whether the graph/diagram communicates geographic information accurately — not whether it looks attractive.

5. **Provide an alternative to live presentation.** Allow students to submit a recorded explanation, a written paragraph, or a one-to-one explanation to the teacher instead of a class presentation. This removes the public speaking barrier while still assessing whether the student can explain their understanding.

6. **Create a content rubric.** Replace the 8-mark content score with a descriptive rubric that distinguishes between listing causes (lower level), explaining causes (middle level), and analysing the relationships and relative significance of causes (higher level).

### Overall Verdict

As currently designed, this assessment is **not fit for purpose**. It claims to measure understanding of climate change but actually measures a blend of geography knowledge (40%), art skills (30%), and public speaking (30%). The single most important modification is **restructuring the mark allocation** so that content understanding dominates the assessment. If a student deeply understands climate change causes and effects, they should score highly — regardless of their poster design or presentation confidence.

---

## Known Limitations

1. **The analysis evaluates the assessment as described, which may differ from how it's implemented.** A teacher who marks generously on design and strictly on content may partially compensate for the mark allocation issue in practice — but the structural problem remains. The assessment's design, not just its implementation, should be valid.

2. **Validity is always relative to purpose.** This analysis evaluates validity for the STATED purpose (measuring understanding of climate change). If the assessment's actual purpose includes developing presentation skills, the validity analysis would differ — but the assessment should then be labelled as measuring multiple constructs.

3. **Some validity threats are trade-offs, not errors.** Including a presentation component may have legitimate pedagogical reasons (building oracy skills, developing confidence). The analysis identifies the validity cost of these design choices — the teacher must decide whether the pedagogical benefits justify the validity compromise. The key is being transparent about what the assessment actually measures.

---
# AGENT SKILLS STANDARD FIELDS (v2)
name: gap-analysis-from-student-work
description: "Analyse student work against criteria to identify specific gaps between current performance and learning objectives. Use when reviewing submissions, planning feedback, or diagnosing learning needs."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "curriculum-assessment/gap-analysis-from-student-work"
skill_name: "Gap Analysis from Student Work"
domain: "curriculum-assessment"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Black & Wiliam (1998) — Assessment and Classroom Learning"
  - "Hattie & Timperley (2007) — The Power of Feedback"
  - "Sadler (1989) — Formative assessment and the design of instructional systems"
  - "Heritage (2010) — Formative Assessment: making it happen in the classroom"
  - "Wiliam (2011) — Embedded Formative Assessment"
input_schema:
  required:
    - field: "student_work_description"
      type: "string"
      description: "A description or transcript of the student's work — what they produced"
    - field: "assessment_criteria"
      type: "string"
      description: "The criteria or rubric the work should be assessed against"
    - field: "learning_objective"
      type: "string"
      description: "What the student was supposed to learn or demonstrate"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "student_profile"
      type: "string"
      description: "From context engine: prior attainment, known strengths and gaps"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "task_description"
      type: "string"
      description: "The task the student was completing"
output_schema:
  type: "object"
  fields:
    - field: "gap_analysis"
      type: "object"
      description: "Specific gaps identified, classified by type — conceptual, procedural, or communication"
    - field: "strengths"
      type: "array"
      description: "What the student does well — specific, evidence-based strengths"
    - field: "next_teaching_steps"
      type: "array"
      description: "Targeted actions to address each gap — not generic advice but specific next steps"
    - field: "feedback_script"
      type: "string"
      description: "How to communicate the analysis to the student in a way that promotes improvement"
chains_well_with:
  - "feedback-quality-analyser"
  - "criterion-referenced-rubric-generator"
  - "error-analysis-protocol"
  - "practice-problem-sequence-designer"
  - "kud-knowledge-type-mapper"
teacher_time: "3 minutes"
tags: ["gap-analysis", "student-work", "formative-assessment", "feedback", "diagnostic"]
---

# Gap Analysis from Student Work

## What This Skill Does

Analyses a student work sample against assessment criteria, identifies specific gaps (not just "needs improvement" but exactly WHAT is missing and WHY), classifies each gap by type (conceptual misunderstanding, procedural error, or communication/presentation issue), and generates targeted next teaching steps — specific actions the teacher can take to close each gap, rather than generic advice like "practise more." The output also includes a feedback script showing how to communicate the analysis to the student in a way that promotes improvement. AI is specifically valuable here because effective gap analysis requires simultaneously comparing the work to the criteria, diagnosing the type of gap (which determines the remedy), identifying strengths (which maintain motivation), and designing a targeted next step (which requires pedagogical knowledge) — a multi-layered analysis that takes significant time and expertise to do well.

## Evidence Foundation

Sadler (1989) established that formative assessment depends on three conditions: the student (and teacher) must understand the goal (what quality looks like), assess the current position (where the work is relative to the goal), and take action to close the gap. Gap analysis operationalises the second condition — systematically identifying where the work falls short and why. Hattie & Timperley (2007) demonstrated that effective feedback must address three questions: "Where am I going?" (the goal), "How am I going?" (current performance relative to the goal), and "Where to next?" (specific actions to close the gap). Most teacher feedback addresses only the first two; the third — specific next steps — is where learning happens. Black & Wiliam (1998) showed that formative assessment is only effective when the information gathered is used to adapt teaching — gap analysis without targeted action is diagnostic without being therapeutic. Heritage (2010) emphasised the importance of classifying gaps: a conceptual gap (the student doesn't understand the underlying idea) requires different intervention from a procedural gap (the student understands but makes errors in execution) or a communication gap (the student understands and can do it but can't express it). Wiliam (2011) argued that the most powerful feedback gives the student a specific, actionable next step rather than a judgement.

## Input Schema

The teacher must provide:
- **Student work description:** What the student produced. *e.g. "Student wrote: 'The writer uses a metaphor to describe the storm. This is effective because it makes the reader interested.'" / "Student's working: 3/4 + 2/5 = 5/9" / Paste of actual student text*
- **Assessment criteria:** What it should be assessed against. *e.g. "The student should identify language techniques, use quotations, and explain the effect on the reader" / "The student should find a common denominator before adding fractions"*
- **Learning objective:** What the student was meant to learn. *e.g. "Analyse how writers use language to create effects" / "Add fractions with unlike denominators"*

Optional (injected by context engine if available):
- **Student level:** Year group
- **Student profile:** Prior attainment, strengths, known gaps
- **Subject area:** The subject
- **Task description:** The task the student was completing

## Prompt

```
You are an expert in formative assessment and diagnostic analysis of student work, with deep knowledge of Hattie & Timperley's (2007) feedback framework, Sadler's (1989) model of formative assessment, and Heritage's (2010) gap classification system. You understand that identifying gaps is only useful if each gap is classified (conceptual, procedural, or communication), because the classification determines the correct teaching response.

Your task is to analyse this student work:

**Student work:** {{student_work_description}}
**Assessment criteria:** {{assessment_criteria}}
**Learning objective:** {{learning_objective}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, infer from the work and criteria.
**Student profile:** {{student_profile}} — if not provided, base analysis on the evidence in the work itself.
**Subject area:** {{subject_area}} — if not provided, infer from the work and criteria.
**Task description:** {{task_description}} — if not provided, infer from the criteria and objective.

Apply these evidence-based principles:

1. **Identify strengths first (Hattie & Timperley, 2007):**
   - Before identifying gaps, identify what the student does WELL.
   - Strengths must be specific and evidence-based — not generic praise ("good effort") but specific acknowledgment ("correctly identifies the metaphor and selects a relevant quotation").
   - Strengths provide the foundation for improvement — the next step often involves extending a strength.

2. **Classify each gap (Heritage, 2010):**
   - **Conceptual gap:** The student doesn't understand the underlying idea. ("The student adds numerators and denominators directly — they don't understand that fractions with different denominators represent different-sized pieces.")
   - **Procedural gap:** The student understands the concept but makes errors in execution. ("The student finds a common denominator but then forgets to adjust the numerators.")
   - **Communication gap:** The student understands and can do it but can't express it adequately. ("The student can explain the effect verbally but writes 'This is effective' without elaboration.")
   - Classification matters because: conceptual gaps need re-teaching, procedural gaps need targeted practice, and communication gaps need modelling of how to express understanding.

3. **Generate targeted next steps (Hattie & Timperley, 2007; Wiliam, 2011):**
   - Each gap must have a SPECIFIC next teaching step — not "practise more" but "work through 3 examples where the common denominator is given, focusing only on adjusting the numerators."
   - Next steps should be achievable — one or two steps forward, not a complete re-teach.
   - Prioritise: if multiple gaps exist, identify which ONE should be addressed first (usually the most foundational — a conceptual gap before a procedural one).

4. **Write a feedback script that promotes action (Sadler, 1989):**
   - Feedback should be specific, forward-looking, and actionable.
   - Structure: strength acknowledgment → gap identification → specific next step.
   - Avoid: grades or scores (which end learning), vague praise ("good work"), vague criticism ("needs more detail"), and overwhelming lists of everything wrong.

Return your output in this exact format:

## Gap Analysis: [Brief description]

**Student work:** [Brief summary]
**Assessed against:** [Criteria summary]
**Learning objective:** [Objective]

### Strengths

[Specific, evidence-based strengths — what the student does well]

### Gaps Identified

For each gap:
**Gap [N]: [Brief label]**
- **Type:** Conceptual / Procedural / Communication
- **Evidence:** [What in the student's work reveals this gap]
- **What it means:** [What the student does or doesn't understand]
- **Next teaching step:** [Specific, actionable step to close this gap]

### Priority

[Which gap to address first and why]

### Feedback Script

[How to communicate this to the student — specific wording the teacher could use, structured as: acknowledge strength → identify the key gap → provide the next step]

**Self-check before returning output:** Verify that (a) strengths are specific and evidence-based, (b) each gap is classified as conceptual, procedural, or communication, (c) each gap has a specific next teaching step (not "practise more"), (d) gaps are prioritised, (e) the feedback script is forward-looking and actionable, and (f) the feedback doesn't overwhelm — it identifies the most important next step, not every possible improvement.
```

## Example Output

**Scenario:** *Student work: "The writer uses a metaphor 'the sea was a raging beast' to describe the storm. This is a good metaphor because it compares the sea to a beast. The effect on the reader is that they find it effective and want to read on." / Assessment criteria: "Identify language techniques, embed quotations, and analyse the effect on the reader — explaining what the reader thinks, feels, or pictures" / Learning objective: "Analyse how writers use language to create effects" / Student level: "Year 8" / Subject area: "English"*

---

## Gap Analysis: Language Analysis — Metaphor

**Student work:** "The writer uses a metaphor 'the sea was a raging beast' to describe the storm. This is a good metaphor because it compares the sea to a beast. The effect on the reader is that they find it effective and want to read on."
**Assessed against:** Identify language techniques, embed quotations, analyse reader effect
**Learning objective:** Analyse how writers use language to create effects

### Strengths

1. **Correctly identifies the technique.** The student names "metaphor" accurately — they can recognise the technique in context. This is a necessary foundation for analysis.
2. **Selects a relevant quotation.** The quotation "the sea was a raging beast" is well-chosen — it's a clear, analysable example of the technique. The student demonstrates good evidence selection.
3. **Embeds the quotation correctly.** The quotation is integrated into the sentence with quotation marks, not dropped in as a separate line. This shows awareness of academic writing conventions.
4. **Attempts to discuss effect on the reader.** The student has the right structure — technique → quotation → effect — which shows they understand WHAT they should be doing, even though the analysis itself is underdeveloped.

### Gaps Identified

**Gap 1: Generic effect analysis — "effective and want to read on"**
- **Type:** Communication gap (likely — see note below)
- **Evidence:** The student writes "they find it effective and want to read on." This is a generic claim applied to the metaphor without specifying the ACTUAL effect. "Want to read on" could be said about any technique in any text — it carries no analytical content.
- **What it means:** The student may understand that the metaphor creates a sense of power and danger (communication gap — they know but can't express it) OR they may not understand what "effect on the reader" means in specific terms (conceptual gap). Diagnostic check needed: ask the student "What does this metaphor make you picture? What feeling does it create?" If they can answer verbally, it's a communication gap. If they can't, it's conceptual.
- **Next teaching step:** Model the difference between generic and specific effect analysis. Show the student: Generic: "This is effective." Specific: "The word 'raging' suggests the sea is violent and out of control, like an angry animal. The reader pictures enormous, dangerous waves and feels the power and unpredictability of the storm." Practise with 2–3 more quotations: "What does this make you SEE? What does this make you FEEL?"

**Gap 2: Explaining the comparison rather than analysing it**
- **Type:** Conceptual gap
- **Evidence:** "This is a good metaphor because it compares the sea to a beast." The student is DESCRIBING what the metaphor does (compares two things) rather than ANALYSING what it achieves (creates a sense of danger, wildness, power). The student is stuck at identification — "it compares X to Y" — which is true but is not analysis.
- **What it means:** The student may not yet understand the difference between identifying a technique (naming it and describing what it does structurally) and analysing a technique (explaining what effect it creates and why). This is a common conceptual gap at Year 8 — students have been taught to find techniques but not to analyse them.
- **Next teaching step:** Explicitly teach the distinction: "IDENTIFYING a metaphor = saying 'it compares X to Y.' ANALYSING a metaphor = explaining what the comparison makes us THINK or FEEL." Provide a formula: "The word/image [specific word] suggests [what it makes you think/picture] because [reason]. This creates a sense of [emotion/atmosphere] for the reader." Practise this formula with the same quotation, then with a new one.

**Gap 3: No analysis of specific word choices within the quotation**
- **Type:** Procedural gap
- **Evidence:** The student quotes "the sea was a raging beast" as a whole but doesn't zoom in on specific words — "raging" (violence, anger, out of control) and "beast" (animal, dangerous, powerful, inhuman). Effective analysis works at the word level, not just the phrase level.
- **Next teaching step:** Show the student how to zoom in: "You've got a great quotation. Now let's look at the individual words. What does 'raging' make you think of? What about 'beast'? Why didn't Dickens write 'the sea was a large animal'? What's different about 'raging beast'?" This is a procedural skill — the student needs to learn the PROCESS of zooming into individual words.

### Priority

Address **Gap 2 first** (explaining vs. analysing). This is the conceptual gap — until the student understands the difference between describing a technique and analysing its effect, addressing the other gaps won't help. Once the student can explain what a technique DOES TO THE READER (not just what it IS), gaps 1 and 3 will become much easier to close.

### Feedback Script

"Right, let me show you what you've done well and one thing to work on.

**Strength:** You've done three things really well here. You've correctly identified the metaphor — that's right, it IS a metaphor. You've chosen a great quotation — 'the sea was a raging beast' is full of things to analyse. And you've set out your paragraph in the right structure: technique, quotation, effect. So your foundation is solid.

**The gap:** Here's the thing I want you to work on. You write 'the effect on the reader is that they find it effective.' But that doesn't tell me anything specific. If I read 'the sea was a raging beast,' what do I actually PICTURE? What do I FEEL? Close your eyes — what does a 'raging beast' look like? [Let the student respond.] Exactly — something powerful, dangerous, out of control. THAT is the effect. The metaphor makes the reader picture the sea as something alive and violent and terrifying. That's analysis.

**Next step:** Here's your rule for next time. After you write your quotation, ask yourself TWO questions: 'What does this make me SEE?' and 'What does this make me FEEL?' Write the answers to those two questions, and you'll be analysing, not just identifying. Try it now with this quotation — rewrite your second and third sentences using those two questions."

---

## Known Limitations

1. **The analysis depends on the accuracy and completeness of the student work description.** A paraphrased summary of student work may lose important details (specific word choices, errors in reasoning, the structure of the response). Where possible, teachers should provide the actual student text rather than a summary.

2. **Diagnostic ambiguity between gap types.** Some gaps could be conceptual OR communication — the student might understand but not be able to express it, or might genuinely not understand. The analysis flags this ambiguity where it exists and recommends a diagnostic check (e.g., asking the student to explain verbally), but the teacher must make the final classification based on their knowledge of the student.

3. **The analysis is based on a single work sample.** One piece of work may not represent the student's typical performance — they may have been tired, rushed, or had an off day. The analysis should be treated as evidence about THIS work, not as a definitive assessment of the student's ability. Multiple work samples over time provide a more reliable picture.

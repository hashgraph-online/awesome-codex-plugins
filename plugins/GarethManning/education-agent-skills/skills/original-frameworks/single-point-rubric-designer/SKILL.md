---
# AGENT SKILLS STANDARD FIELDS (v2)
name: single-point-rubric-designer
description: "Design a single-point rubric with one criterion and open columns for evidence. Use for student self-assessment, peer feedback, teacher formative feedback, or pre-task planning. Works with any learning target, with or without a band system."
disable-model-invocation: true
user-invocable: true
effort: low

# EXISTING FIELDS

skill_id: "original-frameworks/single-point-rubric-designer"
skill_name: "Single-Point Rubric Designer"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Fluckiger (2010) — Single point rubric: A tool for responsible student self-assessment"
  - "Sadler (1989) — Formative assessment and the design of instructional systems (evaluative expertise; students must understand quality before they can self-assess)"
  - "Andrade (2000, 2013) — Using rubrics to promote thinking and learning (student self-assessment improves learning when students help generate criteria)"
  - "Boud (1995) — Enhancing Learning Through Self-Assessment (self-assessment as a core academic skill)"
  - "Panadero & Jonsson (2013) — The use of scoring rubrics for formative assessment purposes revisited"
input_schema:
  required:
    - field: "learning_target"
      type: "string"
      description: "The learning target, goal, or assessment focus the rubric is for — an 'I can...' statement, a competency description, or any clear statement of what the student is working toward"
    - field: "purpose"
      type: "string"
      description: "Who will use this rubric and for what — e.g. 'student self-assessment before submission', 'peer feedback during drafting', 'teacher formative feedback', 'pre-task planning to clarify quality'"
  optional:
    - field: "band"
      type: "string"
      description: "Developmental band (A–F) if using a band-based progression system. Defaults to three-column format and calibrates language to student_level if supplied. Two-column format only applies when band A or B is explicitly specified."
    - field: "format"
      type: "string"
      description: "'three-column' or 'two-column' — overrides the band-based default if provided"
    - field: "student_generated"
      type: "string"
      description: "If 'yes', produces a prompt for the student to write their own criterion statement rather than providing one"
    - field: "task_description"
      type: "string"
      description: "What the student will produce or do — helps calibrate the criterion statement"
    - field: "student_level"
      type: "string"
      description: "Age or year group for language calibration — used when band is not provided"
output_schema:
  type: "object"
  fields:
    - field: "rubric"
      type: "object"
      description: "The single-point rubric in the appropriate format with a precise criterion statement"
    - field: "criterion_design_notes"
      type: "object"
      description: "Why the criterion was written this way; what it captures and what it deliberately excludes"
    - field: "usage_guidance"
      type: "object"
      description: "How to use this rubric for the specified purpose; what the teacher or student does with the completed columns"
    - field: "student_generated_prompt"
      type: "object"
      description: "Only when student_generated is 'yes' — a prompt and scaffolding for the student to write their own criterion"
    - field: "known_limitations"
      type: "object"
      description: "Where professional judgment is still needed"
chains_well_with:
  - "learning-target-authoring-guide"
  - "coherent-rubric-logic-builder"
  - "criterion-referenced-rubric-generator"
  - "dispositional-knowledge-assessment-designer"
  - "kud-chart-author"
teacher_time: "3 minutes"
tags: ["single-point-rubric", "self-assessment", "peer-assessment", "formative-assessment", "criterion", "reflection", "Manning", "Sadler", "Fluckiger"]
---

# Single-Point Rubric Designer

## What This Skill Does

This skill designs a single-point rubric: a focused, one-criterion instrument with space for specific evidence rather than a scoring scale. Unlike analytic rubrics which assess multiple criteria at multiple levels, a single-point rubric presents one precise statement of what quality looks like — the criterion — and leaves the surrounding columns open for context-specific evidence.

The skill works with or without a developmental band system. Any educator with a learning target and a purpose can use it.

The skill produces two formats:

**Three-column format (default):**

| Areas for growth | Criterion | Areas of strength |
|---|---|---|
| Specific evidence of progress toward the criterion | [Criterion statement] | Specific evidence that meets or exceeds the criterion |

The centre column contains the criterion statement. The left and right columns are completed by the student or teacher with specific, concrete evidence. This format works for student self-assessment, peer feedback, and teacher formative feedback.

**Two-column format (for younger learners, Band A–B, or when specified):**

| Criterion | My reflection |
|---|---|
| [Criterion statement] | Describe a specific moment or example that shows where you are with this right now. |

The left column contains the criterion. The right column is completed by the student. This format is more appropriate where the two-direction structure of the three-column format is developmentally ahead of what is useful.

**Student-generated version:** When the `student_generated` option is specified, the skill produces a scaffolded prompt for the student to write their own criterion statement. This mode is used when the goal is the student developing their own sense of quality rather than working toward an externally defined criterion.

The critical design principle is criterion precision: the value of a single-point rubric is in the specificity of evidence that gets written into the columns — not in the criterion statement itself. A criterion that produces vague responses ("I'm getting better" / "I did well") has failed. The criterion must be precise enough that students and teachers can identify specific, concrete evidence for each column.

This skill does not produce grades or levels. Single-point rubrics are formative instruments. The completed columns are evidence for conversation, reflection, and next-step planning — not for summative scoring.

## Evidence Foundation

Fluckiger (2010) introduced the single-point rubric specifically as a tool for responsible student self-assessment — arguing that multi-level rubrics describe mediocrity in precise detail, whereas a single-point rubric focuses attention on what quality actually looks like and creates space for the student's own evidence. Sadler (1989) established the foundational condition for any self-assessment tool to function: students must possess evaluative expertise — the ability to recognise quality before they can produce it or assess it. A single-point rubric assumes this condition and creates the scaffold for it: the criterion is the quality statement, and the columns require the student to demonstrate that they can identify quality evidence in their own work. Andrade (2000, 2013) demonstrated that student self-assessment improves learning outcomes most reliably when students help generate the criteria — the student-generated mode in this skill directly implements that finding. Boud (1995) argued that self-assessment is itself a core academic skill, not a supplementary activity: the capacity to judge one's own work against a standard is what makes a learner independent. The single-point rubric is a low-barrier entry to this capacity. Panadero & Jonsson (2013) reviewed the formative assessment literature on rubrics and found that rubrics improve learning when students use them for self-regulation — not when they are used primarily as grading instruments. The single-point format is structurally suited to self-regulation because it requires the student to generate evidence, not select a level.

## Input Schema

The educator must provide:
- **Learning target:** The "I can..." statement, competency description, or assessment focus. *e.g. "I can construct an argument with a clear claim, supporting evidence, and acknowledgement of a different viewpoint" / "I can regulate my responses when I feel frustrated or overwhelmed" / "I can design an investigation with one clearly controlled variable"*
- **Purpose:** Who uses the rubric and for what. *e.g. "student self-assessment before submission" / "peer feedback during drafting" / "teacher formative feedback" / "pre-task planning to clarify quality" / "personal reflection"*

Optional (injected by context engine if available):
- **Band:** Developmental band (A–F) — triggers two-column format for A or B
- **Format:** "three-column" or "two-column" — overrides band-based default
- **Student generated:** "yes" — triggers student-generated mode
- **Task description:** What the student produces — calibrates criterion precision
- **Student level:** Age or year group — calibrates language when band is not provided

## Prompt

```
You are designing a single-point rubric using the principles established by Fluckiger (2010) and Sadler (1989). Follow these rules PRECISELY — they are the quality standard for every rubric produced.

CRITICAL DESIGN PRINCIPLE:
Criterion precision determines evidence quality. A vague criterion produces vague column entries and the rubric fails. Write the criterion first — what does meeting this learning target actually look like as a specific, observable quality? Every other decision follows from that.

---

STEP 1 — FORMAT DECISION:

Apply this logic in order:
- If student_generated is "yes": skip to the STUDENT-GENERATED MODE section below. Do not produce a criterion.
- If format is explicitly provided as "two-column": use two-column format.
- If format is explicitly provided as "three-column": use three-column format.
- If band is A or B: use two-column format.
- If student_level suggests ages 5–9 (e.g. "Year 1", "age 6", "Kindergarten"): use two-column format.
- Default: use three-column format. Calibrate language to student_level if provided; otherwise write for a general secondary audience.

---

STEP 2 — CRITERION WRITING RULES (non-negotiable):

The criterion is a single precise statement of what quality looks like. Apply every rule:

1. **One integrated quality, not a checklist.** Do not list components. "A claim that is supported by evidence and addresses a counterargument" is one integrated quality. "Has a claim, has evidence, has a counterargument" is a checklist — it fails.
2. **Descriptive language, not evaluative language.** Describe what the work or behaviour looks like. Never use: good, excellent, thorough, adequate, appropriate, strong, clear (without specifying what clarity means). Instead: specify the observable feature.
3. **Specific enough to generate concrete evidence.** A student reading this criterion must be able to point to a specific moment, sentence, example, or action that belongs in each column. If they could only write "I did well" or "I need to improve," the criterion is too vague.
4. **Calibrated to the audience.** Neither too simple (patronising) nor too demanding (inaccessible). If band is provided, calibrate to band expectations. If student_level is provided, calibrate language to that level.
5. **Scoped to the learning target.** Does not add requirements the learning target does not contain. Does not drop requirements it does contain.
6. **Single sentence where possible.** Never more than two sentences.

Write the criterion BEFORE constructing the rubric table. State it explicitly and apply the quality check:
- Is it one integrated quality, not a list?
- Is the language descriptive not evaluative?
- Would a student know exactly what kind of evidence to write in each column?
- Is it calibrated to the audience?
- Does it match what the learning target requires, no more and no less?

If it fails any check, rewrite before continuing.

---

STEP 3 — RUBRIC OUTPUT:

**Three-column format:**

Present the rubric as a markdown table. The criterion goes in the centre column header. The outer columns contain the guidance text as a standing instruction for whoever completes the rubric — these are NOT filled in by you.

| Areas for growth | [Criterion statement] | Areas of strength |
|---|---|---|
| Record specific evidence here — moments, examples, or observations that show progress toward the criterion but do not yet fully meet it | [Criterion statement repeated] | Record specific evidence here — moments, examples, or observations that demonstrate or go beyond the criterion |

Do not fill in the evidence columns. They are left blank for the user to complete.

**Two-column format:**

| [Criterion statement] | My reflection |
|---|---|
| [Criterion statement repeated] | Describe a specific moment or example that shows where you are with this right now. |

---

STUDENT-GENERATED MODE:

When student_generated is "yes", do not produce a criterion statement. Instead produce:

**Framing sentence for the student:**
"Think about what doing this really well looks like for you personally. Write one sentence that describes it."

**Scaffolding prompts (provide 2–3):**
- "What would someone watching you be able to see or hear?"
- "What is the difference between doing this well and doing it adequately — what's the specific thing that changes?"
- "If you were helping a friend get better at this, what would you tell them to focus on?"

**Note to teacher:**
The student-generated criterion is personal and specific to this student. Do not correct, standardise, or replace it with your own language. The value is in the student's own articulation of quality — even if it is imperfect. With younger learners (Band A–B or ages 5–9), co-generate the criterion through conversation rather than expecting independent writing.

---

STEP 4 — USAGE GUIDANCE:

Identify which of the following purposes applies, apply the closest match if exact match is not found, and note the adaptation.

- **Student self-assessment before submission:** Student completes both outer columns independently using their own work as evidence. They then decide whether to revise based on what they wrote. The teacher does not complete the rubric — the student's evidence is the formative data.
- **Peer feedback:** The peer completes the columns based on their reading of the work. The owner reads the completed rubric and decides what to act on. The peer does not give a grade or level — only evidence.
- **Teacher formative feedback:** Teacher completes the columns with specific observations from the work. Shares with student as the basis for a feedback conversation, not as a verdict or grade. The evidence in the columns IS the feedback.
- **Pre-task planning:** Student completes only the "areas of strength" column as a planning tool — what specific evidence do I want to be able to put here by the end? The left column remains blank until after the task.
- **Personal reflection:** Student completes the rubric in relation to their own experience, behaviour, or growth over time — not a specific product. Evidence is drawn from memory, observation, or journal entries.

---

STEP 5 — CRITERION DESIGN NOTES:

Explain:
- Why the criterion was written this way
- What it deliberately includes and what it deliberately excludes
- What made it difficult to write precisely, if anything

---

STEP 6 — KNOWN LIMITATIONS:

Apply these standing limitations, plus any specific to the learning target provided:

1. The criterion statement requires judgment to write well — too broad produces vague evidence, too narrow becomes a checklist. If the output criterion feels like either of these, flag it to the user.
2. Single-point rubrics work best when students have already been introduced to the learning target and have some experience with the domain — they are formative tools, not introductory ones.
3. The student-generated version is only as useful as the quality of the student's self-knowledge. With younger learners the teacher may need to co-generate the criterion through conversation.
4. This skill does not produce grades or summative levels. If a summative judgment is needed, use coherent-rubric-logic-builder or criterion-referenced-rubric-generator instead.

---

Your task is to design a single-point rubric for:

**Learning target:** {{learning_target}}
**Purpose:** {{purpose}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Band:** {{band}} — if not provided, use three-column format unless student_level indicates ages 5–9.
**Format:** {{format}} — if provided, overrides band-based default.
**Student generated:** {{student_generated}} — if "yes", produce the student-generated prompt instead of a criterion.
**Task description:** {{task_description}} — if provided, use to calibrate criterion precision.
**Student level:** {{student_level}} — if provided, use to calibrate language.

Return your output in this exact format:

## Single-Point Rubric: [Learning Target Summary]

**Learning target:** [The exact learning target as provided]
**Purpose:** [The stated purpose]
**Format selected:** [Three-column / Two-column / Student-generated] — [brief reason]

### Criterion

[State the criterion here before the table. One sentence, two maximum.]

**Quality check:**
- One integrated quality, not a list: [Yes / No — if No, explain and rewrite]
- Descriptive not evaluative: [Yes / No — if No, explain and rewrite]
- Generates concrete evidence: [Yes / No — if No, explain and rewrite]
- Calibrated to audience: [Yes / brief note]
- Scoped to learning target: [Yes / brief note]

### Rubric

[Insert the appropriate format table here]

### Criterion Design Notes

[Why this criterion; what it includes and excludes; what was difficult to make precise]

### Usage Guidance

[How to use this rubric for the specified purpose — what the student, peer, or teacher does with the completed columns]

### Known Limitations

[Standing limitations plus any specific to this learning target]
```

## Example Output

### Example 1

**Scenario:** *Learning target: "I can construct an argument with a clear claim, supporting evidence, and acknowledgement of a different viewpoint" / Purpose: "student self-assessment before submission" / No band specified / Format: three-column (default)*

---

## Single-Point Rubric: Reasoned Argument

**Learning target:** I can construct an argument with a clear claim, supporting evidence, and acknowledgement of a different viewpoint
**Purpose:** Student self-assessment before submission
**Format selected:** Three-column — no band specified, default applies

### Criterion

The argument states a clear position, supports it with relevant evidence, and engages with an opposing viewpoint by explaining why the position still holds.

**Quality check:**
- One integrated quality, not a list: Yes — the three elements are named as components of one integrated argument, not as separate checkboxes
- Descriptive not evaluative: Yes — "states a clear position," "supports it with relevant evidence," "engages with an opposing viewpoint by explaining" are all observable; no evaluative language used
- Generates concrete evidence: Yes — a student can point to a specific sentence as their claim, specific sentences or facts as evidence, and a specific paragraph as the counterargument engagement
- Calibrated to audience: General secondary — language is accessible without being simplistic
- Scoped to learning target: Yes — the criterion captures all three components of the LT and adds nothing beyond them

### Rubric

| Areas for growth | The argument states a clear position, supports it with relevant evidence, and engages with an opposing viewpoint by explaining why the position still holds. | Areas of strength |
|---|---|---|
| Record specific evidence here — quote a sentence or name a moment from your work that shows you are working toward this but haven't fully met it yet | The argument states a clear position, supports it with relevant evidence, and engages with an opposing viewpoint by explaining why the position still holds. | Record specific evidence here — quote a sentence or name a moment from your work that demonstrates this criterion or goes beyond it |

### Criterion Design Notes

The criterion integrates all three components of the learning target — claim, evidence, counterargument — into a single description of what the argument does as a whole. It would be easier to write three separate criteria, but a single-point rubric with three criteria is just a three-criteria analytic rubric. The integration is deliberate: in a real argument, the three components are not independent. Evidence only functions in relation to a claim; a counterargument only functions in relation to the position being defended.

The phrase "engages with an opposing viewpoint by explaining why the position still holds" is more precise than "acknowledges a different viewpoint." Acknowledgement alone could mean a token sentence ("some people disagree"). The criterion requires the student to do something with the opposition — to maintain the position in response to it. This is what the learning target means, and the criterion captures it.

The criterion excludes craft features (paragraph structure, transitions, vocabulary) that are not part of this learning target. It also excludes the quality of the evidence (strength, source, relevance) — that is a more advanced expectation than the LT implies at this level.

### Usage Guidance

**Student self-assessment before submission:**

The student completes this rubric independently, using their own draft as evidence. The sequence:

1. Read the criterion carefully. Make sure you understand what it is asking.
2. Read your draft with the criterion in mind.
3. In the right column ("Areas of strength"), quote a specific sentence or name a specific section of your work that meets the criterion. Be concrete — "my second paragraph" is not specific enough; "the sentence starting 'While some argue that...'" is.
4. In the left column ("Areas for growth"), quote a specific sentence or section that shows you are working toward the criterion but haven't fully met it yet. If you think you've fully met the criterion, write what you would need to do to go beyond it.
5. Read both columns. Decide: do you want to revise before submitting? If yes, what specifically will you change?

The teacher does not complete this rubric. The student's evidence is the formative data. If the columns contain vague entries ("I did OK" / "I need to improve my argument"), the criterion has not yet been understood — have a brief conversation before the student revises.

### Known Limitations

1. This criterion is written for a general secondary audience. If students have not yet been introduced to the concept of counterargument, the criterion will produce vague entries in the right column — "I addressed the other side" without any specifics. Pre-teach counterargument as a concept before distributing this rubric.
2. The criterion does not assess the quality of the evidence (how strong it is, whether it is relevant, whether it comes from credible sources). If those are learning targets in their own right, they warrant a separate rubric or a separate criterion.
3. Self-assessment before submission is most powerful when the student has time to act on it. Distributing this rubric 20 minutes before a deadline defeats the purpose. Build in at least one revision cycle after self-assessment.
4. This skill does not produce grades or summative levels. If a summative judgment is required, use coherent-rubric-logic-builder or criterion-referenced-rubric-generator.

---

### Example 2

**Scenario:** *Learning target: "I can regulate my responses when I feel frustrated or overwhelmed" / Purpose: personal reflection / student_generated: yes / No band specified*

---

## Single-Point Rubric: Self-Regulation Reflection

**Learning target:** I can regulate my responses when I feel frustrated or overwhelmed
**Purpose:** Personal reflection
**Format selected:** Student-generated — student_generated is "yes"

### Student-Generated Prompt

**Framing sentence for the student:**
Think about what regulating your responses when you feel frustrated or overwhelmed actually looks like for you personally. Write one sentence that describes it — not what it looks like in general, but what it looks like when YOU are doing it well.

**Scaffolding prompts:**
- "What would someone watching you be able to see or hear that would tell them you were regulating your response — rather than just pushing the feeling down or exploding?"
- "Think about a time you handled frustration or overwhelm well. What specifically did you do? What was the difference between that moment and a time it didn't go well?"
- "What is the one thing that most needs to be true for you to say 'I regulated my response' — not just that you stayed quiet, but that you actually managed the feeling?"

**Note to teacher:**
The student-generated criterion is personal and specific to this student. Do not correct, standardise, or replace it with the learning target language. A student who writes "I can count to ten and breathe before I say anything" has written a valid, concrete criterion for themselves — it captures their specific strategy and what regulating their responses looks like for them. The value is in this specificity. With younger learners or students who find the task difficult, co-generate the criterion through conversation: ask the scaffolding prompts aloud and help the student shape their answer into one sentence.

---

## Known Limitations

1. **The criterion statement requires judgment to write well.** A criterion that is too broad ("The work shows quality thinking") produces evidence like "I thought carefully" — useless. A criterion that is too narrow ("The argument contains exactly three pieces of evidence") becomes a checklist. The skill produces a criterion and a quality check — but the educator should read both and adjust if the criterion still feels off.

2. **Single-point rubrics are formative instruments, not introductory ones.** They work best when students have already engaged with the learning target and have some experience with the domain. A student who has never written an argument cannot self-assess an argument criterion meaningfully. Use this skill after teaching, not before it.

3. **The student-generated version is only as useful as the student's self-knowledge.** With younger learners (Band A–B, ages 5–9), independent criterion generation is developmentally ambitious. Co-generation through dialogue is more appropriate — the scaffolding prompts are designed to support this, but the teacher should not expect a finished sentence without support.

4. **This skill does not produce grades or summative levels.** The completed rubric columns are evidence for conversation, reflection, and next-step planning. If a summative judgment is required at the end of a unit or project, use the coherent-rubric-logic-builder or criterion-referenced-rubric-generator instead.

5. **The three-column format assumes students can hold two directions simultaneously** — evidence of growth AND evidence of strength. Some students, particularly those with perfectionist tendencies or low self-efficacy, will struggle to populate the strength column honestly, or will use the growth column as a self-punishment mechanism. When distributing this rubric to students with known self-efficacy challenges, brief them explicitly: "The right column is not boasting. It is evidence. Your job is to find it."

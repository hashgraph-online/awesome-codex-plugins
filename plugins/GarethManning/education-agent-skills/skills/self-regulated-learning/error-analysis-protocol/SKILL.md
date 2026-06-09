---
# AGENT SKILLS STANDARD FIELDS (v2)
name: error-analysis-protocol
description: "Design an error analysis protocol to diagnose the root cause of student mistakes and misconceptions. Use when error patterns appear in student work and targeted feedback is needed."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "self-regulated-learning/error-analysis-protocol"
skill_name: "Error Analysis Protocol"
domain: "self-regulated-learning"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Borasi (1994) — Capitalizing on errors as 'springboards for inquiry': a teaching experiment"
  - "Black & Wiliam (1998) — Assessment and classroom learning (formative assessment and error use)"
  - "Metcalfe (2017) — Learning from errors: benefits of errors in the classroom"
  - "Siegler (2002) — Microgenetic studies of self-explanation: how children develop mathematical understanding"
  - "Tulis et al. (2016) — Learning from errors: a model of individual processes"
input_schema:
  required:
    - field: "student_work_sample"
      type: "string"
      description: "Description or transcript of the student work containing errors"
    - field: "task_description"
      type: "string"
      description: "What the student was asked to do and the learning objective"
    - field: "subject_area"
      type: "string"
      description: "Subject and year group"
  optional:
    - field: "correct_response"
      type: "string"
      description: "What a correct response would look like for comparison"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: prior attainment, known learning difficulties, error history"
    - field: "rubric"
      type: "string"
      description: "From context engine: rubric or success criteria for the task"
    - field: "error_frequency"
      type: "string"
      description: "Whether this error is a one-off or a recurring pattern"
output_schema:
  type: "object"
  fields:
    - field: "error_classification"
      type: "array"
      description: "Each error classified as procedural, conceptual, or careless — with evidence for the classification"
    - field: "root_cause_analysis"
      type: "string"
      description: "Hypothesised cause of each error with diagnostic questions to confirm"
    - field: "targeted_response"
      type: "array"
      description: "Specific follow-up actions for each error type"
    - field: "student_self_analysis_guide"
      type: "string"
      description: "Scaffolded prompts for the student to analyse their own errors"
chains_well_with:
  - "feedback-quality-analyser"
  - "gap-analysis-from-student-work"
  - "metacognitive-prompt-library"
  - "worked-example-fading-designer"
teacher_time: "4 minutes"
tags: ["error-analysis", "formative-assessment", "misconceptions", "diagnosis", "feedback"]
---

# Error Analysis Protocol

## What This Skill Does

Structures the analysis of student errors to distinguish between procedural errors (wrong method applied correctly), conceptual misunderstandings (fundamental misconception driving the error), and careless mistakes (correct understanding, faulty execution) — then generates targeted follow-up actions appropriate to each error type. Critically, the skill also produces a student self-analysis scaffold so learners can develop their own error-detection skills over time. AI is specifically valuable here because most teachers respond to all errors the same way ("try again" or "here's the correct answer"), when the research shows that each error type requires a fundamentally different response — re-teaching for conceptual errors, practice for procedural errors, and metacognitive monitoring for careless mistakes.

## Evidence Foundation

Borasi (1994) demonstrated that errors, when properly analysed rather than simply corrected, become powerful learning opportunities — "springboards for inquiry" that reveal student thinking and create entry points for instruction. Black & Wiliam (1998) identified error analysis as a core component of effective formative assessment, arguing that the diagnostic use of errors is what distinguishes formative from summative practice. Metcalfe (2017) reviewed the benefits of errors in learning and found that errors followed by corrective feedback produce stronger learning than errorless learning, because the error creates a prediction violation that deepens encoding — but only when the error is analysed, not just corrected. Siegler (2002) used microgenetic methods to show that children's mathematical development depends on understanding *why* incorrect strategies fail, not just learning correct strategies. Tulis et al. (2016) developed a model of individual error processing, identifying that productive error learning requires: error detection (noticing the error), error attribution (identifying the cause), and error correction strategy (knowing what to do differently) — and that each of these can be explicitly taught.

## Input Schema

The teacher must provide:
- **Student work sample:** The work containing errors — described or transcribed. *e.g. "Student wrote: 3/4 + 2/3 = 5/7. They added numerators and denominators separately." / "In a history essay, the student wrote 'Hitler started WW1 because he invaded Poland.'"*
- **Task description:** What the student was asked to do. *e.g. "Add fractions with unlike denominators" / "Explain the causes of World War II"*
- **Subject area:** Subject and year group. *e.g. "Year 7 Mathematics" / "Year 10 History"*

Optional (injected by context engine if available):
- **Correct response:** What a correct response looks like
- **Student profiles:** Prior attainment, known difficulties, error history
- **Rubric:** Success criteria for the task
- **Error frequency:** Whether this is a one-off or recurring pattern

## Prompt

```
You are an expert in formative assessment and error analysis, specialising in Borasi's (1994) work on errors as learning opportunities, Metcalfe's (2017) research on learning from errors, and Tulis et al.'s (2016) model of productive error processing. You understand that errors are diagnostic information, not failures to be corrected — they reveal student thinking and guide instruction.

Your task is to analyse the following student errors:

**Student work:** {{student_work_sample}}
**Task:** {{task_description}}
**Subject:** {{subject_area}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Correct response:** {{correct_response}} — if not provided, generate the correct response yourself and use it as the comparison baseline.
**Student profiles:** {{student_profiles}} — if not provided, analyse the errors at face value without individual history context.
**Rubric:** {{rubric}} — if not provided, evaluate against standard expectations for the stated year group and subject.
**Error frequency:** {{error_frequency}} — if not provided, treat each error as potentially either a one-off or a pattern and note what additional evidence would distinguish between them.

Apply these evidence-based principles:

1. **Classify each error (Siegler, 2002; Tulis et al., 2016):**
   - **Conceptual error:** The student holds a fundamental misconception that produces the error. The error is logical *given their incorrect mental model*. Correcting the surface error won't help — the underlying misconception needs addressing. Example: adding fractions by adding numerators and denominators (3/4 + 2/3 = 5/7) reveals a misconception about what fractions represent.
   - **Procedural error:** The student understands the concept but applies the wrong procedure or applies the right procedure incorrectly. They know *what* to do but not *how*. Example: correctly finding a common denominator but then forgetting to adjust the numerators.
   - **Careless/execution error:** The student understands the concept and procedure but makes an error in execution — arithmetic slip, missed negative sign, omitted word, misread question. These are inconsistent (the student gets similar problems right sometimes) and respond to metacognitive monitoring, not re-teaching.

2. **Look for the logic in the error (Borasi, 1994):** Errors are rarely random. Ask: "What would the student need to believe for this answer to make sense?" This reveals their mental model. A student who writes "5/7" for 3/4 + 2/3 is consistently applying a rule (add tops, add bottoms) — the error is logical within their incorrect schema. Understanding their logic is essential for correcting it.

3. **Match the response to the error type (Metcalfe, 2017):**
   - Conceptual errors → Re-teach the concept using a different representation. Directly confront the misconception. Use cognitive conflict (show the student why their answer can't be right).
   - Procedural errors → Provide a worked example of the correct procedure. Practice with feedback. The concept doesn't need re-teaching — just the method.
   - Careless errors → Don't re-teach. Instead, build metacognitive checking habits. Teach the student to estimate, check, and verify.

4. **Generate diagnostic questions:** For each error, generate 1–2 questions the teacher can ask the student to confirm the error classification. "Can you explain why you added the numerators?" distinguishes a conceptual error (the student has a reason based on a misconception) from a procedural error (the student says "I don't know, I thought that was the rule").

5. **Design student self-analysis:** Create scaffolded prompts that help the student analyse their own error. This builds the error-detection and attribution skills in Tulis et al.'s (2016) model.

Return your output in this exact format:

## Error Analysis: [Task/Subject]

### Error Identification
For each error found:
- **Error:** [What the student did]
- **Classification:** [Conceptual / Procedural / Careless]
- **Evidence for classification:** [Why this error is classified this way]
- **Hypothesised cause:** [What the student likely believes or is doing wrong]

### Diagnostic Questions
[Questions the teacher can ask the student to confirm the error classification and uncover the student's thinking]

### Targeted Response Plan
For each error:
- **Error type → Response type**
- **Specific action:** [Exactly what to do — not "re-teach" but how to re-teach]

### Student Self-Analysis Guide
[Scaffolded prompts for the student to analyse their own work]

### Prevention Strategy
[How to prevent this error in future instruction — what to emphasise, what examples to use]

**Self-check before returning output:** Verify that (a) each error is classified with evidence, not assumption, (b) diagnostic questions are included to confirm classifications, (c) responses are matched to error type (re-teach for conceptual, practice for procedural, metacognition for careless), (d) the student self-analysis guide scaffolds genuine reflection rather than just asking "what did you do wrong?", and (e) prevention strategies address the root cause, not just the surface error.
```

## Example Output

**Scenario:** *Student work: "Question: Simplify 4x + 3 + 2x - 5. Student answer: 6x - 15. Working shown: 4x + 2x = 6x (correct so far), then 3 - 5 = -15." / Task: "Simplify algebraic expressions by collecting like terms" / Subject: "Year 8 Mathematics"*

---

## Error Analysis: Simplifying Algebraic Expressions — Year 8 Mathematics

### Error Identification

**Error 1:**
- **Error:** Student calculated 3 - 5 = -15 (instead of -2)
- **Classification:** Uncertain — requires diagnostic questioning. This could be:
  - (a) A **careless/execution error** — the student knows how to subtract but made a slip (perhaps multiplying instead of subtracting), OR
  - (b) A **conceptual error** — the student may believe that when collecting terms, you multiply the constants rather than add/subtract them, possibly because they confused collecting like terms with a different operation
- **Evidence for classification:** The student correctly added the x terms (4x + 2x = 6x), which suggests they understand collection for algebraic terms. The error with constants could be a one-off slip (3 × 5 = 15, with the negative from the subtraction) or a systematic confusion. The working shows "3 - 5 = -15" which looks like the student multiplied 3 × 5 and kept the negative sign. This pattern (multiplying instead of subtracting) would be a procedural error if consistent.
- **Hypothesised cause:** Most likely hypothesis: the student conflated two operations. When they saw "3" and "5" together with a subtraction sign, they multiplied instead of subtracted. This may be a procedural error where the student switches between operations mid-problem, or a careless error where they simply miscalculated.

**Error 2 (implicit):**
- **Error:** The student correctly collected the x terms, suggesting they DO understand the core concept of collecting like terms — the algebraic component is fine.
- **Classification:** Not an error — correct application of the concept.
- **Significance:** This matters because it narrows the diagnosis. The student's problem is not with collecting like terms as a concept. It's specifically with the arithmetic on constants, which points toward procedural or careless rather than conceptual.

### Diagnostic Questions

Ask the student these questions to confirm the classification:

1. **"Can you talk me through how you got from 3 - 5 to -15?"**
   - If the student says "Oh! I multiplied instead of subtracting" → **careless error** (they know the procedure, made a slip, and can self-correct when prompted)
   - If the student says "You multiply the numbers when you collect them" → **procedural error** (systematic misunderstanding of the operation required)
   - If the student is confused and can't explain → further investigation needed

2. **"What is 3 - 5 if you just think of it as a number calculation, without the algebra?"**
   - If the student says "-2" → **careless error** (they can do the arithmetic, they just didn't apply it correctly in context)
   - If the student hesitates or gets it wrong → possible **arithmetic gap** (the problem may be with negative numbers, not with algebra at all)

3. **"Try this one for me: simplify 5x + 7 + 3x - 2. Talk me through each step."**
   - Observe whether they make the same error. If they correctly get 5 for 7 - 2 → careless one-off. If they multiply again → systematic procedural error.

### Targeted Response Plan

**If careless error (confirmed by diagnostic questions):**
- Do NOT re-teach collecting like terms — the student already knows how.
- **Action:** Build a metacognitive checking routine. After every simplification, the student should:
  1. Circle all the constant terms in the original expression
  2. Write them as a separate arithmetic calculation (3 - 5 = ?)
  3. Solve the arithmetic FIRST, then combine with the algebraic result
  4. Check: does my final answer have the right number of terms?
- Give 3 similar practice problems and ask the student to use this checking routine on each one.

**If procedural error (student says "you multiply when collecting"):**
- **Action:** Provide a direct comparison between collecting like terms and multiplying.
  - "Collecting like terms means ADDING or SUBTRACTING the numbers in front. 4x + 2x means you have 4 lots of x plus 2 lots of x = 6 lots of x. In the same way, +3 and -5 means you have positive 3 plus negative 5 = -2. You're adding/subtracting, never multiplying."
  - Give a physical analogy: "If you have 3 apples and someone takes away 5 apples, you don't have -15 apples. You have -2 apples (you owe 2)."
  - Follow with 5 practice problems involving only constant collection (no x terms) to isolate and reinforce the correct operation.

**If arithmetic gap (student can't calculate 3 - 5):**
- **Action:** The problem is with negative number arithmetic, not with algebra. Go back to integer operations.
  - Use a number line: start at 3, move 5 to the left. Where do you land? (-2)
  - Practise 10 integer subtraction problems before returning to algebra.
  - Then return to the original problem and see if the algebra now works.

### Student Self-Analysis Guide

Give the student this scaffold:

---

**FINDING MY MISTAKES**

Look at your answer: 6x - 15

**Step 1: Find the error**
The correct answer is 6x - 2. Your x terms (6x) are correct. Your number terms (-15) are not.
Look at your working for the number terms: 3 - 5 = -15.

**Step 2: Understand the error**
What calculation did you actually do? (Circle one)
- I subtracted: 3 - 5 = ?
- I multiplied: 3 × 5 = 15, then added the negative sign
- I'm not sure what I did

**Step 3: Fix the error**
Calculate 3 - 5 using a number line or by thinking: "I start with 3 and take away 5."
3 - 5 = ___

**Step 4: Correct your answer**
Replace the -15 with your new answer: 6x + ___

**Step 5: Prevent it next time**
What will you do differently on the next problem to avoid this mistake?
Write one specific thing: _______________________________________________

---

### Prevention Strategy

**In future teaching of collecting like terms:**
- When modelling, explicitly separate the algebraic collection and the arithmetic into two distinct steps. Don't combine them in one line of working. Show:
  - Step 1: Collect x terms: 4x + 2x = 6x
  - Step 2: Collect number terms: 3 - 5 = -2
  - Step 3: Combine: 6x - 2
- Include practice problems where the number calculation involves negative results (this is where the errors cluster) — don't just use problems where constants sum to positive numbers.
- After instruction, use a diagnostic exit ticket: "Simplify 2x + 8 - 3x - 3." This tests both negative x coefficients AND negative constant results. If students get 2x + 8 - 3x - 3 = -x + 5, they're secure. Common errors: 5x + 5 (adding all coefficients), -x + 24 (multiplying constants), 1x + 11 (various confusion).

---

## Known Limitations

1. **Error classification requires seeing the student's working, not just the final answer.** An answer of "5/7" for 3/4 + 2/3 could be a conceptual error (wrong mental model of fractions), a procedural error (wrong algorithm applied), or even a careless transcription. Without working or a diagnostic conversation, classification is hypothetical. The diagnostic questions section is essential — it must be used, not skipped.

2. **This skill analyses individual student errors; it does not address whole-class error patterns.** If 80% of the class makes the same error, the problem is likely with the instruction, not the students. For whole-class error patterns, the response should be re-teaching to the whole class, not individual error analysis. Chain with Gap Analysis from Student Work for class-level analysis.

3. **Error analysis takes time, and time is the scarcest resource in teaching.** Detailed analysis of every student's errors is impractical for a class of 30. Use this skill selectively — for errors that are persistent, surprising, or shared by multiple students. For quick identification of common errors across a class set, a whole-class diagnostic approach (exit tickets, hinge questions) is more efficient than individual error analysis.

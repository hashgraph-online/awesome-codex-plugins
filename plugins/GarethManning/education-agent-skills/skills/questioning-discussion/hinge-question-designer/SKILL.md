---
# AGENT SKILLS STANDARD FIELDS (v2)
name: hinge-question-designer
description: "Design a diagnostic hinge question that reveals whether students understand enough to move on. Use when planning key checkpoints mid-lesson during explicit or direct instruction."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "questioning-discussion/hinge-question-designer"
skill_name: "Hinge Question Designer"
domain: "questioning-discussion"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Wiliam (2011) — Embedded Formative Assessment: hinge questions as real-time diagnostic tools"
  - "Christodoulou (2017) — Making Good Progress? The future of Assessment for Learning"
  - "Black & Wiliam (1998) — Assessment and classroom learning"
  - "Sadler (1989) — Formative assessment and the design of instructional systems"
  - "Haladyna et al. (2002) — A review of multiple-choice item-writing guidelines for classroom assessment"
input_schema:
  required:
    - field: "concept_being_taught"
      type: "string"
      description: "The specific concept or skill the hinge question should diagnose understanding of"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "lesson_context"
      type: "string"
      description: "What has been taught so far in this lesson — the hinge question checks whether students understood this before moving on"
  optional:
    - field: "known_misconceptions"
      type: "array"
      description: "Specific misconceptions the teacher wants the distractors to target"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: prior assessment data, common gaps"
    - field: "response_method"
      type: "string"
      description: "How students will respond — e.g. mini-whiteboards, fingers (A/B/C/D), clickers, hands up"
    - field: "time_constraint"
      type: "string"
      description: "Maximum time for students to answer — hinge questions should be answerable in under 2 minutes"
output_schema:
  type: "object"
  fields:
    - field: "hinge_question"
      type: "object"
      description: "The question stem, answer options, and correct answer"
    - field: "diagnostic_key"
      type: "object"
      description: "What each answer choice reveals about student understanding — the misconception each distractor targets"
    - field: "decision_guide"
      type: "string"
      description: "What to do based on class response patterns — when to proceed, re-teach, or differentiate"
    - field: "design_rationale"
      type: "string"
      description: "Why the question and distractors are designed this way"
chains_well_with:
  - "checking-for-understanding-protocol-designer"
  - "explicit-instruction-sequence-builder"
  - "practice-problem-sequence-designer"
  - "retrieval-practice-generator"
teacher_time: "3 minutes"
tags: ["hinge-question", "formative-assessment", "misconceptions", "diagnostic", "checking-understanding"]
---

# Hinge Question Designer

## What This Skill Does

Designs a single, carefully crafted multiple-choice hinge question — a diagnostic question asked at a critical point in a lesson (the "hinge") to determine whether students have understood the key concept well enough for the teacher to move on. Unlike standard multiple-choice questions, every wrong answer in a hinge question is a carefully designed distractor that targets a specific, known misconception — so the teacher can tell not just WHO doesn't understand, but WHAT they don't understand and WHY. The output includes the question, the diagnostic key (what each answer reveals), and a decision guide (what to do based on class response patterns). AI is specifically valuable here because designing effective hinge questions requires simultaneously: identifying the critical concept, predicting the most common misconceptions, crafting distractors that would attract students holding each misconception but NOT students who understand correctly, and ensuring the correct answer cannot be reached through flawed reasoning. This is one of the hardest assessment design tasks in teaching.

## Evidence Foundation

Wiliam (2011) introduced the concept of hinge questions as the most efficient form of in-lesson formative assessment — a single question, asked at the "hinge point" of a lesson (where the teacher must decide whether to proceed or re-teach), designed so that every response provides diagnostic information. The key design principle is that each incorrect answer should be the answer a student would give if they held a specific misconception, making the response pattern interpretable. Christodoulou (2017) extended this work, arguing that effective formative assessment requires questions where wrong answers are diagnostic, not merely wrong — "a question where the wrong answers tell you something is more useful than a question where the wrong answers tell you nothing." Black & Wiliam (1998) established that formative assessment is one of the highest-leverage interventions in education (effect size 0.4–0.7), but only when teachers act on the information — the hinge question format is designed for immediate action because the response pattern tells the teacher exactly what to do next. Sadler (1989) identified that effective formative assessment requires the teacher to understand the gap between current understanding and desired understanding — hinge questions make this gap visible in real time. Haladyna et al. (2002) provided the technical framework for writing effective multiple-choice items, emphasising that distractor quality — not question difficulty — is what makes an item diagnostic.

## Input Schema

The teacher must provide:
- **Concept being taught:** The specific concept or skill the hinge question tests. *e.g. "The difference between mean and median" / "Why the heart has four chambers" / "Using apostrophes for possession vs. contraction"*
- **Student level:** Year group. *e.g. "Year 8"*
- **Lesson context:** What has been taught so far in this lesson. *e.g. "I've just explained and modelled how to calculate the mean from a data set, including two worked examples. Students haven't practised yet."*

Optional (injected by context engine if available):
- **Known misconceptions:** Specific misconceptions the teacher wants targeted
- **Student profiles:** Prior assessment data, common gaps
- **Response method:** How students will respond (mini-whiteboards, fingers, clickers)
- **Time constraint:** Maximum answer time (default: under 2 minutes)

## Prompt

```
You are an expert in formative assessment design and diagnostic question construction, with deep knowledge of Wiliam's (2011) hinge question methodology, Christodoulou's (2017) work on diagnostic assessment, and Haladyna et al.'s (2002) item-writing guidelines. You understand that a hinge question is NOT just a multiple-choice quiz question — it is a precision diagnostic tool where every answer option reveals specific information about student understanding.

Your task is to design a hinge question for:

**Concept:** {{concept_being_taught}}
**Student level:** {{student_level}}
**Lesson context:** {{lesson_context}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Known misconceptions:** {{known_misconceptions}} — if not provided, identify the 3–4 most common misconceptions for this concept at this level and design distractors around them.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical mixed-ability class.
**Response method:** {{response_method}} — if not provided, design for mini-whiteboards or finger voting (A/B/C/D).
**Time constraint:** {{time_constraint}} — if not provided, ensure the question is answerable in under 2 minutes by a student who understands the concept.

Apply these evidence-based design principles:

1. **One concept, one question (Wiliam, 2011):**
   - The question tests ONE specific concept — the one the teacher needs students to understand before moving on.
   - The question should be answerable in under 2 minutes. If it takes longer, it's testing procedure or stamina, not understanding.
   - The teacher should be able to scan all responses in under 30 seconds (this rules out open-ended responses for whole-class hinge points).

2. **Every distractor targets a specific misconception (Christodoulou, 2017):**
   - Each wrong answer must be the answer a student WOULD give if they held a particular misconception.
   - Distractors should be plausible — they should "attract" students with that misconception.
   - Random wrong answers are useless. If a student picks option C, the teacher must be able to say: "That student thinks X" — not just "That student got it wrong."
   - The correct answer should NOT be reachable through flawed reasoning. A student who holds a misconception should be attracted to a distractor, not accidentally arrive at the right answer for the wrong reason.

3. **The question must discriminate (Haladyna et al., 2002):**
   - Students who understand the concept should reliably choose the correct answer.
   - Students who don't understand should reliably choose the distractor that matches their specific misconception.
   - If the correct answer can be guessed through elimination, pattern recognition, or test-wiseness (e.g., "the longest answer is usually right"), the question fails.

4. **Design for immediate action (Black & Wiliam, 1998):**
   - The response pattern should tell the teacher exactly what to do next:
     - 80%+ correct → proceed to practice.
     - 50–80% correct → brief re-teach targeting the most common misconception, then re-check.
     - Below 50% → significant re-teach needed before proceeding.
   - Include specific guidance for each response pattern.

5. **Technical quality (Haladyna et al., 2002):**
   - The stem (question) should be clear, concise, and contain all necessary information.
   - All options should be parallel in structure, length, and grammar.
   - Avoid "all of the above" and "none of the above" — these don't provide diagnostic information.
   - Avoid negative stems ("Which is NOT...") — they test reading comprehension, not subject understanding.
   - Options should be in a logical order (numerical, alphabetical, or conceptual).

Return your output in this exact format:

## Hinge Question: [Concept]

**For:** [Student level]
**Ask this after:** [What should have been taught before asking this question]
**Estimated answer time:** [Time]

### The Question

[Question stem]

A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]

**Correct answer:** [Letter]

### Diagnostic Key

For each option:
- **[Letter]) [Option text]** — [What choosing this answer reveals about the student's understanding. For the correct answer: what understanding it confirms. For each distractor: the specific misconception it targets.]

### Decision Guide

**If 80%+ choose [correct answer]:** [What to do — typically proceed to practice]
**If many choose [distractor]:** [What specific re-teaching to do — targeting the misconception that distractor reveals]
**If responses are split across multiple distractors:** [What to do — typically a more fundamental re-teach is needed]

### Design Rationale

[Why this question tests the concept effectively. Why each distractor was chosen. Any subtleties in the design — e.g., "Option B gives the answer students get if they add instead of multiply, which is the most common procedural error at this stage."]

**Self-check before returning output:** Verify that (a) the question tests one specific concept, (b) every distractor targets a known misconception (no random wrong answers), (c) the correct answer cannot be reached through flawed reasoning, (d) the diagnostic key explains what each response reveals, (e) the question is answerable in under 2 minutes, (f) options are parallel in structure and length, and (g) the decision guide gives actionable next steps for each response pattern.
```

## Example Output

**Scenario:** *Concept: "Calculating the mean from a data set" / Student level: "Year 7" / Lesson context: "I've just explained that the mean is calculated by adding all the values and dividing by how many there are. I've demonstrated two worked examples: finding the mean of 3, 5, 7 (answer: 5) and finding the mean of 10, 12, 8, 6 (answer: 9). Students haven't practised independently yet."*

---

## Hinge Question: Calculating the Mean

**For:** Year 7 Mathematics
**Ask this after:** Teacher explanation and worked examples of calculating the mean
**Estimated answer time:** 60–90 seconds

### The Question

Five students scored the following marks in a test:

**6, 4, 8, 3, 9**

What is the mean score?

A) 5
B) 6
C) 8
D) 30

**Correct answer:** B) 6

### Diagnostic Key

- **A) 5** — This is the **median** (the middle value when ordered: 3, 4, 6, 8, 9). A student choosing this has confused mean with median — they may have ordered the numbers and picked the middle one, or they may have a general confusion between the two averages. This is one of the most common errors when mean and median are taught in close proximity.

- **B) 6** — **Correct.** The student has added all values (6 + 4 + 8 + 3 + 9 = 30) and divided by the number of values (30 ÷ 5 = 6). This confirms they understand both steps: the sum AND the division by the count.

- **C) 8** — This is the **range** (9 – 3 = 6... wait, no — this is a deliberately chosen distractor). Actually, 8 is the answer a student gets if they **divide by 4 instead of 5** — that is, they miscounted the number of values or forgot to count one of them (30 ÷ 4 = 7.5... let me recalculate).

Let me redesign. The data set is **6, 4, 8, 3, 9**.
- Sum = 30. Mean = 30 ÷ 5 = 6. ✓
- Median = 6 (middle of 3, 4, 6, 8, 9). This would overlap with the correct answer.

I need to adjust the data set so the mean and median are different.

**Revised data set: 2, 3, 5, 8, 12**
- Sum = 30. Mean = 30 ÷ 5 = 6.
- Median = 5 (middle of 2, 3, 5, 8, 12).
- Range = 10 (12 – 2).

### The Question (Revised)

Five students scored the following marks in a test:

**2, 3, 5, 8, 12**

What is the mean score?

A) 5
B) 6
C) 10
D) 30

**Correct answer:** B) 6

### Diagnostic Key

- **A) 5** — This is the **median** (the middle value when the data is ordered). A student who chooses this has confused mean with median. They may understand that "average" involves finding a central value but are using the wrong method — picking the middle number instead of calculating. This is the most common misconception when students have recently learned both types of average.

- **B) 6** — **Correct.** The student has added all five values (2 + 3 + 5 + 8 + 12 = 30) and divided by the number of values (30 ÷ 5 = 6). This confirms understanding of both components of the mean calculation: summing all values AND dividing by the count.

- **C) 10** — This is the **range** (12 – 2 = 10). A student who chooses this has confused mean with range — they've subtracted the smallest from the largest instead of calculating. This error is common in students who know there are several "summary statistics" but mix up which procedure goes with which name. It may also indicate that the student has only partially attended to the lesson and is applying a recently-learned but incorrect procedure.

- **D) 30** — This is the **sum without dividing** (2 + 3 + 5 + 8 + 12 = 30). A student who chooses this has completed the first step (adding all values) but forgotten or not understood the second step (dividing by the count). This is a partial understanding — they know the mean involves adding, but don't know what to do with the total. This is the most actionable error: the student needs a brief re-teach of WHY we divide (to share the total equally).

### Decision Guide

**If 80%+ choose B (correct):** Proceed to independent practice. Students understand the procedure. Move to practice problems that vary the number of values and include decimals in the answer.

**If many choose A (median confusion):** Stop and clarify the distinction. "Some of you found the middle number — that's the median, not the mean. The mean is when we ADD everything up and SHARE it equally. The median is when we put them in order and find the middle. Different questions, different methods. Let me show you both side by side." Re-do the example calculating both, labelling each clearly. Then re-ask with a new data set.

**If many choose D (sum without dividing):** Brief re-teach of the second step. "Some of you got 30 — you've done the first step perfectly. But the mean isn't the total. Think of it this way: if all five students scored EQUALLY, what would each score be? You're sharing 30 marks equally between 5 students. That's what dividing does." Re-ask with a simpler example.

**If many choose C (range confusion):** This suggests a labelling problem — students are confusing the names of different statistical measures. "Some of you subtracted the smallest from the largest — that gives us the range, not the mean. Let's be really clear about which word goes with which calculation." Create a quick reference: Mean = add and divide. Median = middle value. Range = biggest minus smallest.

**If responses are split across A, C, and D:** More fundamental re-teaching needed. Students are not secure on what the mean IS, not just how to calculate it. Return to the conceptual explanation: "The mean is the value each person would get if we shared everything equally." Use a physical model (counters shared between groups) before returning to the numerical procedure.

### Design Rationale

This question works as a hinge question because:

1. **The numbers are simple enough to calculate mentally** (sum = 30, divide by 5 = 6), so the question tests understanding of the concept, not arithmetic ability. A student who understands the method should reach the answer within 60 seconds.

2. **Every distractor is the correct answer to a DIFFERENT question** about the same data set — the median (A), the range (C), and the sum (D). This means each wrong answer reveals a specific confusion about which statistical measure is which, or which step of the procedure the student has completed.

3. **The correct answer (6) is not the "obvious" or most memorable number** in the set. It requires calculation to reach, unlike the median (5, which is literally in the data) or the sum (30, which is the first number students calculate). A student cannot guess the correct answer without performing the full procedure.

4. **The data set was deliberately chosen** so that the mean (6) and median (5) are different — if they were the same, the question couldn't distinguish between a student who calculated correctly and one who found the median by mistake.

---

## Known Limitations

1. **Hinge questions only work if the teacher acts on the response data.** A beautifully designed hinge question is worthless if the teacher asks it, sees that 40% of students chose the wrong answer, and proceeds anyway. The decision guide provides specific actions for each response pattern, but the teacher must be willing to adjust the lesson plan in real time. This requires both flexibility and confidence — some teachers find it difficult to deviate from a planned lesson even when the data says they should.

2. **Multiple-choice format limits what can be tested.** Hinge questions work best for concepts where understanding can be revealed through a single choice — typically factual knowledge, procedural understanding, or conceptual distinctions. They are less effective for testing complex reasoning, extended argument, or creative application, where the interesting information is in the student's process, not their final answer. For these skills, other checking-for-understanding methods (mini-whiteboards with working shown, think-pair-share) are more appropriate.

3. **Distractor design requires deep knowledge of student misconceptions.** The quality of a hinge question depends entirely on whether the distractors target REAL misconceptions that ACTUAL students hold — not just plausible-looking wrong answers. The generator uses common misconceptions from the research literature and teaching experience, but specific student populations may hold different misconceptions. Teachers should review the distractors and modify them based on their knowledge of their own students' typical errors. If a distractor doesn't match a real misconception in the class, it provides no diagnostic information — it's just "a wrong answer."

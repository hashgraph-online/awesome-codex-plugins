---
# AGENT SKILLS STANDARD FIELDS (v2)
name: checking-for-understanding-protocol-designer
description: "Design a checking-for-understanding protocol with specific techniques for each lesson stage. Use when planning systematic comprehension checks during explicit or direct instruction."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "explicit-instruction/checking-for-understanding-protocol-designer"
skill_name: "Checking for Understanding Protocol Designer"
domain: "explicit-instruction"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Rosenshine (2012) — Principles of Instruction, Principle 3: ask a large number of questions and check all student responses"
  - "Wiliam (2011) — Embedded Formative Assessment: practical strategies for checking understanding"
  - "Lemov (2015) — Teach Like a Champion 2.0: cold call, show call, and other CFU techniques"
  - "Black & Wiliam (1998) — Assessment and classroom learning: formative assessment effect size ~0.66"
  - "Christodoulou (2017) — Making Good Progress?: hinge questions and diagnostic assessment"
input_schema:
  required:
    - field: "lesson_content"
      type: "string"
      description: "What is being taught in the lesson"
    - field: "lesson_stage"
      type: "string"
      description: "When CFU is needed: during instruction, after guided practice, end of lesson, or all stages"
    - field: "student_level"
      type: "string"
      description: "Age/year group and class characteristics"
  optional:
    - field: "class_size"
      type: "integer"
      description: "Number of students — affects technique selection"
    - field: "common_misconceptions"
      type: "array"
      description: "Known misconceptions to probe for"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: specific students to monitor, confidence patterns"
    - field: "available_resources"
      type: "string"
      description: "Mini-whiteboards, devices, response cards — what's available in the room"
output_schema:
  type: "object"
  fields:
    - field: "cfu_techniques"
      type: "array"
      description: "Selected techniques with implementation scripts for each lesson stage"
    - field: "hinge_question"
      type: "object"
      description: "A diagnostic hinge question with distractor analysis"
    - field: "cold_call_plan"
      type: "object"
      description: "Structured cold-calling sequence with question stems"
    - field: "response_decision_tree"
      type: "string"
      description: "What to do based on CFU results: proceed, re-teach, or adjust"
chains_well_with:
  - "explicit-instruction-sequence-builder"
  - "hinge-question-designer"
  - "formative-assessment-technique-selector"
  - "retrieval-practice-generator"
teacher_time: "3 minutes"
tags: ["formative-assessment", "checking-understanding", "questioning", "cold-calling", "feedback"]
---

# Checking for Understanding Protocol Designer

## What This Skill Does

Generates a set of checking-for-understanding techniques appropriate for a specific lesson stage, including cold-calling scripts, mini-whiteboard prompts, exit tickets, and hinge questions — each with implementation detail and a decision tree for what to do based on results. The output tells the teacher not just *how* to check but *what to do with the information*. AI is specifically valuable here because effective CFU requires matching the right technique to the right moment (you don't use an exit ticket mid-explanation) and designing questions that reveal understanding rather than just confirming that students were listening. Most CFU in practice is "Any questions?" or "Does everyone understand?" — which checks nothing.

## Evidence Foundation

Rosenshine (2012) identified frequent checking for understanding as Principle 3 of effective instruction: "Successful teachers ask a large number of questions, check the responses of all students, and provide systematic feedback and corrections." Black & Wiliam (1998) demonstrated that formative assessment — the use of assessment information to adjust instruction — produces an effect size of approximately 0.66, but only when teachers act on the results. Wiliam (2011) operationalised formative assessment into five key strategies, with "engineering effective classroom discussions, activities, and learning tasks that elicit evidence of learning" at the core. Lemov (2015) provided practical classroom techniques including cold calling (asking students who haven't volunteered, with thinking time), show call (selecting student work for whole-class analysis), and standardised formats that allow quick scanning of all student responses. Christodoulou (2017) advanced the concept of hinge questions — single diagnostic questions whose answers reveal whether students have understood the critical concept well enough to progress.

## Input Schema

The teacher must provide:
- **Lesson content:** What is being taught. *e.g. "How to calculate the area of a circle using πr²" / "The causes of the English Civil War" / "Writing a balanced argument with counter-claims"*
- **Lesson stage:** When CFU is needed. *e.g. "During instruction — I want to check before moving on" / "End of lesson — exit ticket" / "All stages — give me a full protocol"*
- **Student level:** Year group and class characteristics. *e.g. "Year 7, enthusiastic but often overconfident — they say they understand when they don't"*

Optional (injected by context engine if available):
- **Class size:** Number of students
- **Common misconceptions:** Misconceptions to specifically probe for
- **Student profiles:** Specific students to monitor, confidence-accuracy patterns
- **Available resources:** Mini-whiteboards, devices, response cards

## Prompt

```
You are an expert in formative assessment and checking for understanding, with deep knowledge of Rosenshine's (2012) Principles of Instruction, Wiliam's (2011) formative assessment strategies, Lemov's (2015) practical CFU techniques, and Christodoulou's (2017) work on hinge questions. You understand that the purpose of CFU is not to confirm that students are paying attention — it is to gather diagnostic evidence that determines whether to proceed, re-teach, or adjust.

Your task is to design a CFU protocol for the following:

**Lesson content:** {{lesson_content}}
**Lesson stage:** {{lesson_stage}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Class size:** {{class_size}} — if not provided, design for a class of 25–30 students.
**Common misconceptions:** {{common_misconceptions}} — if not provided, identify the 2–3 most likely misconceptions for this content and design probes that surface them.
**Student profiles:** {{student_profiles}} — if not provided, assume a typical mixed-ability class with some students who overestimate their understanding.
**Available resources:** {{available_resources}} — if not provided, assume mini-whiteboards are available (the single most effective CFU resource) and no devices.

Apply these evidence-based principles:

1. **Check ALL students, not just volunteers (Rosenshine, 2012; Lemov, 2015):**
   - Hands-up questioning checks only the students who already know. It tells you nothing about the other 80%.
   - Use techniques that require ALL students to respond simultaneously: mini-whiteboards, response cards, finger voting, or written responses.
   - Cold calling (calling on students who haven't volunteered) is essential — but always give thinking time first (Wiliam, 2011). "Think for 10 seconds... [pause]... Jordan, what's your answer?"

2. **Design questions that reveal understanding, not recall (Christodoulou, 2017):**
   - "What is the formula for the area of a circle?" checks recall.
   - "The area of a circle is 50 cm². What can you tell me about the radius?" checks understanding — students must work backward and reason with the formula.
   - The best CFU questions require students to APPLY, not REPEAT.

3. **Include a hinge question (Wiliam, 2011; Christodoulou, 2017):**
   - A hinge question is a single multiple-choice question where each wrong answer reveals a specific misconception.
   - The teacher should be able to scan responses in under 30 seconds.
   - The hinge point is the decision: if 80%+ correct, proceed. If 50–80%, address the specific misconception revealed by the most common wrong answer. If below 50%, re-teach.

4. **Plan what to do with the results (Black & Wiliam, 1998):**
   - CFU without a response plan is pointless. For every check, specify:
     - What 80%+ correct means → proceed
     - What common errors mean → which misconception, and how to address it
     - What widespread confusion means → re-teach using a different approach

5. **Match technique to moment:**
   - During instruction: quick checks (cold call, finger vote, mini-whiteboard flash)
   - After guided practice: show call (project one student's work for class analysis)
   - End of lesson: exit ticket (5-minute written task that diagnoses readiness for next lesson)
   - Between lessons: review of exit ticket data to plan the following lesson

Return your output in this exact format:

## CFU Protocol: [Lesson Content]

**For:** [Student level]
**Stage:** [When checks will occur]

### During-Instruction Checks
[2–3 quick-fire checks to use while teaching, with exact questions and technique]

### Hinge Question
[A single diagnostic multiple-choice question with distractor analysis — what each wrong answer reveals]

### Cold-Call Sequence
[A scripted sequence of 3–4 cold-call questions with thinking time built in]

### End-of-Lesson Check (Exit Ticket)
[A 5-minute exit ticket with 2–3 questions that diagnose readiness for the next lesson]

### Response Decision Tree
[What to do based on CFU results — proceed, re-teach, or adjust]

**Self-check before returning output:** Verify that (a) all techniques check ALL students, not just volunteers, (b) the hinge question has distractors that map to specific misconceptions, (c) cold calls include thinking time before naming the student, (d) a response decision tree is included for every check, and (e) questions test understanding and application, not just recall.
```

## Example Output

**Scenario:** *Lesson content: "Calculating the area of a circle using πr², including problems where the diameter is given instead of the radius" / Lesson stage: "All stages — full protocol" / Student level: "Year 8 Mathematics, mid-ability, tend to be overconfident — often rush and make errors with radius vs diameter"*

---

## CFU Protocol: Area of a Circle (πr²)

**For:** Year 8 Mathematics, mid-ability
**Stage:** All stages — full protocol

### During-Instruction Checks

**Check 1 — After introducing the formula (2 minutes in):**
*Technique: Mini-whiteboards*
"Write the formula for the area of a circle on your whiteboard. Hold it up in 3... 2... 1... Show me."
- **Looking for:** A = πr². Watch for: A = πd² (diameter instead of radius — the key misconception), A = 2πr (circumference confused with area), A = πr (missing the squared).
- **If widespread error:** Don't just correct. Ask: "I can see some boards say πd². Who can explain why the formula uses r, not d? What is the relationship between radius and diameter?" Draw the distinction on the board.

**Check 2 — After the first worked example (8 minutes in):**
*Technique: Finger vote*
"A circle has a diameter of 10 cm. I need to calculate the area. What is the first thing I should do? Show me: hold up 1 finger if 'multiply 10 by π', 2 fingers if 'divide 10 by 2 to get the radius', 3 fingers if 'square the 10'."
- **Correct answer:** 2 (find the radius first).
- **If many show 1 or 3:** Students are plugging the diameter directly into the formula. Stop and address: "If the question gives you the diameter, what must you do BEFORE you use the formula? Why?" This is the single most common error source in this topic.

**Check 3 — After guided practice (20 minutes in):**
*Technique: Show call*
Select two students' whiteboard solutions for the same problem (one correct, one with the diameter/radius error). Display side by side (anonymised or with permission).
"Which solution is correct? How do you know? Where did the error occur in the other one?"
This makes the common error visible to the whole class without singling anyone out.

### Hinge Question

**Display on board or screen (30 seconds to answer):**

A circle has a radius of 5 cm. What is its area?

(A) 78.5 cm²
(B) 31.4 cm²
(C) 15.7 cm²
(D) 314 cm²

*Students hold up A, B, C, or D on fingers (or whiteboards).*

**Distractor analysis:**

| Answer | What it reveals | Calculation the student did |
|--------|----------------|---------------------------|
| **(A) 78.5 cm²** | **Correct** — π × 5² = π × 25 = 78.5 | Correct application of A = πr² |
| (B) 31.4 cm² | **Circumference/area confusion** — student calculated 2πr instead of πr² | 2 × π × 5 = 31.4 |
| (C) 15.7 cm² | **Missing the square** — student calculated πr instead of πr² | π × 5 = 15.7 |
| (D) 314 cm² | **Used diameter instead of radius** — student doubled the radius first, then squared | π × 10² = 314 |

**Decision:**
- 80%+ choose A → Proceed to independent practice.
- Many choose B → Stop. "Some of you got 31.4. That's the circumference, not the area. What's the difference between 2πr and πr²? Area is the space INSIDE — we need the squared formula."
- Many choose C → Stop. "Some of you got 15.7. You used πr but forgot to square the radius. Remember: r² means r times r, so 5² is 25, not 5."
- Many choose D → Stop. "Some of you got 314. You used the diameter (10) instead of the radius (5). The formula uses r — always check: did the question give you radius or diameter?"

### Cold-Call Sequence

All cold calls follow the pattern: ask the question → give thinking time → THEN name the student.

**Q1:** "A circle has a radius of 3 cm. Without calculating, estimate — will the area be bigger or smaller than 30 cm²? Think for 5 seconds... [pause]... Amira, what do you think and why?"
*(Tests: number sense and rough understanding of the formula. π × 9 ≈ 28, so slightly less than 30.)*

**Q2:** "The area of a circle is 50 cm². Is the radius bigger or smaller than 5 cm? Think for 10 seconds... [pause]... Jayden, what's your answer?"
*(Tests: reasoning backward from the formula. If r = 5, area = 78.5, which is bigger than 50. So r must be smaller than 5. This requires understanding, not just procedure.)*

**Q3:** "I calculated the area of a circle with diameter 8 cm. I got 200.96 cm². My friend says I'm wrong. Without recalculating, can you tell me what mistake I might have made? Think for 10 seconds... [pause]... Sophie, what do you think?"
*(Tests: error detection. 200.96 = π × 8² = π × 64. The error is using diameter instead of radius. With r = 4, area = π × 16 = 50.27.)*

**Q4:** "Can you have a circle with an area of exactly 100 cm²? Think for 15 seconds — this is a hard one... [pause]... Kian, what do you think?"
*(Tests: deeper understanding. Yes — r = √(100/π) ≈ 5.64 cm. If students struggle, this reveals whether they can manipulate the formula or only apply it forward.)*

### End-of-Lesson Check (Exit Ticket)

**5 minutes. On a slip of paper or in books. No calculators allowed for Q1–Q2.**

**Q1.** A circle has a radius of 4 cm. Write the calculation you would do to find the area. You don't need to work out the final answer — just set up the calculation correctly.
*(Tests: can they set up πr² correctly? Separates formula knowledge from arithmetic.)*

**Q2.** A circle has a diameter of 12 cm. What is the radius? What calculation would you set up to find the area?
*(Tests: the diameter-to-radius conversion, which is the highest-error step. Two-part question isolates where the error occurs.)*

**Q3.** (Calculator allowed) A circular garden has a diameter of 6 metres. The gardener wants to buy grass seed. Each bag covers 10 m². How many bags does the gardener need?
*(Tests: application in context — must find area AND round up to a whole number of bags. This is the kind of problem that appears on exams.)*

**Sorting the exit tickets:**
After the lesson, sort tickets into three piles:
- **Got it (all 3 correct):** Ready for next lesson. Give these students interleaved practice mixing circles with other area calculations.
- **Partial (Q1 correct, Q2 or Q3 wrong):** Knows the formula but struggles with diameter conversion or application. Next lesson: start with 2 quick examples converting diameter to radius, then practise Q3-type problems.
- **Not yet (Q1 wrong):** Doesn't have the formula secure. Next lesson: brief re-teach with a different worked example before independent practice.

### Response Decision Tree

```
CFU result → Action

During instruction (Check 1-3):
├── 80%+ correct → Proceed to next phase
├── 50-80% correct → Address the specific error shown by the most common wrong answer (2-3 min reteach)
└── Below 50% → Stop. Reteach using a different representation (e.g., draw the circle, shade the area, physically count squares)

Hinge question:
├── 80%+ choose A → Move to You Do
├── Most common error is B (circumference) → Reteach the difference between area and circumference with diagrams
├── Most common error is C (missing square) → Reteach r² with physical demonstration (5 rows of 5 = 25, not 5)
└── Most common error is D (diameter) → Reteach diameter/radius with a circle drawn on the board — measure both

Exit ticket (reviewed after lesson):
├── 80%+ all correct → Next lesson proceeds as planned
├── Cluster of Q2 errors → Start next lesson with diameter-to-radius mini-lesson (5 min)
└── Cluster of Q1 errors → Re-teach the formula next lesson before any new content
```

---

## Known Limitations

1. **CFU techniques tell you what students can do in the moment, not what they'll retain.** A student who correctly answers a hinge question today may have forgotten the formula by next week. CFU checks current understanding; it must be combined with spaced retrieval practice (chain with Retrieval Practice Generator and Spaced Practice Scheduler) to ensure long-term retention.

2. **Mini-whiteboards and finger votes can be gamed.** Students can copy from neighbours, wait to see others' answers before showing theirs, or hold boards at angles. Lemov (2015) recommends "boards up on my count — 3, 2, 1, show" to reduce copying, but no technique eliminates it entirely. Cold calling individuals is the strongest complement because it cannot be gamed.

3. **The response decision tree requires teacher judgment in real time.** The tree provides guidance, but the teacher must make rapid decisions about whether to re-teach, how long to spend, and when to move on. This is a professional skill that improves with practice — the protocol supports it but cannot replace it.

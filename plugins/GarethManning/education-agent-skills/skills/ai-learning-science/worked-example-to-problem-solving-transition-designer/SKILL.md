---
# AGENT SKILLS STANDARD FIELDS (v2)
name: worked-example-to-problem-solving-transition-designer
description: "Design the transition from worked examples to independent problem-solving using expertise-reversal principles. Use when students follow examples but cannot solve problems alone."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-learning-science/worked-example-to-problem-solving-transition-designer"
skill_name: "Worked Example to Problem Solving Transition Designer"
domain: "ai-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Kalyuga et al. (2003) — The expertise reversal effect (seminal paper)"
  - "Kalyuga (2007) — Expertise reversal effect and its implications for learner-tailored instruction"
  - "Renkl & Atkinson (2003) — Structuring the transition from example study to problem solving"
  - "Sweller et al. (2011) — Cognitive load theory (chapter on expertise reversal)"
  - "Van Merriënboer & Kirschner (2018) — Ten steps to complex learning (4C/ID model)"
input_schema:
  required:
    - field: "skill_being_taught"
      type: "string"
      description: "The specific skill or procedure students are learning — what they need to be able to do independently by the end of the sequence"
    - field: "current_student_state"
      type: "string"
      description: "Where students are now — what they already know and what evidence you have of their current competence"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and proficiency level"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "number_of_practice_problems"
      type: "integer"
      description: "How many practice problems are available or practical"
    - field: "time_available"
      type: "string"
      description: "How much time is available for the transition sequence"
    - field: "assessment_format"
      type: "string"
      description: "How competence will be assessed — timed test, project, practical, or other"
output_schema:
  type: "object"
  fields:
    - field: "transition_sequence"
      type: "object"
      description: "The complete sequence from worked examples to independent problem solving — with the fading stages, transition triggers, and problem selection"
    - field: "expertise_reversal_checkpoints"
      type: "array"
      description: "The specific points where the system checks whether continued scaffolding is helping or hindering"
    - field: "fading_schedule"
      type: "object"
      description: "How scaffolding is gradually removed — which elements fade first and why"
    - field: "independent_practice_design"
      type: "object"
      description: "The design of the independent practice phase — problem types, difficulty progression, and what to do when students get stuck"
chains_well_with:
  - "digital-worked-example-sequence"
  - "adaptive-hint-sequence-designer"
  - "cognitive-tutoring-architecture-designer"
  - "productive-failure-desirable-difficulty-designer"
teacher_time: "5 minutes"
tags: ["expertise-reversal", "Kalyuga", "fading", "worked-examples", "Renkl", "transition", "scaffolding", "cognitive-load"]
---

# Worked Example to Problem Solving Transition Designer

## What This Skill Does

Designs the transition sequence from studying worked examples to solving problems independently — the critical phase where scaffolding is gradually removed and students take over the cognitive work. This addresses one of the most important findings in cognitive load theory: the expertise reversal effect (Kalyuga et al., 2003). When students are novices, worked examples are highly effective — they reduce extraneous cognitive load and allow students to build schemas. But as students develop competence, the same worked examples become REDUNDANT and actually HARM learning — the scaffolding that helped novices now prevents more advanced students from engaging in the active processing that drives further learning. The optimal instruction is not fixed but ADAPTIVE: it should shift from worked examples to problem solving as the student's expertise grows. Renkl & Atkinson (2003) developed the "fading" approach: rather than an abrupt switch from examples to problems, gradually remove steps from the worked examples so students progressively take over more of the work. This skill designs the complete fading sequence, including the triggers for when to fade (based on student performance), the order of fading (which steps to remove first), and the design of the independent practice phase that follows.

## Evidence Foundation

Kalyuga et al. (2003) demonstrated the expertise reversal effect through a series of experiments showing that instructional techniques highly effective for novices become ineffective or harmful for more advanced learners. In the context of worked examples: novices who studied worked examples significantly outperformed novices who solved problems (the worked example effect), but as students gained expertise, this advantage reversed — more advanced students learned more from problem solving than from studying examples. The explanation is cognitive load theory: for novices, worked examples reduce the extraneous load of means-ends analysis (trying to figure out what to do), freeing cognitive resources for schema building. For advanced students, the worked example creates REDUNDANCY — the student already has a schema and the example is now unnecessary information that competes with their existing knowledge for processing resources. Kalyuga (2007) extended this work, arguing that learner-tailored instruction must continuously assess the learner's expertise level and adjust the instructional format accordingly. The practical implication: there is no single "best" instructional approach — the best approach depends on where the learner is RIGHT NOW. Renkl & Atkinson (2003) proposed fading as the solution to the example-to-problem transition. Rather than a sharp switch from "study examples" to "solve problems," they designed a gradual transition: first, full worked examples; then, examples with one step removed (the student completes that step); then, examples with two steps removed; and so on until the student is solving complete problems. They found that fading produced better learning than either fixed worked examples or fixed problem solving, because it continuously calibrated the cognitive demand to the student's growing expertise. Sweller et al. (2011) integrated the expertise reversal effect into the broader cognitive load theory framework, arguing that all instructional design must consider the INTERACTION between the learner's current knowledge and the instructional format. A technique that is optimal at one stage of learning may be counterproductive at another. Van Merriënboer & Kirschner (2018) developed the 4C/ID model for complex learning, which systematically designs the transition from heavily scaffolded task performance to independent performance through a sequence of task classes with decreasing support.

## Input Schema

The teacher must provide:
- **Skill being taught:** What students need to do independently. *e.g. "Solving quadratic equations by factorisation — finding factors, setting each factor to zero, solving for both roots" / "Writing a balanced argument essay — introduction with thesis, supporting paragraphs with evidence, counterargument paragraph, conclusion with evaluated position" / "Calculating the mean, median, and mode from a frequency table and interpreting which average is most appropriate"*
- **Current student state:** Where students are now. *e.g. "Students have seen two teacher-led worked examples. They can follow the steps when watching but haven't attempted any problems independently yet" / "Students can write persuasive essays (one-sided argument) but have never structured a balanced argument" / "Students can calculate mean from raw data but haven't worked with frequency tables"*

Optional (injected by context engine if available):
- **Student level:** Year group and proficiency
- **Subject area:** The curriculum subject
- **Number of practice problems:** How many problems are available
- **Time available:** Duration for the transition sequence
- **Assessment format:** How competence will be tested

## Prompt

```
You are an expert in the expertise reversal effect and the transition from worked examples to problem solving, with deep knowledge of Kalyuga et al.'s (2003) expertise reversal research, Kalyuga's (2007) learner-tailored instruction principles, Renkl & Atkinson's (2003) fading approach, Sweller et al.'s (2011) cognitive load theory, and Van Merriënboer & Kirschner's (2018) 4C/ID model. You understand that the most common instructional error is using a FIXED approach (always examples, or always problems) when the optimal approach is ADAPTIVE — shifting from scaffolded examples to independent problem solving as the student's expertise grows.

CRITICAL PRINCIPLES:
- **The expertise reversal effect is real and consequential.** Continuing to provide worked examples after students have built adequate schemas REDUCES learning. The scaffolding becomes cognitive clutter that the brain must process and suppress. This is not about student preference (students often prefer continued scaffolding because it feels easier) — it's about cognitive science.
- **Fade gradually, don't switch abruptly.** Renkl & Atkinson (2003): the transition from examples to problems should be a GRADIENT, not a cliff. Remove one step at a time, starting with the LAST step (backward fading) so students complete the final step first, then the last two steps, and so on. This builds confidence and ensures each fading stage builds on the previous one.
- **Use performance to trigger fading.** The trigger for removing the next step should be PERFORMANCE-BASED: the student consistently completes the current step correctly. Do not fade on a fixed schedule — students learn at different rates. An AI system can personalise the fading; a teacher can use quick checks.
- **Independent practice must be DESIGNED, not just assigned.** Once fading is complete, the problem-solving phase needs its own design: problem difficulty should increase gradually, problems should be interleaved (not blocked by type), and students who get stuck should receive the MINIMUM help needed (not a return to full worked examples).
- **Watch for the "illusion of competence" during fading.** Students who successfully complete faded examples may FEEL more competent than they are, because the remaining worked steps are doing much of the cognitive work. True competence is demonstrated only in FULLY independent problem solving.

Your task is to design the transition sequence for:

**Skill being taught:** {{skill_being_taught}}
**Current student state:** {{current_student_state}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for a general secondary school context.
**Subject area:** {{subject_area}} — if not provided, infer from the skill.
**Number of practice problems:** {{number_of_practice_problems}} — if not provided, design for 8-12 problems across the full sequence.
**Time available:** {{time_available}} — if not provided, design for two 50-minute lessons.
**Assessment format:** {{assessment_format}} — if not provided, assume a timed test without scaffolding.

Return your output in this exact format:

## Worked Example to Problem Solving Transition: [Skill]

**Target skill:** [What students will do independently]
**Starting point:** [Where students are now]
**Transition approach:** [Fading method and rationale]

### Complete Transition Sequence

[The full sequence from worked example to independent problem solving, with each stage clearly defined]

**Stage [N]: [Name] — [Scaffolding level]**
- **What the student sees:** [The example/problem at this stage]
- **What the student does:** [Which steps the student completes]
- **Fading trigger:** [How to know the student is ready for the next stage]
- **Estimated problems at this stage:** [How many before moving on]

### Expertise Reversal Checkpoints

[The specific points where the system/teacher checks whether continued scaffolding is helping or hindering. Include the check method and the decision rule.]

### Fading Schedule

[Which steps are faded in which order, and why this order was chosen]

| Stage | Steps Shown | Steps Faded | Rationale |
|---|---|---|---|
| [Stage] | [Which steps the student can see] | [Which steps the student must complete] | [Why this order] |

### Independent Practice Design

[The design of the fully independent problem-solving phase — problem selection, difficulty progression, and stuck protocols]

### Common Pitfalls

[What can go wrong during the transition and how to address it]

**Self-check before returning output:** Verify that (a) fading is gradual not abrupt, (b) performance triggers the fading, (c) backward fading is used (last steps removed first), (d) expertise reversal checkpoints are included, and (e) independent practice is designed not just assigned.
```

## Example Output

**Scenario:** *Skill being taught: "Solving quadratic equations by factorisation — finding two numbers that multiply to give c and add to give b in x² + bx + c = 0, writing the factored form (x + p)(x + q) = 0, setting each factor to zero, and solving for both roots" / Current student state: "Students have seen two teacher-led worked examples on the board. They can identify that the equation needs to be factorised and understand the concept of 'two numbers that multiply to c and add to b' but have not attempted any problems independently. Some students are still unclear about WHY setting each factor to zero gives the solutions" / Student level: "Year 10, GCSE Higher tier" / Subject area: "Mathematics" / Time available: "One 60-minute lesson plus homework" / Assessment format: "End-of-unit test, no scaffolding, 8 quadratic equations to solve in 25 minutes"*

---

## Worked Example to Problem Solving Transition: Solving Quadratics by Factorisation

**Target skill:** Independently solve quadratic equations of the form x² + bx + c = 0 by factorisation
**Starting point:** Students have seen 2 worked examples; can follow the method but haven't attempted independently; some confusion about WHY factoring produces solutions
**Transition approach:** Backward fading (Renkl & Atkinson, 2003) — remove steps from the end first so students build confidence on the final stages before taking responsibility for earlier stages

### Complete Transition Sequence

The procedure has 4 key steps:
1. **Identify:** Write equation in standard form (x² + bx + c = 0)
2. **Factor-find:** Find two numbers that multiply to c and add to b
3. **Factor-write:** Write factored form (x + p)(x + q) = 0
4. **Solve:** Set each factor to zero and solve for x

**Stage 1: Full Worked Example with Self-Explanation (1 problem)**

- **What the student sees:** Complete worked solution: x² + 5x + 6 = 0 → "Need two numbers that multiply to 6 and add to 5" → 2 and 3 → (x + 2)(x + 3) = 0 → x + 2 = 0 or x + 3 = 0 → x = -2 or x = -3
- **What the student does:** Studies the example. At Step 4, self-explanation prompt: "WHY does (x + 2)(x + 3) = 0 mean that x + 2 = 0 OR x + 3 = 0? What mathematical rule makes this work?" (Target: if a product equals zero, at least one factor must be zero.)
- **Fading trigger:** Student can articulate the zero-product property in their own words
- **Estimated problems at this stage:** 1

**Stage 2: Fade Step 4 — Student Solves from Factored Form (2 problems)**

- **What the student sees:** Steps 1-3 completed: x² + 7x + 12 = 0 → factors are 3 and 4 → (x + 3)(x + 4) = 0 → [STUDENT COMPLETES FROM HERE]
- **What the student does:** Sets each factor to zero and solves: x = -3 or x = -4. This is the simplest step — arithmetic with one operation.
- **Fading trigger:** Student correctly solves 2 consecutive problems at this stage (both factors set to zero, correct signs on both roots)
- **Estimated problems at this stage:** 2-3

**Stage 3: Fade Steps 3-4 — Student Writes Factored Form and Solves (2 problems)**

- **What the student sees:** Steps 1-2 completed: x² + 8x + 15 = 0 → "The two numbers are 3 and 5" → [STUDENT COMPLETES FROM HERE]
- **What the student does:** Writes (x + 3)(x + 5) = 0, then sets each factor to zero and solves: x = -3 or x = -5
- **Fading trigger:** Student correctly writes the factored form AND solves for 2 consecutive problems
- **Estimated problems at this stage:** 2-3

**Stage 4: Fade Steps 2-4 — Student Finds Factors, Writes Form, and Solves (2-3 problems)**

- **What the student sees:** Step 1 only: x² + 9x + 20 = 0 → [STUDENT COMPLETES FROM HERE]
- **What the student does:** Finds the two numbers (4 and 5), writes (x + 4)(x + 5) = 0, solves to get x = -4 or x = -5. The student is now doing everything except identifying the standard form.
- **Fading trigger:** Student correctly completes 2 consecutive problems including finding the factor pair
- **Estimated problems at this stage:** 2-4

**Stage 5: Fully Independent Problem Solving (4-6 problems)**

- **What the student sees:** Just the equation: x² + 11x + 24 = 0. No scaffolding.
- **What the student does:** The entire procedure from start to finish
- **Fading trigger:** N/A — this is the target performance. Mastery criterion: 3 consecutive correct solutions
- **Estimated problems at this stage:** 4-6 (including gradually increasing difficulty — see Independent Practice Design)

### Expertise Reversal Checkpoints

**Checkpoint 1 (after Stage 2):** If the student completes Stage 2 problems instantly and seems bored, SKIP Stage 3 and go directly to Stage 4. The scaffolding is becoming redundant. Sign of expertise reversal: student says "I already know this part" or completes the faded step before reading the shown steps.

**Checkpoint 2 (after Stage 3):** If the student is completing Stages 2-3 correctly but slowly (more than 2 minutes per problem), they may benefit from one MORE problem at Stage 3 before advancing. If they're completing them in under 1 minute, advance to Stage 4 immediately.

**Checkpoint 3 (during Stage 5):** If a student who was succeeding at Stages 3-4 suddenly struggles at Stage 5, do NOT return them to full worked examples. Instead, return to Stage 4 (one step shown) for 1-2 problems, then try Stage 5 again. The appropriate response to a setback is to STEP BACK ONE STAGE, not to restart from the beginning.

**Checkpoint 4 (during Stage 5, different students):** For the fastest students who reach Stage 5 within 15 minutes, introduce VARIATIONS: equations where a ≠ 1 (e.g., 2x² + 7x + 3 = 0), equations requiring rearrangement first (x² + 5x = -6), or equations with negative coefficients. This prevents the expertise reversal effect: once simple factorisation is mastered, continued practice of simple problems is less effective than progressing to harder variations.

### Fading Schedule

| Stage | Steps Shown | Steps Faded (Student Completes) | Rationale |
|---|---|---|---|
| 1 (Full) | All 4 steps | None (self-explanation only) | Student builds schema by studying complete procedure |
| 2 | Steps 1, 2, 3 | Step 4 (solve from factors) | Last step faded first — simplest cognitive demand, builds confidence |
| 3 | Steps 1, 2 | Steps 3, 4 (write factors + solve) | Student now handles the "output" stages while the "input" (finding factors) is shown |
| 4 | Step 1 only | Steps 2, 3, 4 (find factors + write + solve) | Student does most of the work; only the standard form is given |
| 5 (Independent) | None | All 4 steps | Full independence — the target state |

**Why backward fading?** Removing the LAST step first means the student always completes the problem — they experience success at every stage (writing the final answer). This builds confidence and motivation. Forward fading (removing Step 1 first) would mean the student starts the problem but then sees the rest of the solution — which feels like "being shown the answer" rather than "solving the problem."

### Independent Practice Design

**Problem selection for Stage 5 (fully independent):**

| Problem | Equation | New Challenge | Purpose |
|---|---|---|---|
| 1 | x² + 6x + 8 = 0 | None — straightforward | Confirm basic competence |
| 2 | x² - 5x + 6 = 0 | Negative coefficient on x | Tests understanding of signs in factoring |
| 3 | x² + 2x - 15 = 0 | Negative constant term | Requires factors with different signs |
| 4 | x² - 9 = 0 | Difference of two squares (no bx term) | Tests whether student recognises the special case |
| 5 | x² + 3x = 10 | Needs rearranging first | Tests whether student handles non-standard form |
| 6 | 2x² + 7x + 3 = 0 | Leading coefficient ≠ 1 (extension) | Stretch — for students who master the standard form quickly |

**Stuck protocol:** If a student gets stuck during independent practice:
1. **First:** Wait 60 seconds. Productive struggle is valuable.
2. **If still stuck:** Ask "Which step are you stuck on?" This diagnostic question helps the student identify the specific difficulty (finding factors? writing the form? solving?).
3. **If the difficulty is Step 2 (finding factors):** Offer a HINT, not an example: "What pairs of numbers multiply to give [c]? Write them all down. Now check which pair adds to [b]."
4. **If the difficulty is conceptual (doesn't understand the method):** Return to Stage 4 (one step shown) for 2 problems, then retry independent.
5. **Do NOT return to a full worked example** unless the student is clearly in distress and the fading has moved too fast. The goal is MINIMUM scaffolding.

### Common Pitfalls

**Pitfall 1: Fading too slowly for strong students.** If a student breezes through Stages 1-3 in 5 minutes, they don't need Stage 4 — they're already past the expertise reversal threshold. Move them to Stage 5 immediately and introduce variations. Continued fading wastes their time and may reduce learning (Kalyuga et al., 2003).

**Pitfall 2: Fading too quickly for struggling students.** If a student makes errors at Stage 3, do NOT advance to Stage 4. Add 1-2 more problems at Stage 3. The fading trigger is CONSISTENT correct performance, not "one correct answer."

**Pitfall 3: Students memorise the factor pairs instead of the method.** If all problems use small, friendly numbers (x² + 5x + 6, x² + 7x + 12), students may spot the factors by inspection without understanding the systematic method. Include at least one problem with larger numbers (x² + 17x + 72) to force the systematic approach.

**Pitfall 4: Conflating the homework with the transition.** The homework should be INDEPENDENT practice (Stage 5 problems), not more faded examples. If students do faded examples for homework, they'll arrive at the test having never solved a complete problem independently. The transition must be completed IN CLASS where support is available; homework consolidates independent competence.

---

## Known Limitations

1. **The expertise reversal effect is well-established in STEM but less studied in other domains.** Kalyuga et al.'s (2003) research was primarily conducted in mathematics, science, and technical domains. The principle transfers (scaffolding that helps novices may hinder experts), but the specific fading approach may need adaptation for domains where "steps" are less clearly defined (essay writing, historical analysis, creative tasks).

2. **Individual variation in fading speed is large.** In a class of 30, some students will reach Stage 5 in 10 minutes while others are still at Stage 2 after 30 minutes. A single whole-class fading schedule will be too fast for some and too slow for others. The design above is optimised for individual or small-group pacing; whole-class implementation requires differentiation.

3. **Backward fading is not always optimal.** Renkl & Atkinson (2003) found backward fading effective for procedural skills with clear step sequences. For tasks with less linear structure (e.g., planning an experiment, structuring an argument), the "last step" may not be clearly defined. In these cases, the fading order needs to be adapted to the specific task structure.

4. **The assessment must match the target.** If the end-of-unit test includes scaffolding (formula sheets, step prompts), the expertise reversal effect is less relevant — the scaffolding is provided in the assessment. The transition design above assumes an UNSCAFFOLDED assessment where students must perform the complete procedure independently.

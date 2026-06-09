---
# AGENT SKILLS STANDARD FIELDS (v2)
name: worked-example-fading-designer
description: "Design a worked example fading sequence from fully worked examples through to independent practice. Use when teaching procedures, algorithms, or multi-step processes to novice learners."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "memory-learning-science/worked-example-fading-designer"
skill_name: "Worked Example Designer with Completion Fading"
domain: "memory-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Sweller & Cooper (1985) — The use of worked examples as a substitute for problem solving in learning algebra"
  - "Atkinson et al. (2000) — Learning from examples: instructional principles from the worked examples research"
  - "Renkl (2014) — Toward an instructionally oriented theory of example-based learning"
  - "Kalyuga et al. (2003) — The expertise reversal effect (when worked examples become counterproductive)"
  - "van Merriënboer & Kirschner (2018) — Ten Steps to Complex Learning: fading and scaffolding principles"
input_schema:
  required:
    - field: "skill_to_teach"
      type: "string"
      description: "The specific procedure or skill students need to learn"
    - field: "student_level"
      type: "string"
      description: "Age/year group and expertise level (novice/developing/advanced)"
    - field: "steps_in_procedure"
      type: "integer"
      description: "Approximate number of steps in the complete procedure"
  optional:
    - field: "common_errors"
      type: "array"
      description: "Known errors students typically make with this procedure"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: individual student readiness data"
    - field: "prior_knowledge"
      type: "string"
      description: "What students already know that this skill builds on"
output_schema:
  type: "object"
  fields:
    - field: "worked_example"
      type: "object"
      description: "A complete worked example with annotated steps and self-explanation prompts"
    - field: "completion_problems"
      type: "array"
      description: "A sequence of 3–4 completion problems with progressive fading"
    - field: "independent_problems"
      type: "array"
      description: "2–3 fully independent practice problems"
    - field: "fading_rationale"
      type: "string"
      description: "Explanation of what is faded at each stage and why"
chains_well_with:
  - "cognitive-load-analyser"
  - "explicit-instruction-sequence-builder"
  - "practice-problem-sequence-designer"
  - "checking-for-understanding-protocol-designer"
teacher_time: "4 minutes"
tags: ["worked-examples", "scaffolding", "fading", "cognitive-load", "novice-learning"]
---

# Worked Example Designer with Completion Fading

## What This Skill Does

Designs a complete scaffold sequence that moves students from studying a fully worked example through progressively faded completion problems to independent practice. For a given procedure or skill, it produces: (1) a worked example with annotated reasoning at each step, (2) a series of completion problems where successive steps are removed, and (3) independent practice problems. AI is specifically valuable here because effective worked examples require expert-level annotation of reasoning (not just showing steps, but explaining *why* each step is taken), and the fading sequence requires careful calibration of which steps to remove and in what order — a task requiring deep knowledge of both the subject content and the cognitive load research.

## Evidence Foundation

Sweller & Cooper (1985) demonstrated that novice learners who studied worked examples learned more effectively than those who attempted problem-solving, because worked examples reduce extraneous cognitive load — students can focus on understanding the procedure rather than searching for a solution path. Atkinson et al. (2000) synthesised the worked examples research and identified key design principles: examples must include explanatory annotations (not just steps), and the transition from examples to independent practice should be gradual. Renkl (2014) refined the theory, showing that self-explanation prompts embedded in worked examples significantly enhance learning because they promote germane processing. The fading approach — where worked examples gradually omit steps, creating "completion problems" — was shown by van Merriënboer & Kirschner (2018) to be more effective than an abrupt transition from examples to problems. Critically, Kalyuga et al. (2003) demonstrated the expertise reversal effect: worked examples that help novices become counterproductive for advanced learners, who learn better from problem-solving. This means fading must be calibrated to student expertise.

## Input Schema

The teacher must provide:
- **Skill to teach:** The specific procedure or skill. *e.g. "Solving simultaneous equations by elimination" / "Writing a topic sentence for an analytical paragraph" / "Balancing chemical equations"*
- **Student level:** Year group and expertise. *e.g. "Year 9, first encounter (novice)" / "Year 11 revision (developing)"*
- **Steps in procedure:** Approximate number of steps. *e.g. 5*

Optional (injected by context engine if available):
- **Common errors:** Known errors students typically make. *e.g. ["Forgetting to multiply both sides", "Sign errors when subtracting equations"]*
- **Student profiles:** Individual readiness data for differentiated fading rates
- **Prior knowledge:** What prerequisite knowledge students have

## Prompt

```
You are an expert in instructional design specialising in worked examples and cognitive load management. You have deep knowledge of Sweller & Cooper (1985) on the worked example effect, Renkl (2014) on self-explanation in worked examples, Atkinson et al. (2000) on design principles for example-based learning, and the fading approach from van Merriënboer & Kirschner (2018).

Your task is to design a complete worked example with completion fading for:

**Skill:** {{skill_to_teach}}
**Student level:** {{student_level}}
**Steps in procedure:** approximately {{steps_in_procedure}} steps

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Known common errors:** {{common_errors}} — if provided, build awareness of these specific errors into the worked example annotations. If not provided, include the most common errors for this procedure based on your subject knowledge.
**Prior knowledge:** {{prior_knowledge}} — if provided, connect new steps to this existing knowledge explicitly. If not provided, assume standard prerequisite knowledge for the stated year group.
**Student profiles:** {{student_profiles}} — if provided, consider differentiated fading rates for different readiness levels. If not provided, design a single fading sequence for a typical mixed-ability class.

Apply these evidence-based design principles:

1. **Complete worked example first (Sweller & Cooper, 1985):** The first example must show EVERY step, fully worked, with no gaps. The student's only task is to study and understand — not to solve anything.

2. **Annotate reasoning, not just steps (Renkl, 2014):** Each step must include a brief annotation explaining WHY this step is taken, not just WHAT is done. The annotation reveals expert thinking. Format: "Step → Reasoning annotation."

3. **Self-explanation prompts (Renkl, 2014):** After the worked example, include 2–3 self-explanation questions that prompt students to explain the reasoning behind key steps. These promote active processing rather than passive reading.

4. **Fading sequence (van Merriënboer & Kirschner, 2018):** Create 3–4 completion problems that progressively remove steps:
   - Completion 1: Remove the final step only. Student completes it.
   - Completion 2: Remove the final 2 steps.
   - Completion 3: Remove middle and final steps (student must do ~50% of the procedure).
   - Completion 4 (if needed): Only the first step is provided.
   Fade from the END of the procedure backward — the final steps are typically the most routine and least conceptually demanding.

5. **Error awareness (where applicable):** If common errors are provided, include a "common error" annotation at the step where the error typically occurs, showing what the error looks like and why it's wrong.

6. **Expertise reversal guard:** Note at what point the fading should accelerate for students who are demonstrating mastery, and when to move directly to independent practice.

Return your output in this exact format:

## Worked Example Sequence: [Skill Name]

**For:** [Student level]
**Fading strategy:** [Brief description of what is faded and why]

### Stage 1: Complete Worked Example

**Problem:** [A specific, realistic problem]

| Step | Action | Reasoning |
|------|--------|-----------|
| 1 | [What is done] | [Why this step — expert thinking made visible] |
| 2 | ... | ... |
| ... | ... | ... |

**Answer:** [Final answer]

**Self-explanation prompts:**
1. [Question prompting student to explain a key reasoning step]
2. [Question prompting comparison or connection]

### Stage 2: Completion Problems (Fading Sequence)

**Completion Problem 1:** [Final step removed]
**Completion Problem 2:** [More steps removed]
**Completion Problem 3:** [~50% removed]

For each, show the provided steps and clearly mark where the student takes over.

### Stage 3: Independent Practice

2–3 problems with no support. Different surface features from the worked example to promote transfer.

### Fading Rationale

[3–4 sentences explaining what is faded at each stage and why, connected to CLT principles]

### Expertise Reversal Note

[When to skip or accelerate stages for advanced learners]

**Self-check before returning output:** Verify that (a) every step in the worked example includes reasoning, not just procedure, (b) fading moves from end to beginning, (c) self-explanation prompts target reasoning not recall, (d) completion problems change surface features to prevent pattern matching, and (e) independent practice problems require the same procedure but look different from the worked example.
```

## Example Output

**Scenario:** *Skill: "Calculating the mean from a frequency table" / Student level: "Year 8 Mathematics, first encounter (novice)" / Steps: 5 / Common errors: ["Adding frequencies instead of multiplying value x frequency", "Dividing by number of rows instead of total frequency"]*

---

## Worked Example Sequence: Calculating the Mean from a Frequency Table

**For:** Year 8 Mathematics, novice
**Fading strategy:** Steps are removed from the end of the procedure backward, because the final steps (division and interpretation) are the most procedurally straightforward once the conceptual setup is understood. The middle steps (fx column, totals) are faded last because they contain the most conceptually demanding elements.

### Stage 1: Complete Worked Example

**Problem:** A teacher recorded the number of books each student read during the term. Calculate the mean number of books read.

| Books read (x) | Frequency (f) |
|:-:|:-:|
| 0 | 3 |
| 1 | 7 |
| 2 | 12 |
| 3 | 5 |
| 4 | 3 |

| Step | Action | Reasoning |
|------|--------|-----------|
| 1 | Add an fx column to the table. Multiply each value by its frequency: 0x3=0, 1x7=7, 2x12=24, 3x5=15, 4x3=12 | We need to find the total of ALL the values, not just the ones shown. "2 books" appears 12 times, so it contributes 2x12=24 books to the total, not just "2." This is where many errors happen — adding 0+1+2+3+4 would only give us the total if each value appeared once. |
| 2 | Find the total of the fx column: 0+7+24+15+12 = 58 | This gives us the total number of books read by ALL students combined. This is the "total of all values" in the mean formula. |
| 3 | Find the total frequency: 3+7+12+5+3 = 30 | This is the total number of students. We divide by THIS number, not by the number of rows in the table (5). Common error: dividing by 5 because there are 5 rows — but there are 30 students, not 5. |
| 4 | Calculate the mean: Total of fx / Total of f = 58 / 30 = 1.93 (2 d.p.) | Mean = sum of all values / number of values. We're using totals from the table because we can't add every individual value (we'd need to write "2" twelve times). The frequency table is a shortcut. |
| 5 | Interpret: The mean number of books read per student is 1.93, or approximately 2 books. | Always state what the mean represents in context. "1.93" alone is meaningless — "1.93 books per student" connects the calculation to the real situation. |

**Answer:** Mean = 1.93 books per student

**Common error alerts:**
- At Step 1: Students who add the x column (0+1+2+3+4 = 10) instead of multiplying x by f are treating the table as if each value appeared only once. Ask: "Did only one student read 2 books?"
- At Step 3: Students who divide by 5 (number of rows) instead of 30 (total frequency) are confusing the number of categories with the number of data points. Ask: "How many students are there — 5 or 30?"

**Self-explanation prompts:**
1. Why do we multiply each value by its frequency in Step 1, rather than just adding the values in the first column? What would go wrong if we only added 0+1+2+3+4?
2. In Step 3, we divide by 30, not by 5. Explain in your own words why dividing by 5 would give the wrong answer. What does each number represent?

### Stage 2: Completion Problems (Fading Sequence)

**Completion Problem 1** *(Step 5 removed — student interprets)*

A shop recorded shoe sizes sold in one day:

| Shoe size (x) | Frequency (f) | fx |
|:-:|:-:|:-:|
| 5 | 4 | 20 |
| 6 | 8 | 48 |
| 7 | 11 | 77 |
| 8 | 6 | 48 |
| 9 | 1 | 9 |
| **Total** | **30** | **202** |

Mean = 202 / 30 = 6.73

**Your turn:** Write a sentence interpreting this mean in context. What does 6.73 represent?

---

**Completion Problem 2** *(Steps 4–5 removed — student calculates and interprets)*

Students were asked how many siblings they have:

| Siblings (x) | Frequency (f) | fx |
|:-:|:-:|:-:|
| 0 | 5 | 0 |
| 1 | 9 | 9 |
| 2 | 8 | 16 |
| 3 | 6 | 18 |
| 4 | 2 | 8 |
| **Total** | **30** | **51** |

**Your turn:** Calculate the mean and write a sentence interpreting it.

---

**Completion Problem 3** *(Steps 2–5 removed — student calculates totals, mean, and interpretation)*

A PE teacher recorded how many laps students completed:

| Laps (x) | Frequency (f) | fx |
|:-:|:-:|:-:|
| 3 | 2 | 6 |
| 4 | 7 | 28 |
| 5 | 10 | 50 |
| 6 | 8 | _____ |
| 7 | 3 | _____ |
| **Total** | **_____** | **_____** |

**Your turn:** Complete the fx column for the remaining rows, find both totals, calculate the mean, and interpret your answer.

---

**Completion Problem 4** *(Only the table provided — student does the entire procedure)*

A survey asked students how many hours of homework they did last night:

| Hours (x) | Frequency (f) |
|:-:|:-:|
| 0 | 6 |
| 1 | 11 |
| 2 | 9 |
| 3 | 4 |

**Your turn:** Add an fx column, calculate all values, find the mean, and interpret your answer.

### Stage 3: Independent Practice

**Problem 1:** A dice was rolled 40 times. The results are recorded below. Calculate the mean score per roll.

| Score | 1 | 2 | 3 | 4 | 5 | 6 |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Frequency | 5 | 8 | 7 | 9 | 6 | 5 |

*(Different format: horizontal table, different context, same procedure)*

**Problem 2:** In a survey, 25 families reported the number of pets they own: 0 pets (8 families), 1 pet (9 families), 2 pets (5 families), 3 pets (2 families), 4 pets (1 family). Calculate the mean number of pets per family.

*(Different format: data given as text, not a table — student must construct the frequency table first)*

**Problem 3:** The mean test score for a class of 20 students is 14.5. The frequency table below is incomplete. Find the missing frequency.

| Score (x) | Frequency (f) |
|:-:|:-:|
| 12 | 4 |
| 13 | ? |
| 14 | 6 |
| 15 | 3 |
| 16 | 2 |
| 17 | 1 |

*(Reverse problem: given the mean, find the missing value — extends the same procedure in a new direction)*

### Fading Rationale

The fading sequence removes steps from the end of the procedure backward because the final steps (division and interpretation) are procedurally simpler and can be handed to the student first without overwhelming working memory. The middle steps (constructing the fx column and finding totals) are the most conceptually demanding — this is where the key insight lives (each value contributes frequency-many times to the total) — so these steps remain supported longest. By Completion Problem 4, only the raw table is provided and the student performs the entire procedure. Independent practice then varies the surface features (horizontal table, text-based data, reverse problem) to promote transfer beyond the specific format of the worked example.

### Expertise Reversal Note

If students are completing Completion Problem 2 accurately and confidently, skip directly to Completion Problem 4 or independent practice. Forcing advanced students through every fading stage wastes time and creates redundancy load (Kalyuga et al., 2003). For Year 11 students revising this topic, skip the worked example entirely — begin at independent practice and provide a worked example only if errors indicate the procedure isn't secure.

---

## Known Limitations

1. **Worked examples are most effective for procedural skills with clear steps.** For tasks that are primarily conceptual, creative, or require judgment (e.g., writing an essay, designing an experiment), the step-by-step worked example format is less applicable. The skill can still produce useful models, but the fading sequence may not transfer as cleanly to open-ended tasks.

2. **The fading sequence assumes relatively homogeneous student readiness.** In a mixed-ability class, some students will need more fading stages and some fewer. Teachers should use Completion Problem 2 as a checkpoint — if a student is accurate, move them forward faster. If they're struggling, provide an additional worked example with different numbers before continuing the fade.

3. **Surface feature variation in independent practice is crucial but hard to fully anticipate.** If all practice problems look too similar to the worked example, students may develop inflexible knowledge that only works for problems that look like the example. The skill attempts to vary surface features, but teachers should add further variations based on their knowledge of what problem formats appear in assessments.

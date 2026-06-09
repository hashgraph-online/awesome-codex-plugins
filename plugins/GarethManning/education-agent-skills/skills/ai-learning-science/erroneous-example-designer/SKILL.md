---
# AGENT SKILLS STANDARD FIELDS (v2)
name: erroneous-example-designer
description: "Design deliberately flawed examples that develop error-detection skills and deepen understanding. Use when students make characteristic errors and need practice spotting mistakes."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-learning-science/erroneous-example-designer"
skill_name: "Erroneous Example Designer"
domain: "ai-learning-science"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "McLaren, Adams & Mayer (2012) — Delayed learning effects with erroneous examples"
  - "McLaren, Adams, Durkin, Goguadze, Mayer & Rittle-Johnson (2015) — To err is human, to explain and correct is divine"
  - "Tsovaltzi, Melis, McLaren, Meyer, Dietrich & Goguadze (2010) — Learning from erroneous examples"
  - "Große & Renkl (2007) — Finding and fixing errors in worked examples"
  - "Siegler (2002) — Microgenetic studies of self-explanation"
input_schema:
  required:
    - field: "problem_domain"
      type: "string"
      description: "The type of problem or procedure where students make characteristic errors"
    - field: "target_errors"
      type: "string"
      description: "The specific, common errors students make — realistic misconceptions or procedural mistakes"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and proficiency level"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "correct_examples_available"
      type: "string"
      description: "Whether students have already seen correct worked examples for this problem type"
    - field: "number_of_examples"
      type: "integer"
      description: "How many erroneous examples to design"
    - field: "delivery_context"
      type: "string"
      description: "Whether delivered digitally, on paper, or discussed in class"
output_schema:
  type: "object"
  fields:
    - field: "erroneous_examples"
      type: "array"
      description: "The set of erroneous worked examples — each containing a realistic, common error at a specific step"
    - field: "error_analysis_scaffold"
      type: "object"
      description: "Prompts that guide students to find, explain, and correct each error"
    - field: "learning_mechanism"
      type: "object"
      description: "Why each erroneous example produces learning — the cognitive mechanism of error detection"
    - field: "correct_version"
      type: "object"
      description: "The corrected version of each example — for teacher reference and student self-checking"
chains_well_with:
  - "adaptive-hint-sequence-designer"
  - "worked-example-fading-designer"
  - "self-explanation-prompt-designer"
  - "diagnostic-question-generator"
teacher_time: "3 minutes"
tags: ["erroneous-examples", "McLaren", "error-detection", "worked-examples", "misconceptions", "self-explanation"]
---

# Erroneous Example Designer

## What This Skill Does

Designs worked examples that contain deliberate, realistic errors for students to identify, explain, and correct — a technique that produces learning effects comparable to or exceeding correct worked examples, with the additional benefit of developing error-detection skills. The critical insight from McLaren et al. (2012, 2015) is that errors must be REALISTIC and COMMON — the kinds of mistakes students actually make, not contrived errors that no one would make. A well-designed erroneous example activates self-explanation (Chi et al., 1989): students must reason about WHY the step is wrong, which forces deeper processing than simply following a correct procedure. The output includes the erroneous examples with realistic errors at specific steps, an error analysis scaffold (prompts that guide students to find and correct the error), the learning mechanism explanation, and the corrected version. AI is specifically valuable here because designing effective erroneous examples requires deep knowledge of the common error patterns for specific problem types — which errors are realistic, which are productively confusing, and which would create harmful misconceptions.

## Evidence Foundation

McLaren, Adams & Mayer (2012) found that students who studied erroneous examples showed significantly better retention and transfer than students who studied correct examples — but this effect was DELAYED (appearing on a one-week post-test, not an immediate test). This suggests that erroneous examples produce deeper, more durable learning than correct examples, possibly because the error-detection process forces more elaborate processing. McLaren et al. (2015) replicated and extended this finding, showing that the combination of erroneous examples WITH self-explanation prompts produced the strongest effects. Tsovaltzi et al. (2010) found that erroneous examples were particularly effective when students were prompted to explain WHY the error was wrong, not just to identify it. Große & Renkl (2007) found that erroneous examples improved learning when students had sufficient prior knowledge to detect the error — but could confuse students who lacked the prerequisite knowledge (they might learn the error as correct procedure). This establishes a critical design constraint: erroneous examples work AFTER students have seen correct examples, not as first exposure. Siegler (2002) showed that children benefit from explaining both correct and incorrect strategies — the contrast between "this works and this doesn't" deepens understanding more than studying either alone.

## Input Schema

The teacher must provide:
- **Problem domain:** The type of problem. *e.g. "Adding fractions with different denominators" / "Calculating percentage increase" / "Using apostrophes for possession vs. contraction" / "Balancing chemical equations"*
- **Target errors:** The specific common errors. *e.g. "Adding numerators and denominators separately: ½ + ⅓ = 2/5" / "Calculating percentage OF the increase rather than percentage increase: confusing 'what is 20% of 80?' with 'what is the percentage increase from 80 to 96?'" / "Using an apostrophe for plurals: apple's instead of apples" / "Changing coefficients into subscripts when balancing"*

Optional (injected by context engine if available):
- **Student level:** Year group and proficiency
- **Subject area:** Curriculum subject
- **Correct examples available:** Whether students have seen correct versions
- **Number of examples:** How many to design
- **Delivery context:** Digital, paper, or class discussion

## Prompt

```
You are an expert in erroneous example design for learning, with deep knowledge of McLaren et al.'s (2012, 2015) research on delayed learning effects from erroneous examples, Tsovaltzi et al.'s (2010) work on error-based learning, Große & Renkl's (2007) research on finding and fixing errors in worked examples, and Siegler's (2002) microgenetic studies of self-explanation with correct and incorrect strategies. You understand that erroneous examples are not "trick questions" — they are carefully designed learning tools where realistic, common errors are embedded at specific steps, and students learn by DETECTING, EXPLAINING, and CORRECTING the error.

CRITICAL PRINCIPLES:
- **Errors must be REALISTIC and COMMON.** The error should be one that students actually make — a genuine misconception or procedural slip, not an absurd mistake. "3 + 4 = 12" is not a realistic error. "½ + ⅓ = 2/5" IS a realistic error (adding numerators and denominators separately). Realistic errors activate recognition: "I've made this mistake" or "I can see why someone would think that."
- **One error per example.** An example with multiple errors is confusing, not instructive. Embed ONE error at ONE specific step, with all other steps correct. This isolates the learning target and makes detection feasible.
- **Students must already have seen correct examples.** Große & Renkl (2007) showed that erroneous examples confuse students who haven't seen correct versions first. Use erroneous examples AFTER correct worked examples, not instead of them. The sequence is: correct examples → erroneous examples → independent practice.
- **The error analysis scaffold is essential.** Simply showing an erroneous example is insufficient. Students need prompts: "Find the error," "Explain why it's wrong," "Correct it," "Explain why your correction is right." This scaffold forces the self-explanation that produces the learning effect.
- **Erroneous examples develop error-detection skills.** Beyond learning the specific content, students who practise with erroneous examples become better at monitoring their OWN work for errors. This metacognitive benefit is separate from and additional to the content learning.

Your task is to design erroneous examples for:

**Problem domain:** {{problem_domain}}
**Target errors:** {{target_errors}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for a general secondary school context.
**Subject area:** {{subject_area}} — if not provided, infer from the problem domain.
**Correct examples available:** {{correct_examples_available}} — if not provided, include a note that students should see correct examples first.
**Number of examples:** {{number_of_examples}} — if not provided, design 3 erroneous examples targeting different common errors.
**Delivery context:** {{delivery_context}} — if not provided, design for paper-based use that could be adapted for digital delivery.

Return your output in this exact format:

## Erroneous Examples: [Problem Domain]

**Problem domain:** [The type of problem]
**Target errors:** [The common errors being addressed]
**Prerequisite:** [What students must already know — correct examples must come first]

### Erroneous Example [N]

**The problem:** [The problem being solved]
**The erroneous solution:**
[Step-by-step solution with ONE deliberate error at a specific step — all other steps correct]

**The error:** [Which step is wrong and what the error is — FOR TEACHER REFERENCE ONLY, not shown to students]
**Why this error is realistic:** [Why students actually make this mistake — the underlying misconception or procedural confusion]

**Error Analysis Scaffold (for students):**
1. "Read through the solution carefully. Is every step correct?"
2. "Find the step that contains an error. Circle it."
3. "Explain WHY this step is wrong. What mistake was made?"
4. "Write the correct version of this step."
5. "Complete the problem correctly from this point."

### Correct Version (Teacher Reference)

[The fully correct solution for comparison]

### Learning Mechanism

[Why these erroneous examples produce learning — the cognitive process of error detection, explanation, and correction]

### Sequencing Guidance

[When to use these erroneous examples in a lesson — after correct examples, before independent practice]

**Self-check before returning output:** Verify that (a) each error is realistic and common, (b) there is only ONE error per example, (c) the error analysis scaffold requires explanation not just identification, (d) correct versions are provided for teacher reference, and (e) the examples are sequenced after correct worked examples.
```

## Example Output

**Scenario:** *Problem domain: "Adding fractions with different denominators — Year 6 Mathematics" / Target errors: "Error 1: Adding numerators and denominators separately (½ + ⅓ = 2/5). Error 2: Finding a common denominator but forgetting to adjust the numerators (½ + ⅓ = 1/6 + 1/6 = 2/6). Error 3: Correctly finding equivalent fractions but making an arithmetic error in the addition (3/6 + 2/6 = 6/6 instead of 5/6)." / Correct examples available: "Yes — students have completed correct worked examples of adding fractions with common denominators and have seen the procedure for finding common denominators"*

---

## Erroneous Examples: Adding Fractions With Different Denominators

**Problem domain:** Adding fractions with different denominators
**Target errors:** Adding numerators/denominators separately, forgetting to adjust numerators, arithmetic errors in final addition
**Prerequisite:** Students must have already studied correct worked examples of finding common denominators and adding equivalent fractions. Erroneous examples are used AFTER correct examples to deepen understanding.

### Erroneous Example 1: "Sam's Solution"

**The problem:** Calculate ½ + ⅓

**Sam's solution:**
- Step 1: I need to add ½ and ⅓
- Step 2: I add the numerators: 1 + 1 = 2
- Step 3: I add the denominators: 2 + 3 = 5
- Step 4: My answer is 2/5 ✓

**The error (teacher reference):** Step 2 and 3. Sam adds numerators and denominators separately, treating fraction addition like whole number addition. This is the most common fraction error and reflects a fundamental misconception about what fractions ARE — the denominator names the size of the parts, and you cannot add parts of different sizes by adding the size-names.

**Why this error is realistic:** Students who have just learned to add whole numbers extend the same logic to fractions. It "looks right" — you're adding the tops and adding the bottoms, just like you'd add two whole numbers. The error is so common that research consistently finds it in 30–50% of students learning fraction addition.

**Error Analysis Scaffold (for students):**
1. "Read Sam's solution. Does each step make sense?"
2. "Sam says ½ + ⅓ = 2/5. Think about this: ½ is the same as 0.5. Is 2/5 bigger or smaller than ½?" (2/5 = 0.4, which is SMALLER than ½ alone. This is impossible — adding a positive fraction to ½ must give a result bigger than ½.)
3. "Which step went wrong? Circle it and explain WHY it's wrong."
4. "What should Sam have done instead? Solve the problem correctly."
5. "Write Sam a note explaining the mistake in a way that would help them understand."

### Erroneous Example 2: "Priya's Solution"

**The problem:** Calculate ½ + ⅓

**Priya's solution:**
- Step 1: I need a common denominator. 2 and 3 both go into 6. The common denominator is 6.
- Step 2: ½ = 1/6 (I changed the denominator to 6)
- Step 3: ⅓ = 1/6 (I changed the denominator to 6)
- Step 4: 1/6 + 1/6 = 2/6
- Step 5: My answer is 2/6 ✓

**The error (teacher reference):** Steps 2 and 3. Priya correctly finds the common denominator (6) but changes ONLY the denominator without adjusting the numerator. She writes ½ = 1/6, but ½ = 3/6 (multiply both top and bottom by 3). Similarly, ⅓ = 2/6 (multiply both top and bottom by 2). Priya understands that she needs a common denominator but has not grasped that the fraction must remain EQUIVALENT — both parts must change by the same factor.

**Why this error is realistic:** Students who have been taught "find a common denominator" sometimes treat it as changing the bottom number without understanding that the fraction must stay equivalent. They follow the PROCEDURE (change the denominator) without understanding the PRINCIPLE (maintain equivalence). This is a procedural-without-conceptual error.

**Error Analysis Scaffold (for students):**
1. "Priya found the correct common denominator (6). Good start. But look at Step 2."
2. "Priya says ½ = 1/6. Use a diagram or fraction strips: is ½ the same as 1/6?" (No — ½ is much bigger than 1/6.)
3. "What went wrong? When Priya changed ½ to sixths, what should the numerator be? How do you know?"
4. "Correct Priya's work from Step 2 onwards."
5. "What RULE should Priya remember? (Hint: what you do to the bottom, you must also do to the ___)"

### Erroneous Example 3: "Marcus's Solution"

**The problem:** Calculate ½ + ⅓

**Marcus's solution:**
- Step 1: I need a common denominator. 2 and 3 both go into 6.
- Step 2: ½ = 3/6 (multiply top and bottom by 3) ✓
- Step 3: ⅓ = 2/6 (multiply top and bottom by 2) ✓
- Step 4: 3/6 + 2/6 = 6/6
- Step 5: 6/6 = 1 whole
- Step 6: My answer is 1 ✓

**The error (teacher reference):** Step 4. Marcus does everything correctly until the final addition: 3/6 + 2/6 = 5/6, not 6/6. This is a simple arithmetic error (3 + 2 = 5, not 6), but it leads to a plausible-looking final answer (1 whole) that might not trigger the student's error-detection because it "looks reasonable."

**Why this error is realistic:** Once students have successfully navigated the conceptually hard parts (finding common denominator, adjusting numerators), they can make careless arithmetic errors at the final step. Because the difficult conceptual work is done, students relax their monitoring and miss the simple mistake. Additionally, 6/6 = 1 looks like a "neat" answer, which confirms the error rather than flagging it.

**Error Analysis Scaffold (for students):**
1. "Marcus found the common denominator correctly and converted both fractions correctly. Well done so far."
2. "Look carefully at Step 4. Check the addition: 3 + 2 = ?"
3. "What should the correct answer be? Write the corrected step."
4. "Marcus's error was small — an arithmetic slip. But it changed the answer completely. What does this tell you about checking your work?"

### Correct Version (Teacher Reference)

½ + ⅓
= 3/6 + 2/6 (common denominator 6; ½ × 3/3 = 3/6; ⅓ × 2/2 = 2/6)
= 5/6

### Learning Mechanism

These three erroneous examples target three DIFFERENT types of error at three different points in the procedure:

1. **Example 1 (Sam):** A CONCEPTUAL error — misunderstanding what fraction addition means. Addresses the most fundamental misconception.
2. **Example 2 (Priya):** A PROCEDURAL-CONCEPTUAL gap — following the procedure without understanding why both numerator and denominator must change. Addresses the disconnect between procedure and understanding.
3. **Example 3 (Marcus):** An ARITHMETIC error — everything conceptually correct but a careless calculation mistake. Addresses monitoring and checking.

By presenting all three, students develop a taxonomy of error types: "When I add fractions, I need to check for conceptual errors (am I adding correctly?), procedural errors (did I adjust the numerators?), AND arithmetic errors (did I add the numbers right?)."

### Sequencing Guidance

**Lesson position:** Use these erroneous examples AFTER students have:
1. Learned the correct procedure through correct worked examples
2. Practised 2–3 problems with guided support

**Introduce as:** "Here are three students' solutions. Each one has made a mistake. Your job is to find the mistake, explain what went wrong, and fix it."

**Follow with:** Independent practice where students solve problems themselves — now with the error-detection skills to monitor their own work.

---

## Known Limitations

1. **Erroneous examples can create misconceptions if used before correct examples (Große & Renkl, 2007).** Students who encounter errors before they have a secure model of the correct procedure may inadvertently learn the error as correct. The sequencing is critical: correct examples FIRST, then erroneous examples to deepen understanding and develop error-detection skills.

2. **The learning effect is often DELAYED (McLaren et al., 2012).** Students who study erroneous examples may not outperform students who study correct examples on an immediate test — but they show superior retention and transfer on delayed tests (one week later). Teachers should be aware that the benefit may not be immediately visible, and should not conclude the approach has failed based on a same-day assessment.

3. **The quality of the error-analysis scaffold determines the learning effect.** Simply showing students an error and saying "find the mistake" produces much weaker effects than providing structured prompts that require explanation and correction (Tsovaltzi et al., 2010). The scaffold above is designed to force self-explanation — but if students skip the explanation step and just identify the error without reasoning about it, the learning benefit is significantly reduced.

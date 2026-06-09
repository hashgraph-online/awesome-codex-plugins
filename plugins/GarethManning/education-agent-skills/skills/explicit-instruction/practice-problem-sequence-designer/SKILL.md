---
# AGENT SKILLS STANDARD FIELDS (v2)
name: practice-problem-sequence-designer
description: "Generate a scaffolded sequence of practice problems with graduated difficulty and strategic variability. Use when creating worksheets, homework sets, or independent practice materials."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "explicit-instruction/practice-problem-sequence-designer"
skill_name: "Practice Problem Sequence Designer"
domain: "explicit-instruction"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Rosenshine (2012) — Principles of Instruction, Principles 5 & 8: guide student practice, provide scaffolds"
  - "Rohrer (2009) — The effects of spacing and mixing practice problems"
  - "Sweller et al. (2019) — Cognitive load theory: variability and worked example effects"
  - "Atkinson et al. (2000) — Learning from examples: varied practice promotes transfer"
  - "Bjork & Bjork (2011) — Making things hard on yourself, but in a good way: desirable difficulties"
input_schema:
  required:
    - field: "skill_to_practise"
      type: "string"
      description: "The specific skill students are practising"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current competence level"
    - field: "problem_count"
      type: "integer"
      description: "Number of practice problems to generate"
  optional:
    - field: "common_errors"
      type: "array"
      description: "Known errors to design problems around"
    - field: "prior_examples"
      type: "string"
      description: "The worked example or model students have already seen"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: ability range, specific needs"
    - field: "assessment_format"
      type: "string"
      description: "How students will be assessed — informs problem format variation"
output_schema:
  type: "object"
  fields:
    - field: "problem_sequence"
      type: "array"
      description: "Ordered sequence of problems with difficulty progression and design rationale"
    - field: "scaffold_reduction_plan"
      type: "string"
      description: "How scaffolding is reduced across the sequence"
    - field: "differentiation_options"
      type: "object"
      description: "Support and extension modifications"
    - field: "monitoring_guide"
      type: "string"
      description: "What to look for as students work and when to intervene"
chains_well_with:
  - "explicit-instruction-sequence-builder"
  - "worked-example-fading-designer"
  - "interleaving-unit-planner"
  - "cognitive-load-analyser"
teacher_time: "4 minutes"
tags: ["practice", "problem-design", "scaffolding", "variability", "desirable-difficulty"]
---

# Practice Problem Sequence Designer

## What This Skill Does

Designs a sequenced set of practice problems that follows principles of distributed difficulty, progressive scaffold reduction, and surface feature variation — moving students from near-transfer (problems very similar to the taught example) through to far-transfer (problems that look different but require the same underlying skill). The output includes the problems, the design rationale for each, scaffold reduction notes, and a monitoring guide for the teacher. AI is specifically valuable here because effective practice sequences require deliberate manipulation of difficulty, surface features, and scaffold levels — most teacher-designed practice sets are either randomly ordered (no progression) or uniformly difficult (no variation), both of which reduce learning.

## Evidence Foundation

Rosenshine (2012) identified guided and independent practice as Principles 5 and 8, emphasising that practice must be scaffolded (beginning with teacher support and gradually reducing it) and that students should achieve a high success rate (80%+) before scaffolds are removed. Rohrer (2009) demonstrated that mixing practice problem types (interleaving) and spacing practice across sessions produces substantially better retention than blocked, massed practice. Sweller et al. (2019) established the variability effect — practising with varied problem types promotes schema abstraction and transfer, while practising with identical problems promotes rigid, context-bound knowledge. Atkinson et al. (2000) showed that surface feature variation (changing the context, numbers, or presentation while keeping the underlying structure the same) is critical for transfer — students who only practise problems that look like the taught example fail when problems look different. Bjork & Bjork (2011) frame this as a "desirable difficulty" — practice that feels harder (because problems vary) produces better long-term learning than practice that feels easy (because problems are identical).

## Input Schema

The teacher must provide:
- **Skill to practise:** The specific skill. *e.g. "Solving linear equations with the unknown on both sides" / "Writing a paragraph using the PEEL structure" / "Drawing and interpreting box plots"*
- **Student level:** Year group and current level. *e.g. "Year 9, have just seen two worked examples — novice with this specific skill"*
- **Problem count:** How many problems. *e.g. 10*

Optional (injected by context engine if available):
- **Common errors:** Known errors to design problems around
- **Prior examples:** The worked example or model already shown
- **Student profiles:** Ability range, specific needs
- **Assessment format:** How students will be assessed

## Prompt

```
You are an expert in practice design and instructional sequencing, with deep knowledge of Rosenshine's (2012) practice principles, Rohrer's (2009) research on practice spacing and mixing, Sweller et al.'s (2019) variability effect, and Bjork & Bjork's (2011) concept of desirable difficulties. You understand that the sequence and structure of practice problems affects learning as much as the number of problems.

Your task is to design a practice problem sequence for:

**Skill:** {{skill_to_practise}}
**Student level:** {{student_level}}
**Number of problems:** {{problem_count}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Common errors:** {{common_errors}} — if not provided, identify the 2–3 most common errors for this skill and include problems specifically designed to surface them.
**Prior examples:** {{prior_examples}} — if not provided, assume students have seen a standard worked example and design the first 2 problems to closely match it.
**Student profiles:** {{student_profiles}} — if not provided, design for a mixed-ability class and include differentiation notes.
**Assessment format:** {{assessment_format}} — if not provided, include at least one problem in the format students are likely to encounter in assessments.

Apply these evidence-based principles:

1. **Near-to-far transfer progression (Atkinson et al., 2000):**
   - Problems 1–2: Nearly identical to the worked example (same structure, similar numbers, same context). Success rate should be 90%+. These build confidence and confirm basic understanding.
   - Problems 3–5: Same underlying skill, different surface features (different context, different numbers, different presentation). The student must recognise the same skill in a new wrapper.
   - Problems 6–8: Increased difficulty — additional steps, missing information to infer, or combining this skill with a previously learned skill.
   - Problems 9+: Far transfer — the problem looks substantially different from the worked example but requires the same underlying skill, possibly embedded in a larger problem or applied to a novel context.

2. **Surface feature variation (Sweller et al., 2019):**
   - Vary the context, numbers, format, and presentation while keeping the underlying structure constant.
   - If the worked example used a word problem about buying apples, practice problems should include different contexts (temperature, distance, money) — students who only practise apple problems can't solve temperature problems because they've learned "the apple procedure," not the underlying mathematics.

3. **Scaffold reduction (Rosenshine, 2012):**
   - Early problems may include partial scaffolds: a hint, a first step, or a reminder of the formula.
   - Middle problems remove these scaffolds.
   - Later problems require students to determine the method independently.

4. **Error-targeting problems:**
   - Include at least 2 problems specifically designed to surface common errors.
   - If students commonly confuse operation X with operation Y, include a problem where the wrong operation gives a plausible-looking answer — forcing students to think carefully about which approach is correct.

5. **One "twist" problem:**
   - Include at least one problem that looks like it requires this skill but actually doesn't — or that requires the student to explain why the skill doesn't apply. This tests whether students are thinking or just applying a procedure mechanically.

Return your output in this exact format:

## Practice Problem Sequence: [Skill]

**For:** [Student level]
**Total problems:** [Count]
**Scaffold reduction:** [Brief overview of how scaffolding reduces across the sequence]

### Problem Sequence

For each problem:
- **Problem [N]:** [The problem text]
- **Design intent:** [Why this problem is at this position — what it tests that previous problems didn't]
- **Difficulty level:** [Near transfer / Developing / Far transfer]
- **Common error to watch for:** [If applicable]

### Scaffold Reduction Plan

[How scaffolding decreases across the sequence — what support is provided early and removed later]

### Differentiation

**Support:** [How to modify for students who struggle — which problems to prioritise, what scaffolds to add back]
**Extension:** [How to challenge students who finish quickly — which problems to add]

### Monitoring Guide

[What the teacher should look for while students work: which problems are diagnostic, what errors signal which misunderstanding, when to intervene vs. let students struggle]

**Self-check before returning output:** Verify that (a) problems progress from near to far transfer, (b) surface features vary across the sequence, (c) at least 2 problems target common errors, (d) scaffolding decreases progressively, (e) one problem tests whether students can discriminate when the skill does/doesn't apply, and (f) the first 2 problems are accessible enough for 90%+ success rate.
```

## Example Output

**Scenario:** *Skill: "Calculating percentage increase and decrease" / Student level: "Year 9, have just seen a worked example of 'find 15% of £240 and add it to the original'" / Problem count: 10 / Common errors: ["Finding the percentage but forgetting to add/subtract it", "Calculating percentage of the new amount instead of the original"]*

---

## Practice Problem Sequence: Percentage Increase and Decrease

**For:** Year 9 Mathematics
**Total problems:** 10
**Scaffold reduction:** Problems 1–2 include a method reminder. Problems 3–5 remove the reminder. Problems 6–8 require method selection. Problems 9–10 embed the skill in unfamiliar contexts.

### Problem Sequence

**Problem 1:** A jacket costs £80. The price increases by 10%. What is the new price?
*Hint: First find 10% of £80, then add it to £80.*
- **Design intent:** Near-identical to the worked example. Same structure (percentage increase), friendly numbers (10% of a round number), hint provided. Confirms basic understanding.
- **Difficulty level:** Near transfer
- **Expected answer:** £88

**Problem 2:** A laptop costs £450. The price is reduced by 20% in a sale. What is the sale price?
*Hint: First find 20% of £450, then subtract it from £450.*
- **Design intent:** Introduces percentage decrease (subtract instead of add) but with a hint. Tests whether students can apply the reverse operation. Still friendly numbers.
- **Difficulty level:** Near transfer
- **Common error to watch for:** Students who add instead of subtract (get £540) — they're applying the increase method automatically without reading the question.

**Problem 3:** A gym membership costs £35 per month. The gym announces a 12% price increase. What is the new monthly cost?
- **Design intent:** No hint provided. Non-round percentage (12%). Smaller base number. Tests whether students can work without scaffolding and handle a less convenient percentage.
- **Difficulty level:** Developing
- **Expected answer:** £39.20

**Problem 4:** A house was bought for £185,000. Its value has decreased by 7%. What is it worth now?
- **Design intent:** Larger numbers (tests whether students can handle £185,000 without panicking), percentage decrease, and a real-world context shift (from shopping to property). Same underlying skill.
- **Difficulty level:** Developing
- **Common error to watch for:** Students who find 7% (£12,950) and write that as the answer — forgetting to subtract from the original.

**Problem 5:** A school has 840 students. Next year, the number of students is expected to increase by 5%. How many students will there be?
- **Design intent:** Context shift (people, not money). The answer must be a whole number (you can't have 0.5 of a student) — tests whether students interpret their answer in context.
- **Difficulty level:** Developing
- **Expected answer:** 882 (840 × 0.05 = 42; 840 + 42 = 882)

**Problem 6:** A car was worth £12,500 at the start of the year. By the end of the year, it was worth £11,250. What was the percentage decrease?
- **Design intent:** REVERSE problem — the percentage is unknown. Students must work backward: find the difference (£1,250), then calculate what percentage £1,250 is of £12,500. Tests deeper understanding of the relationship, not just forward application.
- **Difficulty level:** Far transfer
- **Common error to watch for:** Students who calculate £1,250 as a percentage of £11,250 (the new value) instead of £12,500 (the original) — this is one of the stated common errors.
- **Expected answer:** 10%

**Problem 7:** A shirt is advertised as "30% off! Now only £28." What was the original price?
- **Design intent:** Another reverse problem — this time finding the original from the reduced price. Students must recognise that £28 is 70% of the original (not 100%). This is significantly harder because it requires proportional reasoning.
- **Difficulty level:** Far transfer
- **Expected answer:** £40 (£28 ÷ 0.7 = £40)

**Problem 8:** A town's population increased by 15% to reach 9,200 people. What was the population before the increase?
- **Design intent:** Same structure as Problem 7 (find the original given the new value and the percentage change) but with increase instead of decrease and a different context. Tests whether students can transfer the reverse method across both directions.
- **Difficulty level:** Far transfer
- **Expected answer:** 8,000 (9,200 ÷ 1.15 = 8,000)

**Problem 9:** A shop increases prices by 20% and then offers a "20% off" sale. A customer says: "The 20% increase and 20% decrease cancel out, so the price is back to normal." Are they correct? Explain your answer using a specific example.
- **Design intent:** The "twist" problem. The answer is NO — a 20% increase followed by a 20% decrease does NOT return to the original price (e.g., £100 → £120 → £96). This surfaces a deep misconception about percentages and forces explanation, not just calculation.
- **Difficulty level:** Far transfer / Critical thinking
- **Expected answer:** No. Example: £100 + 20% = £120. £120 - 20% = £96, not £100. The 20% decrease is calculated on the higher amount.

**Problem 10:** An investment grows by 5% per year. If you invest £1,000, how much will it be worth after 3 years?
- **Design intent:** Compound percentage increase — the percentage applies to the new total each year, not the original. This extends the skill into a new territory (compound growth) and previews a future topic. It's OK if not all students get this — it's extension territory.
- **Difficulty level:** Far transfer / Extension
- **Expected answer:** £1,157.63 (£1,000 × 1.05³)

### Scaffold Reduction Plan

| Problems | Scaffold level |
|----------|---------------|
| 1–2 | Method hint provided ("First find X% of Y, then add/subtract") |
| 3–5 | No hints. Students must recall and apply the method independently |
| 6–8 | Reverse problems. Students must determine the method (work backward from a new value to find the original). No guidance on approach |
| 9–10 | Conceptual reasoning and extension. Students must explain, argue, or extend the skill into new territory |

### Differentiation

**Support (for students struggling with Problems 1–3):**
- Provide a method card: "Step 1: Find the percentage. Step 2: Add (increase) or subtract (decrease)."
- Reduce to Problems 1–5 only. Problems 6+ require secure forward application before attempting reverse problems.
- Pair with a worked example for Problem 6 (reverse percentage) — chain with Worked Example Fading Designer.

**Extension (for students who complete all 10):**
- Problem 11: "A price increases by 25% and then decreases by 20%. Is the final price higher, lower, or the same as the original? Prove it algebraically."
- Problem 12: "How many years would it take for an investment at 5% compound interest to double? Estimate first, then calculate."

### Monitoring Guide

- **Problems 1–2:** These should take 2–3 minutes. If a student is stuck here, they don't have the basic method — intervene immediately with a quick re-teach using the worked example.
- **Problem 4:** Check answers here. If students write £12,950 (the percentage amount rather than the new value), they understand the calculation but are forgetting the final step. This is a procedural reminder, not a re-teach.
- **Problem 6:** This is the diagnostic problem. If students attempt to divide by the wrong amount (e.g., finding the percentage of the new value instead of the original), they have the common misconception. Stop and address with a targeted example: "The percentage change is always calculated relative to the ORIGINAL amount."
- **Problem 9:** Don't reveal the answer if students say "yes, they cancel out." Instead ask: "Test it with £100. Show me the maths." Let the surprise of getting £96 (not £100) create cognitive conflict.
- **General rule:** Circulate for the first 5 minutes, checking Problems 1–3. If 80%+ are correct on Problem 3, the class is ready to continue independently. If fewer than 80%, pause and address the gap.

---

## Known Limitations

1. **The problem sequence assumes a single skill focus.** Real exam problems often combine multiple skills (percentage change + reading a graph + interpreting in context). This sequence builds fluency with the core skill; interleaving with other skills should happen in subsequent lessons, not within this initial practice set. Chain with Interleaving Unit Planner for mixed practice in later lessons.

2. **Surface feature variation may confuse students who haven't mastered the basic procedure.** For very low-ability students, too much variation too early can feel overwhelming. For these students, begin with 4–5 near-transfer problems (varying only the numbers) before introducing context variation. The sequence can be compressed by skipping Problems 1–2 for higher-ability groups.

3. **The monitoring guide requires the teacher to circulate effectively.** Designing good problems is necessary but not sufficient — the teacher must actually observe students working, identify error patterns, and intervene at the right moment. The guide helps direct attention but cannot replace the teacher's professional judgment about when to let students struggle and when to step in.

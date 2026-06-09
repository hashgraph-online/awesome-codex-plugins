---
# AGENT SKILLS STANDARD FIELDS (v2)
name: interleaving-unit-planner
description: "Redesign a blocked topic sequence into an interleaved plan with mixed practice across related topics. Use when planning units, homework schedules, or revision programmes."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "memory-learning-science/interleaving-unit-planner"
skill_name: "Interleaving Unit Planner"
domain: "memory-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Kornell & Bjork (2008) — Learning concepts and categories: is spacing the enemy of induction?"
  - "Rohrer et al. (2015) — Interleaved practice improves mathematics learning in a classroom setting"
  - "Taylor & Rohrer (2010) — The effects of interleaved practice on learning"
  - "Bjork & Bjork (2011) — Making things hard on yourself, but in a good way: creating desirable difficulties"
  - "Pan (2015) — The interleaving effect: mixing it up boosts learning"
input_schema:
  required:
    - field: "topics"
      type: "array"
      description: "The sequence of topics currently planned in blocked order"
    - field: "subject"
      type: "string"
      description: "The subject area and year group"
    - field: "unit_length"
      type: "string"
      description: "How many lessons or weeks the unit covers"
  optional:
    - field: "prerequisite_dependencies"
      type: "array"
      description: "Topics that must be taught before others (hard constraints)"
    - field: "curriculum_sequence"
      type: "string"
      description: "From context engine: mandated curriculum order"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: class ability profile, prior knowledge levels"
output_schema:
  type: "object"
  fields:
    - field: "interleaved_sequence"
      type: "array"
      description: "Restructured lesson sequence with interleaving applied"
    - field: "interleaving_rationale"
      type: "string"
      description: "Why these specific topics benefit from interleaving"
    - field: "teacher_briefing"
      type: "string"
      description: "How to explain the approach to students who will find it harder"
    - field: "blocked_vs_interleaved"
      type: "string"
      description: "Side-by-side comparison of original and interleaved sequence"
chains_well_with:
  - "spaced-practice-scheduler"
  - "retrieval-practice-generator"
  - "practice-problem-sequence-designer"
  - "cognitive-load-analyser"
teacher_time: "5 minutes"
tags: ["interleaving", "desirable-difficulty", "planning", "memory", "practice"]
---

# Interleaving Unit Planner

## What This Skill Does

Takes a blocked topic sequence (Topic A, A, A, then Topic B, B, B) and restructures it to interleave related but distinct concepts (A, B, A, C, B, A...), producing a sequence that exploits the interleaving effect to improve long-term retention and discrimination between similar concepts. The output includes the restructured plan, the rationale for interleaving these specific topics, and a briefing for explaining the approach to students. AI is specifically valuable here because interleaving requires identifying which topics benefit from interleaving (related but distinct concepts), which must stay blocked (genuinely prerequisite knowledge), and how to sequence the interleaving pattern — a task that requires understanding both the cognitive science and the specific subject content.

## Evidence Foundation

Kornell & Bjork (2008) demonstrated that interleaving the study of different categories (as opposed to studying each category in a block) improved later classification accuracy by 30–40%, despite students rating blocked study as more effective. Rohrer et al. (2015) confirmed these findings in a real mathematics classroom: students who practised interleaved problem sets scored 25% higher on a delayed test than students who practised blocked problem sets. Taylor & Rohrer (2010) showed that the benefit of interleaving is especially strong for tasks requiring discrimination — knowing which strategy or concept to apply, not just how to apply it. Bjork & Bjork (2011) explain interleaving as a "desirable difficulty" — it makes initial learning feel harder and slower, but produces substantially better long-term retention and transfer. Critically, interleaving works because it forces learners to discriminate between similar concepts on every practice attempt, rather than knowing the answer type in advance because they're in a "block" of that topic.

## Input Schema

The teacher must provide:
- **Topics:** The current sequence of topics, in the order currently planned. *e.g. ["Fractions — addition", "Fractions — subtraction", "Fractions — multiplication", "Fractions — division"]*
- **Subject:** Subject area and year group. *e.g. "Year 8 Mathematics"*
- **Unit length:** Duration of the unit. *e.g. "12 lessons over 4 weeks"*

Optional (injected by context engine if available):
- **Prerequisite dependencies:** Topics that must come before others. *e.g. "Addition must precede subtraction"*
- **Curriculum sequence:** Any mandated order from the school's scheme of work
- **Student profiles:** Class ability profile and prior knowledge data

## Prompt

```
You are an expert in the cognitive psychology of learning, specialising in the interleaving effect and desirable difficulties. You have deep knowledge of Kornell & Bjork (2008), Rohrer et al. (2015), and Taylor & Rohrer (2010) on how interleaved practice improves discrimination and long-term retention compared to blocked practice.

Your task is to restructure the following blocked topic sequence into an interleaved plan:

**Subject:** {{subject}}
**Current blocked sequence:** {{topics}}
**Unit length:** {{unit_length}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Prerequisite constraints:** {{prerequisite_dependencies}} — if provided, these are hard constraints: do not interleave a topic before its prerequisite has been taught. If not provided, infer likely prerequisites from the topic content and flag your assumptions.
**Mandated sequence:** {{curriculum_sequence}} — if provided, respect this where possible and explain any deviations. If not provided, treat the listed topic order as the teacher's preferred sequence.
**Student profiles:** {{student_profiles}} — if provided, adjust the density of interleaving based on ability (lower-ability students may need more initial blocked practice before interleaving begins). If not provided, design for a typical mixed-ability class.

Apply these evidence-based principles:

1. **Interleave related but distinct concepts.** Interleaving works best when topics are related enough to require discrimination but distinct enough to have different solution strategies. Topics that are entirely unrelated (e.g., fractions and Shakespeare) don't benefit — there's no discrimination challenge. Topics that are almost identical (e.g., two lessons on the same sub-skill) should stay blocked during initial instruction.

2. **Teach before interleaving.** Each topic needs initial instruction in a focused block (typically 1–2 lessons) before it enters the interleaved rotation. Interleaving is a practice strategy, not an instruction strategy. Students need to understand each concept individually before being asked to discriminate between them.

3. **Introduce interleaving progressively.** Start with 2-topic interleaving, then add topics as students become comfortable. Don't interleave all topics simultaneously from lesson 1.

4. **Expect it to feel harder.** Kornell & Bjork (2008) found that students rated blocked practice as more effective even when interleaved practice produced better outcomes. Build in a brief explanation for students about why this approach feels harder but works better.

5. **Respect prerequisite dependencies.** Some topics genuinely require prior knowledge of another topic. These must stay in sequence. Interleave around constraints, not through them.

6. **Include discrimination practice.** The key benefit of interleaving is forcing students to decide WHICH strategy or concept applies, not just HOW to apply it. Include mixed-practice tasks where students must first identify the problem type.

Return your output in this exact format:

## Interleaved Unit Plan: [Subject/Unit Title]

### Original Blocked Sequence vs. Interleaved Sequence

A side-by-side comparison showing the original plan and the restructured plan.

### Interleaved Lesson Sequence

For each lesson, show:
- **Lesson [N]:** [Primary teaching focus] + [Interleaved practice from previous topic(s)]
- Note which topics are being interleaved in practice tasks

### Interleaving Rationale

3–4 sentences explaining why these specific topics benefit from interleaving, what discrimination challenge it creates, and what the expected benefit is.

### Student Briefing Script

A 4–5 sentence script the teacher can use to explain to students why the practice feels harder and why that's productive.

### Practice Task Examples

For 2–3 lessons, provide specific interleaved practice tasks that force discrimination between topics.

**Self-check before returning output:** Verify that (a) prerequisite dependencies are respected, (b) each topic receives initial blocked instruction before entering interleaved practice, (c) the interleaving is between related concepts that require discrimination, (d) mixed practice tasks require students to identify the problem type, not just solve it, and (e) the plan is realistic for the given number of lessons.
```

## Example Output

**Scenario:** *Topics: ["Area of triangles", "Area of parallelograms", "Area of trapeziums", "Area of compound shapes"] / Subject: "Year 8 Mathematics" / Unit length: "10 lessons over 2.5 weeks" / Prerequisite dependencies: "Compound shapes requires all three individual shape types first"*

---

## Interleaved Unit Plan: Year 8 Mathematics — Area of 2D Shapes

### Original Blocked Sequence vs. Interleaved Sequence

| Lesson | Blocked (Original) | Interleaved (Restructured) |
|--------|-------------------|---------------------------|
| 1 | Area of triangles | Area of triangles — initial teaching |
| 2 | Area of triangles | Area of triangles — practice + intro parallelograms |
| 3 | Area of triangles | Area of parallelograms — initial teaching |
| 4 | Area of parallelograms | Mixed practice: triangles and parallelograms |
| 5 | Area of parallelograms | Area of trapeziums — initial teaching |
| 6 | Area of parallelograms | Mixed practice: triangles, parallelograms, trapeziums |
| 7 | Area of trapeziums | Discrimination challenge: "Which formula? Which shape?" |
| 8 | Area of trapeziums | Area of compound shapes — initial teaching |
| 9 | Area of compound shapes | Mixed practice: all four shape types interleaved |
| 10 | Area of compound shapes | Assessment: interleaved problem set |

### Interleaved Lesson Sequence

**Lesson 1:** Teach area of triangles (base x height / 2). Focused blocked practice — 10 worked examples and 10 independent problems. Students need fluency with the formula before interleaving begins.

**Lesson 2:** Brief triangles recap (5 min retrieval), then introduce area of parallelograms (base x perpendicular height). Last 10 minutes: 6 practice problems — 3 triangles, 3 parallelograms, shuffled order. Students must identify the shape type and select the correct formula.

**Lesson 3:** Teach area of parallelograms in depth. Focused blocked practice with parallelograms, including problems where the perpendicular height must be identified from a diagram (common error source).

**Lesson 4 — First full interleaving session:** No new content. Mixed practice set: 12 problems with triangles and parallelograms in random order. Crucially, some problems present shapes at unusual orientations or with extra measurements that must be ignored. Students must (1) identify the shape, (2) select the formula, (3) identify the correct measurements, (4) calculate.

**Lesson 5:** Teach area of trapeziums ((a + b) / 2 x h). Focused blocked practice. Highlight the relationship between trapezium formula and the triangle/parallelogram formulas.

**Lesson 6 — Three-topic interleaving:** Mixed practice: 15 problems interleaving all three shape types. Include problems where shapes look similar (e.g., a parallelogram oriented to look like a trapezium). Last 5 minutes: students sort 10 shapes into categories before calculating.

**Lesson 7 — Discrimination challenge:** "Which formula? Which shape?" Students receive 20 problems. For the first 10, they do NOT calculate — they only identify the shape type and write the correct formula. For the final 10, they identify and calculate. This isolates the discrimination skill that interleaving develops.

**Lesson 8:** Teach area of compound shapes. Demonstrate decomposing compound shapes into triangles, parallelograms, and trapeziums. Blocked practice on decomposition strategy.

**Lesson 9 — Full interleaving:** Mixed set of 15 problems: individual shapes (requiring formula selection) and compound shapes (requiring decomposition + formula selection). Random order.

**Lesson 10 — Assessment:** Interleaved assessment with all four shape types in random order, including compound shapes. This tests both calculation skill and the discrimination ability that interleaving builds.

### Interleaving Rationale

These four topics are ideal for interleaving because they share a surface structure (2D shapes, base, height, area formula) but require different solution strategies. The core discrimination challenge is: given a shape, which formula applies? In blocked practice, students never face this decision — they know every problem uses the same formula because they're "in the parallelograms chapter." Interleaving forces the decision on every single problem, which is exactly the challenge they'll face on any assessment or real-world application. Rohrer et al. (2015) found this specific type of mathematical interleaving produced a 25% improvement on delayed tests.

### Student Briefing Script

"For the next few lessons, we're going to mix up our practice instead of doing all triangle problems, then all parallelogram problems. This will feel harder — you might feel like you're getting more wrong and learning less. That's actually a sign that your brain is working harder, because you have to think about WHICH method to use, not just how to use it. Research by Professor Doug Rohrer and his team showed that students who practised this way scored 25% higher on tests weeks later, even though they felt less confident during practice. Trust the process — the difficulty is the point."

### Practice Task Examples

**Lesson 4 — Mixed practice set (sample):**
1. Find the area of a triangle with base 8 cm and height 5 cm.
2. Find the area of a parallelogram with base 12 cm and perpendicular height 4 cm.
3. A triangle has a base of 6.5 cm and a height of 9 cm. Calculate its area.
4. Find the area of this parallelogram. [Diagram shows a parallelogram with base 10 cm, slant side 7 cm, and perpendicular height 6 cm — students must ignore the slant side]
5. A triangle is drawn with measurements 4 cm, 7 cm, and a height of 3.5 cm. Which measurement is not needed? Calculate the area.
6. Find the area of a parallelogram where the base is 15 cm and the height is 8 cm.

**Lesson 7 — Discrimination-only task (sample):**
"For each shape below, do NOT calculate. Write: (a) the shape type, (b) the correct formula, (c) which measurements from the diagram you would use."
[10 shapes at various orientations with multiple measurements shown, including irrelevant ones]

---

## Known Limitations

1. **Interleaving is a practice strategy, not an instruction strategy.** This skill restructures practice sequences; it does not help with initial instruction quality. If students don't understand a concept after its initial blocked teaching, interleaving that concept with others will increase confusion, not learning. Check for understanding before interleaving.

2. **The evidence base is strongest for mathematics and category-learning tasks.** Rohrer et al. (2015) and Taylor & Rohrer (2010) used mathematical and perceptual classification tasks. Transfer to humanities subjects (e.g., interleaving essay types, historical periods) is theoretically supported but has less direct experimental evidence. Use with appropriate caution outside mathematics and science.

3. **Students and sometimes colleagues will resist.** Kornell & Bjork (2008) consistently found that learners rated blocked practice as more effective. Teachers may face pushback from students ("this is confusing"), parents ("they're jumping around"), and colleagues ("they need to master one topic before moving on"). The student briefing script is essential, not optional.

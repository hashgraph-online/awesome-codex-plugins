---
# AGENT SKILLS STANDARD FIELDS (v2)
name: cpa-sequence-designer
description: "Design a Concrete-Pictorial-Abstract learning sequence for a mathematical concept using manipulatives. Use when teaching maths through Singapore method or when students struggle with abstraction."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "global-cross-cultural-pedagogies/cpa-sequence-designer"
skill_name: "Concrete-Pictorial-Abstract Sequence Designer"
domain: "global-cross-cultural-pedagogies"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Bruner (1966) — Toward a Theory of Instruction (enactive, iconic, symbolic)"
  - "Ministry of Education Singapore (2012) — Mathematics Syllabus: Primary and Secondary"
  - "Leong, Ho & Cheng (2015) — Concrete-Pictorial-Abstract: surveying its origins and charting its future"
  - "Fyfe, McNeil, Son & Goldstone (2014) — Concreteness fading in mathematics and science instruction"
  - "Kaur (2019) — The what, why and how of the 'Model' method in Singapore mathematics"
input_schema:
  required:
    - field: "mathematical_concept"
      type: "string"
      description: "The concept students need to understand — what they should grasp at abstract level by the end"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current mathematical understanding"
  optional:
    - field: "current_approach"
      type: "string"
      description: "How the teacher currently teaches this concept — what they do now"
    - field: "common_errors"
      type: "string"
      description: "Typical mistakes students make with this concept"
    - field: "available_manipulatives"
      type: "string"
      description: "Physical resources available — cubes, counters, base-ten blocks, fraction pieces"
    - field: "lesson_time"
      type: "string"
      description: "How much lesson time is available for the CPA sequence"
output_schema:
  type: "object"
  fields:
    - field: "cpa_sequence"
      type: "object"
      description: "The complete C→P→A sequence — what students do at each stage, with explicit bridging between stages"
    - field: "concrete_stage"
      type: "object"
      description: "Manipulative-based activities — what students physically handle and what understanding this builds"
    - field: "pictorial_stage"
      type: "object"
      description: "Visual representation activities — bar models, diagrams, number lines — bridging concrete to abstract"
    - field: "abstract_stage"
      type: "object"
      description: "Symbolic/numerical work — connecting to the formal mathematical notation"
    - field: "bridging_questions"
      type: "array"
      description: "Questions that help students connect each stage to the next"
chains_well_with:
  - "variation-theory-task-designer"
  - "worked-example-fading-designer"
  - "explicit-instruction-sequence-builder"
  - "diagnostic-question-generator"
  - "pedagogical-content-knowledge-developer"
teacher_time: "4 minutes"
tags: ["CPA", "Singapore-maths", "Bruner", "manipulatives", "bar-model", "concreteness-fading", "mathematics"]
---

# Concrete-Pictorial-Abstract Sequence Designer

## What This Skill Does

Designs a learning sequence that moves students from concrete manipulation (physical objects), through pictorial representation (diagrams, bar models, number lines), to abstract notation (symbols and numbers) — following the CPA approach central to the Singapore Mathematics Curriculum Framework. The approach is rooted in Bruner's (1966) theory that learners progress through enactive (action-based), iconic (image-based), and symbolic (language/symbol-based) modes of representation. The critical insight is that the stages are not separate activities but a connected progression — each stage builds understanding that makes the next stage meaningful. The output includes activities for each stage with explicit bridging questions that help students see the connection between what they did with objects, what they drew in diagrams, and what the numbers and symbols mean. AI is specifically valuable here because designing effective CPA sequences requires ensuring that the concrete and pictorial stages genuinely represent the mathematical structure (not just illustrate it), and that the transitions between stages are explicit, not assumed.

## Evidence Foundation

Bruner (1966) proposed that learners represent knowledge in three modes: enactive (through action — handling objects), iconic (through images — diagrams and pictures), and symbolic (through symbols — words and numbers). He argued that new concepts should be introduced through enactive experience before being represented iconically and then symbolically. The Singapore Ministry of Education (2012) adopted this as the CPA approach at the heart of their mathematics curriculum, producing a system that consistently ranks among the top performers in international assessments (TIMSS, PISA). Leong, Ho & Cheng (2015) traced the Singapore implementation, showing that CPA is not merely "use concrete materials" but a carefully designed progression where each stage is deliberately connected to the next. The pictorial stage — particularly the bar model (a rectangular visual representation of mathematical relationships) — is a distinctive Singapore contribution that bridges concrete manipulation and abstract algebra. Fyfe et al. (2014) provided experimental evidence for "concreteness fading" — starting with concrete representations and gradually removing concrete features until only the abstract structure remains. They showed that starting concrete and fading to abstract produced better transfer than starting abstract, starting concrete without fading, or using concrete and abstract simultaneously. Kaur (2019) documented the "Model method" (bar modelling) in Singapore mathematics, showing how this pictorial tool enables students to represent and solve complex word problems that would otherwise require algebraic equations.

## Input Schema

The teacher must provide:
- **Mathematical concept:** What students need to understand. *e.g. "Adding fractions with different denominators" / "Solving word problems involving ratio" / "Understanding place value in 3-digit numbers" / "Multiplying a 2-digit number by a 1-digit number"*
- **Student level:** Year group and current understanding. *e.g. "Year 4, can add fractions with same denominators but struggle when denominators are different" / "Year 2, understand tens and ones but get confused with hundreds"*

Optional (injected by context engine if available):
- **Current approach:** How the teacher currently teaches this
- **Common errors:** Typical mistakes students make
- **Available manipulatives:** Physical resources available
- **Lesson time:** Time available

## Prompt

```
You are an expert in the Concrete-Pictorial-Abstract (CPA) approach as implemented in the Singapore Mathematics Curriculum Framework, with deep knowledge of Bruner's (1966) representational theory, the Singapore MOE's (2012) mathematics syllabus design, Leong et al.'s (2015) analysis of CPA implementation, Fyfe et al.'s (2014) research on concreteness fading, and Kaur's (2019) documentation of the Singapore bar model method. You understand that CPA is not "use blocks, then draw, then do sums" — it is a carefully designed progression where each stage builds a specific aspect of understanding that is EXPLICITLY connected to the next stage.

CRITICAL PRINCIPLES:
- **The concrete stage must represent the mathematical structure.** Giving students cubes to count is not CPA — it's just counting with props. The concrete manipulation must embody the mathematical relationship. For fractions: physically breaking a whole into parts and comparing. For multiplication: arranging objects into arrays where the structure of rows × columns IS multiplication.
- **The pictorial stage is not illustration — it is a thinking tool.** Bar models, number lines, and diagrams are not pictures of the answer — they are tools for THINKING about the mathematical structure. Students should learn to draw the representation as a problem-solving strategy, not just as a way to show their working.
- **Bridging between stages must be EXPLICIT.** The most common CPA failure is assuming students will automatically see the connection between the concrete, the pictorial, and the abstract. They won't. The teacher must explicitly connect: "Remember when you broke the fraction strip into quarters? This bar model shows the same thing. And this fraction symbol ¼ means the same thing again." Each stage must be named and linked.
- **Concreteness fading, not replacement.** The concrete stage is not abandoned when students move to pictorial — it remains available as a reference. Students should be able to move BACK to a previous stage if they get confused at a higher level. The stages are cumulative, not sequential.

Your task is to design a CPA sequence for:

**Mathematical concept:** {{mathematical_concept}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Current approach:** {{current_approach}} — if not provided, design the full CPA sequence from scratch.
**Common errors:** {{common_errors}} — if not provided, identify likely errors from the concept.
**Available manipulatives:** {{available_manipulatives}} — if not provided, suggest accessible, low-cost manipulatives.
**Lesson time:** {{lesson_time}} — if not provided, design for a 60-minute lesson.

Return your output in this exact format:

## CPA Sequence: [Mathematical Concept]

**Concept:** [What students will understand]
**Students:** [Year group and starting point]
**Mathematical structure:** [The underlying mathematical relationship the CPA sequence must represent]

### Stage 1 — Concrete (Enactive)

**Manipulative:** [What physical objects students use]
**Activity:** [What students do with the objects — step by step]
**What this builds:** [What understanding the concrete manipulation develops]
**Key teacher language:** [What the teacher says to name the mathematical structure while students manipulate]

### Bridging: Concrete → Pictorial

[How the teacher explicitly connects the physical objects to the visual representation — "This block you're holding is the same as this bar I'm drawing"]

### Stage 2 — Pictorial (Iconic)

**Representation:** [Bar model / number line / array diagram / other visual tool]
**Activity:** [What students draw and how they use the representation to solve problems]
**What this builds:** [What understanding the pictorial representation develops beyond the concrete stage]
**Key teacher language:** [What the teacher says to connect the diagram to the physical experience]

### Bridging: Pictorial → Abstract

[How the teacher explicitly connects the visual representation to the symbolic notation — "This section of the bar model represents the same thing as this number in the equation"]

### Stage 3 — Abstract (Symbolic)

**Notation:** [The formal mathematical symbols and procedures]
**Activity:** [What students do with numbers and symbols]
**What this builds:** [Fluent, flexible use of the abstract notation, grounded in concrete and pictorial understanding]
**Connection back:** [How students can return to pictorial or concrete representations if they get stuck at the abstract level]

### Common Errors and CPA Responses

[For each common error, explain which CPA stage addresses it — "Students who make this error need to return to the concrete/pictorial stage because..."]

### Assessment Check

[How to verify that students understand the concept at all three levels — not just procedurally at the abstract level]

**Self-check before returning output:** Verify that (a) the concrete stage genuinely represents the mathematical structure, not just provides counting props, (b) the pictorial stage is a thinking tool, not just an illustration, (c) the bridging between stages is explicit — the teacher names the connection, (d) all three stages represent the SAME mathematical relationship in different modes, and (e) the sequence allows students to move back to earlier stages when needed.
```

## Example Output

**Scenario:** *Mathematical concept: "Adding fractions with different denominators — for example, ½ + ⅓" / Student level: "Year 5, comfortable adding fractions with the same denominator (⅓ + ⅓ = ⅔), but confused when denominators are different — many students add numerators and denominators separately (½ + ⅓ = ⅖)" / Common errors: "Adding numerators and denominators: ½ + ⅓ = 2/5. Not understanding why you need a common denominator. Finding a common denominator procedurally but not understanding what it means." / Available manipulatives: "Fraction strips, fraction circles, Cuisenaire rods"*

---

## CPA Sequence: Adding Fractions With Different Denominators

**Concept:** Adding fractions with different denominators by finding equivalent fractions with a common denominator
**Students:** Year 5, can add like fractions, confused by unlike fractions
**Mathematical structure:** To add fractions, the parts must be the SAME SIZE (same denominator). If the parts are different sizes, they must be subdivided into equal-sized parts before combining. This is what finding a common denominator means — making the parts the same size so they can be counted together.

### Stage 1 — Concrete (Enactive)

**Manipulative:** Fraction strips — paper strips of equal length divided into halves, thirds, quarters, sixths, twelfths.

**Activity:**
1. Give each student a "half" strip and a "third" strip. Ask: "How much pizza do you have altogether if you eat half of one pizza and a third of another?" Students place the ½ strip and the ⅓ strip end-to-end. They can see the total length, but they cannot NAME it because the pieces are different sizes.

2. Ask: "Can you tell me EXACTLY how much that is? Not 'a bit more than a half' — an exact fraction?" Students will struggle. This is the key moment: you CANNOT just count the pieces because they're DIFFERENT SIZES. ½ is not the same size as ⅓. You can't say "1 + 1 = 2 pieces" because the pieces are different.

3. Now give students the sixths strip. Ask: "Can you find pieces from the sixths strip that are exactly the same length as your half? How many sixths make a half?" Students physically lay sixths on top of the half strip: 3 sixths = 1 half. Then: "How many sixths make a third?" 2 sixths = 1 third.

4. Replace the ½ strip with 3/6 and the ⅓ strip with 2/6. Now the pieces are the SAME SIZE. Ask: "Now can you tell me the total?" 3 sixths + 2 sixths = 5 sixths. The pieces are the same size, so they can be counted.

**What this builds:** The physical experience of WHY you need a common denominator — you cannot combine pieces of different sizes. Students feel the problem (the pieces don't match) before they learn the solution (find equivalent pieces that do match).

**Key teacher language:** "The pieces are different sizes. We can't count them together until they're the same size. We need to find smaller pieces that match both." Use the word "same size" repeatedly — this IS what "common denominator" means.

### Bridging: Concrete → Pictorial

The teacher draws the fraction strips on the board WHILE students still have the physical strips in front of them:

"Look at your fraction strips. I'm going to draw exactly what you have." Draw a bar divided into 2 (shade 1). "This is your half." Draw a bar divided into 3 (shade 1). "This is your third." Draw a bar divided into 6 (shade 3). "This is your 3 sixths — the same as your half." Draw a bar divided into 6 (shade 2). "This is your 2 sixths — the same as your third."

"Can you see that my drawing shows the same thing as your strips? Put your strips next to my drawing and check."

### Stage 2 — Pictorial (Iconic)

**Representation:** Bar models — rectangular bars of equal length, divided into sections.

**Activity:**
1. Students draw their OWN bar models (not just look at the teacher's). Problem: "What is ½ + ¼?" Students draw:
   - A bar divided into 2, shade 1 section (½)
   - A bar divided into 4, shade 1 section (¼)
   - Ask: "Can you see a way to make the pieces the same size?" Students notice that each half can be split into 2 quarters. Redraw: a bar divided into 4, shade 2 sections (2/4 = ½). Now: 2/4 + 1/4 = 3/4.

2. Repeat with ⅓ + ¼:
   - Draw a bar divided into 3, shade 1. Draw a bar divided into 4, shade 1.
   - "What size pieces would work for both thirds AND quarters?" Students experiment with their drawings: twelfths work. Redraw both bars divided into 12: 4/12 + 3/12 = 7/12.

3. Students begin to PREDICT the common denominator from the bar model before they have a formal method: "I need a number that both 3 and 4 divide into evenly."

**What this builds:** The bar model makes the mathematical structure visible without physical objects. Students can see WHY ⅓ = 4/12 (the bar shows it), and they can use the drawing as a problem-solving tool — drawing different subdivisions until they find one that works for both fractions.

**Key teacher language:** "Your bar model shows the same thing as the fraction strips. The bars must be the SAME LENGTH — because we're talking about parts of the same whole. What size pieces would match both fractions?"

### Bridging: Pictorial → Abstract

Once students have solved several problems with bar models, the teacher writes the symbolic version alongside the diagram:

"Let's write what you just drew in maths notation. You drew ⅓ as 4/12 — we write: ⅓ = 4/12. You drew ¼ as 3/12 — we write: ¼ = 3/12. Then you added: 4/12 + 3/12 = 7/12. The numbers say EXACTLY what your bar model shows."

Point to each part of the equation and the corresponding part of the bar model simultaneously: "This 4 [point to numerator] is these 4 shaded sections [point to bar]. This 12 [point to denominator] is these 12 equal sections the bar is divided into [point to bar]."

### Stage 3 — Abstract (Symbolic)

**Notation:** ⅓ + ¼ = 4/12 + 3/12 = 7/12

**Activity:**
1. Students practise finding common denominators and adding fractions using numbers only: ⅕ + ⅓, ⅔ + ¼, ¾ + ⅙.
2. For each problem, students write the equivalent fractions, add, and simplify if needed.
3. Students check their first few answers by drawing a quick bar model: "Does 7/12 LOOK right? Draw the bar and check."

**What this builds:** Fluent, efficient use of the standard procedure — but GROUNDED in understanding. When students write ⅓ = 4/12, they know what this MEANS (the bar divided into 12 pieces, 4 of them shaded). The procedure is not arbitrary; it represents the concrete and pictorial experience.

**Connection back:** If a student gets stuck at the abstract level ("I don't know what common denominator to use for ⅗ + ¼"), the teacher says: "Draw a bar model. What size pieces would work for both fifths and quarters?" The pictorial stage remains available as a thinking tool, not something left behind.

### Common Errors and CPA Responses

| Error | What Student Does | CPA Response |
|---|---|---|
| Adding numerators and denominators | ½ + ⅓ = 2/5 | Return to concrete: "Show me 2/5 with a fraction strip. Now show me ½ + ⅓ end-to-end. Are they the same length?" They won't be — 2/5 is less than ½ alone. The physical evidence disproves the error. |
| Finding common denominator but not understanding why | Writes ⅓ = 4/12 correctly but can't explain it | Return to pictorial: "Draw a bar divided into 3. Now divide each third into 4 pieces. How many pieces do you have? How many are shaded?" The bar model shows WHY ⅓ = 4/12. |
| Not simplifying | Writes 4/12 + 3/12 = 7/12 but doesn't simplify 6/12 to ½ | Return to pictorial: "Draw 6/12. Now look — can you see a simpler way to describe this? How many halves is it?" The bar model shows that 6 out of 12 sections is exactly half the bar. |

### Assessment Check

Give students three tasks that test understanding at each CPA level:

1. **Concrete/Pictorial check:** "Draw a bar model to show ⅔ + ¼. Use your diagram to find the answer." (Tests whether students can use the pictorial tool independently.)

2. **Abstract check:** "Calculate ⅗ + ¼. Show your working." (Tests whether students can use the standard procedure.)

3. **Understanding check:** "Ali says ½ + ⅓ = 2/5. Explain why Ali is wrong. You can use a diagram to help your explanation." (Tests whether students understand WHY the common denominator procedure works — can they explain the error, not just avoid it?)

If students can answer all three, they understand adding fractions at all three CPA levels — not just procedurally, but conceptually.

---

## Known Limitations

1. **CPA is most thoroughly validated in mathematics.** The Singapore framework was designed for mathematics education, and the evidence base is strongest there. The principles (concrete before abstract, bridge representations explicitly) apply across subjects, but the specific tools — bar models, fraction strips, base-ten blocks — are mathematical. Teachers applying CPA to other subjects should adapt the principle, not copy the tools.

2. **The concrete stage requires quality manipulatives and teacher skill.** Poorly designed manipulatives (counters used for fractions, for example) can create misconceptions rather than prevent them. The manipulative must embody the mathematical structure. Teachers need training in which manipulatives represent which concepts — using the wrong concrete material is worse than no concrete material.

3. **CPA does not mean every lesson must start from concrete.** Once students have solid concrete and pictorial understanding of a concept, they can work at the abstract level without going through all three stages every time. CPA is a learning progression for NEW concepts, not a ritual for every lesson. The stages should be revisited when students encounter a new application or get confused, not repeated when students are already fluent.

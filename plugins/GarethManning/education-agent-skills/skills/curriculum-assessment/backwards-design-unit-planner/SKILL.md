---
# AGENT SKILLS STANDARD FIELDS (v2)
name: backwards-design-unit-planner
description: "Plan a unit using backwards design from desired outcomes through assessment evidence to learning activities. Use when starting a new unit or redesigning an existing one from standards."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "curriculum-assessment/backwards-design-unit-planner"
skill_name: "Backwards Design Unit Planner"
domain: "curriculum-assessment"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Wiggins & McTighe (1998, 2005) — Understanding by Design"
  - "Wiggins & McTighe (2011) — The Understanding by Design Guide to Creating High-Quality Units"
  - "Tomlinson & McTighe (2006) — Integrating Differentiated Instruction and Understanding by Design"
  - "Hattie (2009) — Visible Learning: backward design and clarity of learning intentions"
  - "Biggs & Tang (2011) — Teaching for Quality Learning at University: constructive alignment"
input_schema:
  required:
    - field: "desired_outcomes"
      type: "string"
      description: "What students should understand, know, and be able to do by the end of the unit"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "unit_duration"
      type: "string"
      description: "Number of lessons or weeks"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: specific curriculum standards to address"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: prior attainment, known gaps, class composition"
    - field: "available_resources"
      type: "string"
      description: "Key texts, materials, or resources available"
output_schema:
  type: "object"
  fields:
    - field: "stage_1_desired_results"
      type: "object"
      description: "Enduring understandings, essential questions, knowledge and skills"
    - field: "stage_2_assessment_evidence"
      type: "object"
      description: "Performance tasks and other evidence that will demonstrate understanding"
    - field: "stage_3_learning_plan"
      type: "object"
      description: "Sequenced learning activities aligned to stages 1 and 2"
    - field: "alignment_check"
      type: "string"
      description: "Verification that activities, assessments, and outcomes are aligned"
chains_well_with:
  - "competency-unpacker"
  - "criterion-referenced-rubric-generator"
  - "formative-assessment-technique-selector"
  - "explicit-instruction-sequence-builder"
  - "curriculum-knowledge-architecture-designer"
  - "kud-knowledge-type-mapper"
  - "critical-thinking-task-designer"
  - "scope-and-sequence-designer"
teacher_time: "5 minutes"
tags: ["UbD", "backwards-design", "unit-planning", "curriculum", "alignment"]
---

# Backwards Design Unit Planner

## What This Skill Does

Generates a complete Stage 1–2–3 Understanding by Design unit structure from a teacher's desired outcomes: Stage 1 defines enduring understandings, essential questions, and target knowledge/skills; Stage 2 designs the assessment evidence that will demonstrate understanding (before any activities are planned); Stage 3 sequences the learning activities that build toward the assessments and outcomes. The critical insight of backwards design is that assessment is designed BEFORE instruction — not as an afterthought but as the definition of what success looks like. AI is specifically valuable here because backwards design requires holding all three stages in mind simultaneously and ensuring tight alignment between them — what is assessed must match what is intended, and what is taught must prepare students for what is assessed. Most teacher-designed units plan activities first and assessments last, which produces misalignment.

## Evidence Foundation

Wiggins & McTighe (1998, 2005) developed Understanding by Design (UbD), the most widely adopted curriculum design framework in education. The framework's central argument is that curriculum should be designed backward from desired results, not forward from available activities. Stage 1 (Desired Results) defines what students should understand — not just know or do, but genuinely understand at a transferable level. Stage 2 (Assessment Evidence) determines what evidence would demonstrate that understanding — designed before instruction so that teaching targets real outcomes, not just coverage. Stage 3 (Learning Plan) sequences the instruction needed to build toward the assessed outcomes. Wiggins & McTighe (2011) provided practical guidance for unit creation, emphasising that enduring understandings should be transferable ideas worth understanding beyond the unit, and essential questions should be genuinely open — questions that provoke inquiry rather than have predetermined answers. Biggs & Tang (2011) developed "constructive alignment" — the principle that learning outcomes, assessment tasks, and teaching activities must be aligned so that what is assessed is what is taught and what is taught prepares for what is assessed. Hattie (2009) confirmed that clarity of learning intentions and success criteria is one of the highest-leverage factors in student achievement.

## Input Schema

The teacher must provide:
- **Desired outcomes:** What students should understand, know, and be able to do. *e.g. "Students will understand how organisms adapt to their environments through natural selection, know key vocabulary (adaptation, variation, natural selection, evolution), and be able to explain how a specific organism's traits relate to its environment."*
- **Student level:** Year group. *e.g. "Year 9"*
- **Unit duration:** Length of the unit. *e.g. "6 lessons (1 hour each)" / "3 weeks"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Curriculum framework:** Specific standards
- **Student profiles:** Prior attainment, known gaps
- **Available resources:** Texts, materials, resources

## Prompt

```
You are an expert in curriculum design, with deep knowledge of Wiggins & McTighe's (1998, 2005) Understanding by Design framework, Biggs & Tang's (2011) constructive alignment, and Hattie's (2009) research on learning intentions and success criteria. You understand that effective unit design works BACKWARD from desired results — defining what students will understand first, then designing assessment evidence, then planning learning activities.

Your task is to design a UbD unit for:

**Desired outcomes:** {{desired_outcomes}}
**Student level:** {{student_level}}
**Unit duration:** {{unit_duration}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the desired outcomes.
**Curriculum framework:** {{curriculum_framework}} — if not provided, design in general terms.
**Student profiles:** {{student_profiles}} — if not provided, assume a typical mixed-ability class.
**Available resources:** {{available_resources}} — if not provided, suggest appropriate resources.

Apply these evidence-based principles:

1. **Stage 1 — Desired Results (Wiggins & McTighe, 2005):**
   - **Enduring understandings:** Big ideas that are transferable beyond this unit. These are not facts to memorise but principles to understand. Frame as "Students will understand that..." statements.
   - **Essential questions:** Open, thought-provoking questions that guide inquiry throughout the unit. These should be genuinely debatable — not questions with a single right answer. They should recur throughout the unit, with students' answers deepening over time.
   - **Knowledge:** Specific facts, concepts, and vocabulary students will know.
   - **Skills:** Specific abilities students will be able to demonstrate.

2. **Stage 2 — Assessment Evidence (Wiggins & McTighe, 2005; Biggs & Tang, 2011):**
   - Design assessment BEFORE instruction. This is the core UbD principle.
   - **Performance task:** A rich, authentic task that requires students to demonstrate understanding through application — not just recall facts. The task should require transfer — applying learning to a new situation.
   - **Other evidence:** Additional assessment methods (quizzes, checks for understanding, observations) that gather evidence of knowledge and skills.
   - Assessment must be aligned to Stage 1 — every enduring understanding and essential question must be assessable through the evidence in Stage 2.

3. **Stage 3 — Learning Plan (Wiggins & McTighe, 2005):**
   - Sequence learning activities that build toward the Stage 2 assessments.
   - Use the WHERETO framework: Where are we going? Hook the student. Explore and equip. Rethink and revise. Evaluate. Tailor to individual needs. Organise for understanding.
   - Activities should be sequenced logically — building knowledge before applying it, scaffolding before independence.
   - Each activity should connect clearly to the Stage 2 assessment — if an activity doesn't prepare students for the assessment, question whether it belongs.

4. **Alignment check (Biggs & Tang, 2011):**
   - Verify that Stage 1 outcomes are assessed in Stage 2 and taught in Stage 3.
   - Flag any misalignment: outcomes that are stated but not assessed, or assessed but not taught.

Return your output in this exact format:

## Unit Plan: [Unit Title]

**For:** [Student level]
**Subject:** [Subject area]
**Duration:** [Unit duration]

### Stage 1: Desired Results

**Enduring Understandings**
[2–3 transferable understandings — "Students will understand that..."]

**Essential Questions**
[2–3 open, recurring questions that guide inquiry]

**Students will know:**
[Specific knowledge — facts, concepts, vocabulary]

**Students will be able to:**
[Specific skills]

### Stage 2: Assessment Evidence

**Performance Task**
[Description of the authentic assessment task, including: the scenario, what students produce, what the task assesses, and brief success criteria]

**Other Evidence**
[Additional assessment methods mapped to specific Stage 1 outcomes]

### Stage 3: Learning Plan

[Lesson-by-lesson or phase-by-phase sequence, showing: what happens, what it builds toward, and how it connects to Stage 2]

### Alignment Check

[Verification that all Stage 1 outcomes are assessed in Stage 2 and addressed in Stage 3. Flag any gaps.]

**Self-check before returning output:** Verify that (a) enduring understandings are transferable ideas, not just facts, (b) essential questions are genuinely open and recurring, (c) the performance task requires application/transfer, not just recall, (d) Stage 2 was designed before Stage 3 in logic (assessment determines instruction), (e) every Stage 1 outcome is assessed and taught, and (f) the learning plan builds progressively toward the performance task.
```

## Example Output

**Scenario:** *Desired outcomes: "Students will understand how natural selection drives adaptation in organisms, know key concepts (adaptation, variation, inheritance, natural selection, evolution), and be able to explain how specific organisms' traits are suited to their environment and how populations change over time." / Student level: "Year 9" / Unit duration: "8 lessons (50 minutes each)" / Subject area: "Science (Biology)"*

---

## Unit Plan: Natural Selection and Adaptation

**For:** Year 9
**Subject:** Science (Biology)
**Duration:** 8 lessons (50 minutes each)

### Stage 1: Desired Results

**Enduring Understandings**
1. Students will understand that **organisms with traits better suited to their environment are more likely to survive and reproduce, and these traits are passed to offspring — leading to populations that change over time.** (This is the mechanism of natural selection.)
2. Students will understand that **variation within a population is essential for natural selection — without variation, there is nothing for the environment to "select."**
3. Students will understand that **adaptation is a result of natural selection over many generations, not a deliberate choice by individual organisms.** (Organisms do not choose to adapt; populations change because better-suited individuals leave more offspring.)

**Essential Questions**
1. "Why do organisms look the way they do?" (Recurring — answers deepen from "because they adapted" in Lesson 1 to "because natural selection favoured traits that increased survival and reproduction in their specific environment" by Lesson 8.)
2. "If the environment changes, what happens to organisms that are well-adapted to the old environment?" (Drives the understanding that adaptation is not permanent — it is context-dependent.)
3. "Why is variation important?" (Connects genetics to evolution — without variation, natural selection cannot operate.)

**Students will know:**
- The definitions of adaptation, variation, inheritance, natural selection, evolution, and species
- Examples of structural, behavioural, and functional adaptations in named organisms
- That variation arises from genetic differences (and sometimes environmental factors)
- The four conditions required for natural selection: variation, inheritance, selection pressure, differential reproduction
- Darwin's contribution to the theory of evolution by natural selection

**Students will be able to:**
- Explain how a named organism's specific traits help it survive in its environment
- Describe the process of natural selection step by step
- Predict what might happen to a population if the environment changes
- Distinguish between Lamarckian (acquired characteristics) and Darwinian (natural selection) explanations — and explain why Lamarck's is incorrect

### Stage 2: Assessment Evidence

**Performance Task: "The Island"**

*Scenario:* "A population of beetles lives on a volcanic island. The beetles vary in colour from green to brown. The island is covered in green vegetation. Recently, a volcanic eruption has covered much of the island in dark grey ash. Scientists predict that the beetle population will look very different in 50 generations. Your task: write a scientific explanation predicting how the beetle population will change and why, using the theory of natural selection. Your explanation must include all four conditions for natural selection and address the common misconception that individual beetles will 'choose' to change colour."

*What students produce:* A 200–300 word scientific explanation.

*What the task assesses:*
- Enduring Understanding 1: mechanism of natural selection (can they explain the process correctly?)
- Enduring Understanding 2: role of variation (do they identify existing colour variation as essential?)
- Enduring Understanding 3: adaptation is not a choice (do they explain that the population changes, not individual beetles?)
- Essential Questions 1 and 2: adapted organisms + environmental change
- Knowledge: four conditions, correct terminology
- Skills: step-by-step explanation, distinguishing Darwinian from Lamarckian reasoning

*Brief success criteria:*
- Identifies existing variation in the population (colour range)
- Explains selection pressure (darker beetles better camouflaged on ash)
- Describes differential survival and reproduction
- Explains inheritance of traits to offspring
- Predicts population change over generations
- Addresses the misconception that beetles "choose" to change colour

**Other Evidence**

| Lesson | Assessment | Stage 1 outcome assessed |
|--------|-----------|------------------------|
| 2 | Exit ticket: "Name 3 adaptations of a polar bear and explain how each helps it survive" | Knowledge (adaptations); Skill (explaining trait–environment link) |
| 4 | Mini-whiteboard hinge question: "A giraffe stretches its neck to reach leaves. Its offspring are born with longer necks. Is this Darwinian or Lamarckian? Why?" | Understanding 3 (adaptation is not a choice); Knowledge (Lamarck vs Darwin) |
| 6 | Peer explanation: students explain natural selection to a partner using a new example; partner checks against a 4-step checklist | Knowledge (four conditions); Skill (step-by-step explanation) |

### Stage 3: Learning Plan

**Lesson 1 — Hook and Explore: "Why Do Organisms Look the Way They Do?"**
- Show 5 images of unusual adaptations (anglerfish, cactus, arctic fox, chameleon, deep-sea tube worm). Students discuss: "Why does this organism look like this? What problem does this trait solve?"
- Introduce Essential Question 1. Students write initial answers.
- Define "adaptation" — structural, behavioural, functional. Students classify the 5 examples.
- *Builds toward:* Stage 2 performance task (explaining trait–environment link).

**Lesson 2 — Equip: Types of Adaptation**
- Detailed study of 3 organisms and their adaptations (one structural, one behavioural, one functional).
- Students explain in writing: "How does [trait] help [organism] survive in [environment]?"
- *Exit ticket assessment.*
- *Builds toward:* Stage 2 performance task (explaining how traits suit environments).

**Lesson 3 — Explore: Variation**
- Practical: measuring variation in a population (e.g., hand span, leaf size, or simulated beetle data).
- Key concept: variation exists within every population. Some variation is genetic.
- Introduce Essential Question 3: "Why is variation important?"
- *Builds toward:* Enduring Understanding 2 (variation is essential for natural selection).

**Lesson 4 — Equip: Natural Selection Step by Step**
- Explicit instruction: the 4 conditions for natural selection (variation, inheritance, selection pressure, differential reproduction).
- Use the peppered moth as a worked example — model the explanation step by step.
- Introduce Lamarck vs. Darwin distinction. Common misconception: "the giraffe stretched its neck."
- *Hinge question assessment.*
- *Builds toward:* Performance task (students must use the 4 conditions).

**Lesson 5 — Explore and Rethink: Simulation**
- Simulation activity: "Survival of the Fittest" using coloured paper "organisms" on different backgrounds. Students observe which are "eaten" (selected against) and which survive. Repeat for 3 "generations."
- Students observe that the population changes over time — without any individual changing.
- Revisit Essential Question 1: update answers.
- *Builds toward:* Enduring Understanding 3 (populations change, not individuals).

**Lesson 6 — Equip and Evaluate: Practice Explanations**
- Students practise writing natural selection explanations using a new example (e.g., antibiotic resistance in bacteria).
- Peer assessment using the 4-step checklist from the performance task criteria.
- Teacher circulates and identifies common errors for whole-class feedback.
- *Builds toward:* Performance task (practising the exact skill assessed).

**Lesson 7 — Performance Task: "The Island"**
- Students complete the performance task under supported conditions.
- Sentence starters available for EAL students. Word bank available for all students (may be removed for extension students).
- Teacher circulates, noting common misconceptions for Lesson 8 feedback.

**Lesson 8 — Rethink and Extend: Feedback and Transfer**
- Return marked work with targeted feedback.
- Whole-class review of most common errors (especially Lamarckian reasoning).
- Extension: "Humans have been using antibiotics for about 80 years. Bacteria are becoming resistant. Use natural selection to explain why."
- Revisit all three Essential Questions: students write final answers and compare with Lesson 1 answers.

### Alignment Check

| Stage 1 Outcome | Assessed in Stage 2? | Taught in Stage 3? | Aligned? |
|-----------------|---------------------|--------------------|---------|
| Understanding 1 (natural selection mechanism) | Performance task + Lesson 6 peer assessment | Lessons 4, 5, 6 | ✓ |
| Understanding 2 (variation is essential) | Performance task | Lesson 3 | ✓ |
| Understanding 3 (adaptation is not a choice) | Performance task + Lesson 4 hinge question | Lessons 4, 5 | ✓ |
| Knowledge (key vocabulary) | All assessments require terminology | Introduced progressively across Lessons 1–4 | ✓ |
| Skill (explain trait–environment link) | Lesson 2 exit ticket + performance task | Lessons 1, 2 | ✓ |
| Skill (step-by-step explanation) | Performance task + Lesson 6 peer check | Lessons 4, 6 (modelled and practised) | ✓ |

No misalignment detected. All Stage 1 outcomes are assessed and taught.

---

## Known Limitations

1. **The unit plan provides structure, not detailed lesson plans.** Each lesson entry describes the key activity and its purpose but does not include full timing, differentiation, resources, or teacher scripts. Teachers should use the Stage 3 sequence as a framework and develop detailed lesson plans using other skills (Explicit Instruction Sequence Builder, Lesson Opening Designer, etc.).

2. **Backwards design assumes clear desired outcomes.** If the teacher's initial outcome statement is vague ("students will learn about natural selection"), the UbD structure will be less precise. The quality of the unit depends on the specificity of the input. Chain with Competency Unpacker if the outcome needs clarifying before unit design.

3. **The performance task is designed for a specific context and may need adaptation.** The "Island" scenario works for this Biology topic but may not transfer directly to other schools' resources or assessment requirements. Teachers should review the performance task against their specific assessment framework and modify the scenario while maintaining the assessment design principles.

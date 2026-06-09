---
# AGENT SKILLS STANDARD FIELDS (v2)
name: scaffolded-task-modifier
description: "Modify a classroom task with language scaffolds that preserve cognitive demand for EAL learners. Use when adapting existing tasks for students at different English proficiency levels."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "eal-language-development/scaffolded-task-modifier"
skill_name: "Scaffolded Task Modifier"
domain: "eal-language-development"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Gibbons (2002, 2015) — Scaffolding Language, Scaffolding Learning: scaffolding that challenges rather than simplifies"
  - "Cummins (2000) — Language, Power and Pedagogy: the BICS/CALP and quadrant frameworks"
  - "Hammond & Gibbons (2005) — Putting scaffolding to work: the contribution of scaffolding in articulating ESL education"
  - "Vygotsky (1978) — Mind in Society: the zone of proximal development"
  - "Walqui (2006) — Scaffolding instruction for English language learners: a conceptual framework"
input_schema:
  required:
    - field: "original_task"
      type: "string"
      description: "The task as originally designed for the class"
    - field: "target_proficiency"
      type: "string"
      description: "The language proficiency level of the students being scaffolded for — e.g. New to English, Early Acquisition, Developing, Consolidating"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: first languages, specific language needs, cognitive ability"
    - field: "learning_objective"
      type: "string"
      description: "The learning objective — what ALL students should understand, regardless of language level"
    - field: "task_materials"
      type: "string"
      description: "Description of texts, worksheets, or resources used in the original task"
output_schema:
  type: "object"
  fields:
    - field: "modified_task"
      type: "object"
      description: "The scaffolded version of the task with language supports added and cognitive demand maintained"
    - field: "cognitive_demand_check"
      type: "string"
      description: "Explicit verification that the modification maintains cognitive challenge"
    - field: "scaffold_types_used"
      type: "array"
      description: "List of scaffolding strategies applied, with rationale for each"
    - field: "removal_plan"
      type: "string"
      description: "How and when to remove scaffolds as proficiency increases"
chains_well_with:
  - "language-demand-analyser"
  - "vocabulary-tiering-tool"
  - "academic-language-sentence-frame-generator"
  - "cognitive-load-analyser"
teacher_time: "4 minutes"
tags: ["scaffolding", "EAL", "differentiation", "cognitive-demand", "task-modification"]
---

# Scaffolded Task Modifier

## What This Skill Does

Adapts a classroom task for a specific language proficiency level while explicitly maintaining cognitive demand — ensuring that EAL students engage with the same thinking as their peers, even when they need language support to do so. The critical design principle is that scaffolding should reduce LANGUAGE barriers, not reduce THINKING. Many well-intentioned task modifications inadvertently lower cognitive demand: giving EAL students a simpler version, removing the analytical component, or replacing an open question with a multiple-choice one. This skill guards against that by producing a modified task alongside an explicit cognitive demand check, verifying that the modification changes the linguistic access route but not the intellectual destination. AI is specifically valuable here because maintaining cognitive demand during scaffolding requires simultaneously understanding the task's intellectual purpose, the student's language level, and the specific scaffolding strategies that support access without reducing challenge — a three-way analysis most teachers don't have time to do.

## Evidence Foundation

Gibbons (2002, 2015) established the fundamental principle that scaffolding for EAL students must challenge rather than simplify — the goal is to support students in doing MORE than they could alone, not to reduce what they're asked to do. Cummins (2000) provided the quadrant model showing that tasks vary along two dimensions: cognitive demand (high/low) and contextual support (embedded/reduced). Effective EAL scaffolding moves a task from quadrant D (high demand, reduced context — inaccessible) to quadrant B (high demand, embedded context — challenging but accessible) — NOT from quadrant D to quadrant A (low demand, embedded context — accessible but unchallenging). Hammond & Gibbons (2005) identified two levels of scaffolding: designed-in scaffolding (planned before the lesson — graphic organisers, sentence frames, pre-teaching vocabulary) and interactional scaffolding (contingent teacher support during the lesson — recasting, elaborating, guiding). Vygotsky (1978) established that learning occurs in the Zone of Proximal Development — what the learner can do with support but not yet independently. Walqui (2006) identified six scaffolding strategies for EAL learners: modelling, bridging, contextualising, building schema, representing text, and developing metacognition.

## Input Schema

The teacher must provide:
- **Original task:** The task as designed for the class. *e.g. "Write a balanced argument essay on whether school uniforms should be compulsory" / "Analyse the data in the table and explain what it shows about population growth" / "Read the extract and answer the inference questions"*
- **Target proficiency:** The language level to scaffold for. *e.g. "Early Acquisition" / "Developing" / "New to English"*
- **Subject area:** The subject. *e.g. "English" / "Geography" / "Science"*

Optional (injected by context engine if available):
- **Student level:** Year group
- **Student profiles:** First languages, cognitive ability, specific needs
- **Learning objective:** What all students should learn
- **Task materials:** Resources used in the original task

## Prompt

```
You are an expert in EAL scaffolding and differentiation, with deep knowledge of Gibbons' (2002, 2015) principle that scaffolding must challenge rather than simplify, Cummins' (2000) quadrant model of cognitive demand and contextual support, and Walqui's (2006) scaffolding strategies for English language learners. You understand that the most common error in EAL differentiation is reducing cognitive demand — giving students an easier task instead of the same task with better support.

Your task is to scaffold:

**Original task:** {{original_task}}
**Target proficiency:** {{target_proficiency}}
**Subject area:** {{subject_area}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, assume a secondary school student.
**Student profiles:** {{student_profiles}} — if not provided, assume the student has age-appropriate cognitive ability but limited academic English proficiency, with conversational fluency.
**Learning objective:** {{learning_objective}} — if not provided, infer the learning objective from the original task. This is critical — the modified task must achieve the SAME objective.
**Task materials:** {{task_materials}} — if not provided, infer typical materials for this task type.

Apply these evidence-based principles:

1. **Maintain cognitive demand (Gibbons, 2002; Cummins, 2000):**
   - The modified task must require the SAME level of thinking as the original.
   - If the original task requires analysis, the modified task must also require analysis — not description.
   - If the original task requires evaluation, the modified task must also require evaluation — not recall.
   - If the original task requires an extended written response, the scaffolded version may provide language support (sentence frames, word banks, graphic organisers) but must still require the student to construct meaning, not just fill blanks.
   - EXPLICITLY check and state: "The original task requires [thinking type]. The modified task also requires [same thinking type] because..."

2. **Scaffold language, not thinking (Gibbons, 2015):**
   - Identify the LANGUAGE barriers in the original task (vocabulary, grammar, text structure, reading load).
   - Add language supports that address these specific barriers.
   - Do NOT: simplify the question, reduce the number of steps, provide the answer in the scaffold, remove the requirement for original thinking, or substitute a lower-order task.

3. **Use appropriate scaffold types (Walqui, 2006; Hammond & Gibbons, 2005):**
   - **Modelling:** Provide a worked example or annotated model showing what a good response looks like.
   - **Bridging:** Connect to the student's existing knowledge or first language.
   - **Contextualising:** Add visual support, diagrams, or concrete examples that make abstract content accessible.
   - **Sentence frames:** Provide the linguistic structure while requiring the student to supply the content and thinking.
   - **Graphic organisers:** Provide a visual structure for organising ideas before writing.
   - **Word banks:** Supply key vocabulary, but require the student to select and use words meaningfully.
   - **Glossary/bilingual support:** Define key terms, ideally with first-language equivalents.

4. **Match scaffold intensity to proficiency level:**
   - **New to English:** Heavy scaffolding — visual support, bilingual resources, adapted text with glossary, sentence frames with minimal gaps, graphic organisers that structure the entire response. The student may respond partially in their first language. The thinking demand remains.
   - **Early Acquisition:** Substantial scaffolding — adapted text, sentence starters (not complete frames), word banks, graphic organisers, models. The student produces English with significant support.
   - **Developing:** Moderate scaffolding — original text with glossary, sentence starters for complex constructions only, optional word bank. The student produces mostly independent English with targeted support.
   - **Consolidating:** Light scaffolding — original text, a few sentence starters for the most complex academic constructions, no word bank (student should be building independence). Nearly independent.

5. **Plan for scaffold removal:**
   - Scaffolds are temporary. Every scaffold should include a note about when and how to remove it.
   - The goal is independence — if the scaffold becomes permanent, it has become a crutch.

Return your output in this exact format:

## Scaffolded Task: [Brief description]

**Original task:** [The original task]
**Scaffolded for:** [Target proficiency level]
**Subject:** [Subject area]
**Learning objective:** [Stated or inferred — must be the SAME for both versions]

### Modified Task

[The complete scaffolded version of the task — including all language supports, visual organisers, sentence frames, word banks, etc.]

### Cognitive Demand Check

**Original task requires:** [Type of thinking — analysis, evaluation, synthesis, application, etc.]
**Modified task requires:** [SAME type of thinking]
**How cognitive demand is maintained:** [Specific explanation of why the scaffolded version still requires the same thinking]
**What was changed:** [Only language access — not intellectual demand]
**What was NOT changed:** [The thinking, the learning objective, the analytical requirement]

### Scaffold Types Used

For each scaffold:
- **[Scaffold type]:** [What was added and why — connected to a specific language barrier]

### Scaffold Removal Plan

[How to progressively remove each scaffold as the student's proficiency increases — specific, practical steps]

**Self-check before returning output:** Verify that (a) the learning objective is the same for both versions, (b) the modified task requires the same TYPE of thinking as the original, (c) scaffolds address language barriers specifically, (d) no scaffold inadvertently provides the answer or removes the need for original thinking, (e) the scaffold intensity matches the stated proficiency level, and (f) the scaffold removal plan is included.
```

## Example Output

**Scenario:** *Original task: "Read the extract from 'An Inspector Calls' (Act 1, Mr Birling's speech about the Titanic). Analyse how Priestley uses dramatic irony to undermine Mr Birling's authority. In your response, explain what dramatic irony is, identify specific examples from the extract, and explain the effect on the audience." / Target proficiency: "Developing" / Subject area: "English Literature" / Student level: "Year 10"*

---

## Scaffolded Task: Dramatic Irony in 'An Inspector Calls'

**Original task:** Analyse how Priestley uses dramatic irony to undermine Mr Birling's authority in the Titanic speech (Act 1). Explain what dramatic irony is, identify examples, and explain the effect on the audience.
**Scaffolded for:** Developing proficiency
**Subject:** English Literature
**Learning objective:** Students analyse how Priestley uses dramatic irony as a technique to shape the audience's view of Mr Birling.

### Modified Task

**Step 1: Understanding the concept (with visual support)**

**Dramatic irony** = when the AUDIENCE knows something that a CHARACTER does not.

| What Mr Birling says (1912) | What the AUDIENCE knows (watching in 1945+) |
|---|---|
| "The Titanic... unsinkable, absolutely unsinkable" | The Titanic sank on its maiden voyage in 1912 — over 1,500 people died |
| "I say there isn't a chance of war" | World War I started in 1914 and World War II started in 1939 |

**This is dramatic irony:** Mr Birling is completely WRONG, and the audience KNOWS he is wrong while he speaks confidently.

**Step 2: Analyse — WHY does Priestley do this?**

Read the extract again. Use the questions below to build your analysis. You must explain your thinking — a one-word answer is not enough.

1. When the audience hears Mr Birling say the Titanic is "unsinkable," what do they think about Mr Birling? Do they trust his judgement?

2. Mr Birling says these wrong predictions with great confidence ("I say there isn't a chance of war"). What effect does his confidence have? Is a confident person who is wrong MORE or LESS ridiculous than an unsure person who is wrong?

3. Mr Birling also makes predictions about business and social responsibility — he says people should only look after themselves. Priestley wants the audience to disagree with this view. How does the dramatic irony about the Titanic and the war HELP Priestley make the audience disagree with Mr Birling's other views too?

**Step 3: Write your response**

Use this structure. Each section requires YOUR thinking — the sentence starters give you the academic language, but you must supply the analysis.

**Paragraph 1 — What dramatic irony is and how Priestley uses it:**

Dramatic irony is when ___. In Mr Birling's speech, Priestley uses dramatic irony when Birling says "___" (quote from the extract). The audience in 1945 would know that ___, which means Birling is ___.

**Paragraph 2 — The effect on the audience:**

This dramatic irony affects the audience because ___. When they hear Birling speak so confidently about something they KNOW is wrong, they begin to ___. Priestley's purpose in doing this is to ___ because ___.

**Paragraph 3 — How this connects to Priestley's wider message:**

Priestley uses the dramatic irony to undermine Birling's authority so that when Birling argues that people should only look after themselves, the audience ___. If the audience already knows Birling is wrong about the Titanic, they are more likely to think he is also wrong about ___. This supports Priestley's message that ___.

**Word bank for analytical language:**

| To describe Birling | To describe the audience's response | To describe Priestley's purpose |
|---|---|---|
| arrogant, overconfident, foolish, misguided, short-sighted | sceptical, distrustful, critical, amused, aware | undermines, discredits, challenges, exposes, reveals |

### Cognitive Demand Check

**Original task requires:** Analysis — students must explain HOW a technique (dramatic irony) creates a specific effect (undermining authority), requiring them to identify examples, explain the mechanism of the technique, and connect it to authorial purpose.

**Modified task requires:** The same analysis. Students must still explain HOW dramatic irony undermines Birling, identify specific examples, explain the effect on the audience, and connect to Priestley's purpose. The guiding questions and sentence starters provide linguistic scaffolding but each one requires the student to supply their OWN analytical thinking.

**How cognitive demand is maintained:**
- Question 2 asks students to evaluate the relationship between confidence and being wrong — this is genuine analysis, not recall.
- Question 3 asks students to explain how dramatic irony about factual predictions transfers to undermine Birling's political views — this is the hardest analytical step and is NOT answered by the scaffold.
- The sentence frames require students to complete the analysis: "Priestley's purpose in doing this is to ___ because ___" — the "because" forces reasoning, not just identification.

**What was changed:** The reading is supported with a summary table. The writing structure is scaffolded with sentence starters. Analytical vocabulary is provided in a word bank. The task is broken into guided steps.

**What was NOT changed:** The requirement to analyse (not describe). The requirement to explain effect on the audience. The requirement to connect technique to authorial purpose. The requirement to use evidence from the text.

### Scaffold Types Used

- **Contextualising (table):** The summary table makes the historical knowledge required for dramatic irony visible — EAL students may not have the cultural background knowledge to recognise why Birling's predictions are ironic. The table provides this context without doing the analysis.
- **Sentence frames:** Provide the grammatical structure of analytical writing (complex sentences with embedded clauses) while requiring the student to supply the content. "Dramatic irony is when ___" requires a definition. "Priestley's purpose in doing this is to ___ because ___" requires reasoning.
- **Guiding questions:** Break the analysis into sequential steps rather than expecting the student to produce a holistic analytical response from a single open prompt. Each question targets one component of the analysis.
- **Word bank:** Provides the evaluative vocabulary (arrogant, sceptical, undermines) that EAL students at Developing level are unlikely to have but need for analytical writing. The student must SELECT the appropriate word — the bank provides options, not answers.

### Scaffold Removal Plan

| Current scaffold | Remove when... | Replace with... |
|---|---|---|
| Summary table (historical context) | Student demonstrates awareness of the historical context independently in class discussion | No replacement — the knowledge should be internalised |
| Sentence frames (full structure) | Student can produce analytical paragraphs with sentence starters only | Sentence starters only: "Priestley uses..." "This suggests..." "The effect on the audience is..." |
| Sentence starters | Student produces analytical writing with appropriate structure independently | No starters — student writes independently, with post-writing feedback on structure |
| Guiding questions | Student can identify the analytical steps independently when given an open prompt | Single open prompt: "Analyse how Priestley uses [technique] to [effect]" |
| Word bank | Student uses 3+ analytical terms independently without the bank | No word bank — but continue to teach new analytical vocabulary as it arises |

**Target timeline:** For a Developing student, aim to remove the sentence frames within 4–6 weeks (with regular analytical writing practice). The word bank can be reduced gradually — remove words the student has used correctly 3+ times. The guiding questions can be reduced to 1–2 prompts within 2–3 months.

---

## Known Limitations

1. **The modification cannot account for students' cognitive ability independently of language proficiency.** A student who is at Developing proficiency in English but has strong analytical ability in their first language needs different scaffolding from a student at the same proficiency level who also finds analysis challenging. The teacher's knowledge of the individual student is essential for adjusting the scaffold.

2. **Scaffold removal requires consistent, longitudinal planning.** This skill designs scaffolds for a single task, but effective scaffold removal happens across weeks and months. A teacher who uses this skill for every task will get well-scaffolded individual tasks, but the progressive removal across tasks requires the teacher to plan the trajectory. Chain with a spaced-practice approach to scaffold reduction.

3. **The modification assumes the original task is well-designed.** If the original task is poorly structured, unclear, or misaligned with the learning objective, scaffolding it will not help — the original task needs redesigning first. Scaffolding is not a fix for bad task design; it's a way to make a good task accessible to students at different language proficiency levels.

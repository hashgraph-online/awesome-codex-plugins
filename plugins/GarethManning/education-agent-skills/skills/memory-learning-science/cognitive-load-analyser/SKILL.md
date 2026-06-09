---
# AGENT SKILLS STANDARD FIELDS (v2)
name: cognitive-load-analyser
description: "Analyse a learning task for cognitive load problems and recommend specific design improvements. Use when tasks overwhelm students, instructions feel complex, or materials need simplifying."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "memory-learning-science/cognitive-load-analyser"
skill_name: "Cognitive Load Analyser"
domain: "memory-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Sweller (1988) — Cognitive load during problem solving: effects on learning"
  - "Sweller (1994) — Cognitive load theory, learning difficulty, and instructional design"
  - "Paas & van Merriënboer (1994) — Instructional control of cognitive load in the training of complex cognitive tasks"
  - "Sweller et al. (2019) — Cognitive Architecture and Instructional Design: 20 Years Later (updated CLT)"
  - "Kalyuga et al. (2003) — The expertise reversal effect"
input_schema:
  required:
    - field: "task_description"
      type: "string"
      description: "The learning task, instruction, or resource to analyse"
    - field: "student_level"
      type: "string"
      description: "Age/year group and expertise level (novice/intermediate/advanced)"
  optional:
    - field: "task_materials"
      type: "string"
      description: "Description or text of worksheets, slides, or instructions used"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: working memory profiles, prior knowledge data"
    - field: "lesson_context"
      type: "string"
      description: "What comes before and after this task in the lesson"
output_schema:
  type: "object"
  fields:
    - field: "load_analysis"
      type: "object"
      description: "Breakdown of intrinsic, extraneous, and germane load with ratings"
    - field: "problem_areas"
      type: "array"
      description: "Specific elements creating unnecessary cognitive load"
    - field: "modification_suggestions"
      type: "array"
      description: "Concrete changes to reduce extraneous load and optimise germane load"
    - field: "expertise_reversal_check"
      type: "string"
      description: "Whether scaffolds may be counterproductive for advanced learners"
chains_well_with:
  - "worked-example-fading-designer"
  - "explicit-instruction-sequence-builder"
  - "scaffolded-task-modifier"
  - "text-complexity-analyser"
teacher_time: "4 minutes"
tags: ["cognitive-load", "task-design", "scaffolding", "instructional-design", "working-memory"]
---

# Cognitive Load Analyser

## What This Skill Does

Evaluates a learning task, instruction set, or resource for cognitive load across three dimensions: intrinsic load (inherent complexity of the content), extraneous load (unnecessary difficulty caused by poor design), and germane load (productive cognitive effort directed at schema building). Produces a specific diagnosis of where load is excessive and concrete modification suggestions. AI is specifically valuable here because cognitive load analysis requires simultaneously evaluating content complexity, instructional design quality, and learner expertise level — a skill that typically requires training in instructional design that most teachers lack.

## Evidence Foundation

Sweller (1988, 1994) established Cognitive Load Theory (CLT) as a framework for understanding why some instructional designs fail: human working memory can hold approximately 4-7 elements simultaneously, and learning fails when the total cognitive load exceeds working memory capacity. Sweller distinguishes intrinsic load (determined by element interactivity — how many elements must be processed simultaneously), extraneous load (caused by poor instructional design), and germane load (productive effort directed at building schemas). Paas & van Merriënboer (1994) operationalised CLT for instructional design, demonstrating that reducing extraneous load consistently improves learning outcomes. Sweller et al. (2019) updated the theory to incorporate evolutionary psychology and refine the distinction between biologically primary and secondary knowledge. Critically, Kalyuga et al. (2003) identified the "expertise reversal effect" — instructional techniques that reduce load for novices (worked examples, integrated diagrams) can actually increase load for advanced learners by requiring them to process redundant information. This means cognitive load analysis must always consider learner expertise.

## Input Schema

The teacher must provide:
- **Task description:** The learning task, instruction, or resource to be analysed. *e.g. "Students read a 2-page text about osmosis while completing a diagram labelling activity and answering comprehension questions simultaneously" / "Solve quadratic equations by completing the square — worksheet with 20 problems"*
- **Student level:** Age/year group and expertise level. *e.g. "Year 10, first encounter with this topic (novice)" / "Year 12, revising for exam (advanced)"*

Optional (injected by context engine if available):
- **Task materials:** The actual text, worksheet, or instructions being used
- **Student profiles:** Working memory profiles, known learning difficulties, prior knowledge data
- **Lesson context:** What happens before and after this task

## Prompt

```
You are an expert in Cognitive Load Theory (CLT) with deep knowledge of Sweller's (1988, 1994) framework, Sweller et al.'s (2019) updated theory, and Kalyuga et al.'s (2003) expertise reversal effect. You understand the distinctions between intrinsic, extraneous, and germane cognitive load and how instructional design affects each.

Your task is to analyse the following learning task for cognitive load:

**Task:** {{task_description}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Materials:** {{task_materials}} — if provided, analyse these specific materials. If not provided, base your analysis on the task description alone.
**Lesson context:** {{lesson_context}} — if provided, consider what comes before and after the task when assessing cumulative load. If not provided, analyse the task in isolation.
**Student profiles:** {{student_profiles}} — if provided, consider specific working memory and prior knowledge factors. If not provided, base your analysis on typical expectations for the stated year group and expertise level.

Conduct your analysis using these CLT principles:

1. **Intrinsic load assessment:** Count the element interactivity. How many elements must a student hold in working memory simultaneously to complete this task? Consider:
   - Number of new concepts introduced at once
   - Whether elements can be learned in isolation (low interactivity) or must be understood in relation to each other (high interactivity)
   - Prior knowledge that may reduce intrinsic load through chunking

2. **Extraneous load identification:** Identify design features that consume working memory without contributing to learning:
   - **Split-attention effect:** Must students mentally integrate information from two or more separated sources (e.g., a diagram on one page and explanation on another)?
   - **Redundancy effect:** Are students processing the same information in multiple formats unnecessarily?
   - **Modality effect:** Could some visual information be presented as audio (or vice versa) to use dual channels?
   - **Transient information effect:** Is important information presented transiently (speech, animation) when it needs to be persistent?
   - **Unnecessary complexity:** Are instructions more complex than necessary? Are there decorative elements that don't aid learning?

3. **Germane load assessment:** What productive cognitive effort does the task demand?
   - Schema construction: Does the task build mental models or just require recall?
   - Comparison and contrast: Does the task require students to see relationships?
   - Self-explanation: Does the task prompt students to explain why, not just what?

4. **Expertise reversal check (Kalyuga et al., 2003):** If the student level is intermediate or advanced, check whether scaffolds or supports that would help novices are actually creating redundancy for these learners.

5. **Total load assessment:** Is the combined load (intrinsic + extraneous + germane) likely to exceed working memory capacity for these learners? If yes, what must change?

Return your output in this exact format:

## Cognitive Load Analysis

### Task Summary
[1–2 sentence restatement of the task]

### Load Breakdown

**Intrinsic Load: [Low / Medium / High]**
- Element interactivity count: [number of elements that must be processed simultaneously]
- [Specific explanation of what makes this content inherently simple or complex]

**Extraneous Load: [Low / Medium / High]**
- [List each source of extraneous load with specific reference to the CLT effect it violates]

**Germane Load: [Low / Medium / High]**
- [What schema-building work the task demands]

### Overall Assessment
[Is total load likely within working memory capacity? Will learning occur or will students be overwhelmed?]

### Problem Areas
[Numbered list of specific elements creating unnecessary load]

### Modification Suggestions
For each problem area, provide a specific, actionable modification:
- **Problem:** [What's wrong]
- **Principle:** [Which CLT principle it violates]
- **Fix:** [Exact change to make]

### Expertise Reversal Check
[Is this task appropriately calibrated for the stated expertise level? Would the scaffolding help or hinder?]

**Self-check before returning output:** Verify that (a) you have distinguished intrinsic from extraneous load — do not label inherent content complexity as a design problem, (b) every modification suggestion is specific and actionable, not generic advice like "simplify the task," (c) you have considered the expertise reversal effect, and (d) modifications reduce extraneous load without also reducing germane load (productive difficulty should be preserved).
```

## Example Output

**Scenario:** *Task: "Year 7 students read a two-page text about the water cycle, then complete a blank diagram labelling activity while answering 10 comprehension questions on a separate worksheet. The text, diagram, and questions are on three separate sheets of paper." / Student level: "Year 7 Science, first time learning the water cycle (novice)"*

---

## Cognitive Load Analysis

### Task Summary
Year 7 novice learners must read a text about the water cycle, label a blank diagram, and answer comprehension questions simultaneously using three separate sheets of paper.

### Load Breakdown

**Intrinsic Load: Medium**
- Element interactivity: approximately 8–10 elements (evaporation, condensation, precipitation, collection, runoff, groundwater flow, transpiration, plus the relationships between them as a cycle)
- The water cycle has moderate element interactivity — each process can be understood in isolation, but understanding the *cycle* requires holding multiple processes in working memory simultaneously and tracking the relationships between them. For novice Year 7 learners with no prior schema, this is at the upper boundary of manageable intrinsic load.

**Extraneous Load: HIGH**
- **Split-attention effect (severe):** Three separate sheets of paper force students to constantly switch between text, diagram, and questions. They must search the text for information, hold it in working memory while switching to the diagram or question sheet, then apply it — all while losing their place each time. This is a textbook example of split attention (Sweller, 1994).
- **Redundancy risk:** The text and diagram may present the same information twice. If the diagram simply illustrates what the text already describes, students are processing the same content in two formats without additional learning benefit.
- **Goal-free problem absence:** The comprehension questions impose a specific search goal that forces means-ends analysis — students search for answers rather than building understanding of the overall system.

**Germane Load: Low**
- The task as designed directs most cognitive effort toward *finding information* (extraneous) rather than *understanding the system* (germane). Students are likely to search-and-copy rather than build a mental model of the water cycle as an interconnected system. The comprehension questions encourage this surface processing by rewarding location of specific facts.

### Overall Assessment
Total load almost certainly exceeds working memory capacity for novice Year 7 learners. The high extraneous load from split attention across three documents, combined with medium intrinsic load from the topic itself, leaves very little working memory capacity for germane processing (actually understanding the cycle). Students will likely complete the activity by copying words from the text to the diagram and questions without building a coherent schema. Learning will be minimal despite significant apparent "work."

### Problem Areas

1. **Three separate sheets create severe split-attention.** Students must hold information in working memory while physically switching between documents, losing their place and consuming working memory on navigation rather than learning.

2. **Simultaneous activities compete for working memory.** Reading, diagram labelling, and question answering are three parallel tasks, each demanding working memory. For novice learners, these should be sequenced, not simultaneous.

3. **Comprehension questions encourage search-and-copy, not understanding.** Students scan the text for keywords matching the questions rather than reading for comprehension. This produces extraneous load (searching) with minimal germane load (understanding).

4. **No worked example or process model.** Novice learners encountering the water cycle for the first time have no schema to organise the information. They need a complete worked example (fully labelled diagram with annotations) before being asked to produce their own.

### Modification Suggestions

- **Problem:** Three separate sheets create split attention
- **Principle:** Split-attention effect (Sweller, 1994) — when learners must mentally integrate information from physically or temporally separated sources, extraneous load increases
- **Fix:** Integrate the text into the diagram itself. Place short explanatory labels directly on the diagram at the relevant points (e.g., an annotation next to the arrow showing evaporation). Eliminate the separate text entirely — the diagram-with-integrated-text becomes the single source. Place questions on the same sheet, directly below the diagram.

- **Problem:** Simultaneous activities overwhelm working memory
- **Principle:** Element interactivity — too many novel elements processed simultaneously
- **Fix:** Sequence the activities: (1) First, study a fully labelled, annotated diagram for 5 minutes (worked example — Sweller & Cooper, 1985). (2) Then, attempt a partially labelled diagram where key terms are removed (completion problem). (3) Finally, attempt a fully blank diagram from memory (independent practice). This is the worked-example fading sequence.

- **Problem:** Comprehension questions encourage search-and-copy
- **Principle:** Goal-free effect — specific goal states force means-ends analysis, increasing extraneous load
- **Fix:** Replace the 10 comprehension questions with a single goal-free instruction: "Study the water cycle diagram. Write down everything you can about how water moves through the system and why." This encourages schema building rather than information hunting. If specific questions are needed, use them *after* the free-study phase, as retrieval practice.

- **Problem:** No worked example for novice learners
- **Principle:** Worked example effect (Sweller & Cooper, 1985) — novices learn more from studying worked examples than from solving problems
- **Fix:** Before any independent work, provide a fully completed, annotated example showing one part of the water cycle in detail (e.g., the evaporation-condensation-precipitation sequence), with explicit annotations explaining WHY each step occurs. Then gradually fade the support.

### Expertise Reversal Check
This task is designed for novice learners, and the modifications above are appropriate for novices. However, if this same task were used with Year 10 students revising the water cycle (who already have a strong schema), the worked example approach would be counterproductive — Kalyuga et al. (2003) demonstrated that worked examples increase load for experts because they must process redundant information. For advanced learners, go directly to the blank diagram + retrieval practice approach, skipping the worked example and completion stages.

---

## Known Limitations

1. **Cannot observe actual student behaviour.** This analysis is based on task design, not on how students actually experience the task. Two students may experience the same task with very different cognitive loads depending on their prior knowledge. Teacher observation during the task remains essential — signs of overload include task abandonment, copying without understanding, and asking procedural questions ("where do I write the answer?") rather than content questions.

2. **Intrinsic load cannot be reduced without changing the content.** If the content itself is inherently complex (high element interactivity), this analysis can only reduce extraneous load and optimise sequencing — it cannot make complex content simple. For high-intrinsic-load content, the answer is often to break the content into sub-elements taught across multiple lessons, not to simplify it within one lesson.

3. **The expertise reversal effect means recommendations are expertise-dependent.** What helps a novice hinders an expert and vice versa. If the student level is inaccurate (e.g., described as "novice" but students actually have substantial prior knowledge), the modifications may be counterproductive. Teachers must calibrate based on actual student knowledge, not assumed knowledge.

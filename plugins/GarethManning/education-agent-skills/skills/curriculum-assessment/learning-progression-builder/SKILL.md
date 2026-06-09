---
# AGENT SKILLS STANDARD FIELDS (v2)
name: learning-progression-builder
description: "Build a learning progression showing prerequisite-to-mastery steps for a target skill or understanding. Use when sequencing content, designing diagnostics, or mapping prerequisite gaps."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "curriculum-assessment/learning-progression-builder"
skill_name: "Learning Progression Builder"
domain: "curriculum-assessment"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Heritage (2008) — Learning progressions: supporting instruction and formative assessment"
  - "Popham (2007) — The lowdown on learning progressions"
  - "Daro et al. (2011) — Learning trajectories in mathematics: a foundation for standards, curriculum, assessment, and instruction"
  - "Wilson & Bertenthal (2005) — Systems for state science assessment"
  - "Hattie & Donoghue (2016) — Learning strategies: a synthesis and conceptual model"
input_schema:
  required:
    - field: "target_skill"
      type: "string"
      description: "The skill or understanding at the end of the progression — what students should be able to do"
    - field: "student_level"
      type: "string"
      description: "Age/year group range the progression covers"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "starting_point"
      type: "string"
      description: "Where students typically begin — their existing knowledge"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: class data showing where different students currently sit on the progression"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: relevant curriculum standards or progression documents"
output_schema:
  type: "object"
  fields:
    - field: "progression_map"
      type: "array"
      description: "Ordered sequence of stages from novice to target, with observable indicators at each stage"
    - field: "prerequisite_relationships"
      type: "object"
      description: "Which stages depend on which — the prerequisite structure"
    - field: "common_stuck_points"
      type: "array"
      description: "Where students commonly stall and why"
    - field: "diagnostic_tasks"
      type: "array"
      description: "Quick tasks that reveal which stage a student is at"
chains_well_with:
  - "competency-unpacker"
  - "formative-assessment-technique-selector"
  - "practice-problem-sequence-designer"
  - "backwards-design-unit-planner"
  - "curriculum-knowledge-architecture-designer"
  - "scope-and-sequence-designer"
teacher_time: "4 minutes"
tags: ["learning-progressions", "trajectories", "prerequisites", "diagnostic", "curriculum-mapping"]
---

# Learning Progression Builder

## What This Skill Does

Maps the learning progression from novice to target proficiency for a specific skill domain, identifying the sequential stages of understanding, the prerequisite relationships between them (what must come before what), common stuck points (where students typically stall and why), and diagnostic tasks that reveal which stage a student is currently at. The output is a progression map that teachers can use for three purposes: planning instruction (teaching in the right sequence), formative assessment (diagnosing where a student is), and differentiation (providing the right support for each student's current stage). AI is specifically valuable here because constructing a valid learning progression requires both deep content knowledge (understanding the logical structure of the domain) and pedagogical knowledge (knowing where students actually get stuck, which is not always where the content logic would predict).

## Evidence Foundation

Heritage (2008) defined learning progressions as "descriptions of the successively more sophisticated ways of thinking about a topic that can follow one another as children learn." She emphasised that progressions are hypothesised pathways, not rigid tracks — students may skip stages, revisit earlier stages, or take alternative routes. Popham (2007) argued that learning progressions are essential for formative assessment because they provide the "map" that makes it possible to locate a student's current understanding and identify the next step. Without a progression, a teacher knows a student is "struggling" but not WHERE in the learning pathway the difficulty lies. Daro et al. (2011) demonstrated that mathematics learning trajectories — empirically validated progressions — provide the foundation for coherent curriculum, assessment, and instruction. Wilson & Bertenthal (2005) applied learning progressions to science assessment, showing that progression-based assessment is more informative than standards-based assessment because it reveals the developmental pathway, not just whether a binary standard is met. Hattie & Donoghue (2016) showed that different learning strategies are effective at different stages of learning — surface strategies (memorisation, rehearsal) are effective early; deep strategies (elaboration, organisation) are effective later — which means the teaching approach should match the student's position on the progression.

## Input Schema

The teacher must provide:
- **Target skill:** What students should be able to do at the end. *e.g. "Solve multi-step equations with the unknown on both sides" / "Write a developed analytical paragraph about a text" / "Design and evaluate a fair scientific experiment"*
- **Student level:** Year group range. *e.g. "Year 7–9" / "KS3" / "Middle school"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Starting point:** Where students begin
- **Student profiles:** Class data showing current positions
- **Curriculum framework:** Relevant standards or progression documents

## Prompt

```
You are an expert in learning progressions and curriculum coherence, with deep knowledge of Heritage's (2008) framework for learning progressions, Popham's (2007) work on progression-based assessment, and Hattie & Donoghue's (2016) research on stage-appropriate learning strategies. You understand that learning progressions are hypothesised pathways — they describe the typical developmental sequence but acknowledge that individual students may follow different routes.

Your task is to build a learning progression for:

**Target skill:** {{target_skill}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the target skill.
**Starting point:** {{starting_point}} — if not provided, identify the typical entry point for students at the beginning of the stated level range.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical class where students are at various points along the progression.
**Curriculum framework:** {{curriculum_framework}} — if not provided, build on general curriculum expectations.

Apply these evidence-based principles:

1. **Identify sequential stages (Heritage, 2008):**
   - Define 5–7 stages from novice to target proficiency.
   - Each stage should describe a qualitatively different level of understanding or capability — not just "more" of the same thing.
   - Each stage should be OBSERVABLE — described in terms of what the student can DO, not what they "understand" internally.
   - Stages should be ordered by typical developmental sequence, acknowledging that some students may not follow this exact order.

2. **Map prerequisite relationships (Daro et al., 2011):**
   - Which stages MUST come before which? (Not just which usually do, but which logically must.)
   - Identify both linear prerequisites (A must come before B) and parallel prerequisites (both C and D must be in place before E).
   - Distinguish hard prerequisites (the stage cannot be attempted without the prior) from soft prerequisites (the stage is easier with the prior but possible without it).

3. **Identify common stuck points (Popham, 2007):**
   - Where do students typically stall? These are the diagnostic priorities.
   - For each stuck point: what does "stuck" look like, and what is usually causing it?
   - Stuck points often occur at transitions between qualitatively different types of thinking (e.g., from procedural to conceptual, from concrete to abstract).

4. **Design diagnostic tasks (Heritage, 2008; Popham, 2007):**
   - For each stage, provide a quick task (2–5 minutes) that reveals whether a student has reached that stage.
   - Diagnostic tasks should be efficient — they test the KEY indicator of each stage, not everything a student at that stage can do.
   - The task should distinguish between adjacent stages — a student at Stage 3 should pass the Stage 3 diagnostic but fail the Stage 4 diagnostic.

5. **Stage-appropriate teaching approaches (Hattie & Donoghue, 2016):**
   - Early stages: surface strategies — explicit instruction, modelling, practice with feedback.
   - Middle stages: deep strategies — elaboration, connection-making, explaining reasoning.
   - Later stages: transfer strategies — application to new contexts, evaluation, independent problem-solving.

Return your output in this exact format:

## Learning Progression: [Target Skill]

**From:** [Starting point]
**To:** [Target proficiency]
**For:** [Student level range]

### Progression Map

For each stage:
**Stage [N]: [Name]**
- **What the student can do:** [Observable indicators]
- **Key shift from previous stage:** [What's qualitatively different]
- **Prerequisite:** [What must be in place first]
- **Diagnostic task:** [Quick task that reveals whether the student is at this stage]

### Prerequisite Diagram

[Visual or textual representation of which stages depend on which]

### Common Stuck Points

For each stuck point:
**Stuck between Stage [X] and Stage [Y]**
- **What "stuck" looks like:** [Observable signs]
- **What usually causes it:** [The underlying difficulty]
- **How to unstick:** [Targeted teaching intervention]

### Teaching Implications

[How the progression should inform instruction — what to teach first, where to invest time, when to use which teaching strategies]

**Self-check before returning output:** Verify that (a) stages are qualitatively distinct, (b) each stage has observable indicators, (c) prerequisite relationships are explicit, (d) diagnostic tasks distinguish between adjacent stages, (e) stuck points are based on common patterns, and (f) the progression represents a developmental pathway, not just a list of topics.
```

## Example Output

**Scenario:** *Target skill: "Write a developed analytical paragraph about a literary text, using embedded quotations and explaining the effect of language on the reader" / Student level: "Year 7–9" / Subject area: "English Literature"*

---

## Learning Progression: Analytical Writing About Literature

**From:** Can retell what happens in a text (narrative summary)
**To:** Can write a developed analytical paragraph using embedded quotations and explaining the effect of language choices on the reader
**For:** Year 7–9 English Literature

### Progression Map

**Stage 1: Retelling**
- **What the student can do:** Summarises what happens in the text in chronological order. "Scrooge is a mean old man who doesn't like Christmas. Then three ghosts visit him and he becomes nice."
- **Key shift from previous stage:** Entry point — no prior stage required.
- **Prerequisite:** Basic reading comprehension (can understand the events of the text).
- **Diagnostic task:** "Tell me what happens in Chapter 1." If the student can retell accurately, they're at Stage 1. If they can ONLY retell (and cannot do Stage 2), they need to progress.

**Stage 2: Identifying Features**
- **What the student can do:** Points out language features without analysis. "The writer uses a simile." "There is alliteration in this sentence." Can name techniques when they see them.
- **Key shift from previous stage:** Moves from "what happens" to "how it's written" — a fundamental shift from content to craft.
- **Prerequisite:** Stage 1 (must understand the text before analysing it). Must know the names of at least 5 techniques.
- **Diagnostic task:** "Highlight and label any language techniques you can find in this paragraph." If the student can identify 2+ techniques correctly, they're at Stage 2.

**Stage 3: Quotation + Comment**
- **What the student can do:** Selects a quotation and makes a comment about it: "The writer says 'dark and stormy night' which shows it was scary." The comment is relevant but undeveloped — it's a single statement, not an explanation.
- **Key shift from previous stage:** Moves from just naming techniques to selecting evidence and making a claim about it.
- **Prerequisite:** Stage 2 (must be able to identify features). Must understand that quotations serve as evidence.
- **Diagnostic task:** "Choose a quotation from the text and explain what it shows." If the student selects a relevant quotation and makes one relevant comment (even if brief), they're at Stage 3.

**Stage 4: Explaining Effect**
- **What the student can do:** Explains what the language does to the reader: "The word 'raging' suggests the sea is violent and out of control, which makes the reader feel afraid for the character." The explanation is specific — it names a feeling, image, or thought the reader experiences.
- **Key shift from previous stage:** Moves from commenting on what the text says to explaining what the text DOES — from content to effect. This is the critical analytical shift.
- **Prerequisite:** Stage 3 (must be able to select evidence and comment). Must understand that writers make choices to create effects on readers.
- **Diagnostic task:** "What effect does the word 'raging' have on the reader? What does it make you think or feel?" If the student can name a specific effect (not "it's effective" or "it makes you want to read on"), they're at Stage 4.

**Stage 5: Developed Analytical Paragraph**
- **What the student can do:** Writes a paragraph that follows a coherent structure: point → embedded quotation → analysis of specific words → explanation of effect → link to wider meaning. Each part connects logically to the next.
- **Key shift from previous stage:** Moves from isolated comments to sustained, structured analysis — multiple sentences that build on each other.
- **Prerequisite:** Stage 4 (must be able to explain effect). Must understand paragraph structure and cohesion.
- **Diagnostic task:** "Write one paragraph analysing how the writer creates tension in this extract." If the paragraph has a clear point, embedded evidence, specific word-level analysis, and explained effect, the student is at Stage 5.

**Stage 6: Evaluative and Comparative Analysis (Target)**
- **What the student can do:** Writes analytical paragraphs that consider multiple possible interpretations, compare techniques, evaluate which is most effective, and connect analysis to the writer's wider purpose and themes. Uses evaluative and comparative language: "While the metaphor creates visual power, it is the sentence structure that truly conveys the character's distress."
- **Key shift from previous stage:** Moves from single-interpretation analysis to evaluative, comparative, multi-layered analysis — the student considers WHY the writer made this choice over alternatives.
- **Prerequisite:** Stage 5 (must be able to write a developed analytical paragraph). Must have sufficient knowledge of the wider text and context.
- **Diagnostic task:** "Analyse how the writer creates [effect] in this extract. Consider at least two techniques and evaluate which is more effective." If the student compares techniques and evaluates with reasoning, they're at Stage 6.

### Prerequisite Diagram

```
Stage 1 (Retelling)
    ↓
Stage 2 (Identifying Features) ← [requires: knowledge of technique names]
    ↓
Stage 3 (Quotation + Comment)
    ↓
Stage 4 (Explaining Effect) ← [critical shift: content → effect]
    ↓
Stage 5 (Developed Paragraph) ← [requires: paragraph structure skills]
    ↓
Stage 6 (Evaluative Analysis) ← [requires: wider text knowledge]
```

Linear progression with lateral prerequisites at Stages 2, 5, and 6.

### Common Stuck Points

**Stuck between Stage 2 and Stage 3: Can identify techniques but can't select evidence**
- **What "stuck" looks like:** The student highlights and labels techniques enthusiastically but freezes when asked to "choose a quotation and explain it." They can spot features but can't select the BEST one for analysis.
- **What usually causes it:** The student has been trained to identify ALL techniques (feature-spotting) but not to evaluate which quotation is worth writing about. They see techniques as things to find, not things to analyse.
- **How to unstick:** Teach quotation selection: "Here are three quotations. Which one gives you the most to write about? Why?" Practise choosing between quotations before asking students to find their own.

**Stuck between Stage 3 and Stage 4: Can comment but can't explain effect (THE MOST COMMON STUCK POINT)**
- **What "stuck" looks like:** The student writes "This shows that..." and makes a relevant comment, but the comment describes the content, not the effect. "The metaphor shows the sea is dangerous" (content) vs. "The metaphor makes the reader feel afraid" (effect). Or the student defaults to generic effect claims: "This is effective and makes the reader want to read on."
- **What usually causes it:** The student doesn't distinguish between what the text SAYS and what it DOES. They have been taught to find meaning in the text but not to consider the reader's experience. This is a conceptual barrier — they need to understand that analysis is about the EFFECT of language, not just its meaning.
- **How to unstick:** Two-question technique: after every quotation, ask "What does this make you SEE?" and "What does this make you FEEL?" These questions force attention toward the reader's experience. Model extensively: show the difference between content comments and effect analysis side by side.

**Stuck between Stage 5 and Stage 6: Can write a paragraph but can't evaluate or compare**
- **What "stuck" looks like:** The student writes competent PEEL paragraphs that analyse one technique at a time, but cannot compare techniques, consider alternative interpretations, or evaluate relative effectiveness. Their paragraphs are solid but independent — they don't build toward a larger analytical argument.
- **What usually causes it:** The student has mastered the procedural skill (writing an analytical paragraph) but hasn't developed the evaluative thinking to go beyond it. Comparison and evaluation are higher-order skills that require the student to hold multiple analyses in mind simultaneously.
- **How to unstick:** Teach comparison explicitly: "You've written about the metaphor. Now write about the sentence structure. Now — which technique is MORE effective at creating tension, and why?" Provide a comparison frame: "While [technique 1] creates [effect], [technique 2] is arguably more effective because..."

### Teaching Implications

1. **Invest the most time at the Stage 3→4 transition.** This is where most students stall and where the critical analytical shift occurs. A student who can explain effect is ready for rapid progress through Stages 5 and 6; a student who can't explain effect will plateau regardless of how much they write.

2. **Don't skip stages.** A student who can't yet identify techniques (Stage 2) should not be asked to write an analytical paragraph (Stage 5). The stages build on each other — skipping to the end task without building the foundation produces overwhelm, not learning.

3. **Use diagnostic tasks to differentiate.** In any Year 8 class, students will be spread across Stages 2–5. Use the diagnostic tasks to locate each student, then provide stage-appropriate instruction: Stage 2 students practise identification, Stage 3 students practise quotation selection, Stage 4 students practise effect explanation, Stage 5 students practise paragraph construction.

4. **Match teaching approach to stage.** Stages 1–3: explicit instruction, modelling, guided practice (surface strategies). Stage 4: think-alouds, worked examples, peer discussion (deep strategies). Stages 5–6: independent practice, self-assessment against criteria, comparative writing tasks (transfer strategies).

---

## Known Limitations

1. **Learning progressions are hypothesised pathways, not fixed tracks.** Individual students may skip stages, regress temporarily, or develop skills in a different order. The progression describes the TYPICAL developmental sequence — the teacher must use professional judgment when students don't follow the expected path.

2. **The progression describes skill development in ONE domain.** A student may be at Stage 5 for poetry analysis but Stage 3 for prose analysis, because the underlying texts present different challenges. Progressions are domain-specific — the teacher should assess each domain separately.

3. **Diagnostic tasks provide a snapshot, not a comprehensive assessment.** A student who passes the Stage 4 diagnostic task on one occasion may not consistently perform at Stage 4. The diagnostic locates the student's approximate position — ongoing formative assessment provides the more complete picture.

---
# AGENT SKILLS STANDARD FIELDS (v2)
name: self-regulation-scaffold-generator
description: "Generate scaffolds supporting student self-regulation across planning, monitoring, and evaluation phases. Use when students struggle to manage their own learning during extended or independent tasks."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "self-regulated-learning/self-regulation-scaffold-generator"
skill_name: "Self-Regulation Scaffold Generator"
domain: "self-regulated-learning"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Zimmerman (2000) — Attaining self-regulation: a social cognitive perspective"
  - "Zimmerman (2002) — Becoming a self-regulated learner: an overview"
  - "Pintrich (2000) — The role of goal orientation in self-regulated learning"
  - "Dignath & Büttner (2008) — Components of fostering self-regulated learning among students: a meta-analysis (effect size ~0.69)"
  - "Panadero (2017) — A review of self-regulated learning: six models and four directions for research"
input_schema:
  required:
    - field: "task_description"
      type: "string"
      description: "The specific learning task students will complete"
    - field: "student_level"
      type: "string"
      description: "Age/year group and self-regulation maturity (novice/developing/independent)"
    - field: "task_duration"
      type: "string"
      description: "How long students have to complete the task (single lesson, multi-lesson, homework, project)"
  optional:
    - field: "srl_phase_focus"
      type: "string"
      description: "Which SRL phase to emphasise: forethought, performance, or reflection"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: individual self-regulation data, executive function profiles"
    - field: "previous_srl_instruction"
      type: "string"
      description: "What SRL strategies students have already been taught"
    - field: "subject_area"
      type: "string"
      description: "Subject context for domain-specific strategy selection"
output_schema:
  type: "object"
  fields:
    - field: "scaffolds"
      type: "object"
      description: "Phase-specific scaffolds for forethought, performance, and reflection"
    - field: "student_handout"
      type: "string"
      description: "A copy-pasteable student-facing scaffold document"
    - field: "teacher_moves"
      type: "array"
      description: "Specific teacher actions to support each SRL phase"
    - field: "fading_plan"
      type: "string"
      description: "How to progressively remove scaffolds as students develop independence"
chains_well_with:
  - "metacognitive-prompt-library"
  - "goal-setting-protocol-designer"
  - "agency-scaffold-generator"
  - "feedback-quality-analyser"
teacher_time: "4 minutes"
tags: ["self-regulation", "metacognition", "scaffolding", "independence", "executive-function"]
---

# Self-Regulation Scaffold Generator

## What This Skill Does

Produces phase-appropriate self-regulated learning scaffolds — structured supports for goal-setting, strategy selection, progress monitoring, and reflection — calibrated to a specific task and student age/maturity level. The output is a student-facing scaffold document plus teacher guidance on when and how to use each element. AI is specifically valuable here because effective SRL scaffolds must be calibrated to three variables simultaneously: the cognitive demands of the specific task, the developmental stage of the learner (a Year 7 student needs very different scaffolds from a Year 12 student), and the specific SRL phase being supported. Most teachers either over-scaffold (removing the self-regulation demand entirely) or under-scaffold (telling students to "plan your work" without showing them how).

## Evidence Foundation

Zimmerman (2000, 2002) established the cyclical model of self-regulated learning comprising three phases: forethought (goal-setting, strategic planning, self-efficacy beliefs), performance (self-monitoring, strategy use, attention control), and self-reflection (self-evaluation, causal attribution, adaptation). Pintrich (2000) extended this to include motivational and contextual factors, showing that goal orientation significantly affects which SRL strategies students deploy. Dignath & Büttner's (2008) meta-analysis of 74 studies found that SRL interventions produce an average effect size of 0.69, with the strongest effects when all three phases are explicitly scaffolded. Panadero (2017) reviewed six major SRL models and identified that the most effective interventions make self-regulation processes visible and teachable — students must be explicitly shown *how* to plan, monitor, and reflect, not just told to do so. Critically, SRL scaffolds must be faded over time; permanent scaffolds create dependency rather than independence.

## Input Schema

The teacher must provide:
- **Task description:** The specific learning task. *e.g. "Write a persuasive essay arguing for or against school uniforms (800 words, due Friday)" / "Complete a group science investigation into factors affecting plant growth over 3 weeks"*
- **Student level:** Year group and SRL maturity. *e.g. "Year 7, novice self-regulators" / "Year 11, developing — can plan but struggle with monitoring"*
- **Task duration:** How long students have. *e.g. "3 lessons plus homework" / "6-week project"*

Optional (injected by context engine if available):
- **SRL phase focus:** Which phase to emphasise (forethought, performance, or reflection)
- **Student profiles:** Individual self-regulation data, executive function profiles
- **Previous SRL instruction:** What strategies students have already been taught
- **Subject area:** Subject context for domain-specific strategies

## Prompt

```
You are an expert in self-regulated learning research, specialising in Zimmerman's (2000, 2002) cyclical SRL model and its classroom application. You understand the three phases of self-regulation (forethought, performance, self-reflection) and how to design scaffolds that develop genuine student independence rather than creating scaffold dependency.

Your task is to generate SRL scaffolds for the following:

**Task:** {{task_description}}
**Student level:** {{student_level}}
**Task duration:** {{task_duration}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**SRL phase focus:** {{srl_phase_focus}} — if not provided, generate scaffolds for all three phases, weighted toward the phase most critical for this task type and student level.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical class at the stated SRL maturity level.
**Previous SRL instruction:** {{previous_srl_instruction}} — if not provided, assume students have had minimal explicit SRL instruction and need concrete, structured scaffolds.
**Subject area:** {{subject_area}} — if not provided, infer from the task description and select domain-appropriate strategies.

Apply these evidence-based principles:

1. **Scaffold all three phases (Zimmerman, 2002):**
   - **Forethought:** Goal-setting (specific, proximal, process-focused), task analysis (what does this task require?), strategic planning (which strategies will I use?), self-efficacy activation (what do I already know that helps?)
   - **Performance:** Self-monitoring prompts (am I on track?), attention control strategies, help-seeking guidance (when and how to ask for help), time management checkpoints
   - **Self-reflection:** Self-evaluation against criteria, causal attribution (why did I succeed/struggle — focus on strategy use, not ability), strategy adaptation (what would I change next time?)

2. **Calibrate to developmental level (Dignath & Büttner, 2008):**
   - **Novice self-regulators (typically Years 5–8):** Highly structured scaffolds with sentence starters, checklists, and explicit step-by-step guides. The scaffold does much of the metacognitive work for the student.
   - **Developing self-regulators (typically Years 9–10):** Prompts rather than scripts. Students choose from strategy options rather than following a fixed sequence. More open-ended monitoring questions.
   - **Independent self-regulators (typically Years 11–13):** Minimal scaffolding. Reflective prompts only. Students design their own plans using frameworks they've internalised.

3. **Make it task-specific, not generic (Panadero, 2017):** "Plan your work" is not a scaffold. "Before you start writing, list the three strongest arguments you will use and the evidence for each" is a scaffold. Every prompt must be specific to this task.

4. **Include a fading plan:** Scaffolds are temporary structures. For each scaffold element, indicate when and how to reduce support as students develop competence. The goal is independence, not permanent reliance on the scaffold.

5. **Avoid ability-focused language:** All self-evaluation should focus on strategy use and effort, not ability. "I struggled because I didn't plan enough time for revision" (strategy attribution) is productive. "I struggled because I'm not good at this" (ability attribution) is counterproductive. Scaffold prompts must model strategy-focused attribution.

Return your output in this exact format:

## Self-Regulation Scaffolds: [Task Name]

**For:** [Student level]
**Task duration:** [Duration]

### Phase 1: Forethought (Before Starting)

**Goal-Setting:**
[Specific, task-relevant goal-setting prompts or templates]

**Task Analysis:**
[Prompts that help students break down what the task requires]

**Strategic Planning:**
[Strategy selection support — what approaches are available and when to use each]

### Phase 2: Performance (During the Task)

**Self-Monitoring Checkpoints:**
[Specific monitoring prompts tied to task milestones — not just "check your work"]

**Attention & Time Management:**
[Concrete strategies for maintaining focus and managing time across the task duration]

**Help-Seeking Guide:**
[When to ask for help, what to try first, how to ask effectively]

### Phase 3: Self-Reflection (After Completing)

**Self-Evaluation:**
[Prompts for evaluating work against specific criteria]

**Attribution & Adaptation:**
[Prompts that focus on strategy use, not ability]

### Student Handout

[A clean, copy-pasteable version of the scaffolds formatted for students — no teacher notes, age-appropriate language]

### Teacher Moves

[Specific teacher actions for each phase — modelling, prompting, checking in]

### Fading Plan

[How to reduce scaffold support over subsequent uses of this task type]

**Self-check before returning output:** Verify that (a) every scaffold prompt is specific to this task, not generic, (b) scaffolds are calibrated to the stated SRL maturity level, (c) self-evaluation focuses on strategy use rather than ability, (d) a fading plan is included, and (e) the student handout is written in student-appropriate language.
```

## Example Output

**Scenario:** *Task: "Write a 600-word analytical essay on how Shakespeare presents conflict in Act 3, Scene 1 of Romeo and Juliet. Use at least three quotations with analysis." / Student level: "Year 9, novice self-regulators" / Task duration: "2 lessons (50 minutes each) plus homework draft"*

---

## Self-Regulation Scaffolds: Analytical Essay — Conflict in Romeo and Juliet

**For:** Year 9, novice self-regulators
**Task duration:** 2 lessons + homework

### Phase 1: Forethought (Before Starting — Lesson 1, first 15 minutes)

**Goal-Setting:**
Complete these sentences before you begin:
- "By the end of today's lesson, I will have: _______________"
- "By the end of lesson 2, I will have: _______________"
- "The quality I most want to improve from my last essay is: _______________"

Teacher models an example: "By the end of today's lesson, I will have chosen my three quotations and written a plan for each paragraph. By the end of lesson 2, I will have a complete first draft. The quality I want to improve is my analysis — last time I described what happened instead of explaining what Shakespeare's language choices mean."

**Task Analysis:**
This task requires you to do four things. Tick each one so you know what's expected:
- [ ] Read Act 3 Scene 1 and identify moments where Shakespeare presents conflict
- [ ] Choose at least 3 quotations that show conflict
- [ ] For each quotation, explain *how* Shakespeare's language creates a sense of conflict (not just *what* happens)
- [ ] Structure your essay with an introduction, 3 analytical paragraphs, and a conclusion

**Strategic Planning:**
Choose your approach from these options:
- **Option A:** Read the scene first, highlight quotations, then plan all paragraphs before writing any.
- **Option B:** Plan and write one paragraph at a time, going back to the text for each one.
- **Option C:** Brain-dump everything you know about conflict in the scene, then organise it into a plan.

Circle one. There's no wrong answer — but you need to choose *before* you start, not just dive in.

### Phase 2: Performance (During the Task — Lessons 1–2)

**Self-Monitoring Checkpoints:**

*Checkpoint 1 — 20 minutes into Lesson 1:*
Stop and check:
- [ ] I have chosen at least 3 quotations. (If not: go back to the text now. Look for moments where characters argue, threaten, or fight.)
- [ ] I have a plan for my essay. (If not: write one sentence for each paragraph saying what it will argue.)
- [ ] I understand what "analyse" means for this task. (If not: ask your teacher to show you the difference between describing and analysing.)

*Checkpoint 2 — 20 minutes into Lesson 2:*
Stop and check:
- [ ] I have written at least 2 analytical paragraphs. (If not: you're behind. Skip the introduction for now and write your strongest paragraph first.)
- [ ] Each paragraph has a quotation AND an explanation of how Shakespeare's language creates conflict. (If not: go back to your most recent paragraph. Underline your quotation. Now check — did you explain what Shakespeare is *doing* with those words, or just describe what happens?)
- [ ] My analysis uses phrases like "Shakespeare uses... to suggest..." or "This creates a sense of... because..." (If not: add one of these sentence starters to each paragraph.)

**Attention & Time Management:**
You have 100 minutes of lesson time plus homework. Suggested split:
| Time | Task |
|------|------|
| Lesson 1: 0–15 min | Read scene, choose quotations, plan |
| Lesson 1: 15–50 min | Write paragraphs 1 and 2 |
| Lesson 2: 0–10 min | Re-read what you wrote. Does it analyse or describe? |
| Lesson 2: 10–45 min | Write paragraph 3, introduction, conclusion |
| Lesson 2: 45–50 min | Self-reflection checkpoint (below) |
| Homework | Read through, improve one paragraph using self-evaluation |

**Help-Seeking Guide:**
Before asking for help, try these steps first:
1. Re-read the task instructions. Does the answer to your question appear there?
2. Look at the model paragraph on the classroom wall. Does it show you what to do?
3. Ask your partner: "Can you tell me if this sentence analyses or describes?"

If you've tried all three and you're still stuck, raise your hand and tell the teacher:
"I'm stuck on ____________. I've tried ____________ but it's not working because ____________."

### Phase 3: Self-Reflection (After Completing — End of Lesson 2 + homework)

**Self-Evaluation:**
Read your essay and answer honestly:

| Criterion | Yes / Partly / Not yet | Evidence |
|-----------|----------------------|----------|
| I used at least 3 quotations from Act 3 Scene 1 | | Which ones? |
| I explained HOW Shakespeare's language creates conflict (not just WHAT happens) | | Pick your best example of analysis. Copy the sentence here: |
| My essay has a clear structure (intro, 3 paragraphs, conclusion) | | |
| I used analytical language ("Shakespeare uses...", "This suggests...", "The effect is...") | | How many times? |

**Attribution & Adaptation:**
Complete these sentences:
- "The strongest part of my essay is ____________ because I used the strategy of ____________."
- "The part I found hardest was ____________. Next time I would try the strategy of ____________ to handle this better."
- "Compared to my last piece of analytical writing, I improved at ____________."

*(Note: all three sentences focus on what you DID, not on what you ARE. "I didn't plan enough" is useful feedback to yourself. "I'm bad at essays" is not.)*

### Student Handout

---

**My Essay Plan — Conflict in Romeo and Juliet**

**My goals for this task:**
1. By the end of lesson 1, I will have: _______________
2. By the end of lesson 2, I will have: _______________
3. The quality I want to improve from last time: _______________

**My approach:** (circle one) A: Plan everything first / B: One paragraph at a time / C: Brain-dump then organise

**My quotations:**
1. "_______________" — I chose this because _______________
2. "_______________" — I chose this because _______________
3. "_______________" — I chose this because _______________

**Checkpoint 1 (20 min into Lesson 1):** 3 quotations? [ ] Plan done? [ ] Know what "analyse" means? [ ]

**Checkpoint 2 (20 min into Lesson 2):** 2+ paragraphs? [ ] Each has quotation + analysis? [ ] Using analytical phrases? [ ]

**Self-evaluation after finishing:**
- Best analysis sentence I wrote: _______________
- Hardest part + what I'd try next time: _______________
- What I improved from last time: _______________

---

### Teacher Moves

- **Forethought phase:** Model goal-setting aloud: "Watch me set my goals for this task. I'm going to think about what I struggled with last time..." Then give students 5 minutes to complete their own. Walk the room and check plans — gently redirect students who set vague goals ("do a good essay") toward specific, process-focused ones ("use analytical language in every paragraph").
- **Performance phase:** At each checkpoint, stop the class for 2 minutes. Ask students to physically tick the boxes. Ask 2–3 students: "What did your checkpoint tell you? What are you going to do about it?" This normalises self-monitoring as a routine, not an interruption.
- **Reflection phase:** Insist on strategy-focused attribution. If a student writes "I'm just not good at analysis," prompt: "What strategy could you use to make your analysis stronger? Let's look at the model — what did they do that you didn't do yet?" Redirect from ability to strategy every time.

### Fading Plan

- **First use (this task):** Full scaffolds — checklists, sentence starters, timed checkpoints, teacher-led modelling.
- **Second use (next analytical essay, ~4 weeks later):** Remove sentence starters for goal-setting. Keep monitoring checklists but ask students to write their own checkpoint questions. Keep self-evaluation framework.
- **Third use (~8 weeks later):** Remove monitoring checklists. Give students a blank planning template and ask them to design their own checkpoints. Keep self-evaluation framework but remove sentence starters.
- **Fourth use onwards:** Scaffold available on request, not distributed automatically. Students who demonstrate consistent self-regulation work without scaffolds. Students who struggle get the previous version. Differentiate by demonstrated competence, not assumed ability.

---

## Known Limitations

1. **SRL scaffolds can become compliance exercises rather than genuine self-regulation.** If students tick checkboxes without actually monitoring their work, the scaffold has failed. Teacher observation is essential — look for students who pause, re-read, and adjust, not just those who tick and continue. The scaffold prompts the behaviour; only teacher follow-up can verify it's genuine.

2. **The fading timeline is approximate and varies enormously across students.** Some students will be ready to shed scaffolds after two uses; others may need them for a full year. Fading should be based on demonstrated self-regulation competence, not time elapsed. Teachers need to observe, not assume.

3. **Self-regulation is culturally and contextually situated.** Zimmerman's model was developed primarily in Western educational contexts. Students from educational traditions that emphasise teacher direction, collective learning, or different relationships to authority may need scaffolds adapted to their cultural context — not because they lack self-regulation capacity, but because the specific behaviours scaffolded (individual goal-setting, self-evaluation, independent help-seeking) may not map directly to their prior educational experience.

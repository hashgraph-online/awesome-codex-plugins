---
# AGENT SKILLS STANDARD FIELDS (v2)
name: goal-setting-protocol-designer
description: "Design a structured goal-setting protocol using SMART or implementation-intention frameworks for students. Use when launching units, projects, or developing student self-direction habits."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "self-regulated-learning/goal-setting-protocol-designer"
skill_name: "Goal-Setting Protocol Designer"
domain: "self-regulated-learning"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Locke & Latham (1990) — A Theory of Goal Setting and Task Performance"
  - "Locke & Latham (2002) — Building a practically useful theory of goal setting and task motivation"
  - "Zimmerman & Bandura (1994) — Impact of self-regulatory influences on writing course attainment"
  - "Schunk (1990) — Goal setting and self-efficacy during self-regulated learning"
  - "Morisano et al. (2010) — Setting, elaborating, and reflecting on personal goals improves academic performance"
input_schema:
  required:
    - field: "learning_context"
      type: "string"
      description: "The unit, project, or task students are setting goals for"
    - field: "student_level"
      type: "string"
      description: "Age/year group and goal-setting experience level"
    - field: "timeframe"
      type: "string"
      description: "Duration over which goals will be pursued"
  optional:
    - field: "goal_type"
      type: "string"
      description: "Process goals, outcome goals, or both"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: self-efficacy levels, previous goal-setting data"
    - field: "success_criteria"
      type: "string"
      description: "From context engine: rubric or assessment criteria for the task"
    - field: "subject_area"
      type: "string"
      description: "Subject context"
output_schema:
  type: "object"
  fields:
    - field: "protocol"
      type: "object"
      description: "Step-by-step goal-setting protocol with teacher script and student templates"
    - field: "goal_examples"
      type: "array"
      description: "Modelled examples of weak vs. strong goals for this context"
    - field: "monitoring_checkpoints"
      type: "array"
      description: "Scheduled check-in points for goal progress review"
    - field: "student_template"
      type: "string"
      description: "Copy-pasteable goal-setting template for students"
chains_well_with:
  - "self-regulation-scaffold-generator"
  - "metacognitive-prompt-library"
  - "agency-scaffold-generator"
  - "self-efficacy-builder-sequence"
teacher_time: "4 minutes"
tags: ["goal-setting", "motivation", "self-regulation", "planning", "self-efficacy"]
---

# Goal-Setting Protocol Designer

## What This Skill Does

Generates a structured goal-setting protocol that guides students through setting specific, proximal, process-focused goals for a unit, project, or task — including teacher modelling scripts, weak-vs-strong goal examples, monitoring checkpoints, and a student template. The protocol is calibrated to developmental level and timeframe. AI is specifically valuable here because effective goal-setting requires understanding three overlapping bodies of research (Locke & Latham's goal-setting theory, Zimmerman's self-regulation model, Bandura's self-efficacy theory) and translating them into age-appropriate, task-specific scaffolds. Most school goal-setting exercises produce vague aspirations ("do my best," "get better at maths") that research shows have no motivational effect.

## Evidence Foundation

Locke & Latham (1990, 2002) established that goals improve performance through four mechanisms: directing attention, energising effort, increasing persistence, and promoting strategy development — but only when goals are specific (not vague), challenging (not easy), and accepted by the learner. Vague goals ("do your best") are no better than no goals at all. Zimmerman & Bandura (1994) demonstrated that self-set goals combined with self-monitoring produce stronger academic outcomes than externally assigned goals, because self-set goals enhance both self-efficacy and commitment. Schunk (1990) showed that proximal goals (short-term, achievable within days) are more effective than distal goals (long-term) for building self-efficacy in younger learners, because they provide more frequent success experiences. Morisano et al. (2010) found that a structured goal-setting and reflection intervention significantly improved academic performance in struggling university students. Critically, process goals ("I will use the PEEL structure in every paragraph") outperform outcome goals ("I will get an A") because students can control their process but not always their outcome — and process goals build transferable strategies.

## Input Schema

The teacher must provide:
- **Learning context:** What students are setting goals for. *e.g. "A 4-week persuasive writing unit" / "End-of-year science exam preparation" / "A design technology project: building a working circuit"*
- **Student level:** Year group and goal-setting experience. *e.g. "Year 7, first time doing structured goal-setting" / "Year 10, have done goal-setting before but goals tend to be vague"*
- **Timeframe:** Duration. *e.g. "4 weeks" / "one lesson" / "Term 2"*

Optional (injected by context engine if available):
- **Goal type:** Whether to focus on process, outcome, or both
- **Student profiles:** Self-efficacy levels, previous goal data
- **Success criteria:** Rubric or assessment criteria to anchor goals to
- **Subject area:** Subject context

## Prompt

```
You are an expert in motivation and goal-setting research, specialising in Locke & Latham's (1990, 2002) goal-setting theory, Zimmerman's self-regulation framework, and Bandura's self-efficacy theory. You understand why most school goal-setting fails (goals are vague, distal, and outcome-focused) and how to design protocols that produce goals students can actually pursue.

Your task is to design a goal-setting protocol for the following:

**Learning context:** {{learning_context}}
**Student level:** {{student_level}}
**Timeframe:** {{timeframe}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Goal type:** {{goal_type}} — if not provided, default to process goals for younger/novice students and a mix of process and outcome goals for older/experienced students. Process goals are always the priority.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical class at the stated experience level.
**Success criteria:** {{success_criteria}} — if provided, anchor goal options to specific criteria from the rubric. If not provided, generate appropriate criteria based on the learning context.
**Subject area:** {{subject_area}} — if not provided, infer from the learning context.

Apply these evidence-based principles:

1. **Specific over vague (Locke & Latham, 2002):** Every goal must be specific enough that both the student and teacher can unambiguously determine whether it has been met. "Improve my writing" fails. "Use at least two pieces of evidence in every analytical paragraph" passes.

2. **Process over outcome (Zimmerman & Bandura, 1994):** Prioritise goals about what students will DO (strategies, behaviours, effort allocation) over what they will ACHIEVE (grades, scores). Students control their process; they don't fully control their outcomes. Process goals also build transferable strategies.

3. **Proximal over distal (Schunk, 1990):** For younger students especially, break long-term goals into weekly or even daily sub-goals. Proximal goals provide frequent success experiences that build self-efficacy. A Year 7 student with a term-long goal will lose track; a Year 7 student with a weekly goal can see progress.

4. **Challenging but achievable:** Goals that are too easy don't motivate. Goals that are too hard undermine self-efficacy. Pitch goals at the "stretch zone" — requires effort but is achievable with good strategy use. For mixed-ability classes, differentiate the challenge level of goals.

5. **Self-set with guidance (Zimmerman & Bandura, 1994):** Students should choose their own goals from a structured set of options, not have goals imposed. Self-set goals produce stronger commitment. But unguided goal-setting produces vague goals — so provide a menu or framework.

6. **Built-in monitoring and revision:** Goals without check-in points decay. Build scheduled monitoring moments (at least weekly for multi-week timeframes) where students evaluate progress and adjust.

7. **Model weak vs. strong goals:** Students need to see the contrast between an ineffective goal and an effective one, with explicit explanation of why the strong goal is better.

Return your output in this exact format:

## Goal-Setting Protocol: [Learning Context]

**For:** [Student level]
**Timeframe:** [Duration]

### Step 1: Teacher Modelling
[A script showing the teacher modelling their own goal-setting process, including thinking aloud about why vague goals don't work]

### Step 2: Weak vs. Strong Goal Examples
[3 pairs of weak/strong goals specific to this learning context, with explanation of what makes each strong]

### Step 3: Goal-Setting Framework
[The framework students use to set their goals — structured choices, sentence stems, or menu options depending on developmental level]

### Step 4: Monitoring Checkpoints
[Scheduled check-in points with specific progress-review prompts]

### Step 5: Reflection and Revision
[End-of-cycle reflection protocol — evaluate goal attainment and set revised goals]

### Student Template
[Copy-pasteable goal-setting document for students]

**Self-check before returning output:** Verify that (a) all example goals are specific and measurable, (b) process goals outnumber outcome goals, (c) the protocol includes monitoring checkpoints, (d) goals are calibrated to be challenging but achievable for the stated level, (e) students choose their own goals within a structured framework rather than being assigned them, and (f) weak-vs-strong examples clearly explain what distinguishes them.
```

## Example Output

**Scenario:** *Learning context: "Year 8 History — 5-week unit on the Industrial Revolution, culminating in an assessed source-analysis essay" / Student level: "Year 8, have done basic goal-setting before but goals are typically vague ('do well in the essay')" / Timeframe: "5 weeks"*

---

## Goal-Setting Protocol: Year 8 History — Industrial Revolution Unit

**For:** Year 8, developing goal-setters
**Timeframe:** 5 weeks (15 lessons)

### Step 1: Teacher Modelling (5 minutes, Lesson 1)

"I'm going to set a goal for this unit too, and I want you to watch how I think about it.

My first instinct is to say: 'My goal is for you all to do well in the essay.' But let me think about why that's not a useful goal. Can I measure 'do well'? Not really — it means different things to different people. Can I control it? Not entirely — your marks depend on what you write, not just what I teach. Is it specific? No.

Let me try again. What do I actually want to improve this unit? Last unit, I noticed that when we did source analysis, lots of you described what the source *said* but didn't explain what it *tells us* — you weren't making inferences. So here's my goal:

*'In every source analysis this unit, I will model how to make an inference — not just what the source says, but what it suggests about life during the Industrial Revolution. I will do at least one live example per lesson.'*

That's specific — I can check it at the end of each lesson. It's about process — what I will DO, not what the result will be. And it's challenging — I sometimes rush past the modelling. That's my goal. Now you're going to set yours."

### Step 2: Weak vs. Strong Goal Examples

| Weak Goal | Strong Goal | Why the strong goal is better |
|-----------|------------|------------------------------|
| "Do well in the essay" | "In my essay, I will explain what each source *suggests* about the Industrial Revolution, not just describe what it says — I will use the phrase 'This suggests that...' at least 3 times" | Specific (exactly what to do and how many times), process-focused (a strategy the student can practise), measurable (count the phrases) |
| "Learn about the Industrial Revolution" | "Each week, I will write a 3-sentence summary of the key cause and effect we studied, without looking at my notes, to test whether I actually remember it" | Process-focused (retrieval practice strategy), proximal (weekly), builds genuine understanding rather than assuming it will happen |
| "Try harder in History" | "I will complete the source analysis homework on time every week, and when I get feedback, I will re-do one paragraph using the teacher's comments before moving on" | Specific behaviours (on-time homework + responding to feedback), within the student's control, directly addresses a common obstacle |

### Step 3: Goal-Setting Framework

Students choose **one process goal** and **one knowledge goal** from the menus below, or write their own following the same structure.

**Process Goal Menu** (choose or adapt one):
- "In every source analysis, I will use the phrase 'This suggests that...' to make at least one inference beyond what the source literally says."
- "Each week, I will test myself by writing what I remember about the week's lesson without notes — if I can't remember, I'll re-read before the next lesson."
- "When I get feedback on my writing, I will re-do one paragraph using the feedback before moving on, instead of just reading the comment."
- "In class discussions, I will contribute at least one idea per lesson — even if I'm not sure it's right."
- "Write my own:" _______________ (Must include: what I will do + how often + how I'll know I've done it)

**Knowledge Goal Menu** (choose or adapt one):
- "By the end of this unit, I will be able to explain three ways the Industrial Revolution changed working people's lives, with a specific example for each."
- "By the end of this unit, I will be able to analyse a source I've never seen before and make two inferences about what it suggests."
- "By the end of this unit, I will understand why historians disagree about whether the Industrial Revolution was mostly positive or mostly negative."
- "Write my own:" _______________ (Must include: what I'll know or be able to do + how I'd prove it)

### Step 4: Monitoring Checkpoints

| Week | Checkpoint | Prompt |
|------|-----------|--------|
| End of Week 1 | In-class (3 min) | "Look at your process goal. Have you done the thing you said you'd do this week? If yes, tick. If no, what got in the way? What will you change this week to make it happen?" |
| End of Week 2 | Written (5 min) | "Give yourself a score: 1 (haven't started), 2 (tried once), 3 (doing it regularly), 4 (it's becoming automatic). For your knowledge goal: can you pass the test right now? Try writing your answer without notes and see." |
| End of Week 3 | Partner check (5 min) | "Explain your goals to a partner. Ask them: 'Have you seen me doing this in class?' Their observation matters because we're often bad judges of our own habits." |
| End of Week 4 | Teacher conference (2 min per student, during independent work) | Teacher asks: "Show me evidence you've worked toward your goal. What's one thing you've improved? What would you change for the essay?" |

### Step 5: Reflection and Revision (Week 5, after essay submission)

**Post-essay reflection (10 minutes):**

1. "Read your process goal from Week 1. Did you do it? Score yourself honestly: 1 (didn't do it), 2 (sometimes), 3 (mostly), 4 (consistently)."
2. "Read your knowledge goal. Can you do the thing you set out to do? Prove it — write 2–3 sentences demonstrating it right now."
3. "Complete this sentence: 'The strategy that helped me most this unit was _____________, and I know it helped because _____________.'"
4. "Complete this sentence: 'Next unit, I would set a different/better goal because _____________.'"
5. "If you scored yourself a 3 or 4 on your process goal, set a harder version for next unit. If you scored 1 or 2, either revise the goal to make it more realistic OR identify what blocked you and address that first."

### Student Template

---

**MY GOALS — Industrial Revolution Unit**

**Name:** _______________ **Date:** _______________

**My process goal** (what I will DO):
_______________________________________________________________
How often: _______________ How I'll know I've done it: _______________

**My knowledge goal** (what I'll KNOW or be able to DO):
_______________________________________________________________
How I'd prove it: _______________

**Weekly check-ins:**
| Week | Did I do my process goal this week? (Y/N) | Score (1–4) | What helped or got in the way? |
|------|------------------------------------------|-------------|-------------------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |

**After the essay:**
- Did I meet my process goal? Score: ___
- Can I demonstrate my knowledge goal right now? ___
- Strategy that helped most: _______________
- Goal I'd set next time: _______________

---

## Known Limitations

1. **Goal-setting is motivating for students with moderate-to-high self-efficacy but can backfire for students with very low self-efficacy.** A student who has repeatedly failed at a subject may experience structured goal-setting as another opportunity for documented failure. For these students, begin with extremely proximal, low-stakes goals (daily, easily achievable) to build early success experiences before increasing challenge. Schunk (1990) emphasises that goal difficulty must be calibrated to current self-efficacy.

2. **Process goals require teachers to value process, not just outcomes.** If the classroom culture only celebrates grades and rankings, students will set outcome goals regardless of the protocol because that's what's actually rewarded. The protocol works best in classrooms where effort, strategy use, and improvement are visibly valued.

3. **Students need to see the goal-setting protocol used consistently across multiple units to develop the habit.** A one-off goal-setting activity in one unit will not produce lasting self-regulation. The research shows that SRL interventions need sustained implementation — Dignath & Büttner (2008) found the strongest effects in interventions lasting 8+ weeks. Teachers should use a consistent goal-setting framework across the year, adapting the content but keeping the structure.

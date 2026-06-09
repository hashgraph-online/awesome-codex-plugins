---
# AGENT SKILLS STANDARD FIELDS (v2)
name: flow-state-condition-designer
description: "Optimise a learning activity for flow by balancing challenge level, skill, clear goals, and immediate feedback. Use when students are bored, anxious, or disengaged during a task."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/flow-state-condition-designer"
skill_name: "Flow State Condition Designer"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Csikszentmihalyi (1990) — Flow: the psychology of optimal experience"
  - "Csikszentmihalyi (1997) — Finding Flow: the psychology of engagement with everyday life"
  - "Shernoff et al. (2003) — Student engagement in high school classrooms from the perspective of flow theory"
  - "Nakamura & Csikszentmihalyi (2002) — The concept of flow: conditions and characteristics"
  - "Hattie & Donoghue (2016) — Learning strategies: a synthesis and conceptual model"
input_schema:
  required:
    - field: "lesson_activity"
      type: "string"
      description: "The learning activity to optimise for flow conditions"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "current_engagement"
      type: "string"
      description: "How engaged students currently are with this activity — bored, compliant, partially engaged, deeply engaged"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: ability range, engagement patterns, specific needs"
    - field: "lesson_duration"
      type: "string"
      description: "Length of the lesson or activity"
    - field: "practical_constraints"
      type: "string"
      description: "Space, resources, technology, time limitations"
output_schema:
  type: "object"
  fields:
    - field: "flow_analysis"
      type: "object"
      description: "Analysis of how well the current activity meets flow conditions — challenge-skill balance, clear goals, immediate feedback"
    - field: "redesigned_activity"
      type: "object"
      description: "The activity redesigned to maximise flow conditions"
    - field: "differentiated_challenge"
      type: "object"
      description: "How to calibrate challenge for different ability levels so all students can experience flow"
    - field: "flow_killers"
      type: "array"
      description: "Common classroom practices that destroy flow and how to avoid them"
chains_well_with:
  - "motivation-diagnostic-task-redesign"
  - "perma-based-lesson-designer"
  - "practice-problem-sequence-designer"
  - "self-efficacy-builder-sequence"
teacher_time: "3 minutes"
tags: ["flow", "Csikszentmihalyi", "engagement", "optimal-experience", "challenge-skill-balance"]
---

# Flow State Condition Designer

## What This Skill Does

Analyses a learning activity against Csikszentmihalyi's flow conditions — challenge-skill balance, clear goals, immediate feedback, sense of control, concentration, and loss of self-consciousness — and redesigns it to maximise the probability of students experiencing flow (deep, absorbed engagement where time seems to disappear and the work itself is rewarding). The critical insight is that flow is not random — it occurs when specific conditions are met, and teachers can deliberately engineer these conditions. The output includes an analysis of which flow conditions the current activity meets or misses, a redesigned version optimised for flow, differentiated challenge calibration (because flow requires a PERSONAL challenge-skill match, not a class-level one), and a list of common classroom practices that destroy flow. AI is specifically valuable here because achieving flow in a classroom requires balancing individual challenge-skill ratios across 30 students simultaneously — a design challenge that benefits from systematic analysis.

## Evidence Foundation

Csikszentmihalyi (1990, 1997) identified flow as the state of optimal experience — the state in which people are so absorbed in what they're doing that nothing else seems to matter. He identified eight conditions for flow: (1) clear goals, (2) immediate feedback, (3) challenge-skill balance (the task is just beyond the person's current ability — not too easy, not too hard), (4) concentration and focused attention, (5) sense of control over the activity, (6) loss of self-consciousness, (7) transformation of time (time seems to fly), and (8) the activity becomes autotelic (rewarding in itself). Shernoff et al. (2003) applied flow theory to high school classrooms and found that flow experiences predicted academic engagement, achievement, and wellbeing. Students reported the highest engagement when challenge and skill were both high — boredom occurred when challenge was low (even if skill was high), and anxiety occurred when challenge was high but skill was low. The "flow channel" is the narrow band where challenge and skill are matched. Nakamura & Csikszentmihalyi (2002) elaborated that flow experiences build over time into "vital engagement" — a sustained relationship with the activity that goes beyond momentary absorption. Hattie & Donoghue (2016) confirmed that matching learning strategies to the student's current stage — surface strategies for early learning, deep strategies for later — is essential for maintaining the challenge-skill balance that flow requires.

## Input Schema

The teacher must provide:
- **Lesson activity:** What students are doing. *e.g. "Students complete a worksheet of 20 algebra questions" / "Students write a creative story based on a stimulus image" / "Students conduct a chemistry experiment following a step-by-step method sheet"*
- **Student level:** Year group. *e.g. "Year 9"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Current engagement:** How engaged students are
- **Student profiles:** Ability range, engagement patterns
- **Lesson duration:** Length of lesson
- **Practical constraints:** Space, resources, time

## Prompt

```
You are an expert in flow theory and optimal engagement, with deep knowledge of Csikszentmihalyi's (1990, 1997) flow conditions, Shernoff et al.'s (2003) application of flow to classroom settings, and the relationship between flow, learning, and wellbeing. You understand that flow is not a mood or a motivational trick — it is a specific psychological state that occurs when clear, measurable conditions are met, and teachers can design for these conditions.

CRITICAL: The most important flow condition is CHALLENGE-SKILL BALANCE. A task that is too easy for a student cannot produce flow (it produces boredom). A task that is too hard cannot produce flow (it produces anxiety). Flow occurs in the narrow channel where the task is just beyond the student's current ability — hard enough to require full concentration but achievable enough that the student believes they can succeed. This means that a SINGLE task at a SINGLE difficulty level cannot produce flow for a mixed-ability class. Flow design requires differentiated challenge.

Your task is to design flow conditions for:

**Lesson activity:** {{lesson_activity}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the activity.
**Current engagement:** {{current_engagement}} — if not provided, analyse the activity's likely engagement level based on its design.
**Student profiles:** {{student_profiles}} — if not provided, assume a mixed-ability class with a wide range.
**Lesson duration:** {{lesson_duration}} — if not provided, assume 50–60 minutes.
**Practical constraints:** {{practical_constraints}} — if not provided, assume standard classroom.

Apply these flow conditions:

1. **Clear goals (Csikszentmihalyi, 1990):**
   - Students must know EXACTLY what they're trying to achieve — not "learn about ecosystems" but "create a food web that includes 8 organisms and shows energy transfer at each level."
   - Goals should be specific, visible, and achievable within the session.
   - Ambiguity kills flow — when students don't know what "good" looks like, they can't enter flow because they can't gauge their progress.

2. **Immediate feedback (Csikszentmihalyi, 1990):**
   - Students must be able to tell whether they're succeeding or not WITHOUT waiting for the teacher.
   - Built-in feedback: answer checks, self-assessment criteria, peer feedback, observable outcomes.
   - If feedback requires waiting (teacher marking, next-lesson returns), flow cannot be sustained.

3. **Challenge-skill balance (Shernoff et al., 2003):**
   - The task must be in the "flow channel" for each student — personally challenging but achievable.
   - Too easy → boredom. Too hard → anxiety. Just right → flow.
   - This requires differentiation: easier entry points for lower-attaining students, extension challenges for higher-attaining students, ALL in the flow channel.

4. **Concentration and minimal interruption:**
   - Flow requires uninterrupted focus. Design protected work periods where students are not interrupted by transitions, instructions, or management.
   - Minimise context-switching — don't alternate between unrelated activities.
   - The teacher should avoid unnecessary interruptions: "Can I have everyone's attention for a moment" during deep work destroys flow for the entire class.

5. **Sense of control (Nakamura & Csikszentmihalyi, 2002):**
   - Students feel they have some control over their approach.
   - Choice of strategy, pace, or starting point creates ownership.
   - Over-prescribed tasks (follow steps 1–10 exactly) remove the sense of control that flow requires.

6. **Autotelic experience:**
   - The best flow tasks are intrinsically rewarding — the work itself is satisfying, not just the grade or the teacher's approval.
   - Design tasks where progress is visible and the product is something students care about.

Return your output in this exact format:

## Flow Conditions: [Activity Description]

**Activity:** [Summary]
**For:** [Student level]

### Flow Analysis

| Flow Condition | Current Status | What's Missing |
|---|---|---|
| Clear goals | [Met/Partially/Not met] | [What's needed] |
| Immediate feedback | [Met/Partially/Not met] | [What's needed] |
| Challenge-skill balance | [Met/Partially/Not met] | [What's needed] |
| Concentration | [Met/Partially/Not met] | [What's needed] |
| Sense of control | [Met/Partially/Not met] | [What's needed] |

### Redesigned Activity

[Complete redesigned version optimised for flow]

### Differentiated Challenge Map

[How to calibrate challenge for different ability levels so ALL students can be in the flow channel]

### Flow Killers to Avoid

[Common classroom practices that destroy flow — with alternatives]

**Self-check before returning output:** Verify that (a) all five key flow conditions are addressed, (b) challenge is differentiated for different ability levels, (c) feedback is immediate (not delayed), (d) goals are specific and visible, (e) the redesign maintains academic rigour, and (f) flow killers are identified with alternatives.
```

## Example Output

**Scenario:** *Lesson activity: "Students complete a worksheet of 20 algebra questions — solving linear equations with one unknown (e.g., 3x + 7 = 22)" / Student level: "Year 8" / Subject area: "Mathematics" / Current engagement: "Compliant — students do the work but without energy. Several finish in 10 minutes and are bored; several struggle with the first 5 questions and give up."*

---

## Flow Conditions: Linear Equations Practice

**Activity:** 20 algebra questions on solving linear equations
**For:** Year 8 Mathematics

### Flow Analysis

| Flow Condition | Current Status | What's Missing |
|---|---|---|
| Clear goals | **Partially met** | "Do 20 questions" is a completion goal, not a learning goal. Students aim to finish, not to master. |
| Immediate feedback | **Not met** | Students don't know if they're right until the teacher marks the work (or they check at the end). No feedback during the task. |
| Challenge-skill balance | **Not met** | ALL students get the SAME 20 questions. Students who find them easy are bored by question 3. Students who find them hard are anxious by question 3. The flow channel is missed for most of the class. |
| Concentration | **Partially met** | The task allows focus, but bored students create distractions, and struggling students call for help, breaking everyone's concentration. |
| Sense of control | **Not met** | Zero choice. Every student does the same 20 questions in the same order. The task is entirely prescribed. |

### Redesigned Activity

**Equations Climb — Self-Paced Challenge Sequence**

Replace the 20 identical-difficulty questions with a structured sequence of 5 levels, each containing 4 questions:

**Level 1 (Foundation):** One-step equations: x + 5 = 12, 3x = 18
**Level 2 (Building):** Two-step equations: 2x + 3 = 11, 5x − 4 = 16
**Level 3 (Core):** Multi-step with brackets: 3(x + 2) = 21, 2(3x − 1) = 16
**Level 4 (Extension):** Unknown on both sides: 3x + 5 = x + 13, 4x − 2 = 2x + 8
**Level 5 (Challenge):** Equations with fractions and negative solutions: (2x + 3)/4 = 5, 3(x − 4) = 2(x − 7)

**Rules:**
- Start at whichever level feels right for you. (Most students will start at Level 2 or 3.)
- Complete all 4 questions at a level. Check your answers against the answer key [provided, face-down on the desk or available on screen].
- If you get 3 or 4 right: move up a level.
- If you get 2 or fewer right: try the level again with new questions (a parallel set of 4 at the same difficulty).
- Your goal: reach the highest level you can in 25 minutes.
- You may work silently or quietly with your partner.

**Why this creates flow:**
- **Clear goals:** "Reach the highest level you can" is specific, personal, and motivating. Progress is visible — students can see themselves climbing.
- **Immediate feedback:** Answer key is available immediately. Students check after each level, not at the end. This creates a tight feedback loop: attempt → check → adjust → attempt.
- **Challenge-skill balance:** Students self-select their starting level and progress at their own pace. A student who finds Level 2 easy quickly reaches Level 3 (their flow channel). A student who struggles at Level 2 stays there until they've mastered it — still in THEIR flow channel. Every student is working at the edge of their ability.
- **Concentration:** The self-paced structure means no one is bored (they can always move up) and no one is stuck (they can repeat at their level). Both conditions sustain focus.
- **Sense of control:** Students choose their starting level and pace. The element of personal challenge ("Can I reach Level 5?") creates intrinsic motivation.

### Differentiated Challenge Map

| Student Group | Starting Level | Flow Channel | Teacher Support |
|---|---|---|---|
| Students who struggle with basic equations | Level 1 | Levels 1–2 | Check in after Level 1 — if they get 3+, celebrate and encourage Level 2. If stuck, provide a worked example for reference. |
| Students at expected level | Level 2 | Levels 2–4 | Most will enter flow here. Monitor by circulating. If stuck at Level 3, suggest: "Look at how you solved Level 2 — what's different about these?" |
| Higher-attaining students | Level 3 | Levels 3–5 | These students often finish worksheets fast and disengage. The climbing structure keeps them challenged. Level 5 is genuinely hard — they'll need to think. |
| Students who usually avoid maths | Level 1 | Levels 1–2 | Start easy — guaranteed success at Level 1 builds self-efficacy. The climb structure is motivating: "You've completed Level 1 — ready for Level 2?" Frame it as achievement, not remediation. |

### Flow Killers to Avoid

1. **Interrupting deep work for whole-class announcements.** "Can I just stop everyone for a moment..." destroys flow for 30 students simultaneously. If you need to give an instruction, wait until a natural transition point (between levels), use a visual countdown timer, or give the instruction to individual students as you circulate.

2. **Requiring students to wait for the teacher to check.** If students must put their hand up and wait for you to verify their answers, the feedback loop is broken. Provide answer keys so students can self-check immediately. Trust them — occasional cheating is less damaging than universal flow destruction.

3. **Setting a single time limit for the whole task.** "You have 20 minutes" creates two problems: fast students finish early and disengage, slow students feel pressured and anxious. The climbing structure has no "finish" — students always have the next level to attempt. Use the time limit to end the task, not to pace it.

4. **Making the whole class stop when one student has a question.** Answer individual questions individually. If multiple students have the same question, address it to a small group, not the whole class.

5. **Publicly displaying who is at which level.** This transforms the flow-inducing personal challenge into a social comparison exercise. Keep levels private — each student knows their own progress, but the class does not need a leaderboard. The motivation should be personal mastery, not competition.

---

## Known Limitations

1. **Flow requires a minimum skill level.** A student who cannot solve even Level 1 equations will not enter flow — they will experience frustration. Flow design assumes that students have sufficient foundational knowledge to engage with the easiest level. If they don't, direct instruction must precede the flow activity.

2. **Not all learning activities can be designed for flow.** Some learning requires low-engagement activities — listening to an explanation, reading a dense text, practising boring-but-necessary procedures. Flow design is most applicable to practice tasks, creative tasks, and problem-solving tasks. It is less applicable to initial instruction or assessment.

3. **Flow is individual.** A class of 30 students will not all be in flow simultaneously. The climbing structure maximises the probability that most students are in their flow channel for most of the time — but some students may still be bored (if Level 5 is too easy) or anxious (if Level 1 is too hard). The teacher must monitor and adjust.

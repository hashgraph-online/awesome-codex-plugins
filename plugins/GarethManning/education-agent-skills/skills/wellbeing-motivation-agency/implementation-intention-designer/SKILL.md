---
# AGENT SKILLS STANDARD FIELDS (v2)
name: implementation-intention-designer
description: "Create if-then implementation intentions and WOOP plans for specific student behaviour change goals. Use when students know what to do but struggle to follow through on habits or routines."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/implementation-intention-designer"
skill_name: "Implementation Intention Designer"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Gollwitzer (1999) — Implementation intentions: strong effects of simple plans"
  - "Gollwitzer & Sheeran (2006) — Implementation intentions and goal attainment: a meta-analysis"
  - "Duckworth et al. (2013) — From self-control to self-regulation: a declaration of independence"
  - "Oettingen & Gollwitzer (2010) — Strategies of setting and implementing goals: mental contrasting and implementation intentions"
  - "Bettinger et al. (2012) — The role of application assistance and information in college decisions"
input_schema:
  required:
    - field: "target_behaviour"
      type: "string"
      description: "The specific behaviour or habit the student needs to develop — what they should START doing or STOP doing"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "current_barrier"
      type: "string"
      description: "What currently prevents the student from doing the target behaviour — the specific obstacle"
    - field: "context"
      type: "string"
      description: "Whether this is for an individual student, a small group, or a whole class"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: prior behaviour patterns, goals, self-regulation capacity"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject, if the implementation intention is academic"
    - field: "time_horizon"
      type: "string"
      description: "How long the behaviour change needs to be maintained — one lesson, one week, one term"
output_schema:
  type: "object"
  fields:
    - field: "implementation_intention"
      type: "object"
      description: "The specific if-then plan — the trigger, the behaviour, and the context"
    - field: "mental_contrasting"
      type: "object"
      description: "The WOOP framework — Wish, Outcome, Obstacle, Plan"
    - field: "student_script"
      type: "string"
      description: "The exact wording for the student to write, say, or rehearse"
    - field: "monitoring_plan"
      type: "object"
      description: "How to track whether the implementation intention is being used and whether it's working"
chains_well_with:
  - "self-efficacy-builder-sequence"
  - "agency-scaffold-generator"
  - "self-regulated-learning-strategy-selector"
  - "metacognitive-prompt-generator"
teacher_time: "2 minutes"
tags: ["implementation-intentions", "Gollwitzer", "if-then-plans", "WOOP", "habits", "self-regulation", "behaviour-change"]
---

# Implementation Intention Designer

## What This Skill Does

Designs specific "if-then" plans (implementation intentions) that help students bridge the gap between intention and action — turning vague goals ("I'll revise more") into concrete, situation-specific plans ("If it's 4pm on a school day, then I will spend 25 minutes on spaced retrieval practice for my weakest subject"). The critical insight from Gollwitzer's research is that most failures of self-regulation are not failures of motivation — students often WANT to do the right thing but fail to follow through because they lack a specific plan for WHEN, WHERE, and HOW. Implementation intentions automate the decision by pre-loading it: the student decides in advance exactly what they will do in a specific situation, which removes the need for willpower in the moment. The output includes the implementation intention in the correct if-then format, a mental contrasting exercise (WOOP: Wish, Outcome, Obstacle, Plan) that strengthens commitment, a student-facing script they can rehearse, and a monitoring plan. AI is specifically valuable here because crafting effective implementation intentions requires identifying the specific situational trigger (not "when I feel like it" but "when I sit down at my desk after dinner"), anticipating obstacles, and calibrating the behaviour to be achievable — a precision that generic goal-setting advice lacks.

## Evidence Foundation

Gollwitzer (1999) demonstrated that implementation intentions — specific if-then plans that link a situational cue to a target behaviour — dramatically increase the probability of follow-through. His meta-analysis (Gollwitzer & Sheeran, 2006) found a medium-to-large effect size (d = 0.65) across 94 studies: people who formed implementation intentions were significantly more likely to achieve their goals than people with equivalent motivation but no specific plan. The mechanism is cognitive: the if-then format creates a mental link between the situation (the "if") and the behaviour (the "then"), so that encountering the situation automatically activates the intended behaviour — bypassing the need for conscious deliberation or willpower. Oettingen & Gollwitzer (2010) combined implementation intentions with mental contrasting (WOOP), showing that the combination is more effective than either alone: mental contrasting creates commitment (by making the person realise the obstacle is real and their plan is needed), and the implementation intention provides the specific action plan. Duckworth et al. (2013) applied this to education, showing that implementation intentions help students with study habits, homework completion, and exam preparation. Bettinger et al. (2012) demonstrated that simple implementation-intention-style assistance (specific plans for when and how to complete college applications) increased college enrollment among low-income students by 8 percentage points — a remarkable effect for a minimal intervention.

## Input Schema

The teacher must provide:
- **Target behaviour:** What the student needs to do. *e.g. "Start homework on the day it's set instead of the night before it's due" / "Use retrieval practice when revising instead of re-reading notes" / "Put their hand up to contribute in class discussion instead of staying silent" / "Take a 4-7-8 breath when they feel anxious before a test instead of panicking"*
- **Student level:** Year group. *e.g. "Year 10"*

Optional (injected by context engine if available):
- **Current barrier:** What prevents the behaviour
- **Context:** Individual, group, or whole class
- **Student profiles:** Prior behaviour patterns, goals
- **Subject area:** The subject
- **Time horizon:** How long the change needs to last

## Prompt

```
You are an expert in implementation intentions and behaviour change, with deep knowledge of Gollwitzer's (1999) if-then planning research, Gollwitzer & Sheeran's (2006) meta-analysis, Oettingen & Gollwitzer's (2010) WOOP framework (mental contrasting + implementation intentions), and Duckworth et al.'s (2013) application to educational settings. You understand that implementation intentions work because they automate decisions — the student decides in advance what they will do in a specific situation, removing the need for willpower in the moment.

IMPORTANT: Implementation intentions must be SPECIFIC. "I will try harder" is a goal intention, not an implementation intention. "If I sit down at my desk after dinner, then I will open my revision folder and do 15 minutes of flashcard practice" is an implementation intention. The power is in the specificity: a precise situational cue ("if") linked to a precise behaviour ("then").

IMPORTANT: The "if" must be a SITUATION, not a feeling. "If I feel motivated, then I will revise" won't work — motivation is unreliable. "If it's 4pm on Tuesday, then I will revise" works because 4pm on Tuesday arrives regardless of how the student feels.

Your task is to design implementation intentions for:

**Target behaviour:** {{target_behaviour}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Current barrier:** {{current_barrier}} — if not provided, identify the most likely barrier based on the target behaviour.
**Context:** {{context}} — if not provided, design for an individual student.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical student at this level.
**Subject area:** {{subject_area}} — if not provided, design for general academic use.
**Time horizon:** {{time_horizon}} — if not provided, design for sustained behaviour change (one term).

Apply these principles:

1. **Craft the if-then plan (Gollwitzer, 1999):**
   - **If:** A specific, observable situational cue. Time + place is the strongest cue. "If it's 4pm and I'm at my desk" is better than "If I have free time."
   - **Then:** A specific, doable action. "Then I will open my revision folder and complete 5 flashcards" is better than "Then I will revise."
   - The behaviour must be small enough to start without resistance. Starting is harder than continuing — design the "then" to overcome the starting barrier.

2. **Use mental contrasting — WOOP (Oettingen & Gollwitzer, 2010):**
   - **Wish:** What do you want to achieve? (The goal.)
   - **Outcome:** What would be the best thing about achieving it? (The motivation.)
   - **Obstacle:** What is the main inner obstacle? (Not external obstacles — internal ones: "I get distracted," "I feel tired," "I don't believe it will help.")
   - **Plan:** If [obstacle], then [strategy]. This is the implementation intention.
   - WOOP works because mental contrasting (imagining the positive outcome AND the real obstacle) creates commitment — the student recognises that the obstacle is real and that they need a plan.

3. **Anticipate obstacles (Gollwitzer & Sheeran, 2006):**
   - For each implementation intention, design a "coping plan": If the obstacle occurs, then...
   - Common obstacles: distraction (phone, siblings, TV), fatigue, forgetting, negative self-talk ("What's the point?").
   - Each obstacle gets its own if-then plan.

4. **Make it rehearsable:**
   - Implementation intentions work best when the student says or writes the if-then plan repeatedly.
   - The student should write it, say it, visualise it.
   - Physical artefacts (a card on the desk, a phone alarm with the plan as the label) serve as external triggers.

5. **Design monitoring (Duckworth et al., 2013):**
   - Simple tracking: did the student do the behaviour when the cue occurred? Yes/no.
   - A weekly check-in: "How many times this week did the situation arise? How many times did you follow through?"
   - Adjust the plan if follow-through is low — the plan may be too ambitious, or the cue may not be reliable.

Return your output in this exact format:

## Implementation Intention: [Target Behaviour]

**Target behaviour:** [What the student needs to do]
**For:** [Student level]

### The Implementation Intention

**If** [specific situational cue], **then** [specific behaviour].

[Explanation of why this cue and this behaviour are chosen]

### WOOP Framework

**Wish:** [The goal]
**Outcome:** [Best thing about achieving it]
**Obstacle:** [Main inner obstacle]
**Plan:** If [obstacle], then [strategy]

### Student Script

[The exact words the student should write, say, or rehearse — ready to use]

### Coping Plans

For each likely obstacle:
**If** [obstacle], **then** [coping strategy].

### Monitoring Plan

[How to track whether the plan is working — what to measure, when to check, when to adjust]

**Self-check before returning output:** Verify that (a) the "if" is a specific situation, not a feeling, (b) the "then" is a specific, small, doable action, (c) WOOP includes a genuine inner obstacle, (d) coping plans address the most likely obstacles, and (e) the monitoring plan is simple enough for the student to maintain.
```

## Example Output

**Scenario:** *Target behaviour: "Use retrieval practice when revising instead of re-reading notes — the student currently 'revises' by highlighting and re-reading, which feels productive but produces poor retention" / Student level: "Year 10" / Current barrier: "The student knows retrieval practice is more effective (they've been told) but defaults to re-reading because it feels easier and more comfortable — re-reading gives the illusion of familiarity, which feels like learning" / Time horizon: "Building a habit for GCSE revision over one term"*

---

## Implementation Intention: Retrieval Practice During Revision

**Target behaviour:** Use retrieval practice (self-testing) instead of re-reading when revising
**For:** Year 10

### The Implementation Intention

**If** I sit down at my desk to revise, **then** I will close my notes, open a blank page, and write everything I can remember about the topic for 5 minutes before looking at my notes.

This cue is chosen because "sitting down at my desk to revise" is a specific, observable moment that happens every revision session. The behaviour (close notes, open blank page, write from memory) is specific enough to follow without decision-making. The "5 minutes" time limit makes it feel achievable — the student isn't committing to an hour of retrieval practice, just 5 minutes of brain-dump before they do anything else. Once they've started, continuing is easier than starting.

### WOOP Framework

**Wish:** I want to revise effectively for my GCSEs so that I actually remember what I study.

**Outcome:** The best thing would be going into exams feeling confident because I KNOW I remember the material — not just recognising it, but actually being able to recall it. I'd feel less anxious and more in control.

**Obstacle:** My main inner obstacle is that re-reading feels easier and more comfortable. When I re-read my notes, everything looks familiar and I feel like I know it. Retrieval practice feels harder and more uncomfortable — I can't remember everything, which makes me feel like I don't know anything. I avoid the uncomfortable feeling by going back to re-reading.

**Plan:** **If** I feel the urge to re-read instead of self-testing, **then** I will say to myself: "Feeling like I can't remember is the POINT — that's the feeling of my brain working harder, which means I'm actually learning. Re-reading feels good but doesn't work. This feels hard but works."

### Student Script

Write this on a card and keep it on your revision desk:

"**Every time I sit down to revise:**
1. Close my notes
2. Open a blank page
3. Write everything I can remember for 5 minutes
4. THEN open my notes and check what I missed
5. Focus my revision on what I MISSED — that's where the learning is

**When it feels hard and I want to re-read instead:**
This feeling means it's working. Re-reading is a comfort blanket. Retrieval practice is a workout. The workout is what makes me stronger."

### Coping Plans

**If** I sit down to revise and immediately open my notes out of habit, **then** I will physically close the notebook, take a breath, and start the blank-page brain-dump. (The physical act of closing the notebook is the trigger for the new behaviour.)

**If** I do the brain-dump and can hardly remember anything (which feels discouraging), **then** I will remind myself: "The gaps I just found are the most valuable part of this revision session. Now I know EXACTLY what to focus on." Then I will check my notes and re-test myself on the things I couldn't remember.

**If** I'm tired and don't feel like doing retrieval practice, **then** I will do a SMALLER version: 2 minutes of brain-dump instead of 5. Doing something is better than doing nothing, and the habit matters more than the duration.

**If** I get to the end of the week and haven't used retrieval practice once, **then** I will not beat myself up (which leads to avoidance) but will set a specific alarm on my phone for Monday at 4pm that says "Close your notes. Blank page. 5 minutes. Go." Starting fresh is better than giving up.

### Monitoring Plan

**Daily:** After each revision session, mark on a simple tracker: "Did I start with the brain-dump? Yes / No." Keep the tracker visible — on the desk or phone home screen.

**Weekly:** At the end of each week, count: how many revision sessions did I do? How many started with retrieval practice? The goal is not 100% immediately — it's a trend upward. Week 1: 2 out of 5. Week 2: 3 out of 5. Week 4: 5 out of 5.

**Fortnightly check-in:** The teacher (or the student themselves) reviews: "Is retrieval practice becoming automatic? Do I still need the card, or am I doing it without thinking?" When the student no longer needs the card, the implementation intention has become a habit.

**Adjustment rule:** If follow-through is below 50% after two weeks, the plan needs adjusting. Possible adjustments: the cue isn't reliable (change the time or location), the behaviour is too demanding (reduce to 2 minutes), or the obstacle hasn't been addressed (identify a different inner barrier and create a new coping plan).

---

## Known Limitations

1. **Implementation intentions work best when motivation already exists.** If the student genuinely does not care about revising, an if-then plan won't create motivation — it provides a bridge from intention to action, not from apathy to intention. For students who lack motivation, pair this with the Motivation Diagnostic & Task Redesign skill before designing implementation intentions.

2. **Implementation intentions are most effective for simple, discrete behaviours.** "Start revision with retrieval practice" is a clear, discrete action. "Become a better student" is too complex for a single implementation intention. Complex behaviour change requires multiple implementation intentions targeting different specific actions.

3. **External obstacles override implementation intentions.** If the student's home environment prevents revision (no quiet space, caring responsibilities, family disruption), the most perfectly designed implementation intention will not help. The teacher must understand the student's context and address environmental barriers before expecting behaviour change from planning alone.

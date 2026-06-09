---
# AGENT SKILLS STANDARD FIELDS (v2)
name: feedback-quality-analyser
description: "Analyse existing written feedback for quality, specificity, actionability, and impact on student learning. Use when reviewing teacher or peer feedback to improve feedback practices."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "memory-learning-science/feedback-quality-analyser"
skill_name: "Feedback Quality Analyser & Rewriter"
domain: "memory-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Hattie & Timperley (2007) — The power of feedback: a meta-analysis (effect size ~0.73)"
  - "Shute (2008) — Focus on formative feedback: a review of the research"
  - "Kluger & DeNisi (1996) — Effects of feedback intervention on performance: a historical review and meta-analysis"
  - "Black & Wiliam (1998) — Assessment and classroom learning: formative assessment principles"
  - "Wisniewski et al. (2020) — The power of feedback revisited: a meta-analysis of educational feedback research"
input_schema:
  required:
    - field: "feedback_text"
      type: "string"
      description: "The existing feedback to analyse (teacher-written or peer-written)"
    - field: "task_context"
      type: "string"
      description: "What the student was asked to do and the learning objective"
  optional:
    - field: "student_work_summary"
      type: "string"
      description: "Brief summary of the student work the feedback refers to"
    - field: "student_level"
      type: "string"
      description: "Age/year group and ability profile"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: self-regulation level, language proficiency, sensitivity factors"
    - field: "rubric"
      type: "string"
      description: "From context engine: the rubric or success criteria used for this task"
output_schema:
  type: "object"
  fields:
    - field: "analysis"
      type: "object"
      description: "Diagnosis of feedback level, specificity, and actionability using Hattie & Timperley's model"
    - field: "rewritten_feedback"
      type: "string"
      description: "Improved version addressing identified weaknesses"
    - field: "improvement_rationale"
      type: "string"
      description: "What was changed and why, referencing evidence"
chains_well_with:
  - "gap-analysis-from-student-work"
  - "criterion-referenced-rubric-generator"
  - "self-regulation-scaffold-generator"
  - "metacognitive-prompt-library"
  - "kud-knowledge-type-mapper"
teacher_time: "3 minutes"
tags: ["feedback", "formative-assessment", "metacognition", "writing", "assessment"]
---

# Feedback Quality Analyser & Rewriter

## What This Skill Does

Takes a piece of teacher or peer feedback, analyses it against Hattie & Timperley's (2007) four-level feedback model, and rewrites it to improve its level, specificity, and actionability. The analysis identifies whether the feedback operates at the task, process, self-regulation, or self level, and evaluates whether it tells the student where they are, where they're going, and how to get there. AI is specifically valuable here because most teacher feedback — even from experienced teachers — defaults to either vague praise ("Good effort!"), vague criticism ("Needs more detail"), or self-level feedback ("You're a great writer") that research shows has zero or negative effect on learning. Rewriting feedback to target process and self-regulation requires explicit knowledge of the feedback research that most teachers have never encountered.

## Evidence Foundation

Hattie & Timperley (2007) conducted a comprehensive meta-analysis finding that feedback has an average effect size of 0.73 — one of the highest in education research — but with enormous variability. Effective feedback answers three questions: Where am I going? (feed up), How am I going? (feed back), Where to next? (feed forward). They identified four feedback levels: task (correctness), process (strategies used), self-regulation (student's monitoring and control), and self (personal praise or criticism). Task-level feedback improves immediate performance; process-level feedback improves strategy use; self-regulation feedback builds independence. Self-level feedback ("You're so clever" / "Disappointing work") has no positive effect and can undermine learning by directing attention to ego rather than task. Kluger & DeNisi (1996) found that one-third of feedback interventions actually decreased performance — typically when feedback threatened self-esteem or directed attention away from the task. Wisniewski et al. (2020) updated the meta-analysis and confirmed that feedback containing information (specific, task-referenced) is significantly more effective than feedback containing only judgments (grades, praise, criticism). Shute (2008) identified that effective formative feedback is specific, timely, non-threatening, and focused on the gap between current and desired performance.

## Input Schema

The teacher must provide:
- **Feedback text:** The existing feedback to analyse. *e.g. "Good work! You clearly tried hard on this. Next time, add more detail to your analysis." / "7/10. Some good points but your conclusion is weak."*
- **Task context:** What the student was doing and what the learning objective was. *e.g. "Year 10 History essay on causes of WWI. Learning objective: construct a causal argument using evidence."*

Optional (injected by context engine if available):
- **Student work summary:** Brief description of the actual student work
- **Student level:** Year group and ability profile
- **Student profiles:** Self-regulation level, language proficiency, emotional factors
- **Rubric:** The success criteria or rubric used for this task

## Prompt

```
You are an expert in educational feedback research, specialising in Hattie & Timperley's (2007) feedback model and Shute's (2008) formative feedback principles. You have deep knowledge of the distinction between feedback levels (task, process, self-regulation, self) and understand why feedback specificity and actionability determine its impact on learning.

Your task is to analyse and rewrite the following feedback:

**Feedback text:** "{{feedback_text}}"
**Task context:** {{task_context}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student work summary:** {{student_work_summary}} — if provided, use the details of the actual work to make the rewritten feedback more specific. If not provided, base your analysis and rewrite on what can be inferred from the feedback text and task context.
**Student level:** {{student_level}} — if provided, calibrate language and expectations accordingly. If not provided, infer from the task context.
**Rubric/Success criteria:** {{rubric}} — if provided, reference specific criteria in the rewritten feedback. If not provided, reference the learning objective from the task context.
**Student profiles:** {{student_profiles}} — if provided, consider self-regulation level when pitching feedback (high self-regulation: more self-monitoring prompts; low self-regulation: more specific task and process guidance). If not provided, pitch feedback at a general level.

Analyse the feedback using these evidence-based criteria:

1. **Feedback level diagnosis (Hattie & Timperley, 2007):**
   - **Task level:** Does it tell the student what is correct or incorrect about their specific work? (Useful but limited — doesn't help them improve next time.)
   - **Process level:** Does it address the strategies, skills, or processes the student used? (More powerful — transfers to future tasks.)
   - **Self-regulation level:** Does it prompt the student to monitor, evaluate, or adjust their own learning? (Most powerful for building independence.)
   - **Self level:** Does it comment on the student as a person rather than on the work? (No learning benefit. Remove or redirect.)

2. **The three feedback questions (Hattie & Timperley, 2007):**
   - **Feed up (Where am I going?):** Does the feedback reference the learning goal or success criteria?
   - **Feed back (How am I going?):** Does the feedback tell the student specifically what they did well or poorly *in relation to the goal*?
   - **Feed forward (Where to next?):** Does the feedback give a specific, actionable next step the student can take?

3. **Specificity check (Shute, 2008):** Is the feedback specific enough that the student knows exactly what to do differently? "Add more detail" is not specific. "In paragraph 3, you claim that militarism caused WWI but don't provide any evidence. Add a specific example of military build-up between 1900–1914 to support this claim" is specific.

4. **Threat check (Kluger & DeNisi, 1996):** Could this feedback be perceived as threatening to self-esteem, particularly for a struggling learner? If so, reframe to focus on the work, not the person.

5. **Actionability check:** Can the student act on this feedback independently? If the feedback requires knowledge or skills the student doesn't have, it's not actionable — it needs to be accompanied by instruction or a resource.

Return your output in this exact format:

## Feedback Analysis

### Original Feedback
[Reproduce the original feedback]

### Level Analysis
| Feedback Level | Present? | Examples from the text |
|---------------|----------|----------------------|
| Task | Yes/No | [Quote specific phrases] |
| Process | Yes/No | [Quote specific phrases] |
| Self-regulation | Yes/No | [Quote specific phrases] |
| Self | Yes/No | [Quote specific phrases] |

**Dominant level:** [Which level dominates and whether that's appropriate]

### Three Questions Check
- **Feed up (Where am I going?):** [Does the feedback reference the goal? Yes/No + detail]
- **Feed back (How am I going?):** [Does it say what was done well/poorly? Yes/No + detail]
- **Feed forward (Where to next?):** [Does it give a specific next step? Yes/No + detail]

### Specificity Rating
[Low / Medium / High] — [Explanation]

### Key Problems
[Numbered list of specific issues with the feedback]

### Rewritten Feedback
[The improved version — same approximate length, dramatically improved quality]

### What Changed and Why
[Bullet list explaining each change with reference to the research]

**Self-check before returning output:** Verify that (a) the rewritten feedback addresses all three feedback questions (feed up, feed back, feed forward), (b) it operates at process or self-regulation level, not just task level, (c) it is specific enough that the student knows exactly what to do, (d) it does not contain self-level comments disguised as encouragement, and (e) it is written in language the student can understand at their level.
```

## Example Output

**Scenario:** *Feedback text: "Good effort, Priya! Some really nice points in here. You need to work on your analysis — try to go deeper next time. Your writing style is lovely. 6/10." / Task context: "Year 10 English Literature essay analysing how Shakespeare presents Lady Macbeth's ambition in Act 1. Learning objective: analyse language and structure to explore how a character is presented."*

---

## Feedback Analysis

### Original Feedback
"Good effort, Priya! Some really nice points in here. You need to work on your analysis — try to go deeper next time. Your writing style is lovely. 6/10."

### Level Analysis
| Feedback Level | Present? | Examples from the text |
|---------------|----------|----------------------|
| Task | Partial | "6/10" provides a score but no information about what was correct or incorrect |
| Process | No | No reference to the strategies, methods, or analytical processes Priya used |
| Self-regulation | No | No prompts for Priya to monitor or evaluate her own work |
| Self | Yes | "Good effort, Priya!" / "Your writing style is lovely" — both address Priya as a person, not her work |

**Dominant level:** Self-level feedback dominates. The two substantive comments ("Good effort" and "Your writing style is lovely") are about Priya, not about her analysis of Lady Macbeth. The only task-level element is the score (6/10), which tells Priya her work is "medium" but not why or how to improve. Self-level feedback has no positive effect on learning (Hattie & Timperley, 2007) and the score without explanation is a judgment, not information (Wisniewski et al., 2020).

### Three Questions Check
- **Feed up (Where am I going?):** No. The feedback does not reference the learning objective (analysing how Shakespeare presents Lady Macbeth's ambition through language and structure). Priya doesn't know what she was aiming for.
- **Feed back (How am I going?):** Barely. "Some really nice points" is vague — which points? What made them nice? "You need to work on your analysis" identifies a gap but not specifically.
- **Feed forward (Where to next?):** No. "Try to go deeper next time" is not actionable. Priya has no way of knowing what "deeper" means, what "deeper analysis" looks like, or how to do it.

### Specificity Rating
**Low** — The feedback contains no specific references to Priya's actual work. The same comment ("good effort, work on your analysis, go deeper") could be written on any student's essay on any topic. This is a strong indicator of low-quality feedback (Shute, 2008).

### Key Problems

1. **"Good effort" is self-level feedback.** It addresses Priya's effort (a personal quality), not her work. It provides no information about what was good or why. Kluger & DeNisi (1996) found that self-directed feedback shifts attention from the task to the ego.

2. **"Some really nice points" is unspecified task-level feedback.** Which points? What made them effective? Without specificity, Priya can't replicate what she did well.

3. **"You need to work on your analysis — try to go deeper" is vague feed-forward.** This is the most common feedback failure in secondary education. "Go deeper" means nothing to a Year 10 student who doesn't know what deep analysis looks like. It requires Priya to already have the skill the feedback is telling her to develop.

4. **"Your writing style is lovely" is self-level feedback with a gender dimension.** It compliments Priya as a writer rather than identifying specific effective writing choices. Research on gendered feedback patterns shows that girls more frequently receive praise for style/presentation while boys receive more substantive content feedback.

5. **"6/10" is a judgment, not feedback.** Butler (1988) found that when comments are accompanied by grades, students attend to the grade and ignore the comments entirely. The score undermines any formative value the comments might have had.

### Rewritten Feedback

Priya, this essay shows you can identify relevant quotations — you chose strong evidence from Act 1, Scene 5, particularly Lady Macbeth's "unsex me here" speech.

Your quotation choices are effective, but your analysis stays at the surface. For example, you write: "This shows Lady Macbeth is ambitious." That's the *what* — but the learning objective asks you to analyse *how* Shakespeare presents her ambition through language. Look at your "unsex me here" quotation again. Ask yourself: why does Shakespeare use the word "unsex"? What does it tell us about how ambition and gender are connected in this speech? What is the effect on the audience of hearing a woman ask to be stripped of femininity in order to be powerful? That's the depth of analysis this essay needs.

**Specific next step:** Choose your two strongest quotations from this essay. For each one, write three sentences: (1) what the quotation shows about Lady Macbeth, (2) why Shakespeare chose that specific word or image, and (3) what effect it creates for the audience. Bring these to our next lesson so we can look at them together.

### What Changed and Why

- **Removed "Good effort" and "lovely writing style"** — self-level feedback that shifts attention to Priya as a person rather than her work. Replaced with specific task-level praise that identifies what she did well: choosing relevant quotations from Act 1, Scene 5 (Hattie & Timperley, 2007 — task-level feedback about what was correct).

- **Replaced "go deeper" with a specific model of what "deeper" means** — the rewrite shows Priya exactly what analytical depth looks like by walking through one of her own quotations and demonstrating the questions she should ask (why this word? what effect?). This is process-level feedback: it addresses the *strategy* of analysis, not just the outcome (Hattie & Timperley, 2007).

- **Added a specific, actionable next step** — "Choose two quotations, write three sentences each using this structure" gives Priya something concrete to do. She can act on this independently. This is genuine feed-forward (Shute, 2008).

- **Removed the grade** — Butler (1988) demonstrated that comment-only feedback produces more learning than comment-plus-grade, because the grade draws attention away from the formative information. If a grade must be recorded, provide it separately or later.

- **Referenced the learning objective** — the rewrite explicitly connects the feedback to the task goal ("the learning objective asks you to analyse *how*"), giving Priya a clear reference point for improvement (feed up).

---

## Known Limitations

1. **The rewrite requires knowing the actual student work.** Without seeing Priya's essay, the rewritten feedback uses the quotation mentioned in the original and makes reasonable inferences about what she wrote. If the student work summary is provided, the rewrite will be more precise. Teachers should treat the rewrite as a model to adapt, not a final product.

2. **Feedback effectiveness depends on the relationship between teacher and student.** Wisniewski et al. (2020) found that the same feedback phrasing can be received differently depending on trust and the classroom culture around feedback. The rewrite assumes a supportive classroom environment. In a context where a student has feedback anxiety, the opening may need further softening — though the research is clear that reducing specificity to protect feelings reduces learning.

3. **This skill analyses individual feedback quality but cannot address systemic feedback problems.** If a teacher's marking load means they have 3 minutes per essay for 30 students, even excellent feedback knowledge won't help. Systemic solutions (reducing marking volume, using whole-class feedback, selective detailed marking) are outside this skill's scope but are often the real bottleneck.

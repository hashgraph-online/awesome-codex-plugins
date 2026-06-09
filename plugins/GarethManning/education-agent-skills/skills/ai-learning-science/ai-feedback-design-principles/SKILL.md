---
# AGENT SKILLS STANDARD FIELDS (v2)
name: ai-feedback-design-principles
description: "Audit and redesign AI-generated feedback for pedagogical quality, timing, and learning impact. Use when building or reviewing automated feedback in digital learning tools."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-learning-science/ai-feedback-design-principles"
skill_name: "AI Feedback Design Principles"
domain: "ai-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Shute (2008) — Focus on formative feedback (comprehensive review)"
  - "Narciss (2008) — Feedback strategies for interactive learning tasks (informative tutoring feedback model)"
  - "Hattie & Timperley (2007) — The power of feedback (meta-analysis, effect size 0.73)"
  - "Dai et al. (2023) — Can large language models provide useful feedback on research papers? A large-scale empirical analysis"
  - "Kluger & DeNisi (1996) — The effects of feedback interventions on performance: A historical review and a meta-analysis"
input_schema:
  required:
    - field: "feedback_scenario"
      type: "string"
      description: "The specific context in which AI will deliver feedback — what the student has done and what kind of feedback is needed"
    - field: "current_feedback_design"
      type: "string"
      description: "The current or proposed AI feedback approach — what the system currently says or plans to say in response to student work"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and proficiency level"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "feedback_goals"
      type: "string"
      description: "What the feedback should achieve — error correction, motivation, deeper thinking, self-regulation, or something else"
    - field: "system_constraints"
      type: "string"
      description: "Technical or practical constraints on the feedback — character limits, timing requirements, or format restrictions"
output_schema:
  type: "object"
  fields:
    - field: "feedback_evaluation"
      type: "object"
      description: "Analysis of the current feedback design against research criteria — what works and what doesn't"
    - field: "improved_feedback"
      type: "object"
      description: "A redesigned version of the feedback that addresses identified weaknesses"
    - field: "feedback_type_analysis"
      type: "object"
      description: "Classification of the feedback by type (verification, elaboration, strategic) with recommendations for the optimal mix"
    - field: "implementation_guidance"
      type: "object"
      description: "Practical advice for deploying the improved feedback in the target system"
chains_well_with:
  - "adaptive-hint-sequence-designer"
  - "formative-assessment-loop-designer"
  - "intelligent-tutoring-dialogue-designer"
  - "self-explanation-prompt-designer"
  - "technological-pedagogical-content-knowledge-developer"
teacher_time: "4 minutes"
tags: ["feedback", "AI-feedback", "formative", "Shute", "Narciss", "Hattie", "LLM", "automated-feedback"]
---

# AI Feedback Design Principles

## What This Skill Does

Evaluates a proposed AI feedback design against research criteria for effective automated feedback and suggests specific improvements. This skill takes a feedback scenario (what the student did) and the current or proposed AI response (what the system says), then analyses the feedback against principles from Shute (2008), Narciss (2008), Hattie & Timperley (2007), and emerging LLM feedback research (Dai et al., 2023). The output includes a diagnosis of what's working and what isn't, a redesigned version of the feedback, and practical implementation guidance. The core challenge is that most AI feedback falls into one of two failure modes: it's either too vague to be actionable ("Good effort! Try to improve your argument.") or too specific and does the thinking for the student ("Your thesis should be: Climate change is the defining challenge of our generation because…"). Effective feedback lives in the narrow space between these extremes — specific enough that the student knows what to do, but not so specific that it bypasses the cognitive work that produces learning. AI is specifically valuable here because it can generate feedback at scale, but this makes the design principles even more critical: bad feedback at scale is worse than no feedback at all.

## Evidence Foundation

Hattie & Timperley (2007) conducted a meta-analysis finding that feedback has an average effect size of 0.73 — making it one of the most powerful influences on learning. However, they found enormous variation: some feedback interventions produced large positive effects while others had zero or even NEGATIVE effects. The critical variable was not whether feedback was given, but WHAT KIND of feedback was given. They proposed a model with four levels: task feedback (is the answer correct?), process feedback (what strategies can improve the work?), self-regulation feedback (how can you monitor your own learning?), and self feedback (you're a great student!). Task and process feedback were most effective; self feedback ("Good job!") was least effective and sometimes harmful because it directs attention to the self rather than the task. Shute (2008) reviewed formative feedback research and identified key principles: effective feedback is specific, timely, non-threatening, and focused on the task rather than the learner. She distinguished between verification feedback (correct/incorrect), elaborated feedback (why it's correct/incorrect and what to do next), and various combinations. She found that elaborated feedback generally outperforms simple verification, BUT that overly detailed feedback can overwhelm novice learners — creating a feedback paradox where more information sometimes produces less learning. Narciss (2008) developed the Informative Tutoring Feedback (ITF) model, which specifies that effective feedback should include: knowledge of result (correct or not), knowledge of the correct response (if wrong), and elaboration on the error (why it's wrong and what misconception it reveals). Critically, Narciss found that the optimal feedback depends on the error type: conceptual errors benefit from elaborated feedback, while careless slips benefit from simple verification. Kluger & DeNisi (1996) found in their meta-analysis that feedback that directs attention to the self (rather than the task) can DECREASE performance — a finding with direct implications for AI systems that generate encouraging but empty praise. Dai et al. (2023) evaluated LLM-generated feedback and found that while LLMs can produce fluent, well-structured feedback, they tend toward a specific pattern: excessive positivity, vague suggestions, and a reluctance to identify specific errors — precisely the pattern that research identifies as least effective.

## Input Schema

The teacher must provide:
- **Feedback scenario:** What the student did. *e.g. "Year 9 student submitted a persuasive essay arguing that school uniforms should be abolished. The argument is passionate but relies entirely on personal anecdotes — no evidence, no counterargument addressed, weak logical structure" / "Year 7 student solved 3x + 5 = 20 and got x = 7 (incorrect — should be x = 5)" / "A-level student wrote a lab report with correct data but a conclusion that doesn't follow from the results"*
- **Current feedback design:** What the AI currently says or plans to say. *e.g. "Great essay! You clearly feel strongly about this topic. To improve, try adding some evidence and considering the other side of the argument" / "Incorrect. The answer is x = 5. Try again" / "Your conclusion needs work. Think about what your data actually shows"*

Optional (injected by context engine if available):
- **Student level:** Year group and proficiency
- **Subject area:** The curriculum subject
- **Feedback goals:** What the feedback should achieve
- **System constraints:** Technical or practical limitations

## Prompt

```
You are an expert in the science of feedback in learning, with deep knowledge of Hattie & Timperley's (2007) feedback model (task, process, self-regulation, self levels), Shute's (2008) formative feedback principles, Narciss's (2008) Informative Tutoring Feedback model, Kluger & DeNisi's (1996) meta-analysis on feedback interventions, and emerging research on LLM-generated feedback quality (Dai et al., 2023). You understand that feedback is one of the most powerful influences on learning — and one of the most dangerous when poorly designed. You know that AI systems tend toward a specific failure mode: generating feedback that is positive, fluent, well-structured, and educationally useless.

CRITICAL PRINCIPLES:
- **Feedback must be SPECIFIC and ACTIONABLE.** "Good effort" is not feedback. "Your introduction states a position but doesn't preview your three supporting arguments — add a sentence that maps out your essay structure" IS feedback. If a student cannot read the feedback and know EXACTLY what to do next, it has failed.
- **Distinguish verification, elaboration, and strategic feedback.** Verification: "This is incorrect." Elaboration: "This is incorrect because you subtracted 5 from the left side but not the right." Strategic: "When you get stuck on equations, always check: did I do the same operation to both sides?" Different errors need different types. A conceptual error needs elaboration. A careless slip needs verification. A recurring pattern needs strategic feedback.
- **Avoid the positivity trap.** AI systems default to excessive positivity. "Great work!" before pointing out fundamental errors sends a contradictory signal and dilutes the corrective message. Positive feedback is appropriate ONLY when genuinely earned AND directed at specific features ("Your use of statistical evidence in paragraph 2 is effective because it directly supports your claim"). Generic praise is worse than no praise at all (Kluger & DeNisi, 1996).
- **Don't do the student's thinking.** Feedback that tells the student exactly what to write, what the answer is, or how to fix their work is not feedback — it's answer-giving. The goal is to close the gap between current and desired performance by showing the student WHERE the gap is and giving them enough information to close it themselves.
- **Match feedback complexity to student level.** Novice learners benefit from simple, clear feedback focused on one or two specific issues. Advanced learners benefit from more complex feedback that addresses multiple dimensions. Overloading novices with comprehensive feedback produces cognitive overload, not learning (Shute, 2008).

Your task is to evaluate and improve this feedback design:

**Feedback scenario:** {{feedback_scenario}}
**Current feedback design:** {{current_feedback_design}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, infer from the scenario.
**Subject area:** {{subject_area}} — if not provided, infer from the scenario.
**Feedback goals:** {{feedback_goals}} — if not provided, assume the goal is to help the student improve their work while preserving their ownership of the thinking.
**System constraints:** {{system_constraints}} — if not provided, assume no significant constraints.

Return your output in this exact format:

## Feedback Evaluation: [Brief Scenario Description]

**Scenario:** [What the student did]
**Current feedback:** [What the AI currently says]
**Verdict:** [One-sentence summary — is this feedback likely to improve learning, have no effect, or actively harm it?]

### Diagnosis

[Analyse the current feedback against each principle. What works? What doesn't? Be specific — quote the problematic parts of the feedback and explain WHY they are problematic, citing the relevant research.]

### Feedback Type Analysis

| Feedback Component | Type | Effectiveness | Issue |
|---|---|---|---|
| [Quote from current feedback] | [Verification / Elaboration / Strategic / Self] | [Effective / Ineffective / Harmful] | [Why] |

### Improved Feedback Design

[The redesigned feedback. Show the exact text the AI should present to the student. Include specific, actionable guidance that addresses the identified weaknesses without doing the student's thinking for them.]

**Redesigned feedback:**

> [The exact feedback text]

### Design Rationale

[Explain why the improved version is better — what principles it follows and what specific changes were made.]

### Implementation Notes

[Practical guidance for deploying this feedback pattern — when it should trigger, how to handle edge cases, and what to watch for.]

**Self-check before returning output:** Verify that (a) the improved feedback is specific and actionable, (b) it doesn't do the student's thinking, (c) it avoids empty praise, (d) it uses the right type of feedback for the error type, and (e) it's appropriate for the student's level.
```

## Example Output

**Scenario:** *Feedback scenario: "Year 9 student submitted a persuasive essay arguing that school uniforms should be abolished. The argument is passionate but relies entirely on personal anecdotes — no evidence, no counterargument addressed, weak logical structure. The essay is about 400 words, has an introduction, three body paragraphs, and a conclusion." / Current feedback design: "Great essay! You clearly feel strongly about this topic and your writing voice is engaging. To improve, try adding some evidence to support your points and consider addressing the opposing viewpoint. Your conclusion could be stronger — try restating your main argument. Overall, a solid effort — keep it up! 7/10" / Student level: "Year 9, target grade 6 (UK GCSE equivalent)" / Subject area: "English Language — persuasive writing"*

---

## Feedback Evaluation: Year 9 Persuasive Essay — School Uniforms

**Scenario:** Year 9 student wrote a persuasive essay relying on personal anecdotes with no evidence, no counterargument, and weak structure.
**Current feedback:** "Great essay! You clearly feel strongly… try adding some evidence… consider addressing the opposing viewpoint… a solid effort — keep it up! 7/10"
**Verdict:** This feedback is unlikely to produce improvement. It is vague, excessively positive, and tells the student they're doing well when their essay has fundamental structural problems.

### Diagnosis

**Problem 1: The positivity trap.** The feedback opens with "Great essay!" — but the essay has fundamental weaknesses (no evidence, no counterargument, weak structure). This sends a contradictory signal: you're telling the student the essay is great while simultaneously listing everything that's wrong with it. Kluger & DeNisi (1996) found that feedback directing attention to the self ("you clearly feel strongly") rather than the task reduces learning. The student's takeaway: "I got 7/10 and the teacher liked my voice. I just need to tweak a few things."

**Problem 2: Vague improvement suggestions.** "Try adding some evidence" — what kind of evidence? Where in the essay? How much? "Consider addressing the opposing viewpoint" — which opposing viewpoint? Where in the essay should it go? How should it be structured? Shute (2008) found that feedback must be specific enough that the student knows exactly what to do. These suggestions are too vague to be actionable.

**Problem 3: No diagnosis of the actual problem.** The essay's fundamental issue is that the student doesn't understand the difference between assertion and argument. Every paragraph makes claims supported only by personal experience. The feedback doesn't name this problem — it treats the symptoms (no evidence, no counterargument) without identifying the underlying cause (the student equates strong feeling with strong argument).

**Problem 4: The score undermines the feedback.** 7/10 signals "this is good." If the essay has no evidence and no counterargument, it has not met the basic criteria for persuasive writing. The score and the feedback are in conflict. The student will anchor on the score and dismiss the suggestions.

### Feedback Type Analysis

| Feedback Component | Type | Effectiveness | Issue |
|---|---|---|---|
| "Great essay!" | Self | Harmful | Empty praise directing attention to self not task |
| "You clearly feel strongly" | Self | Ineffective | Describes the student, not the work |
| "Your writing voice is engaging" | Task | Mildly effective | Specific enough to be useful, but buried in generic praise |
| "Try adding some evidence" | Strategic | Ineffective | Too vague — what evidence, where, how? |
| "Consider addressing the opposing viewpoint" | Strategic | Ineffective | Too vague — which viewpoint, where in the essay? |
| "Your conclusion could be stronger" | Task | Ineffective | "Stronger" is meaningless without specifics |
| "A solid effort — keep it up!" | Self | Harmful | False reassurance when major revisions needed |
| "7/10" | Verification | Harmful | Score contradicts the need for fundamental revision |

### Improved Feedback Design

**Redesigned feedback:**

> **What's working:** Your writing voice is confident and direct — "I shouldn't have to wear someone else's idea of who I am every single day" is a strong, memorable line. Hold onto that voice.
>
> **The main issue — assertion vs. argument:** Right now, every paragraph makes a claim and supports it with your personal experience. That's assertion, not argument. Persuasive writing needs EVIDENCE — facts, statistics, expert opinions, or real examples that someone who disagrees with you would have to take seriously. Your reader is thinking: "That's how YOU feel, but why should I care?"
>
> **One specific fix to try first:** Pick your strongest paragraph (I'd suggest paragraph 2 about comfort). Find ONE piece of evidence that supports your point — a study about student concentration, a school that removed uniforms and measured the effect, or a quote from an education expert. Add it. Then look at what it does to the paragraph. That's the difference between assertion and argument.
>
> **Next step after that:** Choose the strongest argument AGAINST your position (probably cost — uniforms save families money). Write a paragraph that acknowledges this argument and then explains why your position is still stronger. This is called a counterargument, and it's the single most persuasive move in argumentative writing — it shows you've considered the other side and still have a stronger case.
>
> **Don't revise yet.** First, reread your essay and put a star next to every sentence that is supported by evidence (not personal experience). Count the stars. That count tells you how much work is needed.

### Design Rationale

The redesigned feedback makes five key changes:

1. **Specific positive feedback first, directed at the task.** "Your writing voice is confident and direct" with a quoted example — this is task-level feedback on a genuine strength, not generic self-level praise. It tells the student exactly what to keep doing.

2. **Names the underlying problem.** "Assertion vs. argument" gives the student a conceptual framework for understanding what's wrong. This is elaborated feedback (Narciss, 2008) — it doesn't just say "add evidence" but explains WHY evidence is needed and what the essay currently lacks.

3. **One specific, manageable action.** Instead of a list of vague improvements, the feedback gives ONE concrete task: find one piece of evidence for one paragraph. This follows Shute's (2008) principle of matching feedback complexity to learner level — a Year 9 student targeting grade 6 needs focused, achievable steps, not a comprehensive critique.

4. **The counterargument instruction is scaffolded.** It doesn't just say "address the opposing viewpoint" — it tells the student which opposing argument to choose and explains the strategic reason for including it. This is process-level feedback (Hattie & Timperley, 2007).

5. **The diagnostic task replaces the score.** "Count the stars" is a self-regulation prompt that helps the student see the problem for themselves, rather than being told. This develops metacognitive awareness — a higher-order feedback function that builds independence.

### Implementation Notes

- **Do not open with a score.** If a score is required by the system, place it at the end, after the actionable feedback. Better yet, withhold the score until after revision.
- **Limit feedback to 2-3 actionable points.** This example addresses two issues (evidence, counterargument) plus one metacognitive prompt. That's the maximum for a Year 9 student. More points produce cognitive overload and paralysis.
- **Watch for the LLM positivity pattern.** If the AI is generating feedback, audit it for the "Great job! But…" pattern (Dai et al., 2023). Instruct the model to lead with specific, earned praise or to lead with the diagnostic — not with generic enthusiasm.
- **Re-evaluate after revision.** The feedback above is designed to produce a specific revision (adding evidence to one paragraph, adding a counterargument paragraph). After revision, the feedback should address different issues — probably structure and logical flow. Don't repeat the same feedback if the student has acted on it.

---

## Known Limitations

1. **This skill evaluates feedback DESIGN, not feedback DELIVERY.** The same feedback text can be effective or harmful depending on timing, student emotional state, and the relationship between student and system. A student who has just failed three assignments in a row needs a different emotional register than a confident student who made a careless error. This skill addresses content and structure, not affect and timing.

2. **The LLM feedback evidence base is still emerging.** Dai et al. (2023) is one of the first large-scale studies of LLM feedback quality, and the field is developing rapidly. The principles from Shute (2008), Narciss (2008), and Hattie & Timperley (2007) are well-established for human feedback — their application to AI-generated feedback is theoretically sound but not yet comprehensively validated.

3. **Cultural context affects feedback norms.** The direct, task-focused feedback style recommended here reflects Western educational research norms. In some cultural contexts, direct criticism (even when constructive) may be received differently. Narciss's (2008) model was developed primarily in European and North American contexts.

4. **Feedback interacts with student self-efficacy in complex ways.** Kluger & DeNisi (1996) found that feedback can decrease performance when it threatens self-concept. For students with very low self-efficacy, the "no empty praise" principle needs to be balanced against the risk of further damaging motivation. This skill does not model the individual student's motivational state.

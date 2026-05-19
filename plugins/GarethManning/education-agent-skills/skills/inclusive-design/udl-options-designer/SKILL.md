---
# AGENT SKILLS STANDARD FIELDS (v2)
name: udl-options-designer
description: "Generates multiple means of engagement, representation, and action/expression for a given learning goal. Produces specific, practical alternatives — not generic options — and recommends the highest-impact single change."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "inclusive-design/udl-options-designer"
skill_name: "UDL Options Designer"
domain: "inclusive-design"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Rose & Meyer (2002) — Teaching Every Student in the Digital Age: Universal Design for Learning"
  - "CAST (2018) — Universal Design for Learning Guidelines version 2.2"
  - "Meyer, Rose & Gordon (2014) — Universal Design for Learning: Theory and Practice"
  - "Ok, Rao, Bryant & McDougall (2017) — Universal Design for Learning in Pre-K to Grade 12 Classrooms: A Systematic Review of Research"
  - "Rao & Meo (2016) — Using Universal Design for Learning to Design Standards-Based Lessons"
  - "Edyburn (2010) — Would You Recognize Universal Design for Learning if You Saw It?"
input_schema:
  required:
    - field: "learning_goal"
      type: "string"
      description: "The specific learning objective or target. Example: Students will explain how photosynthesis converts light energy into chemical energy."
    - field: "current_approach"
      type: "string"
      description: "How the teacher currently plans to teach this. Example: Read textbook section, watch video, complete worksheet."
  optional:
    - field: "learner_context"
      type: "string"
      description: "Known student variability — age, language backgrounds, learning profiles, known challenges"
    - field: "available_resources"
      type: "string"
      description: "Technology, materials, spaces available. Example: Chromebooks 1:1, no printer, shared classroom."
output_schema:
  type: "object"
  fields:
    - field: "engagement_options"
      type: "array"
      description: "2-3 specific alternatives for Multiple Means of Engagement, with rationale for which learners each supports"
    - field: "representation_options"
      type: "array"
      description: "2-3 specific alternatives for Multiple Means of Representation, with rationale"
    - field: "action_expression_options"
      type: "array"
      description: "2-3 specific alternatives for Multiple Means of Action and Expression, with rationale"
    - field: "minimum_viable_udl"
      type: "string"
      description: "The single highest-impact change if the teacher can only do one thing differently"
    - field: "implementation_notes"
      type: "array"
      description: "Practical notes on how to offer options without overwhelming students"
chains_well_with:
  - "inclusive-design/udl-lesson-auditor"
  - "inclusive-design/udl-barrier-anticipator"
  - "curriculum-assessment/differentiation-adapter"
  - "curriculum-assessment/formative-assessment-technique-selector"
  - "self-regulated-learning/self-regulation-scaffold-generator"
teacher_time: "5-10 minutes"
tags: ["UDL", "inclusive-design", "options", "multiple-means", "access", "differentiation", "CAST"]
---

# UDL Options Designer

## What This Skill Does

Given a learning goal and current teaching approach, generates genuine alternatives across Universal Design for Learning's three principles: Multiple Means of Engagement, Multiple Means of Representation, and Multiple Means of Action and Expression. The alternatives maintain the same learning goal while varying the path. This is the design-thinking skill of UDL — not a checklist of options added after the fact, but genuine consideration of how different learners might reach the same understanding by different routes.

The key distinction is specificity. This skill does not generate generic options ("provide visual supports"). It generates specific ones: "Create a labelled diagram of the photosynthesis process with colour-coded inputs and outputs, so students can trace the energy conversion visually before or alongside reading the text." Each alternative notes which learners it particularly supports and connects the rationale to learning science, not just UDL labels. The output also includes a minimum viable UDL recommendation — the one highest-impact change if the teacher can only do one thing.

## Evidence Foundation

Universal Design for Learning is a design framework developed by CAST, grounded in three principles derived from neuroscience, cognitive science, and educational research (Rose & Meyer, 2002; CAST, 2018). The framework holds that learner variability is not the exception but the norm, and that instructional design should anticipate variability rather than respond to it after learning has failed. Evidence for UDL as a complete framework is moderate: well-established in practice and grounded in related research, but implementation evidence is mostly quasi-experimental (Ok, Rao, Bryant & McDougall, 2017).

The individual strategies within UDL draw on stronger evidence bases. Offering multiple representations builds on multimedia learning research showing that information encoded in multiple modalities produces deeper understanding than single-mode presentation (Mayer, 2009). Offering choice in how students demonstrate learning connects to self-determination theory, which consistently shows that perceived autonomy supports intrinsic motivation (Ryan & Deci, 2000). Varied engagement strategies draw on research into interest, attention, and executive function variability. UDL is a design framework that helps teachers anticipate and reduce access barriers — it is not a validated intervention, and it does not guarantee that all learners will access all content equally.

## Prompt

```text
You are a UDL specialist and learning designer. Your task is to generate specific, practical learning options across Universal Design for Learning's three principles for the learning goal below. You are NOT generating a generic UDL checklist. You are generating genuine alternatives that maintain the same learning goal while varying the path — each option must be specific enough to implement immediately.

Inputs:
Learning goal: {{learning_goal}}
Current approach: {{current_approach}}
Learner context: {{learner_context}}
Available resources: {{available_resources}}

For EACH UDL principle, generate 2-3 genuine alternatives. For each alternative:
- Name the specific option (not a category — a concrete activity, format, or tool)
- Note which learners it particularly supports and WHY (connect to learning science where you can: cognitive load, dual coding, self-determination, executive function, language processing — not just "UDL labels")
- Note any resource or preparation requirements

Rules for generating options:
1. SPECIFICITY: "Use a graphic organiser" is not specific enough. "Provide a partially completed T-chart with the inputs and outputs of photosynthesis already labelled, so students complete the energy conversion relationships" is specific.
2. PRACTICALITY: Options must be achievable in a real classroom. If resources are constrained, work within them.
3. GOAL INTEGRITY: Every option must target the same learning goal. Options that inadvertently reduce cognitive demand or shift to a different goal should be flagged, not presented as equivalent.
4. RATIONALE: For each option, briefly explain WHY it supports particular learners — not because UDL says so, but because of how learning works for those learners.

UDL Principle 1: Multiple Means of Engagement (the WHY — recruiting interest, sustaining effort, supporting self-regulation)
Generate 2-3 specific engagement alternatives. Consider: How can the learning connect to different student interests or contexts? How can students have some agency in how they pursue the goal? What supports persistence for students with attention variability?

UDL Principle 2: Multiple Means of Representation (the WHAT — perception, language, comprehension)
Generate 2-3 specific representation alternatives. Consider: What information do students need to reach this goal, and how can it be presented in more than one modality? What vocabulary or symbols need explicit support? What background knowledge might be missing?

UDL Principle 3: Multiple Means of Action and Expression (the HOW — physical action, communication, executive function)
Generate 2-3 specific alternatives for how students demonstrate their understanding. Consider: What response formats maintain the cognitive demand of the goal while varying how students show their thinking? What executive function scaffolds help students organise their response?

After generating all options:
- Minimum viable UDL: Identify the single highest-impact change if the teacher can only do ONE thing differently. This should be the option most likely to reduce the most significant barrier for the most learners in this specific context.
- Implementation note: Not every lesson needs all options simultaneously. That is UDL-as-checkbox, not UDL-as-design-thinking. Suggest how to offer options without overwhelming students with choice — particularly for students with executive function challenges, for whom more options can reduce rather than increase access.

Self-check before returning output: Are all options specific enough to implement tomorrow? Do they all maintain the same learning goal? Am I connecting rationale to learning science, not just UDL category labels? Have I recommended a minimum viable UDL (not just a list)?

Return in this format:

## UDL Options: [Learning Goal]

**Current approach:** [brief]
**Learner context:** [brief or "not specified"]

### Multiple Means of Engagement
1. **[Option name]** — [Description, which learners, why]
2. **[Option name]** — [Description, which learners, why]
3. **[Option name — optional]** — [Description, which learners, why]

### Multiple Means of Representation
1. **[Option name]** — [Description, which learners, why]
2. **[Option name]** — [Description, which learners, why]
3. **[Option name — optional]** — [Description, which learners, why]

### Multiple Means of Action and Expression
1. **[Option name]** — [Description, which learners, why]
2. **[Option name]** — [Description, which learners, why]
3. **[Option name — optional]** — [Description, which learners, why]

### Minimum Viable UDL
[The single highest-impact change, with rationale]

### Implementation Notes
[How to offer options without overwhelming students; any practical cautions]
```

## Common Pitfalls

1. **Generic options instead of specific ones.** The output should be implementable without further interpretation. "Provide visual supports" requires another design decision before it becomes an action. "Create a labelled diagram with the vocabulary pre-filled and the connections left blank" is an action.
2. **Options that inadvertently lower cognitive demand.** Some alternatives feel accessible but actually reduce the rigour of the learning goal. Reading an article and watching a video are not equivalent paths to the same understanding — they have different cognitive demands and different relationships to the goal. Flag this rather than presenting all options as interchangeable.
3. **Offering too many options simultaneously.** More choice is not always more accessible, particularly for students with executive function challenges. The minimum viable UDL recommendation exists for this reason.
4. **Treating UDL options as permanent scaffolds rather than proactive design.** The goal of UDL is to design for variability from the start, not to create elaborate scaffolding systems. Options should be integrated into the instructional design, not bolted on.

## Known Limitations

1. **Generating options is not the same as knowing which options a specific group needs.** Teacher knowledge of their students is primary. The options generated here are informed by general learner variability and the described context — the teacher knows which ones will actually land for the students in their room.
2. **Options that look equivalent may not be.** Reading a text and watching a video are different cognitive tasks with different relationships to the learning goal. Some options may inadvertently shift the task's difficulty, language demand, or cognitive pathway. The skill flags obvious mismatches but cannot assess all possible interactions between option and goal.
3. **The skill cannot verify that suggested alternatives maintain equivalent rigour.** Some modifications that appear to support access may inadvertently reduce cognitive demand, changing what students are actually learning. Teacher review of each option against the intended goal is essential.
4. **Too many options can reduce access for some learners.** Students with executive function challenges, decision fatigue, or anxiety may find multiple simultaneous choices overwhelming. More choice is not always more inclusive — structured choice (choose one from column A) is often more accessible than open-ended choice.

## Verification Checklist

- [ ] All options are specific enough to implement without further design decisions.
- [ ] All options maintain the same learning goal — no inadvertent difficulty reduction.
- [ ] Each option includes rationale connected to learning science, not just UDL labels.
- [ ] A minimum viable UDL recommendation is included.
- [ ] Implementation notes address how to offer options without overwhelming choice.
- [ ] No claim that providing multiple options guarantees equal access for all learners.

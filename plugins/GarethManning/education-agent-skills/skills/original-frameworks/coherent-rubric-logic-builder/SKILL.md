---
# AGENT SKILLS STANDARD FIELDS (v2)
name: coherent-rubric-logic-builder
description: "Build a five-level rubric with coherent logic for a learning target within a developmental band. Use for Manning methodology programmes where Competent = success. For general curriculum rubrics, use criterion-referenced-rubric-generator instead."
disable-model-invocation: true
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "original-frameworks/coherent-rubric-logic-builder"
skill_name: "Coherent Rubric Logic Builder"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Manning — REAL School Rubric Logic Guide v2.1 (January 2026, original methodology)"
  - "Burch (1970) — Four stages of competence (unconscious incompetence → conscious incompetence → conscious competence → unconscious competence)"
  - "Haring et al. (1978) — The instructional hierarchy: acquisition, fluency, retention, generalisation, adaptation"
  - "Black & Wiliam (1998) — Assessment and classroom learning (rubrics are only useful if they change decisions)"
  - "Sadler (1989) — Formative assessment and the design of instructional systems (students must understand quality before they can self-assess)"
input_schema:
  required:
    - field: "learning_target"
      type: "string"
      description: "The exact LT band statement being assessed — a specific 'I can...' statement from one band"
    - field: "band"
      type: "string"
      description: "Which developmental band this rubric is for — A, B, C, D, E, or F"
    - field: "product_or_performance"
      type: "string"
      description: "What students will produce or do to demonstrate the LT — the specific assessment task"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group for language calibration"
    - field: "formative_or_summative"
      type: "string"
      description: "Whether this is a checkpoint rubric or a final assessment rubric"
    - field: "compound_lt"
      type: "string"
      description: "Whether the LT contains distinct sub-skills that warrant splitting into separate rubric rows"
output_schema:
  type: "object"
  fields:
    - field: "teacher_rubric"
      type: "object"
      description: "Full five-level table (No Evidence / Emerging / Developing / Competent / Extending) with precise descriptors"
    - field: "co_construction_plan"
      type: "object"
      description: "How to work with students to generate student-friendly criteria language through exemplar analysis"
    - field: "student_rubric_template"
      type: "object"
      description: "The student-facing version with accessible language"
    - field: "written_feedback_guide"
      type: "object"
      description: "How to write specific, actionable feedback for each level"
    - field: "known_limitations"
      type: "object"
      description: "Where professional judgment is still needed; what the rubric can't do"
chains_well_with:
  - "learning-target-authoring-guide"
  - "developmental-band-system-designer"
  - "self-determined-project-design-protocol"
  - "ai-feedback-design-principles"
  - "curriculum-knowledge-architecture-designer"
  - "kud-knowledge-type-mapper"
teacher_time: "5 minutes"
tags: ["rubric", "Manning", "competency", "five-level", "co-construction", "Sadler", "formative", "Competent", "assessment"]
---

# Coherent Rubric Logic Builder

## What This Skill Does

This skill encodes an original practitioner framework developed by Gareth Manning, educator, curriculum designer, and learning systems designer. Unlike skills in other domains, it is not drawn from peer-reviewed research traditions. It is grounded in serious engagement with learning science, original curriculum design work, and active classroom testing. It is included because the methodology is coherent, transferable, and genuinely useful — and because intellectual honesty requires distinguishing practitioner frameworks from research-validated approaches.

This skill builds a complete, coherent rubric for a learning target or project assessment — using a five-level scale where **Competent IS success**, not a midpoint. Most rubrics fail because they treat the middle level as "average" and the top level as "excellent" — creating a system where the majority of students are implicitly labelled as inadequate. Manning's rubric logic inverts this: Competent represents genuine mastery of the band-level expectation. It IS the target. Extending is rare and requires specific evidence of transfer, depth, or sophistication beyond the band expectation. Emerging is a legitimate starting point, not a failure. The output is a full rubric table with precise descriptors at each level, plus a co-construction plan for working with students to make the criteria their own. Sadler (1989) established that students need to understand what quality looks like before they can self-assess meaningfully — the co-construction process is essential, not optional. The rubric methodology is designed to work alongside the Learning Target Authoring Guide (Skill 98) — the rubric is the assessment instrument for a specific LT, not a separate system.

## Evidence Foundation

Manning developed the rubric logic through curriculum design, documented in the Rubric Logic Guide v2.1 (January 2026). The five-level scale is anchored by two complementary frameworks: Burch's (1970) four stages of competence — unconscious incompetence (doesn't know they don't know), conscious incompetence (knows they don't know), conscious competence (can do it with deliberate effort), unconscious competence (can do it automatically) — provides the developmental logic for the levels. Haring et al.'s (1978) instructional hierarchy — acquisition, fluency, retention, generalisation, adaptation — maps to the levels and determines the appropriate instructional response: a student at Emerging needs guided acquisition practice, not homework; a student at Competent is ready for independent application. Black & Wiliam (1998) established that rubrics are only useful if they change teaching and learning decisions. A rubric that is used only for grading at the end of a unit is not formative — it's a labelling system. The co-construction process ensures that students understand the criteria BEFORE they begin work, enabling ongoing self-assessment and goal-setting throughout the learning process. Sadler (1989) argued that three conditions must be met for effective self-assessment: (a) the student must understand what quality looks like (the standard), (b) the student must be able to compare their current work to the standard (monitoring), and (c) the student must know how to close the gap (strategy). The exemplar analysis component of co-construction addresses condition (a) — students study examples of strong, average, and weak work before generating criteria language.

## Input Schema

The educator must provide:
- **Learning target:** The exact "I can..." statement. *e.g. "I can construct an argument with a clear claim, supporting evidence, and acknowledgement of a different viewpoint" (Band C, Critical Thinking LT2) / "I can design and conduct a fair investigation with one controlled variable" (Band B, Scientific Investigation LT1) / "I can collaborate with my group by contributing ideas and building on others' contributions" (Band B, Collaboration LT1)*
- **Band:** Which developmental band. *e.g. "Band C (ages 10-12)" / "Band B (ages 8-10)" / "Band A (ages 5-7)"*
- **Product or performance:** What students will do. *e.g. "A written persuasive essay (300-500 words) arguing a position on a real local issue" / "A science investigation report including question, method, results, and conclusion" / "Observable participation in a 30-minute group problem-solving task"*

Optional (injected by context engine if available):
- **Student level:** Age/year group for language calibration
- **Formative or summative:** Checkpoint or final assessment
- **Compound LT:** Whether the LT needs splitting

## Prompt

```
You are building a rubric using Gareth Manning's coherent rubric logic (Rubric Logic Guide v2.1). You must follow these rules PRECISELY — they are the quality standard for every rubric produced.

THE FIVE LEVELS:
1. **No Evidence** — The student has not produced work that demonstrates any aspect of this LT. This is NOT "bad work" — it is the absence of evidence. It may mean the student did not attempt the task, was absent, or produced work so unrelated that no assessment is possible. ≤10 words.

2. **Emerging** — The student demonstrates initial awareness or partial engagement with the LT. They are at the beginning of the learning journey. This is a LEGITIMATE starting point — all learners begin here. It is not failure. Corresponds to Burch's "conscious incompetence" — the student knows what they're trying to do but can't yet do it reliably. Instructional response: guided acquisition practice. ≤15 words.

3. **Developing** — The student demonstrates growing capability but is not yet consistent or complete. They can do parts of the task reliably but not all of it. This is a NATURAL and EXPECTED stage of growth on the way to Competent. It is not a punishment. Corresponds to the early stages of "conscious competence." Instructional response: practice with feedback. ≤20 words.

4. **Competent** — **This IS success.** The student has met the band-level expectation. They can reliably perform the LT across contexts relevant to their band. Competent is not "average" — it represents genuine mastery. This is the target. Corresponds to reliable "conscious competence." Instructional response: independent application and transfer. ≤25 words.

5. **Extending** — The student demonstrates evidence BEYOND the band expectation — transfer to unfamiliar contexts, unusual depth or sophistication, or the ability to teach or mentor others. Extending is RARE. It is not a motivational tool or an aspirational target for every student. It represents genuine extension beyond what the band requires. Instructional response: mentoring others, self-directed extension. ≤20 words.

QUANTITATIVE EQUIVALENTS (calibration guides, not targets):
- No Evidence: 0%
- Emerging: 1-49%
- Developing: 50-74%
- Competent: 75-89%
- Extending: 90-100%

RUBRIC WRITING RULES:
- **Work-facing voice throughout.** Describe the WORK, not the student. "Shows clear structure" not "You showed clear structure" or "The student demonstrates clear structure."
- **Word limits are mandatory.** No Evidence ≤10 words. Emerging ≤15. Developing ≤20. Competent ≤25. Extending ≤20. This forces precision and prevents waffle.
- **Each level must be DISTINCT.** A reader should be able to place a piece of student work at one level without ambiguity. If two levels sound similar, one of them is wrong.
- **Competent is the anchor.** Write Competent first — it defines what success looks like. Then write Extending (what goes beyond). Then Emerging (where the journey begins). Then Developing (the space between Emerging and Competent). Finally, No Evidence.
- **Compound LTs:** If the LT contains distinct sub-skills (e.g., "construct an argument with claim, evidence, AND counterargument"), consider whether to split into separate rubric rows. Rule: split only when pedagogically justified. Summative judgment rule for compound LTs: Competent on majority of sub-skills, none below Developing.

CO-CONSTRUCTION SEQUENCE:
1. Teacher prepares the rubric (this skill's output)
2. Students analyse 3 exemplars: one strong, one average, one weak — WITHOUT seeing the rubric first
3. Students generate their own criteria language: "What makes the strong one strong? What's missing from the weak one?"
4. Teacher maps student language to the formal rubric criteria
5. Both versions are published side by side — the teacher rubric for formal assessment, the student rubric for self-assessment

Your task is to build a rubric for:

**Learning target:** {{learning_target}}
**Band:** {{band}}
**Product or performance:** {{product_or_performance}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, infer from the band.
**Formative or summative:** {{formative_or_summative}} — if not provided, design for summative assessment with formative use built in.
**Compound LT:** {{compound_lt}} — if not provided, assess whether the LT needs splitting.

Return your output in this exact format:

## Rubric: [LT Summary]

**Learning target:** [The exact "I can..." statement]
**Band:** [Which band]
**Assessment task:** [What students produce]

### Compound LT Check

[Does this LT need splitting? Apply the test: are there distinct sub-skills that warrant separate rubric rows?]

### Teacher Rubric

| Level | Descriptor | Word Count |
|---|---|---|
| **No Evidence** | [≤10 words] | [Count] |
| **Emerging** | [≤15 words] | [Count] |
| **Developing** | [≤20 words] | [Count] |
| **Competent** | [≤25 words] | [Count] |
| **Extending** | [≤20 words] | [Count] |

### Co-Construction Plan

[How to run the exemplar analysis with students — what exemplars to use, what questions to ask, and how to map student language to the formal criteria]

### Student Rubric Template

| Level | Student-Friendly Language |
|---|---|
| **Not yet** | [Accessible version of No Evidence / Emerging] |
| **Getting there** | [Accessible version of Developing] |
| **Got it!** | [Accessible version of Competent] |
| **Wow!** | [Accessible version of Extending] |

### Written Feedback Guide

[For each level: what specific, actionable feedback to give. Focus on what to DO NEXT, not just what the current level IS.]

### Connection to Instructional Hierarchy

[What the rubric level tells the teacher about the appropriate instructional response — Haring et al.'s hierarchy]

| Level | Instructional Stage | Appropriate Response |
|---|---|---|
| Emerging | Acquisition | [What to do] |
| Developing | Fluency/Retention | [What to do] |
| Competent | Generalisation | [What to do] |
| Extending | Adaptation | [What to do] |

### Known Limitations

[Where professional judgment is still needed; what this rubric cannot capture]

**Self-check before returning output:** Verify that (a) Competent IS success, (b) Extending is rare not aspirational, (c) Emerging is legitimate not failure, (d) word limits are respected, (e) work-facing voice is used, (f) each level is distinct, and (g) the co-construction plan is included.
```

## Example Output

**Scenario:** *Learning target: "I can construct an argument with a clear claim, supporting evidence, and acknowledgement of a different viewpoint" / Band: "Band C (ages 10-12)" / Product or performance: "A written persuasive essay (300-500 words) arguing a position on a real local issue — e.g., whether the school should ban single-use plastics" / Student level: "Year 6, age 10-11" / Formative or summative: "Summative — end of project assessment"*

---

## Rubric: Reasoned Argument (Band C)

**Learning target:** I can construct an argument with a clear claim, supporting evidence, and acknowledgement of a different viewpoint
**Band:** C (ages 10-12)
**Assessment task:** Written persuasive essay, 300-500 words, on a real local issue

### Compound LT Check

This LT contains three identifiable sub-skills: (1) clear claim, (2) supporting evidence, (3) acknowledgement of counterargument. These are distinct but deeply interconnected — an argument without a claim isn't an argument, evidence without a claim has no purpose, and the counterargument only makes sense in relation to the claim. **Decision: single rubric row.** The sub-skills are best assessed holistically as one integrated capability. However, the written feedback guide below will address each sub-skill separately to help students identify where their specific strengths and weaknesses lie.

### Teacher Rubric

| Level | Descriptor | Word Count |
|---|---|---|
| **No Evidence** | No argument or claim present in the work. | 8 |
| **Emerging** | States a position but provides no evidence or reasoning to support it. | 13 |
| **Developing** | Presents a claim with some supporting evidence but does not address any alternative viewpoint. | 15 |
| **Competent** | Presents a clear claim, supports it with relevant evidence, and acknowledges at least one alternative viewpoint with a reasoned response. | 20 |
| **Extending** | Builds a sustained argument integrating multiple evidence sources, addresses counterarguments with nuance, and evaluates the limitations of the position. | 18 |

### Co-Construction Plan

**Before the essay is assigned — allocate 30-40 minutes:**

**Step 1: Exemplar analysis (20 minutes).**
Provide three anonymised student essays on a similar topic (NOT the topic they will write about):
- **Essay A (strong):** Clear claim in the first paragraph, three pieces of evidence, a paragraph acknowledging the opposing view with a reasoned response, a conclusion that restates the position.
- **Essay B (average):** Has a claim and some evidence, but doesn't mention any opposing view. Evidence is relevant but thin — one example repeated.
- **Essay C (weak):** States an opinion ("I think...") without any evidence. Passionate but unsupported.

Read all three aloud. Then ask:
- "Which essay would convince a reader who DISAGREES with the position? Why?"
- "What does Essay A have that Essay C is missing?"
- "What would make Essay B stronger?"

**Step 2: Student criteria generation (10 minutes).**
In pairs, students write down: "What makes a persuasive argument convincing?" Collect responses. Common student language: "It has facts," "It talks about the other side," "It makes sense," "It has a clear point."

**Step 3: Mapping (10 minutes).**
Teacher maps student language to the formal rubric, side by side:
- "It has a clear point" → "Presents a clear claim"
- "It has facts" → "Supports it with relevant evidence"
- "It talks about the other side" → "Acknowledges at least one alternative viewpoint"

Publish both versions — teacher rubric for formal assessment, student rubric for self-assessment.

### Student Rubric Template

| Level | Student-Friendly Language |
|---|---|
| **Not yet** | I haven't written an argument yet, or my writing doesn't take a clear side. |
| **Getting there** | I've said what I think and given some reasons, but I haven't talked about what someone who disagrees would say. |
| **Got it!** | I've made a clear argument with evidence, AND I've explained why someone might disagree and why I still think I'm right. |
| **Wow!** | I've built a really strong argument with lots of evidence, thought carefully about the other side, and been honest about where my argument is weaker. |

### Written Feedback Guide

**No Evidence:** "I can't see an argument in your work yet. Start by answering this question in one sentence: What is your position on [the issue]? That sentence is your claim — everything else supports it."

**Emerging:** "You've told me what you think — that's the start. Now I need to know WHY you think it. Can you find two pieces of evidence (facts, examples, expert opinions) that support your position? Add them."

**Developing:** "Your claim is clear and you've supported it with evidence — that's solid work. The next step: think about what someone who DISAGREES with you would say. Write one paragraph that addresses their strongest argument and explains why your position is still stronger."

**Competent:** "This is a well-constructed argument. You have a claim, evidence, and you've addressed the counterargument. If you want to push further, consider: is there any weakness in your OWN argument? What would you say to someone who pointed it out?"

**Extending:** "This is exceptional work. You've built a sophisticated argument that considers multiple perspectives honestly. Think about presenting this to a real audience — could you submit it to the school newsletter or share it with the [relevant authority]?"

### Connection to Instructional Hierarchy

| Level | Instructional Stage | Appropriate Response |
|---|---|---|
| **Emerging** | Acquisition | Guided practice: model argument construction live, have student co-construct an argument with you. NOT homework — the student needs to see the process before practising independently. |
| **Developing** | Fluency/Retention | Structured practice with feedback: provide argument frames (claim-evidence-counterargument templates). Give specific feedback on the missing counterargument component. Practice with progressively less scaffolding. |
| **Competent** | Generalisation | Independent application: assign new topics, new contexts, new audiences. The student can construct arguments — now test whether they can do it across different subjects and situations. |
| **Extending** | Adaptation | Self-directed extension: student mentors others in argument construction, analyses published arguments (newspaper editorials, political speeches), or tackles genuinely contentious issues where the "right" position is unclear. |

### Known Limitations

1. **The rubric assesses the written PRODUCT, not the thinking PROCESS.** A student who thinks critically but writes poorly may be assessed as Developing based on the essay, even though their analytical thinking is Competent. The essay is evidence of the LT, not the LT itself. Teachers should triangulate with class discussion, oral explanation, and other evidence.

2. **The co-construction process requires 30-40 minutes and three exemplars.** Teachers who skip this step and simply hand out the rubric will find that students use it as a checklist ("Have I included a counterargument? Yes. Done.") rather than as a tool for understanding quality. The co-construction is what makes the rubric formative — without it, the rubric is a grading instrument.

3. **"Extending" is a professional judgment call.** The descriptor provides guidance ("integrates multiple evidence sources, addresses counterarguments with nuance, evaluates limitations"), but recognising genuine extension versus polished Competent work requires experienced judgment. When in doubt, assess as Competent — Extending is rare by design.

---

## Known Limitations

1. **This is a practitioner methodology for rubric design.** The five-level scale, the "Competent IS success" principle, the word limits, and the co-construction sequence are Manning's original synthesis. They are grounded in established assessment research (Black & Wiliam, Sadler, Burch, Haring) but the specific rubric logic has not been independently validated through controlled research.

2. **Word limits force precision but may oversimplify.** The ≤25 word limit for Competent prevents waffle and forces clear thinking, but some complex LTs resist description in 25 words. When the descriptor feels forced or vague because of the word limit, the issue may be the LT (too compound) rather than the rubric.

3. **The student rubric language ("Not yet / Getting there / Got it! / Wow!") is age-dependent.** These labels work well for primary and early secondary students. Older students (14+) may find them patronising. Adapt the language to the audience: "Beginning / Progressing / Achieved / Distinguished" may work for older learners.

**This rubric approach is not appropriate for dispositional knowledge.** The five-level scale works for hierarchical and horizontal knowledge — where criteria-referencing is legitimate and where a student can demonstrate competency through a specific task or performance. It does not work for dispositional knowledge (agency, collaboration, self-regulation, creative confidence, regenerative mindset), where the "knowledge" exists only in enactment across time and context. Applying a summative rubric to dispositional development risks reducing a complex developmental trajectory to a label, and can undermine the intrinsic motivation and psychological safety that dispositional development requires. For dispositional knowledge, use the Dispositional Knowledge Assessment Designer skill instead.

---
# AGENT SKILLS STANDARD FIELDS (v2)
name: criterion-referenced-rubric-generator
description: "Generate a criterion-referenced rubric with descriptive performance levels for a task or objective. Use for marking guides and general curriculum contexts. For Manning programmes where Competent = success, use coherent-rubric-logic-builder instead."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "curriculum-assessment/criterion-referenced-rubric-generator"
skill_name: "Criterion-Referenced Rubric Generator"
domain: "curriculum-assessment"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Brookhart (2013) — How to Create and Use Rubrics for Formative Assessment and Grading"
  - "Andrade (2000, 2013) — Using rubrics to promote thinking and learning"
  - "Jonsson & Svingby (2007) — The use of scoring rubrics: reliability, validity and educational consequences"
  - "Sadler (1989) — Formative assessment and the design of instructional systems"
  - "Panadero & Jonsson (2013) — The use of scoring rubrics for formative assessment purposes revisited"
input_schema:
  required:
    - field: "learning_objective"
      type: "string"
      description: "The learning objective the rubric assesses"
    - field: "task_description"
      type: "string"
      description: "The specific task students will complete"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "criteria_count"
      type: "integer"
      description: "Number of criteria (default: 4)"
    - field: "performance_levels"
      type: "integer"
      description: "Number of performance levels (default: 4)"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "existing_criteria"
      type: "string"
      description: "Any criteria the teacher wants included — the rubric will build around these"
output_schema:
  type: "object"
  fields:
    - field: "rubric"
      type: "object"
      description: "Complete rubric with criteria, performance level descriptors, and scoring guidance"
    - field: "design_rationale"
      type: "string"
      description: "Why these criteria were chosen and how descriptors were differentiated"
    - field: "student_friendly_version"
      type: "string"
      description: "A simplified version students can use for self and peer assessment"
    - field: "calibration_notes"
      type: "string"
      description: "Notes to help multiple markers apply the rubric consistently"
chains_well_with:
  - "competency-unpacker"
  - "backwards-design-unit-planner"
  - "gap-analysis-from-student-work"
  - "feedback-quality-analyser"
  - "kud-knowledge-type-mapper"
teacher_time: "3 minutes"
tags: ["rubric", "assessment", "criteria", "descriptive-language", "formative-assessment"]
---

# Criterion-Referenced Rubric Generator

## What This Skill Does

Produces a criterion-referenced rubric from a learning objective and task description, with descriptive (not evaluative) language at each performance level. Each criterion describes what the student's work LOOKS LIKE at each level — not how "good" it is. The output includes the full rubric, a design rationale, a student-friendly version for self/peer assessment, and calibration notes for consistency across markers. AI is specifically valuable here because effective rubric design requires precise, descriptive language that distinguishes between performance levels without using evaluative labels ("excellent," "good," "poor") or vague quantity indicators ("some," "many," "thorough") — and each descriptor must be qualitatively distinct from the adjacent levels, not just a scaled version of the same description.

## Evidence Foundation

Brookhart (2013) established that effective rubrics use descriptive rather than evaluative language — they describe what is PRESENT in the work, not how good it is. "Uses specific textual evidence to support each analytical point" is descriptive; "Good use of evidence" is evaluative. Descriptive rubrics produce more reliable scoring and more useful feedback because they tell students exactly what to do differently, not just that they need to "do better." Andrade (2000, 2013) demonstrated that rubrics improve both instruction and learning when shared with students before the task — they function as learning tools, not just grading tools. The effect is strongest when rubrics are used for self-assessment. Jonsson & Svingby (2007) found that analytic rubrics (separate criteria scored independently) are more reliable and produce better feedback than holistic rubrics (single overall judgment), though they take longer to use. Sadler (1989) established that assessment quality depends on the "gap" being visible — students must be able to see the difference between where they are and where they need to be. Descriptive rubric levels make this gap concrete. Panadero & Jonsson (2013) confirmed that rubric use improves student performance, particularly when combined with self-assessment, with moderate effect sizes.

## Input Schema

The teacher must provide:
- **Learning objective:** What the rubric assesses. *e.g. "Students can write a persuasive speech that uses rhetorical devices to influence the audience" / "Students can design and carry out a fair test and draw valid conclusions"*
- **Task description:** The specific task. *e.g. "Write and deliver a 3-minute persuasive speech on a topic of your choice" / "Plan and carry out an experiment investigating the effect of light on plant growth, then write a conclusion"*
- **Student level:** Year group. *e.g. "Year 8"*

Optional (injected by context engine if available):
- **Criteria count:** Number of criteria (default: 4)
- **Performance levels:** Number of levels (default: 4)
- **Subject area:** The curriculum subject
- **Existing criteria:** Criteria the teacher wants included

## Prompt

```
You are an expert in assessment design and rubric construction, with deep knowledge of Brookhart's (2013) principles of effective rubric design, Andrade's (2000, 2013) research on rubrics as learning tools, and Sadler's (1989) formative assessment framework. You understand that effective rubrics use DESCRIPTIVE language (describing what is present) rather than EVALUATIVE language (judging how good it is), and that each performance level must be QUALITATIVELY distinct — not just a scaled version of the same description.

Your task is to generate a rubric for:

**Learning objective:** {{learning_objective}}
**Task description:** {{task_description}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Criteria count:** {{criteria_count}} — if not provided, use 4 criteria.
**Performance levels:** {{performance_levels}} — if not provided, use 4 levels.
**Subject area:** {{subject_area}} — if not provided, infer from the learning objective.
**Existing criteria:** {{existing_criteria}} — if provided, incorporate these and add others as needed.

Apply these evidence-based principles:

1. **Descriptive, not evaluative language (Brookhart, 2013):**
   - NEVER use: excellent, good, satisfactory, poor, limited, basic, outstanding, weak.
   - NEVER use vague quantifiers: some, many, few, several, thorough, adequate.
   - INSTEAD: describe specifically what is PRESENT in the work at each level.
   - Bad: "Good use of evidence." Good: "Each analytical point is supported by a specific, relevant quotation from the text."
   - Bad: "Limited vocabulary." Good: "Vocabulary is predominantly everyday; academic or technical terms are absent or used inaccurately."

2. **Qualitatively distinct levels (Sadler, 1989; Brookhart, 2013):**
   - Adjacent levels must describe qualitatively DIFFERENT work, not just more or less of the same thing.
   - Bad progression: "Uses some evidence" → "Uses more evidence" → "Uses a lot of evidence" (quantitative — just more).
   - Good progression: "States claims without evidence" → "Includes evidence but does not connect it to claims" → "Connects evidence to claims with explicit reasoning" → "Selects the most compelling evidence and explains why it is the strongest support for each claim" (qualitative — different type of work).

3. **Criteria must be independent (Jonsson & Svingby, 2007):**
   - Each criterion should assess a distinct, separable aspect of the work.
   - A student should be able to score at different levels on different criteria — not all criteria tracking together.
   - If two criteria always produce the same score, they're probably measuring the same thing.

4. **Student-friendly version (Andrade, 2000, 2013):**
   - Produce a version using student-accessible language.
   - Written in second person: "You support each point with a specific quotation" rather than "The student supports each point with a specific quotation."
   - Can be used for self-assessment before submission.

5. **Calibration notes (Jonsson & Svingby, 2007):**
   - Include notes that help multiple markers apply the rubric consistently.
   - Identify the key distinctions between levels — the "decision points" where markers are most likely to disagree.
   - Where possible, describe what a borderline response looks like between two levels.

Return your output in this exact format:

## Rubric: [Task Description]

**Assesses:** [Learning objective]
**For:** [Student level]
**Criteria:** [Count] | **Levels:** [Count]

### Rubric

[Full rubric table with criteria as rows and performance levels as columns. Each cell contains descriptive language.]

### Design Rationale

[Why these criteria were chosen and how the levels are distinguished]

### Student-Friendly Version

[Simplified rubric in student-accessible language, suitable for self/peer assessment]

### Calibration Notes

[Guidance for consistent application — key decision points, borderline cases]

**Self-check before returning output:** Verify that (a) NO evaluative language appears (no "good," "excellent," "poor," "limited"), (b) NO vague quantifiers appear (no "some," "many," "thorough"), (c) adjacent levels are qualitatively distinct, (d) each criterion is independent, (e) the student-friendly version is genuinely accessible, and (f) calibration notes address the most likely points of marker disagreement.
```

## Example Output

**Scenario:** *Learning objective: "Students can write a persuasive speech that uses rhetorical devices to influence the audience" / Task description: "Write and deliver a 3-minute persuasive speech on a topic of your choice to your class" / Student level: "Year 9" / Subject area: "English"*

---

## Rubric: Persuasive Speech (Written and Delivered)

**Assesses:** Write a persuasive speech that uses rhetorical devices to influence the audience
**For:** Year 9 English
**Criteria:** 4 | **Levels:** 4

### Rubric

| Criterion | Level 1 | Level 2 | Level 3 | Level 4 |
|-----------|---------|---------|---------|---------|
| **Argument and Structure** | The speech states an opinion but does not develop it with reasons. Points are listed without logical connection. There is no clear beginning, middle, or end — the speech could start or stop at any point without the audience noticing. | The speech states a position and provides 1–2 reasons, but the reasons are not fully developed. The speech has a recognisable opening and closing, but the middle section lacks clear organisation — points do not build on each other. | The speech presents a clear position supported by 3+ developed reasons arranged in a logical sequence. Each point builds on the previous one, creating a cumulative argument. The opening engages the audience and the conclusion reinforces the position without simply repeating it. | The speech constructs a strategic argument where the ordering of points is deliberate — the strongest point is positioned for maximum impact. Counter-arguments are acknowledged and addressed. The conclusion reframes the argument in a way that leaves the audience with a lasting impression. |
| **Rhetorical Devices** | The speech relies on personal opinion ("I think...") without any deliberate use of rhetorical techniques. Language is conversational throughout. | The speech includes 1–2 rhetorical devices (e.g., rhetorical question, repetition, rule of three) but they appear isolated — inserted into conversational language rather than integrated into the argument. The devices are present but do not noticeably strengthen the persuasion. | The speech uses 3+ rhetorical devices that are integrated into the argument — each device serves a specific persuasive purpose (a rhetorical question to challenge the audience, repetition to emphasise a key point, emotive language to create urgency). The speaker can explain why they chose each device. | The speech demonstrates controlled and varied use of rhetoric — devices are combined for effect (e.g., a rhetorical question followed by a tricolon that answers it). The tone shifts strategically (from rational to emotional, from calm to urgent) to position the audience. Language choices reflect awareness of the specific audience. |
| **Audience Awareness** | The speech is written for a general audience — there are no specific references to the listeners, their experiences, or their likely objections. The speaker talks AT the audience rather than TO them. | The speech includes some awareness of the audience (e.g., "As students, we all know...") but this awareness is surface-level — it acknowledges the audience without adapting the argument to their specific concerns or perspectives. | The speech directly addresses the audience's likely views, concerns, or experiences. The speaker anticipates what the audience might think or feel and addresses it: "You might be thinking... but consider this." The speech feels directed at THESE listeners, not any audience. | The speech is strategically tailored to the specific audience — it uses shared references, anticipates specific objections, and adjusts register, vocabulary, and tone to match the listeners. The speaker reads the room during delivery and responds to audience reactions (adjusting pace, adding emphasis, making eye contact with sceptics). |
| **Delivery** | The speech is read from a script with minimal eye contact. Volume is either too quiet to hear or monotone throughout. The speaker appears disconnected from their own argument. | The speech is mostly read with occasional glances at the audience. Volume is audible. Some variation in tone is attempted, but pacing is uneven — the speaker rushes through some sections and pauses awkwardly in others. | The speaker uses notes as prompts rather than reading a full script. Eye contact is regular and distributed across the audience. Volume, pace, and emphasis vary deliberately to reinforce key points. Pauses are used for effect, not from uncertainty. | The speaker is largely independent of notes. Delivery feels natural and confident — the speaker appears to be thinking and speaking, not performing a memorised text. Gestures, movement, facial expression, and vocal variety all serve the argument. The speaker commands the room. |

### Design Rationale

**Why these four criteria:**
1. **Argument and Structure** — the foundation. A speech without a clear argument is not persuasive, regardless of how well it's delivered.
2. **Rhetorical Devices** — the tool kit. The learning objective specifically requires rhetorical devices; this criterion assesses whether they're present AND functional.
3. **Audience Awareness** — the persuasive lens. Persuasion is fundamentally about the audience; this criterion assesses whether the speaker writes FOR their listeners or just AT them.
4. **Delivery** — the performance dimension. A speech is a spoken genre; content quality and delivery quality are separate skills that should be assessed independently. A student might write a brilliant speech and deliver it poorly, or vice versa — separate criteria capture both.

**How levels are distinguished:**
- Level 1 → Level 2: The element is PRESENT but not effective (devices exist but don't persuade; structure exists but doesn't build).
- Level 2 → Level 3: The element is FUNCTIONAL — it serves a purpose and achieves an effect (devices are integrated, structure builds, audience is directly addressed).
- Level 3 → Level 4: The element is STRATEGIC — the student makes deliberate, sophisticated choices and can explain them (rhetoric is combined, argument is ordered for impact, audience is read and responded to).

### Student-Friendly Version

**Before you submit, check your speech against these criteria:**

**Your argument:**
- Level 1: You state your opinion but don't really explain why.
- Level 2: You give reasons but they're not fully developed — you haven't explained WHY your reasons are convincing.
- Level 3: You present a clear argument with 3+ reasons that build on each other. Your opening grabs attention and your ending reinforces your point.
- Level 4: You've arranged your points strategically — putting your strongest point where it has the most impact. You address what the other side would say.

**Your use of rhetorical devices:**
- Level 1: You haven't used any persuasive techniques — it just sounds like you're talking normally.
- Level 2: You've used 1–2 techniques but they feel "stuck on" — like you added them because you had to.
- Level 3: You've used 3+ techniques and each one has a PURPOSE — you can explain why you chose it and what effect it creates.
- Level 4: Your techniques work TOGETHER — you combine them, and you change your tone deliberately to affect the audience.

**Your awareness of the audience:**
- Level 1: You're talking AT your audience, not TO them.
- Level 2: You mention the audience ("As students, we...") but don't really adapt your argument to them.
- Level 3: You directly address what your audience thinks and feels. "You might be thinking... but consider this."
- Level 4: Your whole speech is shaped for THIS specific audience — you use their language, anticipate their objections, and adjust as you go.

**Your delivery:**
- Level 1: You're reading your speech with your eyes on the paper.
- Level 2: You look up sometimes. Your voice is audible but doesn't really change.
- Level 3: You use notes, not a full script. You make eye contact. You deliberately change speed, volume, and emphasis.
- Level 4: You barely need notes. Your delivery feels natural and confident. Your body language and voice both serve your argument.

### Calibration Notes

**Key decision points for markers:**

1. **Level 2 vs. Level 3 on Rhetorical Devices:** The distinction is between devices that are PRESENT and devices that are FUNCTIONAL. Ask: "If I removed this rhetorical question, would the speech be less persuasive?" If yes → Level 3 (it's doing work). If no → Level 2 (it's decorative).

2. **Level 3 vs. Level 4 on Argument and Structure:** Level 3 has a clear, logical argument. Level 4 has a STRATEGIC argument — the ordering is deliberate, and counter-arguments are addressed. If the speech presents good points but in no particular order → Level 3. If the ordering itself reveals strategic thinking (building to a climax, saving the strongest point) → Level 4.

3. **Delivery is independent of content.** A student may deliver a poorly structured speech with great confidence (high Delivery, low Argument) or a brilliant speech in a monotone (high Argument, low Delivery). Score each criterion independently.

4. **Borderline between Level 2 and Level 3:** The most common borderline. If in doubt, ask: "Is the student just doing the thing (using a device, addressing the audience) or is the student doing the thing WITH PURPOSE (using the device to achieve a specific effect, addressing the audience's specific concerns)?" Purpose → Level 3. Going through the motions → Level 2.

---

## Known Limitations

1. **Rubrics describe performance but do not explain how to improve.** A student who reads the rubric and sees they are at Level 2 for Rhetorical Devices knows WHAT to do differently (integrate devices with purpose) but may not know HOW. The rubric should be paired with teaching and feedback that shows students how to move from one level to the next. Chain with Feedback Quality Analyser for targeted improvement advice.

2. **Four levels is a practical compromise.** Some tasks would benefit from more levels (to distinguish fine gradations) or fewer (to simplify assessment). Four levels balance reliability (enough levels to be informative) with usability (few enough to be practical). If the rubric is being used for high-stakes grading, additional level descriptors may be needed.

3. **Descriptive language is harder to write but more useful than evaluative language.** The rubric avoids "good," "excellent," and "poor," which makes each cell longer and more specific. This is a deliberate trade-off — evaluative rubrics are shorter but less useful for feedback. Teachers may need time to become comfortable with descriptive rubric language.

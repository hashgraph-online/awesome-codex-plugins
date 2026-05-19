---
# AGENT SKILLS STANDARD FIELDS (v2)
name: ladder-of-inference-reflection
description: "Slow down interpretation from observation to action. Use when students or adults need to examine assumptions in conflict, dialogue, or inquiry."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "systems-thinking/ladder-of-inference-reflection"
skill_name: "Ladder of Inference Reflection"
domain: "systems-thinking"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Argyris (1990) — Overcoming Organizational Defenses (ladder of inference and defensive reasoning)"
  - "Argyris & Schön (1974) — Theory in Practice (reflection on reasoning and action)"
  - "Senge et al. (1994) — The Fifth Discipline Fieldbook (ladder of inference as dialogue tool)"
  - "Yeager & Walton (2011) — Social-psychological interventions in education (meaning-making and interpretation)"
input_schema:
  required:
    - field: "situation"
      type: "string"
      description: "The moment, conflict, observation, decision, or interpretation to examine"
    - field: "context"
      type: "string"
      description: "Where this happened and who is involved"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "current_interpretation"
      type: "string"
      description: "What someone currently thinks the situation means"
    - field: "desired_use"
      type: "string"
      description: "Reflection, restorative dialogue, bias check, discussion, or inquiry"
output_schema:
  type: "object"
  fields:
    - field: "ladder_map"
      type: "object"
      description: "Observation, selected data, meanings, assumptions, conclusions, beliefs, and actions"
    - field: "alternative_ladders"
      type: "array"
      description: "Other plausible interpretations"
    - field: "questions_to_test"
      type: "array"
      description: "Evidence-seeking questions"
    - field: "dialogue_script"
      type: "object"
      description: "Language for safe classroom use"
chains_well_with:
  - "mental-model-mapper"
  - "restorative-practice-protocol-designer"
  - "dialogic-teaching-move-generator"
  - "socratic-questioning-sequence-generator"
  - "systems-awareness-iceberg"
teacher_time: "5 minutes"
tags: ["ladder-of-inference", "assumptions", "dialogue", "reflection", "conflict", "bias", "compassionate-systems"]
---

# Ladder of Inference Reflection

## What This Skill Does

Helps students and adults slow down the movement from observation to interpretation to action. The Ladder of Inference is useful when a person has leapt from limited data to a strong conclusion: "She ignored me because she dislikes me," "Students are lazy," "The school doesn't care," or "The community will never change."

This skill does not tell people their feelings are wrong. It separates what was observed from what was selected, interpreted, assumed, concluded, believed, and done. It then opens alternative ladders and evidence-seeking questions.

## Evidence Foundation

The Ladder of Inference is associated with Argyris' work on reasoning, defensive routines, and organisational learning, and was popularised for systems learning through Senge and colleagues. It is especially useful in compassionate systems work because mental models often become visible through the meanings people make from selected data.

## Input Schema

Required:
- **Situation:** The moment, conflict, decision, or interpretation.
- **Context:** Where it happened and who is involved.

Optional:
- **Student level:** Age/year group.
- **Current interpretation:** What someone currently believes the situation means.
- **Desired use:** Reflection, restorative dialogue, bias check, inquiry, staff discussion.

## Prompt

```text
You are guiding a Ladder of Inference reflection. Help the user move carefully from observed data to selected data, meanings, assumptions, conclusions, beliefs, and actions.

Inputs:
Situation: {{situation}}
Context: {{context}}
Student level: {{student_level}}
Current interpretation: {{current_interpretation}}
Desired use: {{desired_use}}

Rules:
1. Validate that interpretations can feel real while still being incomplete.
2. Distinguish observable data from selected data and meaning-making.
3. Include at least two alternative ladders that could also fit the observable data.
4. Do not force forgiveness, positivity, or reconciliation.
5. In conflict contexts, protect dignity and safety.
6. End with questions that gather evidence or open dialogue.

Return exactly:

## Ladder of Inference: [Situation]

**Context:** [brief]
**Purpose:** [reflection/dialogue/inquiry]

### Step 1: Observable Data
What someone could have seen/heard/read without interpretation:
- [observable fact]
- [observable fact]

### Step 2: Selected Data
What the person may have noticed most:
- [selected clue]
- [selected clue]

### Step 3: Meanings Added
Possible meanings attached to the selected data:
- [meaning]

### Step 4: Assumptions
Possible assumptions underneath the meaning:
- [assumption]

### Step 5: Conclusions
What the person may conclude:
- [conclusion]

### Step 6: Beliefs Reinforced
Wider beliefs or mental models this conclusion may strengthen:
- [belief/model]

### Step 7: Actions
What actions this ladder may lead to:
- [action/avoidance/response]

### Alternative Ladders
**Alternative ladder 1:** [same data, different possible meaning]
**Alternative ladder 2:** [same data, different possible meaning]

### Evidence-Seeking Questions
- What did I actually observe?
- What did I not observe?
- What else could this mean?
- What could I ask safely and respectfully?
- What evidence would change my interpretation?

### Dialogue Language
- "The story I'm telling myself is..."
- "What I noticed was..."
- "I may be missing something. Can you help me understand...?"
- "Another possibility is..."

Self-check: Do not invalidate emotion. Do not present alternatives as truth. Keep safety and dignity central.
```

## Common Pitfalls

1. **Using the ladder to dismiss emotion.** Feelings are data about experience, but not always proof of the whole story.
2. **Over-intellectualising harm.** If harm occurred, do not use alternative ladders to excuse it.
3. **Skipping observable data.** Start with what can be seen/heard/read.
4. **Assuming one correct interpretation.** The goal is better inquiry, not forced consensus.

## Known Limitations

1. **Does not determine what actually happened.** The ladder is a reflective tool, not an investigative one. It cannot resolve factual disputes, adjudicate harm, or substitute for restorative or disciplinary processes.
2. **Not appropriate immediately after significant harm.** Generating alternative interpretations of a recent serious incident can feel invalidating to those harmed. The skill needs time, trust, and often a restorative framing to be used safely.
3. **Power asymmetry risk.** When the people involved hold significantly different power (e.g. teacher and student, or adult and child), alternative ladders may feel dismissive of the less-powerful person's experience if not carefully facilitated.
4. **Culturally bounded.** The skill may not work well when the interpretation in question involves cultural knowledge, community history, or lived experience that the facilitator does not share. External cultural expertise may be required.

## Verification Checklist

- [ ] Observable data is separated from interpretation.
- [ ] Assumptions are named tentatively.
- [ ] At least two alternative ladders are included.
- [ ] Dialogue language is safe and age-appropriate.
- [ ] The output does not excuse harm or force reconciliation.

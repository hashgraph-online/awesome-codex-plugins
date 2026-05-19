---
# AGENT SKILLS STANDARD FIELDS (v2)
name: mental-model-mapper
description: "Surface beliefs, assumptions, stories, and values shaping a system. Use when deeper mental models need examining with care and evidence."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "systems-thinking/mental-model-mapper"
skill_name: "Mental Model Mapper"
domain: "systems-thinking"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Senge (1990) — The Fifth Discipline (mental models as assumptions shaping action)"
  - "Argyris & Schön (1974) — Theory in Practice (espoused theories and theories-in-use)"
  - "Meadows (2008) — Thinking in Systems (paradigms as deep leverage points)"
  - "Bang, Medin & Atran (2007) — Cultural mosaics and mental models of nature"
input_schema:
  required:
    - field: "system_focus"
      type: "string"
      description: "The issue, aspiration, decision, curriculum area, conflict, or place-based system to examine"
    - field: "context"
      type: "string"
      description: "Where the system exists and who is involved"
  optional:
    - field: "visible_evidence"
      type: "string"
      description: "Events, language, routines, artefacts, or decisions that may reveal mental models"
    - field: "stakeholders"
      type: "array"
      description: "Groups whose mental models may differ"
    - field: "purpose"
      type: "string"
      description: "Whether the goal is reflection, redesign, conflict repair, curriculum planning, or action"
output_schema:
  type: "object"
  fields:
    - field: "mental_model_map"
      type: "object"
      description: "Current and alternative mental models with evidence and effects"
    - field: "belief_to_structure_links"
      type: "array"
      description: "How models shape structures, patterns, and actions"
    - field: "reflection_questions"
      type: "array"
      description: "Prompts for students/adults"
    - field: "safer_language"
      type: "array"
      description: "Phrases that avoid accusation"
chains_well_with:
  - "systems-awareness-iceberg"
  - "aspirational-systems-iceberg"
  - "ladder-of-inference-reflection"
  - "systems-wellbeing-impact-mapper"
  - "culturally-responsive-teaching-designer"
  - "place-based-inquiry-anchor"
teacher_time: "5 minutes"
tags: ["mental-models", "assumptions", "systems-thinking", "compassionate-systems", "culture", "reflection", "beliefs"]
---

# Mental Model Mapper

## What This Skill Does

Surfaces the beliefs, assumptions, stories, values, identities, fears, and definitions of success that shape a system. A mental model is not merely an opinion. It is a way of interpreting reality that influences what people notice, what they treat as normal, what they design for, and what they consider possible.

This skill is useful after an iceberg, inside an aspirational iceberg, during conflict reflection, when redesigning curriculum, or when examining culture. It helps students and adults say: "What are we assuming? What story is operating here? What structures does that story keep alive? What alternative model might be more compassionate, systemic, or regenerative?"

## Evidence Foundation

Senge identifies mental models as deeply held assumptions that shape organisational behaviour. Argyris and Schön distinguish between espoused theories (what people say guides them) and theories-in-use (what their actions reveal). Meadows identifies paradigms and goals as deep leverage points in systems. Bang, Medin and Atran show that mental models of nature differ across cultural communities and shape ecological reasoning, making this tool especially important for place-based and regenerative work.

## Input Schema

Required:
- **System focus:** The issue, aspiration, conflict, curriculum area, or place-based system.
- **Context:** Where this is happening and who is involved.

Optional:
- **Visible evidence:** Language, routines, artefacts, decisions, student work, interactions, or observations.
- **Stakeholders:** Whose models may need mapping.
- **Purpose:** Reflection, redesign, conflict repair, curriculum planning, or action.

## Prompt

```text
You are mapping mental models in a compassionate systems-aware way. Your task is to surface possible beliefs and assumptions shaping a system without accusing people of holding them.

Inputs:
System focus: {{system_focus}}
Context: {{context}}
Visible evidence: {{visible_evidence}}
Stakeholders: {{stakeholders}}
Purpose: {{purpose}}

Rules:
1. Treat every mental model as a hypothesis, not a verdict.
2. Distinguish espoused models from models-in-use:
   - Espoused model: what people say they believe.
   - Model-in-use: what routines, decisions, incentives, or artefacts imply.
3. Include multiple stakeholders. Different groups may hold different models for good reasons.
4. Link each mental model to visible structures or patterns. Do not list abstract beliefs without consequences.
5. Name possible protective functions. Some limiting models may have developed to protect safety, efficiency, identity, status, or belonging.
6. Propose alternative models that are believable, not just virtuous slogans.
7. Use careful language: "A possible model is..." / "The system may be acting as if..." / "One story that might be present..."

Return exactly:

## Mental Model Map: [System Focus]

**Context:** [brief]
**Purpose:** [reflection/redesign/repair/action]
**Stance:** Mental models are hypotheses to test through evidence and dialogue.

### Visible Clues
- **Language clues:** [phrases, labels, metaphors]
- **Routine clues:** [what keeps happening]
- **Artefact clues:** [policies, displays, tools, forms, spaces]
- **Decision clues:** [what gets prioritised]

### Current Mental Models That May Be Operating
For each:
**Model [N]: [short name]**
- **Possible belief/story:** [belief]
- **May be held by:** [stakeholder/s or "the system as a whole"]
- **Evidence suggesting it:** [visible clues]
- **Structures it sustains:** [rules, routines, roles, incentives, artefacts]
- **Patterns it produces:** [repeated behaviours]
- **Protective function:** [what this model might be trying to protect]
- **Risk or harm:** [what it may constrain or damage]
- **Evidence needed before concluding:** [what to ask/observe]

### Aspirational or Alternative Mental Models
For each:
**Alternative model:** [belief/story]
- **Why it may be more compassionate/systemic/regenerative:** [reason]
- **What structures would make it credible:** [routines, roles, artefacts, experiences]
- **First practice that could embody it:** [small action]

### Dialogue Prompts
- [Question that invites reflection without blame]
- [Question that helps students/adults test evidence]
- [Question that opens alternative possibilities]

### Safer Language Guide
Instead of: "People believe..."
Say: "The system may be acting as if..."
Instead of: "Students don't care..."
Say: "One possible story is that students have learned their contribution does not change anything. What evidence would test that?"

Self-check: Do not claim to know what people believe. Do not moralise mental models. Link models to structures and patterns. Include alternative models plus the structures needed to make them real.
```

## Common Pitfalls

1. **Mind-reading.** We infer mental models from evidence; we do not declare what someone secretly believes.
2. **Moralising.** Mental models are not sins. They are often adaptive responses to lived conditions.
3. **Only mapping negative models.** Aspirational models need mapping too.
4. **Ignoring culture.** Mental models may be culturally situated; do not universalise one worldview.
5. **Changing language without changing structures.** A new story needs routines and artefacts that make it believable.

## Known Limitations

1. **Cannot confirm what people actually believe.** All mental models are inferences from visible evidence — language, routines, artefacts, decisions. The skill produces hypotheses, not confirmed beliefs. Do not present outputs as psychological assessments of named individuals.
2. **Degrades without visible evidence.** When there is limited observable evidence of the system in action, the mapper cannot generate credible hypotheses. It needs clues to work from.
3. **Does not surface power dynamics automatically.** Some mental models are enforced by people with institutional authority, not just held individually. This distinction matters for action design and must be named explicitly by the teacher.
4. **Not suitable as a live classroom exercise without careful facilitation planning.** When students are present and could recognise themselves or peers in the mental model map, psychological safety planning is required before use.

## Verification Checklist

- [ ] Mental models are labelled as hypotheses.
- [ ] Each model links to visible evidence.
- [ ] Each model links to structures and patterns.
- [ ] Protective functions are considered.
- [ ] Alternative models include enabling structures.
- [ ] Dialogue prompts are safe enough for classroom or staff use.

---
# AGENT SKILLS STANDARD FIELDS (v2)
name: systems-awareness-iceberg
description: "Map a current event below the surface into patterns, structures, and mental models. Use when a class or team needs systemic understanding before action."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "systems-thinking/systems-awareness-iceberg"
skill_name: "Systems Awareness Iceberg"
domain: "systems-thinking"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Center for Systems Awareness (2022) — Guided Iceberg and Aspirational Iceberg practitioner resources"
  - "Senge (1990) — The Fifth Discipline (systems thinking, mental models, learning organisations)"
  - "Meadows (2008) — Thinking in Systems (patterns, structures, leverage points)"
  - "Böll & Senge (2021) — Compassionate Systems Framework, Centre for Systems Awareness (practitioner framework materials, not peer-reviewed)"
input_schema:
  required:
    - field: "focal_event"
      type: "string"
      description: "The visible current event or repeated issue to investigate"
    - field: "context"
      type: "string"
      description: "Class, school, community, ecological, or curriculum context"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "stakeholders"
      type: "array"
      description: "People, groups, or more-than-human stakeholders involved"
    - field: "existing_evidence"
      type: "string"
      description: "Observations, data, stories, artefacts, or student work already available"
output_schema:
  type: "object"
  fields:
    - field: "iceberg_map"
      type: "object"
      description: "Event, patterns/behaviours, structures, and mental models"
    - field: "evidence_questions"
      type: "array"
      description: "Questions that distinguish evidence from assumptions"
    - field: "leverage_possibilities"
      type: "array"
      description: "Places where a response might shift structures or mental models"
    - field: "facilitation_cautions"
      type: "array"
      description: "Risks, sensitivities, and teacher judgement checks"
chains_well_with:
  - "aspirational-systems-iceberg"
  - "mental-model-mapper"
  - "agency-circles-for-systems-action"
  - "ladder-of-inference-reflection"
  - "place-based-inquiry-anchor"
  - "restorative-practice-protocol-designer"
teacher_time: "5 minutes"
tags: ["systems-thinking", "iceberg", "compassionate-systems", "mental-models", "structures", "leverage", "classroom-inquiry"]
---

# Systems Awareness Iceberg

## What This Skill Does

Helps educators and students investigate a visible event by moving below the surface into repeated patterns, enabling structures, and underlying mental models. The skill is designed for compassionate systems awareness: it slows the rush to blame or fix, asks what evidence we actually have, and preserves the dignity of the people inside the system. Use it when a class, project group, school team, or community inquiry keeps noticing the same issue and needs to understand the conditions that reproduce it.

The output is not a causal diagram pretending to be certain. It is a disciplined map of current hypotheses: what happened, what seems to keep happening, what structures may be shaping the pattern, and what beliefs or assumptions may be sustaining those structures. It should lead naturally into mental-model mapping, agency circles, or leverage-and-response design.

## Evidence Foundation

The iceberg model is a common systems-thinking tool used by the Center for Systems Awareness and in the Compassionate Systems Framework. It aligns with Senge's account of learning organisations, where recurring events are produced by deeper structures and mental models, and with Meadows' explanation that systems behaviour emerges from stocks, flows, feedback, rules, goals, and paradigms. In education, the value is not only analytical but relational: the iceberg helps students and adults move from individual blame to curiosity about context, patterns, and design.

## Input Schema

The teacher must provide:
- **Focal event:** A visible event, incident, outcome, or repeated issue. Example: "Students rarely speak during class discussions" or "Our recycling bins are often contaminated."
- **Context:** Where this happens and why it matters.

Optional context:
- **Student level:** Age/year group, to calibrate language and abstraction.
- **Stakeholders:** Who is affected, including non-human/ecological stakeholders where relevant.
- **Existing evidence:** Observations, data, stories, student work, photos, notes, or artefacts.

## Prompt

```text
You are facilitating a compassionate systems-thinking inquiry using the Systems Awareness Iceberg. Your role is to help the teacher or students move below a visible current event into patterns, structures, and mental models without blaming individuals or overclaiming causality.

Inputs:
Focal event: {{focal_event}}
Context: {{context}}
Student level: {{student_level}}
Stakeholders: {{stakeholders}}
Existing evidence: {{existing_evidence}}

Use these rules:
1. Start with one clear visible event. If the input is broad, narrow it to an observable moment or outcome.
2. Separate evidence from interpretation. Mark uncertain claims as hypotheses.
3. Move down the iceberg:
   - Event: What happened? What can be observed?
   - Patterns and behaviours: What keeps happening over time? What trends, routines, or repeated responses are visible?
   - Structures: What schedules, spaces, rules, incentives, roles, tools, policies, resources, assessment practices, histories, or power relationships make the pattern more likely?
   - Mental models: What beliefs, assumptions, stories, values, fears, expectations, or definitions of success may sustain the structures?
4. Use compassionate language. Do not describe students, teachers, families, or communities as deficient. Describe conditions and interpretations.
5. Include more than one possible explanation. Complex systems rarely have a single cause.
6. End with questions and leverage possibilities, not a final solution.

Return exactly:

## Systems Awareness Iceberg: [Focal Event]

**Context:** [brief]
**Working stance:** This is a hypothesis map, not a verdict.

### 1. Event
[The visible event in precise, observable language]

### 2. Patterns and Behaviours
- [Repeated pattern or trend]
- [Repeated response]
- [What seems to intensify or reduce it]

### 3. Structures
Organise as:
- **Routines and time:**
- **Space and materials:**
- **Rules, incentives, and assessment:**
- **Roles and relationships:**
- **Information flows:**
- **History and power:**

### 4. Mental Models
For each mental model, include whose model it might be and how tentative it is:
- **Possible belief/story:** [belief]
  - **May be held by:** [stakeholder/s]
  - **How it shapes the system:** [effect]
  - **Evidence needed:** [what would confirm/disconfirm]

### Evidence We Still Need
[List questions or data needed before acting strongly]

### Possible Leverage Points
[List 3-5 possible structural or mental-model leverage points, phrased as experiments or inquiries]

### Facilitation Cautions
[How to avoid blame, stereotyping, over-individualising systemic issues, or pushing students into unsafe disclosure]

Self-check: The output must move beyond behaviour management; must include structures and mental models; must avoid blaming individuals; must name uncertainty; and must preserve teacher judgement.
```

## Common Pitfalls

1. **Treating the first explanation as the cause.** Keep multiple hypotheses alive until evidence narrows them.
2. **Stopping at behaviour.** "Students don't care" is not a systems explanation; it is usually a mental model to examine.
3. **Skipping power and history.** Structures include rules, resources, status, institutional memory, and who gets heard.
4. **Turning the iceberg into blame with better vocabulary.** The tool should increase compassion and agency, not produce more elegant judgement.
5. **Jumping straight to solutions.** Use the iceberg to understand; use later tools to choose action.

## Known Limitations

1. **Hypotheses only.** This skill maps possible explanations, not confirmed causes. It cannot verify whether identified patterns, structures, or mental models are factually operating without additional inquiry and local evidence.
2. **Degrades with overly broad focal events.** "Inequality in education" is too large. The tool works best with a specific, locally observable event or repeated pattern a teacher can actually witness.
3. **Does not generate action.** The iceberg produces a hypothesis map, not a response plan. Use agency-circles-for-systems-action or a project planning skill for action design.
4. **Cannot assess facilitation safety.** The skill cannot determine whether a particular classroom group is emotionally ready for public systems mapping. Teacher judgement about trauma history, peer dynamics, and disclosure risk is irreplaceable.

## Verification Checklist

- [ ] The event is observable and specific.
- [ ] Patterns describe repetition over time, not a single anecdote.
- [ ] Structures include routines, roles, rules, incentives, information, space, resources, history, and power where relevant.
- [ ] Mental models are framed as hypotheses, not accusations.
- [ ] The output identifies evidence needed before major action.
- [ ] The response suggests leverage possibilities without pretending certainty.

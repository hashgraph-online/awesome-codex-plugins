---
# AGENT SKILLS STANDARD FIELDS (v2)
name: aspirational-systems-iceberg
description: "Design the deeper patterns, structures, artefacts, and mental models needed to grow a desired event. Use when a class imagines a better future."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "systems-thinking/aspirational-systems-iceberg"
skill_name: "Aspirational Systems Iceberg"
domain: "systems-thinking"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Center for Systems Awareness (2022) — Guided Iceberg and Aspirational Iceberg practitioner resources"
  - "Senge (1990) — The Fifth Discipline (systems thinking, mental models, learning organisations)"
  - "Meadows (2008) — Thinking in Systems (patterns, structures, leverage points)"
  - "Böll & Senge (2021) — Compassionate Systems Framework, Centre for Systems Awareness (practitioner framework materials, not peer-reviewed)"
input_schema:
  required:
    - field: "desired_event"
      type: "string"
      description: "A visible event or outcome students/educators want to grow"
    - field: "context"
      type: "string"
      description: "Class, school, community, ecological, curriculum, or project context"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "current_reality"
      type: "string"
      description: "What currently happens instead"
    - field: "stakeholders"
      type: "array"
      description: "People, groups, or more-than-human stakeholders affected"
    - field: "constraints"
      type: "string"
      description: "Time, power, policy, safety, resource, or access constraints"
output_schema:
  type: "object"
  fields:
    - field: "aspirational_iceberg"
      type: "object"
      description: "Desired event, patterns/behaviours, structures/artefacts, and mental models"
    - field: "first_experiments"
      type: "array"
      description: "Safe small experiments that could begin growing the aspiration"
    - field: "classroom_sequence"
      type: "object"
      description: "Teacher-friendly activity flow"
    - field: "quality_gates"
      type: "array"
      description: "Checks that the design is observable, systemic, and realistic"
chains_well_with:
  - "systems-awareness-iceberg"
  - "mental-model-mapper"
  - "agency-circles-for-systems-action"
  - "place-based-inquiry-anchor"
  - "agency-scaffold-generator"
  - "project-brief-designer"
teacher_time: "5 minutes"
tags: ["aspirational-iceberg", "systems-thinking", "future-design", "student-agency", "compassionate-systems", "mental-models", "regenerative"]
---

# Aspirational Systems Iceberg

## What This Skill Does

Designs the flipped version of the systems iceberg. Instead of starting with an undesirable event and asking what deeper patterns, structures, and mental models produce it, this skill starts with a visible event students or educators want to grow. It then asks: what repeated patterns would make this event normal, what structures and artefacts would sustain those patterns, and what mental models would need to be cultivated or shifted?

This is especially useful in classrooms because it turns systems thinking toward possibility. Students learn that a better future is not produced by a wish or slogan. It requires conditions: routines, roles, spaces, supports, information flows, incentives, relationships, and beliefs that make the desired event more likely.

## Evidence Foundation

The Center for Systems Awareness publishes a Guided Iceberg (Aspirational) resource that begins with "What are we trying to grow?" and asks what patterns, structures, artefacts, values, beliefs, and transformed thinking would support the aspiration. This skill adapts that practitioner tool for classroom and curriculum design. It also draws on Senge's work on mental models and learning organisations and Meadows' work on systems structures and leverage points.

## Input Schema

The teacher must provide:
- **Desired event:** A visible, recognisable event or outcome. Example: "Students notice exclusion and respond with care" or "Our class uses feedback to improve work without shame."
- **Context:** Where this aspiration matters and who is involved.

Optional context:
- **Student level:** Age/year group.
- **Current reality:** What tends to happen now.
- **Stakeholders:** Who is affected or needed.
- **Constraints:** What limits action.

## Prompt

```text
You are facilitating an Aspirational Systems Iceberg. Start with the desired visible event and work downward to the deeper system that would make it more likely.

Inputs:
Desired event: {{desired_event}}
Context: {{context}}
Student level: {{student_level}}
Current reality: {{current_reality}}
Stakeholders: {{stakeholders}}
Constraints: {{constraints}}

Rules:
1. Make the desired event observable. If the aspiration is vague, translate it into visible evidence: what would someone see, hear, read, or experience?
2. Work downward from aspiration to conditions:
   - Event: What are we trying to grow? What visible evidence would show it is happening?
   - Patterns and behaviours: What repeated actions, habits, interactions, and trends would need to become normal?
   - Structures and artefacts: What routines, roles, spaces, tools, protocols, schedules, policies, resources, rituals, feedback loops, or artefacts would sustain those patterns?
   - Mental models: What beliefs, values, assumptions, identities, and definitions of success would need to be strengthened, questioned, or shifted?
3. Include current reality without letting it dominate. The purpose is design, not complaint.
4. Avoid magical thinking. Every aspiration must be connected to concrete structures and small experiments.
5. Preserve agency and responsibility. Do not imply students alone must fix institutional or systemic problems.
6. End with first safe experiments that the class or teacher can try within their real sphere of influence.

Return exactly:

## Aspirational Systems Iceberg: [Desired Event]

**Context:** [brief]
**Design stance:** We are identifying the conditions that could help this aspiration grow.

### 1. Desired Event
**What we want to see happen:** [observable event]
**How we would recognise it:**
- [Visible/heard evidence]
- [Student/community experience evidence]
- [Artefact/product/data evidence]

### 2. Patterns and Behaviours to Grow
- [Repeated behaviour/habit/interaction]
- [Trend over time]
- [Pattern of response when difficulty appears]

### 3. Structures and Artefacts to Create or Strengthen
- **Routines:** [repeatable practices]
- **Roles:** [who holds what responsibility]
- **Spaces/materials:** [physical/digital/environmental supports]
- **Protocols/tools:** [scripts, forms, prompts, checklists, dialogue moves]
- **Time and rhythms:** [when this happens]
- **Feedback loops:** [how the system notices whether it is growing]
- **Institutional supports:** [adult, policy, resource, community supports]

### 4. Mental Models to Cultivate or Shift
For each mental model:
- **Current model that may limit growth:** [belief/story]
- **Aspirational model to cultivate:** [belief/story]
- **What would make the new model credible:** [experience/evidence/practice]

### 5. First Safe Experiments
Suggest 3 small experiments:
1. **Experiment:** [small action]
   - **Why this tests the system:** [pattern/structure/mental model]
   - **Evidence to notice:** [what to watch]
   - **Risk/safety check:** [how to keep it low-harm]

### 6. Classroom Facilitation Sequence
- **Opening prompt:** [student-friendly]
- **Individual think time:** [what students write/draw]
- **Group mapping:** [how groups build the iceberg]
- **Gallery walk or discussion:** [how patterns across groups are noticed]
- **Action selection:** [how to choose one experiment]
- **Reflection:** [what to revisit later]

### Quality Gates
- [ ] Desired event is observable.
- [ ] Patterns are repeated behaviours, not one-off hopes.
- [ ] Structures are concrete enough to design.
- [ ] Mental models are examined with humility, not used to judge people.
- [ ] First experiments sit within real control or influence.
- [ ] Institutional responsibility is named where needed.
```

## Example Classroom Uses

- Build an inclusive class culture: "A student who usually feels invisible is invited into a group without the teacher prompting."
- Redesign feedback culture: "Students use critique to improve their work and still feel proud of trying."
- Plan student agency: "Students propose a change to school life and adults take their reasoning seriously."
- Design regenerative action: "The school community treats the local creek as a living system we are responsible to."

## Common Pitfalls

1. **Starting with a slogan.** "Everyone belongs" is not yet an event. Translate it into visible evidence.
2. **Listing values without structures.** Values matter, but they need routines, artefacts, roles, and feedback loops.
3. **Ignoring current constraints.** Aspirational does not mean unrealistic.
4. **Putting the burden only on students.** Name adult and institutional structures too.
5. **Treating mental models as posters.** A new mental model becomes credible through repeated experience, not just words on a wall.

## Known Limitations

1. **Produces a design hypothesis, not a validated programme.** The aspirational iceberg and its supporting structures need testing through real classroom experiments before any claim of effectiveness can be made.
2. **May generate unreachable structures.** Some identified structures may be beyond the teacher's or students' sphere of control. Teacher judgement is needed to filter for feasibility before investing in full design.
3. **Degrades with vague aspirations.** "A welcoming class culture" is harder to design for than "a student who usually eats alone is invited to join a group by a peer without teacher prompting." The tool needs an observable, specific desired event to function well.
4. **Does not model time or capacity required.** The skill identifies what structures are needed but not how long they take to embed, how much staff capacity they require, or what must stop to make room for them.

## Verification Checklist

- [ ] The aspiration is stated as an observable event.
- [ ] At least five patterns/behaviours are named.
- [ ] Structures include routines, roles, artefacts, time, feedback, and support.
- [ ] Mental-model shifts are paired with experiences that could make them believable.
- [ ] The first experiment is small enough to try soon.
- [ ] The activity could be facilitated with students, not only adults.

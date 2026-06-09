---
# AGENT SKILLS STANDARD FIELDS (v2)
name: agency-circles-for-systems-action
description: "Map control, influence, and concern after systems analysis. Use when students need wise agency without being made responsible for everything."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "systems-thinking/agency-circles-for-systems-action"
skill_name: "Agency Circles for Systems Action"
domain: "systems-thinking"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Covey (1989) — The 7 Habits of Highly Effective People (circle of concern/influence)"
  - "Zimmerman (2002) — Becoming a self-regulated learner (agency and self-regulation)"
  - "Manyukhina & Wyse (2019) — Learner agency and the curriculum: a critical realist perspective"
  - "Meadows (2008) — Thinking in Systems (leverage points and systemic action)"
input_schema:
  required:
    - field: "system_issue_or_aspiration"
      type: "string"
      description: "The issue or aspiration students are considering"
    - field: "context"
      type: "string"
      description: "Class, school, community, ecological, or project context"
  optional:
    - field: "iceberg_or_system_map"
      type: "string"
      description: "Prior systems analysis to draw from"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "stakeholders"
      type: "array"
      description: "People or groups with roles in the system"
    - field: "constraints"
      type: "string"
      description: "Safety, authority, policy, time, or resource constraints"
output_schema:
  type: "object"
  fields:
    - field: "agency_map"
      type: "object"
      description: "Control, influence, collective influence, and concern zones"
    - field: "action_options"
      type: "array"
      description: "Safe action options matched to zones"
    - field: "adult_responsibility_flags"
      type: "array"
      description: "Issues that should not be placed on students"
    - field: "reflection_prompts"
      type: "array"
      description: "Prompts for agency without blame"
chains_well_with:
  - "systems-awareness-iceberg"
  - "aspirational-systems-iceberg"
  - "mental-model-mapper"
  - "agency-scaffold-generator"
  - "self-regulation-scaffold-generator"
  - "project-brief-designer"
teacher_time: "5 minutes"
tags: ["agency", "circle-of-control", "systems-action", "student-voice", "wellbeing", "influence", "collective-action"]
---

# Agency Circles for Systems Action

## What This Skill Does

Helps students and educators sort possible responses into what they can control, what they can influence, what requires collective or institutional action, and what remains a concern to name without carrying as personal responsibility. It adapts the Circle of Control / Influence / Concern tradition for compassionate systems work.

The key design move is to avoid over-individualising systemic problems. Students should not be told that a structural issue is simply their mindset problem. At the same time, systems thinking should not leave them overwhelmed. This skill turns analysis into wise agency: small actions, relationship-building, evidence-sharing, partnership, advocacy, and careful naming of constraints.

## Evidence Foundation

Covey popularised the circle of concern and circle of influence as a practical agency framework. Education research on learner agency cautions that agency is relational and structured, not just personal will. Meadows' leverage-point framework helps connect agency to system structures rather than isolated effort. The result is a tool for agency with humility: act where possible, influence with others, and name larger responsibilities truthfully.

## Input Schema

Required:
- **System issue or aspiration:** The issue students want to respond to, or the aspiration they want to grow.
- **Context:** Where this action might happen.

Optional:
- **Iceberg or system map:** Prior analysis.
- **Student level:** Age/year group.
- **Stakeholders:** Who has formal or informal power.
- **Constraints:** Authority, safety, policy, time, resources.

## Prompt

```text
You are helping students and/or educators translate systems analysis into wise agency using agency circles.

Inputs:
System issue or aspiration: {{system_issue_or_aspiration}}
Context: {{context}}
Iceberg/system map: {{iceberg_or_system_map}}
Student level: {{student_level}}
Stakeholders: {{stakeholders}}
Constraints: {{constraints}}

Rules:
1. Use four zones, not three:
   - Control: what students/teacher can directly do or choose.
   - Direct influence: what they can affect through relationship, evidence, modelling, invitation, or dialogue.
   - Collective/institutional influence: what requires adults, leaders, community partners, policy, money, or coordinated action.
   - Concern: what matters but is outside current influence; name it without pretending students must fix it.
2. Never place systemic responsibility only on students.
3. Connect each action to prior systems analysis: which pattern, structure, or mental model does it touch?
4. Prefer small safe experiments over heroic action.
5. Include wellbeing: acting should not require students to sacrifice safety, dignity, or belonging.
6. Include partnership: who needs to be invited, informed, or asked?

Return exactly:

## Agency Circles for Systems Action: [Issue/Aspiration]

**Context:** [brief]
**Important stance:** Agency is real, but responsibility is shared across the system.

### Circle 1: Direct Control
Things we can directly do or choose:
- **Action:** [specific]
  - **Touches:** [pattern/structure/mental model]
  - **Evidence of effect:** [what to notice]
  - **Safety check:** [risk]

### Circle 2: Direct Influence
Things we may influence through relationships, evidence, modelling, or dialogue:
- **Influence move:** [specific]
  - **Who is involved:** [stakeholder]
  - **How to approach:** [language/process]
  - **Evidence of effect:** [what to notice]

### Circle 3: Collective or Institutional Influence
Things that require partnership, adult authority, policy, resources, or coordination:
- **Collective move:** [specific]
  - **Who holds authority/resources:** [stakeholder]
  - **Student role:** [evidence, voice, proposal, participation]
  - **Adult/institutional responsibility:** [what adults must own]

### Circle 4: Concern to Name Without Carrying Alone
Things that matter but are not currently controllable:
- [Concern]
  - **Why it matters:** [reason]
  - **How to hold it:** [learn, name, witness, seek allies, avoid self-blame]

### Recommended First Step
[One low-risk action or experiment that fits the current sphere of control/influence]

### Reflection Prompts
- What are we taking responsibility for that is truly ours?
- What belongs to adults, leaders, institutions, or wider systems?
- What can we influence together that none of us can influence alone?
- What evidence would show that our action is helping rather than only making us feel busy?

Self-check: Do not tell students to fix structural harm alone. Include collective/institutional responsibility. Every action should be specific, safe, and connected to the system map.
```

## Common Pitfalls

1. **Making control too large.** Students cannot control other people's beliefs, policies, or resource allocation.
2. **Making influence too small.** Students can often influence through evidence, modelling, invitation, design, and collective voice.
3. **Confusing concern with apathy.** Naming concern can be honest and compassionate.
4. **Heroic individualism.** Systems action is usually collective and relational.
5. **Ignoring adult responsibility.** Some issues require adults to act.

## Known Limitations

1. **Cannot determine actual authority or access.** The skill provides general categories of control, influence, and concern, but the real sphere of action for a specific student, class, or teacher must be assessed locally. The output is a map, not a permission structure.
2. **Metacognitive demand.** With younger students, the distinction between collective influence and institutional responsibility may be difficult to communicate without significant adult scaffolding. The tool assumes some capacity for abstract self-reflection.
3. **Does not plan the action.** Agency circles identify zones and options; designing the actual action or project requires a subsequent step using project-brief-designer or agency-scaffold-generator.
4. **Risk of making structural harm feel manageable.** Sorting actions into circles can inadvertently imply that systemic problems are addressable through personal and small collective action. Teachers must explicitly name when structural change beyond student agency is required.

## Verification Checklist

- [ ] Four zones are used.
- [ ] Actions are specific and safe.
- [ ] Institutional responsibility is visible where appropriate.
- [ ] Student agency is real but bounded.
- [ ] The first step is small enough to try soon.
- [ ] The map reduces overwhelm rather than minimising the issue.

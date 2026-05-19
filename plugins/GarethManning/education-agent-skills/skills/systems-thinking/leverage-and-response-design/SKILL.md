---
# AGENT SKILLS STANDARD FIELDS (v2)
name: leverage-and-response-design
description: "Design a wise systems intervention from an existing analysis. Maps proposed actions against Meadows' leverage points, checks for unintended consequences, and generates alternatives."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "systems-thinking/leverage-and-response-design"
skill_name: "Leverage and Response Design"
domain: "systems-thinking"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Meadows (2008) — Thinking in Systems (leverage points hierarchy, 12 places to intervene)"
  - "Meadows (1999) — Leverage Points: Places to Intervene in a System"
  - "Senge (1990) — The Fifth Discipline (unintended consequences, systems archetypes)"
  - "Sterman (2000) — Business Dynamics (policy resistance, feedback loops)"
  - "Kim (1999) — Systems Archetypes (shifting the burden, fixes that fail, limits to growth)"
input_schema:
  required:
    - field: "systems_analysis"
      type: "string"
      description: "The systems analysis already done — iceberg, mental model map, agency circles output, or description of the system and its patterns"
    - field: "proposed_action"
      type: "string"
      description: "What students or educators are currently thinking of doing about the problem"
  optional:
    - field: "age_range"
      type: "string"
      description: "Student age range"
    - field: "scope_constraints"
      type: "string"
      description: "What students can realistically do (time, budget, authority, reach)"
    - field: "context"
      type: "string"
      description: "Community, school, or environmental context"
output_schema:
  type: "object"
  fields:
    - field: "leverage_assessment"
      type: "object"
      description: "Where the proposed action sits in Meadows' hierarchy and whether higher-leverage alternatives exist"
    - field: "alternative_responses"
      type: "array"
      description: "2-3 responses at different leverage levels, each with system effects, feedback loops, risks, and feasibility"
    - field: "unintended_consequences"
      type: "array"
      description: "Feedback loops the proposed action might trigger and systems archetypes to watch for"
    - field: "proportionality_check"
      type: "object"
      description: "Whether the response is proportionate to what students can actually influence"
    - field: "do_less_harm_check"
      type: "string"
      description: "Whether doing nothing or less is the wiser response in this case"
chains_well_with:
  - "systems-awareness-iceberg"
  - "agency-circles-for-systems-action"
  - "mental-model-mapper"
  - "compassionate-systems-awareness-orchestrator"
teacher_time: "10-15 minutes"
tags: ["systems-thinking", "leverage-points", "intervention-design", "unintended-consequences", "meadows", "feedback-loops", "action-design"]
---

# Leverage and Response Design

## What This Skill Does

Helps students and educators design a thoughtful intervention once they know where to act in a system. The skill fills the action gap in systems thinking: existing tools help students analyse systems (iceberg), surface assumptions (mental models, ladder of inference), and identify where they have agency (agency circles). This skill bridges analysis and action by asking: given what we know about the system, what response would be wise?

The key insight: in complex systems, the most obvious intervention is rarely the wisest. High-visibility actions (posters, petitions, one-off events) tend to target symptoms. Higher-leverage interventions target the structures, feedback loops, and mental models that produce the symptoms. This skill does not dismiss low-leverage action — sometimes it is the right and only available response — but it ensures students have considered the full range before choosing.

## Evidence Foundation

Meadows' 12 leverage points hierarchy (1999, 2008) provides the structural framework: interventions range from adjusting parameters (low leverage) through changing rules, information flows, and goals, up to shifting paradigms and transcending the system (high leverage). Meadows cautions that higher leverage does not always mean more accessible — paradigm shifts require different kinds of work than rule changes. Senge's systems archetypes (shifting the burden, fixes that fail, limits to growth) provide pattern recognition for common failure modes in intervention design. Sterman's work on policy resistance shows why well-intentioned interventions so often produce outcomes opposite to intent. Kim's Systems Archetypes toolkit gives practitioners language for naming these patterns in educational contexts.

## Input Schema

Required:
- **Systems analysis:** The prior systems work students have done — this could be an iceberg analysis, a mental model map, an agency circles output, or a description of the system and the patterns within it. The richer the prior analysis, the more specific the response design can be.
- **Proposed action:** What students are currently thinking of doing. This is the starting point for the leverage analysis, not the final answer.

Optional:
- **Age range:** Student age range, to calibrate complexity and language.
- **Scope constraints:** What students can realistically do given time, budget, authority, and reach.
- **Context:** Community, school, or environmental context.

## Prompt

```text
You are a systems thinking specialist with expertise in intervention design and unintended consequences, drawing on Meadows' leverage points hierarchy, Senge's systems archetypes, and Sterman's work on policy resistance.

Inputs:
Systems analysis: {{systems_analysis}}
Proposed action: {{proposed_action}}
Age range: {{age_range}}
Scope constraints: {{scope_constraints}}
Context: {{context}}

Use these rules:

1. MAP THE PROPOSED ACTION against Meadows' leverage points hierarchy. Identify where it sits:
   - Parameters (numbers, sizes, flows) — lowest leverage
   - Buffers and stocks
   - Stock-and-flow structures
   - Delays
   - Balancing feedback loops
   - Reinforcing feedback loops
   - Information flows
   - Rules (incentives, constraints, regulations)
   - Self-organisation (power to change the system structure)
   - Goals
   - Paradigms (shared assumptions, goals, values)
   - Transcendence — highest leverage
   
   Ask: Is there a higher-leverage intervention available that is within the students' scope? Does the proposed action target symptoms or the structures that produce them?

2. ANALYSE FOR UNINTENDED CONSEQUENCES using systems archetypes:
   - Shifting the burden: Does the proposed action make the symptom more comfortable, reducing pressure to address the root cause?
   - Fixes that fail: Does the proposed action trigger a delayed negative side effect that cancels the benefit?
   - Limits to growth: What feedback loop will eventually limit the effect of the proposed action?
   - What reinforcing loops might the action trigger? What balancing loops might push back?

3. GENERATE 2-3 ALTERNATIVE OR REFINED RESPONSES at different leverage levels. For each:
   - What it changes in the system (which leverage point it targets)
   - What feedback loops it creates or disrupts
   - What could go wrong (unintended consequences, archetype risks)
   - What makes it more or less feasible for these students in this context

4. PROPORTIONALITY CHECK for each response option:
   - Is this response proportionate to what students can actually influence?
   - Does it place systemic burdens (emotional, civic, logistical) on young people that belong to adults, institutions, or wider society?
   - If the intervention is disproportionate to student power, say so clearly and redirect toward appropriately scaled action.

5. DO LESS HARM CHECK:
   - Is doing nothing or doing less actually the wisest response in this case?
   - Sometimes the best systems response is observation, understanding, and honest naming rather than intervention.
   - Are there reasons why acting now, with current information, might cause more harm than good?

Self-check: Am I helping students think carefully about intervention, or am I just helping them plan a more elaborate version of their first idea? Have I considered that the wisest response might be smaller, not bigger? Have I checked whether the proposed action risks 'shifting the burden' away from structural accountability?

Return exactly:

## Leverage and Response Design: [Brief system/issue label]

**Prior analysis summary:** [One-sentence synthesis of the systems analysis provided]
**Proposed action:** [Restate the proposed action clearly]

### Leverage Assessment
- **Leverage level of proposed action:** [Which of Meadows' levels it targets]
- **What it changes:** [Which system element it affects]
- **What it does not change:** [Structures or mental models the action leaves untouched]
- **Higher-leverage alternatives to consider:** [Yes/No — if yes, identified below]

### Unintended Consequence Analysis
- **Archetype risks:**
  - [Archetype name]: [How it might operate here]
- **Feedback loops triggered:**
  - [Loop]: [What it reinforces or balances]
- **Policy resistance risk:** [How the system might push back against the action]

### Response Options

**Option 1: [Name — e.g. the proposed action, refined]**
- Targets: [leverage level]
- System effect: [what changes]
- Feedback loop created: [reinforcing or balancing]
- What could go wrong: [specific risk]
- Feasibility: [honest assessment for these students]

**Option 2: [Name — e.g. higher-leverage alternative]**
- Targets: [leverage level]
- System effect: [what changes]
- Feedback loop created: [reinforcing or balancing]
- What could go wrong: [specific risk]
- Feasibility: [honest assessment for these students]

**Option 3: [Name — e.g. lower-leverage but more accessible]**
- Targets: [leverage level]
- System effect: [what changes]
- Feedback loop created: [reinforcing or balancing]
- What could go wrong: [specific risk]
- Feasibility: [honest assessment for these students]

### Proportionality Check
[Is each option proportionate to student power? Are any interventions placing structural responsibility on students that belongs elsewhere?]

### Do Less Harm Check
[Is acting now, with current knowledge, wiser than observing and naming? What evidence would justify action over continued inquiry?]

### Recommended Next Step
[One specific, proportionate, well-reasoned first action or decision point]
```

## Common Pitfalls

1. **Treating the first idea as the plan.** Students' initial proposals are usually parameter-level interventions on a symptom. The skill should expand thinking before returning to action, not just validate the first idea with systems language.
2. **Conflating higher leverage with better.** Paradigm-level change is higher leverage but also harder, slower, and less accessible. Match ambition to real capacity.
3. **Omitting the do-less-harm option.** It feels like failure to recommend doing less. It is often the most systems-sophisticated response.
4. **Burden-shifting to students.** Climate education, social justice work, and community resilience projects can inadvertently ask young people to fix structural problems. The proportionality check must name when adult and institutional responsibility is being misplaced.
5. **Ignoring feedback loops.** Listing what an action changes without asking what the system does next is not systems thinking — it is optimistic planning.

## Verification Checklist

- [ ] The proposed action is mapped against Meadows' leverage points.
- [ ] At least two unintended consequence pathways are named.
- [ ] 2-3 response options are offered at different leverage levels.
- [ ] Each option includes what could go wrong.
- [ ] The proportionality check names whether the response is appropriate for students to own.
- [ ] The do-less-harm check is completed honestly.
- [ ] The recommended next step is specific and feasible.

## Known Limitations

1. **Cannot predict actual system behaviour.** All intervention analysis is based on simplified models of complex systems. The leverage points framework is a heuristic for thinking, not a physics of social change.
2. **Higher-leverage does not always mean better.** Meadows herself emphasised that leverage points are also places where systems resist intervention most fiercely. The hierarchy describes potential impact, not ease of change.
3. **Students may find it discouraging.** Analysis revealing that a proposed action has limited leverage can feel deflating. The skill should normalise this as a feature of systems thinking, not a failure of the students or their idea.
4. **Proportionality is a judgment call the skill cannot make.** Whether an intervention is appropriate for students of a given age requires teacher judgment about emotional and developmental readiness, not just systemic analysis.

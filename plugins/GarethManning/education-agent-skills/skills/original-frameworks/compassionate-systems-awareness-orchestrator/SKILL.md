---
# AGENT SKILLS STANDARD FIELDS (v2)
name: compassionate-systems-awareness-orchestrator
description: "Orchestrate compassionate systems tools from issue or aspiration to wise action. Use when a class needs a complete inquiry workflow."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "original-frameworks/compassionate-systems-awareness-orchestrator"
skill_name: "Compassionate Systems Awareness Orchestrator"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Center for Systems Awareness (2022) — Compassionate Systems Framework and tools practitioner resources"
  - "Senge (1990) — The Fifth Discipline (systems thinking and learning organisations)"
  - "Meadows (2008) — Thinking in Systems (structures, feedback, leverage points)"
  - "Argyris (1990) — Ladder of inference and defensive reasoning"
  - "Covey (1989) — Circle of concern and influence as agency framing"
input_schema:
  required:
    - field: "starting_point"
      type: "string"
      description: "The current issue, aspiration, place-based concern, project idea, or class culture focus"
    - field: "context"
      type: "string"
      description: "Class, school, community, ecological, or curriculum context"
    - field: "intended_use"
      type: "string"
      description: "Student lesson, teacher planning, project design, staff inquiry, or community action"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "available_time"
      type: "string"
      description: "Single lesson, sequence, project, staff meeting, or unit"
    - field: "prior_evidence"
      type: "string"
      description: "Existing data, stories, observations, or student work"
    - field: "safety_sensitivities"
      type: "string"
      description: "Conflict, trauma, identity, power, or safeguarding considerations"
output_schema:
  type: "object"
  fields:
    - field: "workflow"
      type: "object"
      description: "Recommended sequence of discrete compassionate systems tools"
    - field: "handoff_outputs"
      type: "array"
      description: "Outputs each step should pass to the next step"
    - field: "lesson_sequence"
      type: "object"
      description: "Teacher-usable sequence"
    - field: "stop_or_slow_down_checks"
      type: "array"
      description: "Decision gates before action"
chains_well_with:
  - "systems-awareness-iceberg"
  - "aspirational-systems-iceberg"
  - "mental-model-mapper"
  - "agency-circles-for-systems-action"
  - "ladder-of-inference-reflection"
  - "place-based-inquiry-anchor"
  - "project-brief-designer"
teacher_time: "5 minutes"
tags: ["orchestrator", "composite-framework", "practitioner-framework", "compassionate-systems", "systems-thinking", "classroom-inquiry", "student-agency", "regenerative", "workflow"]
---

# Compassionate Systems Awareness Orchestrator

## What This Skill Does

Sequences the compassionate systems awareness tools into a coherent teacher-usable workflow. The orchestrator makes pathway options visible before committing to a route, then helps the educator choose which tool to use first, what output should be passed forward, when to stop for evidence or safety, and how to move from systems understanding to wise action without collapsing into blame, vague empathy, or superficial projects.

Use this when the task is larger than one tool: a class wants to understand a recurring issue, design a desired culture, investigate a local system, or plan a regenerative/action project. The orchestrator should not duplicate the discrete skills. It coordinates them.

## Evidence Foundation

The workflow draws from the Center for Systems Awareness and Compassionate Systems Framework, combining the iceberg, mental models, reflective dialogue tools, and agency/action framing. It also uses systems-thinking principles from Senge and Meadows: behaviour emerges from structures and mental models, and effective action requires attention to leverage, feedback, and unintended consequences.

## Evidence Space and Strength of Evidence

This is a composite practitioner framework. It coordinates several evidence-informed pedagogical traditions, but the exact pathway architecture has not yet been directly evaluated as a complete intervention. Use it as a curriculum-design scaffold, not as a claim that this sequence reliably produces specified outcomes.

### Component Evidence

- **Systems Awareness Iceberg** (moderate): practitioner-developed by the Center for Systems Awareness, consistent with Senge (1990) and Meadows (2008). In classroom use by systems thinking educators; no direct RCT evidence.
- **Aspirational Systems Iceberg** (emerging): practitioner resource from the Center for Systems Awareness; limited classroom research evidence but theoretically grounded.
- **Mental Model Mapper** (moderate): grounded in Argyris & Schön (1974), Senge (1990), and Meadows (2008). Strong theoretical basis; application to K-12 classroom settings is practitioner-led.
- **Ladder of Inference** (moderate): Argyris (1990); used in organisational learning, coaching, and dialogue settings. Classroom adaptation is practitioner-led.
- **Agency Circles for Systems Action** (moderate): adapted from Covey (1989); supported by learner agency research (Manyukhina & Wyse, 2019) and Meadows' leverage-point framing.

### Synthesis Evidence

The complete orchestration sequence — including pathway menus, routing logic, handoff structure, and quality gates — is an original synthesis by Gareth Manning. It should be treated as emerging evidence until tested with real educators and revised from classroom use.

### What This Skill Should Not Claim

Do not claim that this framework has been validated as a programme, intervention, or guaranteed route to improved student outcomes. Do not use it to bypass teacher judgement, local knowledge, cultural protocols, learner needs, or safety checks.

### Appropriate Use

Use this skill as a design scaffold for planning, reflection, pathway selection, and curriculum coherence. It is most appropriate when an educator needs help choosing among plausible design routes and understanding the tradeoffs of each.

## Dependency Maintenance

This skill depends on the five discrete systems-thinking tools listed above. Review this orchestrator whenever any chained skill changes its evidence strength, output schema, core quality gates, or major cautions. Do not strengthen the evidence claim of this composite framework unless the composite workflow itself has been tested. If a component skill is deprecated or substantially revised, this orchestration pathway must be reviewed before use.

## Input Schema

Required:
- **Starting point:** Current issue or aspiration.
- **Context:** Where it happens.
- **Intended use:** Student lesson, teacher planning, project design, staff inquiry, community action.

Optional:
- **Student level:** Age/year group.
- **Available time:** Time available.
- **Prior evidence:** Existing observations, student work, surveys, photos, stories.
- **Safety sensitivities:** Conflict, trauma, power, identity, safeguarding.

## Prompt

```text
You are orchestrating a compassionate systems awareness workflow. First make the possible pathways visible to the educator. Do not assume the educator knows which pathway fits. If a pathway is not already selected, present options, recommend a best fit with assumptions, and ask the educator to choose before producing a full workflow. If the user explicitly asks for a full workflow immediately, proceed with the recommended pathway and label it provisional.

Choose and sequence the appropriate discrete tools. Do not use every tool by default. Select the smallest coherent pathway that fits the starting point, time, and safety context.

Inputs:
Starting point: {{starting_point}}
Context: {{context}}
Intended use: {{intended_use}}
Student level: {{student_level}}
Available time: {{available_time}}
Prior evidence: {{prior_evidence}}
Safety sensitivities: {{safety_sensitivities}}

Available tools:
- systems-awareness-iceberg: use when starting from an undesirable/current event or recurring issue.
- aspirational-systems-iceberg: use when starting from a desired event or future to grow.
- mental-model-mapper: use when assumptions, beliefs, stories, values, or paradigms need deeper examination.
- ladder-of-inference-reflection: use when a conflict or interpretation needs slowing down.
- agency-circles-for-systems-action: use after analysis to locate control, influence, collective influence, and concern.
- place-based-inquiry-anchor: use when a specific local place should become the primary text.
- project-brief-designer or agency-scaffold-generator: use when the inquiry needs to become a student project or agency scaffold.

Decision rules:
1. Always present pathway options before committing to a workflow unless the educator has already selected a pathway.
2. If the starting point is "what is wrong / why does this keep happening?" recommend the Current Problem to Wise Response pathway, usually beginning with systems-awareness-iceberg.
3. If the starting point is "what do we want to grow?" recommend the Desired Culture / Aspirational Future pathway, usually beginning with aspirational-systems-iceberg.
4. If the starting point is a wellbeing or pastoral pattern, recommend the Systems-Aware Wellbeing pathway and consider belonging, restorative, trauma-informed, or emotional-literacy skills as adjacent supports.
5. If the starting point is a place, ecological system, or regenerative project, recommend the Place / Regenerative Systems pathway and chain with place-based or regenerative orchestrators only if useful.
6. If strong interpretations, blame, conflict, or identity threat are present, insert ladder-of-inference before public systems mapping.
7. If mental models are central or underdeveloped, insert mental-model-mapper after the iceberg.
8. Always use agency-circles before action if students are asked to respond to a systemic issue.
9. Do not proceed to action if the group lacks evidence, authority, safety, or adult support.
10. Keep the pathway small enough for the available time.

Return exactly:

## Compassionate Systems Awareness Pathway Options

Present these options before choosing unless a pathway has already been selected:
- **Current Problem to Wise Response:** for recurring issues or undesired events.
- **Desired Culture / Aspirational Future:** for designing a wanted pattern.
- **Systems-Aware Wellbeing:** for belonging, help-seeking, conflict, feedback culture, digital wellbeing, or pastoral patterns.
- **Place / Regenerative Systems:** for place-based, ecological, civic, or social-ecological issues where CSA tools may support another orchestrator.

State the recommended pathway, why it fits, and one viable alternative if relevant. If no pathway is selected, ask which pathway to develop.

## Compassionate Systems Awareness Workflow: [Starting Point]

**Context:** [brief]
**Intended use:** [lesson/planning/project/staff inquiry]
**Recommended pathway:** [short list of tools in order]

### Why This Pathway
[Explain why these tools, and why this order]

### Step-by-Step Sequence
For each step:
**Step [N]: [Tool Name]**
- **Purpose:** [what this step does]
- **Teacher/student prompt:** [prompt to use]
- **Output to capture:** [exact handoff output]
- **Do not proceed if:** [safety/evidence/quality gate]
- **Feeds into:** [next tool]

### Handoff Map
- From [tool] pass [output] to [tool].
- From [tool] pass [output] to [tool].

### Lesson or Workshop Shape
Adapt to time available:
- **Opening:** [grounding/check-in/framing]
- **Main mapping:** [tool sequence]
- **Sensemaking:** [discussion/gallery walk/synthesis]
- **Agency/action:** [circle or first experiment]
- **Reflection:** [closing prompts]

### Stop or Slow Down Checks
- [ ] Are we blaming individuals for structural patterns?
- [ ] Are students being asked to carry adult/institutional responsibility?
- [ ] Do we have enough evidence to act?
- [ ] Could this activity expose students to identity, trauma, or peer harm?
- [ ] Is the proposed action inside real control or influence?
- [ ] Have we named who else must be involved?

### Expected Final Output
[Describe the final artefact: iceberg map, aspirational iceberg, mental-model map, agency circles, first experiment, project brief, etc.]

Self-check: The workflow must be coherent, not maximal. It must preserve compassion and systems depth. It must end with bounded agency, not heroic fixing.
```

## Common Pathways

### Current problem to wise response
1. Ladder of inference if interpretation/conflict is hot.
2. Systems awareness iceberg.
3. Mental model mapper.
4. Agency circles.
5. First safe experiment.

### Desired class culture to first experiment
1. Aspirational systems iceberg.
2. Mental model mapper.
3. Agency circles.
4. Agency scaffold or project brief.

### Place-based regenerative inquiry
1. Place-based inquiry anchor.
2. Systems awareness or aspirational iceberg.
3. Mental model mapper focused on human-nature relationships.
4. Agency circles.
5. Project brief.

## Common Pitfalls

1. **Using all tools every time.** Orchestration means choosing the necessary path.
2. **Moving to action too early.** Analysis first; agency second.
3. **Staying in analysis forever.** Bounded experiments help learning continue.
4. **Ignoring safety.** Public mapping can expose conflict or identity harm if poorly facilitated.
5. **Confusing aspiration with solution.** Aspirational icebergs still need structures and evidence.

## Known Limitations

1. **Cannot assess local conditions.** This orchestrator coordinates tool selection but cannot replace teacher knowledge of specific students, classroom dynamics, community trauma history, or cultural protocols — pathway appropriateness depends entirely on local conditions the orchestrator cannot assess.
2. **Not a feedback loop.** The pathway is presented as a sequence, but classroom systems inquiry is recursive. In practice, a class may need to return to earlier tools as new evidence or conflict emerges. The orchestrator provides a starting map, not a dynamic workflow.
3. **Degrades with vague starting points.** "Improve classroom culture" is too broad to route effectively. The orchestrator works best when the starting point names a specific recurring issue or a clearly stated desired event.
4. **Produces a plan, not the outputs.** The orchestrator sequences the discrete tools but does not run them. Using this skill without then running each discrete tool produces only a pathway outline — not actual iceberg maps, mental model maps, or agency circles.

## Verification Checklist

- [ ] The pathway begins with the right kind of iceberg or reflection tool.
- [ ] Each step has a handoff output.
- [ ] Stop/slow checks are explicit.
- [ ] Student agency is bounded and supported.
- [ ] Teacher/institutional responsibility is not hidden.
- [ ] The final output is practical enough for a real teacher to use.

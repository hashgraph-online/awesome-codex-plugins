---
# AGENT SKILLS STANDARD FIELDS (v2)
name: regenerative-project-design-orchestrator
description: "Present project-design pathway options and orchestrate regenerative projects using backwards design, PBL, SEEDS, compassionate systems action, or civic/service pathways."
disable-model-invocation: false
user-invocable: true
effort: high

# EXISTING FIELDS
skill_id: "original-frameworks/regenerative-project-design-orchestrator"
skill_name: "Regenerative Project Design Orchestrator"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Wiggins & McTighe (2005) — Understanding by Design"
  - "Larmer, Mergendoller & Boss (2015) — Gold Standard Project Based Learning"
  - "Manning (2025) — SEEDS regenerative inquiry cycle and regenerative learning design"
  - "Kimmerer (2013) — Braiding Sweetgrass (reciprocity and care)"
  - "Meadows (2008) — Thinking in Systems (leverage, feedback, unintended consequences)"
input_schema:
  required:
    - field: "project_intent"
      type: "string"
      description: "What the educator wants students to design, improve, investigate, regenerate, or contribute to"
    - field: "learner_stage"
      type: "string"
      description: "Age range or year group"
  optional:
    - field: "curriculum_goals"
      type: "string"
      description: "Required content, standards, competencies, or assessment goals"
    - field: "system_or_context"
      type: "string"
      description: "The classroom, school, community, ecological, social, digital, or institutional system involved"
    - field: "time_available"
      type: "string"
      description: "Lesson sequence, project week, term, semester, or year"
    - field: "community_or_adult_partners"
      type: "string"
      description: "Adults, community groups, experts, or institutions who should be involved"
    - field: "constraints"
      type: "string"
      description: "Assessment, safety, permission, resources, power, or implementation constraints"
    - field: "pathway_choice"
      type: "string"
      description: "Optional selected project pathway. If absent, present options before designing the full project."
output_schema:
  type: "object"
  fields:
    - field: "pathway_options"
      type: "array"
      description: "Project pathway menu with fit, outputs, and tradeoffs"
    - field: "recommended_pathway"
      type: "object"
      description: "Best-fit pathway recommendation with assumptions and alternatives"
    - field: "orchestrated_skill_chain"
      type: "array"
      description: "Selected skills in order with handoff outputs"
    - field: "project_design"
      type: "object"
      description: "The resulting regenerative project sequence once a pathway is selected"
    - field: "regenerative_quality_gates"
      type: "array"
      description: "Checks for reciprocity, stewardship, bounded agency, feasibility, and unintended consequences"
chains_well_with:
  - "backwards-design-unit-planner"
  - "project-brief-designer"
  - "self-determined-project-design-protocol"
  - "seeds-regenerative-inquiry-cycle"
  - "agency-scaffold-generator"
  - "service-learning-project-designer"
  - "systems-awareness-iceberg"
  - "aspirational-systems-iceberg"
  - "agency-circles-for-systems-action"
  - "assessment-validity-checker"
teacher_time: "8 minutes"
tags: ["orchestrator", "composite-framework", "practitioner-framework", "regenerative", "emerging-evidence", "project-design", "PBL", "backwards-design", "SEEDS", "service-learning", "student-agency"]
---

# Regenerative Project Design Orchestrator

## What This Skill Does

This orchestrator designs projects whose aim is not only to produce a product or presentation, but to contribute to the health, capacity, or flourishing of a system. The system might be ecological, social, cultural, classroom-based, digital, institutional, or community-based.

It is model-agnostic. It can route to backwards design, project-based learning, SEEDS, compassionate systems action, or service/civic action. It should not assume SEEDS is always the right model, and it should not assume a conventional PBL structure is always sufficient.

## Evidence Space and Strength of Evidence

This is a composite practitioner framework. It coordinates several evidence-informed pedagogical traditions, but the exact pathway architecture has not yet been directly evaluated as a complete intervention. Use it as a curriculum-design scaffold, not as a claim that this sequence reliably produces specified outcomes.

### Component Evidence

- **Backwards Design / Understanding by Design** (strong): Wiggins & McTighe (2005) is widely researched and used in curriculum planning. Strong evidence base for curriculum alignment and assessment validity.
- **Project-Based Learning** (moderate-strong): Larmer, Mergendoller & Boss (2015) Gold Standard PBL has a substantial research base showing benefits for engagement, deeper learning, and skill development in well-implemented contexts.
- **SEEDS Regenerative Inquiry** (emerging/original): Manning (2025) is a practitioner framework. Theoretically grounded in Kimmerer (2013) and Meadows (2008) but has not been independently evaluated as a classroom programme.
- **Compassionate Systems Action** (emerging): see evidence ratings for systems-awareness-iceberg and agency-circles-for-systems-action. The composite application to project design is practitioner-synthesised.
- **Service / Civic Learning** (moderate): a substantial literature supports service-learning benefits for civic engagement and learning; effects depend heavily on quality, framing, and community reciprocity.

### Synthesis Evidence

The orchestration pathway — including the five named pathway options, routing logic, handoff structure, and regenerative quality gates — is an original synthesis by Gareth Manning. It should be treated as emerging evidence until tested with real educators and revised from classroom use.

### What This Skill Should Not Claim

Do not claim that this framework has been validated as a regenerative education programme or guaranteed route to improved student or ecological outcomes. Do not use it to bypass teacher judgement, community relationships, cultural protocols, or assessment validity requirements.

### Appropriate Use

Use this skill as a design scaffold for project planning and pathway selection. It is most appropriate when an educator needs help choosing among plausible project design routes and understanding the tradeoffs before committing to a full project sequence.

## Dependency Maintenance

This skill depends on backwards-design-unit-planner, project-brief-designer, seeds-regenerative-inquiry-cycle, systems-awareness-iceberg, aspirational-systems-iceberg, agency-circles-for-systems-action, service-learning-project-designer, and assessment-validity-checker. Review this orchestrator whenever any chained skill changes its evidence strength, output schema, core quality gates, or major cautions. Do not strengthen the evidence claim of this composite framework unless the composite workflow itself has been tested. If a component skill is deprecated or substantially revised, this orchestration pathway must be reviewed before use.

## Pathway Principle

Before designing the project, present pathway options. The educator may not know the difference between a backwards-designed project, a PBL inquiry, a SEEDS cycle, a compassionate systems action project, or a civic/service project. The orchestrator should make those options visible and recommend a route.

If `pathway_choice` is absent, return the pathway menu and recommendation first. If the user explicitly requests a full design immediately, proceed provisionally with the recommended pathway.

## Pathway Options

### 1. Backwards Design Project
Use when learning outcomes and assessment requirements are fixed. Best when curriculum coherence, evidence of learning, and validity matter strongly.

Typical chain: `backwards-design-unit-planner` → `project-brief-designer` → `criterion-referenced-rubric-generator` or `coherent-rubric-logic-builder` → `assessment-validity-checker`.

### 2. Project-Based Learning / Inquiry Project
Use when the project needs a driving question, student inquiry, critique/revision, public product, and authentic audience.

Typical chain: `project-brief-designer` → `learning-target-authoring-guide` → `formative-assessment-technique-selector` → `assessment-validity-checker`.

### 3. SEEDS Regenerative Inquiry
Use when place, ecology, care, stewardship, and continuation are central. This pathway begins with Sense and ends with Design to Last and Share.

Typical chain: `seeds-regenerative-inquiry-cycle` → optional `ecological-inquiry-anchor-designer` → `dispositional-knowledge-assessment-designer`.

### 4. Compassionate Systems Action Project
Use when the project is about social, wellbeing, cultural, or institutional patterns: belonging, help-seeking, feedback culture, peer norms, school routines, or conflict.

Typical chain: `systems-awareness-iceberg` or `aspirational-systems-iceberg` → `mental-model-mapper` → `agency-circles-for-systems-action` → `agency-scaffold-generator`.

### 5. Civic / Service Learning Project
Use when students are working with community needs, public issues, service, advocacy, or civic participation. Requires reciprocity and adult/community partnership.

Typical chain: `service-learning-project-designer` → `place-based-inquiry-anchor` if local → `agency-scaffold-generator` → `assessment-validity-checker`.

## Prompt

```text
You are a regenerative project design orchestrator. Your job is to help the educator choose a project design pathway before building the full project.

Inputs:
Project intent: {{project_intent}}
Learner stage: {{learner_stage}}
Curriculum goals: {{curriculum_goals}}
System/context: {{system_or_context}}
Time available: {{time_available}}
Community/adult partners: {{community_or_adult_partners}}
Constraints: {{constraints}}
Pathway choice: {{pathway_choice}}

Step 1: Present the five pathway options:
- Backwards Design Project
- Project-Based Learning / Inquiry Project
- SEEDS Regenerative Inquiry
- Compassionate Systems Action Project
- Civic / Service Learning Project

For each option, explain what it is for, what it produces, when to choose it, and when not to choose it.

Step 2: Recommend the best-fit pathway. Explain why and name the assumptions behind the recommendation. Include at least one viable alternative if there is one.

Step 3: If no pathway_choice was provided, ask the educator to choose before producing the full project design. If a full design is explicitly requested, proceed with the recommended pathway and label it provisional.

Step 4: Once a pathway is selected, create an orchestrated skill chain. For every skill, name:
- purpose
- input needed
- output produced
- handoff to next skill
- do-not-proceed-if check

Step 5: Produce the project design with regenerative quality gates. The project should avoid heroic student-fixer narratives and should distinguish student agency from adult/institutional responsibility.

Return:

## Regenerative Project Pathway Options
[Menu with recommendation and choice prompt if needed]

## Recommended Pathway
[Best fit, assumptions, alternatives]

## Orchestrated Skill Chain
[Step-by-step skill sequence and handoffs]

## Regenerative Project Design
[Only if pathway selected or provisional design requested]

## Regenerative Quality Gates
- [ ] Does the project increase capacity for the system to thrive, rather than only reduce harm or produce a display?
- [ ] Are students learning before acting?
- [ ] Is action bounded by real control, influence, or supported collective influence?
- [ ] Are adult/community responsibilities named?
- [ ] Are unintended consequences anticipated?
- [ ] Is there a stewardship, handoff, maintenance, or continuation plan where needed?
- [ ] Does assessment measure the intended learning, not just the attractiveness of the final product?
```

## Common Pitfalls

1. Forcing SEEDS when the teacher mainly needs curriculum-aligned backwards design.
2. Forcing conventional PBL when the project needs stewardship and long-term care.
3. Treating “regenerative” as a vibe rather than a testable design standard.
4. Asking students to fix adult or institutional failures without authority or support.
5. Skipping assessment validity because the project feels authentic.
6. Confusing a public product with genuine impact.

## Known Limitations

1. **Regenerative intent is not a regenerative outcome.** This orchestrator designs projects aimed at contributing to system health — whether outcomes are actually regenerative depends on implementation, adult support, community conditions, and sustained effort beyond this skill's reach.
2. **Cannot assess student readiness.** The skill does not evaluate whether students have the prior knowledge, skills, or emotional readiness for the chosen pathway. That requires teacher diagnostic judgement or a prior assessment step.
3. **Produces a plan, not the skills outputs.** Each pathway chains to other discrete skills (seeds-regenerative-inquiry-cycle, systems-awareness-iceberg, project-brief-designer, etc.) that must be run separately. The orchestrator provides the sequence and handoff logic, not the full project design.
4. **Regenerative quality gates are advisory.** The skill cannot enforce the quality gates it identifies — a teacher can proceed with a project that fails them. The gates require teacher and institutional commitment to mean anything.

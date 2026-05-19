---
# AGENT SKILLS STANDARD FIELDS (v2)
name: place-based-curriculum-orchestrator
description: "Present pathway options and orchestrate place-based curriculum design from a local place, curriculum requirement, or community issue. Use when place should become a primary text for learning."
disable-model-invocation: false
user-invocable: true
effort: high

# EXISTING FIELDS
skill_id: "original-frameworks/place-based-curriculum-orchestrator"
skill_name: "Place-Based Curriculum Orchestrator"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Sobel (2004) — Place-Based Education: connecting classrooms and communities"
  - "Smith (2002) — Place-based education: learning to be where we are"
  - "Gruenewald (2003) — The best of both worlds: a critical pedagogy of place"
  - "Castagno & Brayboy (2008) — Culturally responsive schooling for Indigenous youth"
  - "Bang, Medin & Atran (2007) — Cultural mosaics and mental models of nature"
input_schema:
  required:
    - field: "starting_point"
      type: "string"
      description: "The place, curriculum requirement, community question, or local issue the educator is starting from"
    - field: "learner_stage"
      type: "string"
      description: "Age range or year group"
  optional:
    - field: "subject_or_curriculum_content"
      type: "string"
      description: "Curriculum content, standards, competencies, or disciplines that need to be addressed"
    - field: "local_place"
      type: "string"
      description: "Specific place: creek, high street, park, school grounds, neighbourhood, building, food system, etc."
    - field: "community_knowledge_holders"
      type: "string"
      description: "People, groups, Elders, organisations, or local experts who know the place"
    - field: "constraints"
      type: "string"
      description: "Time, access, safety, transport, permission, assessment, policy, or resource constraints"
    - field: "pathway_choice"
      type: "string"
      description: "Optional selected pathway. If absent, present options before designing the full sequence."
output_schema:
  type: "object"
  fields:
    - field: "pathway_options"
      type: "array"
      description: "Menu of suitable pathways with when-to-use notes and tradeoffs"
    - field: "recommended_pathway"
      type: "object"
      description: "Best-fit pathway recommendation with assumptions; should not hide alternatives"
    - field: "orchestrated_skill_chain"
      type: "array"
      description: "Discrete skills to use in order with handoff outputs"
    - field: "curriculum_design_sequence"
      type: "object"
      description: "Teacher-usable place-based unit or lesson sequence once pathway is selected"
    - field: "stop_slow_checks"
      type: "array"
      description: "Checks for ethics, safety, cultural humility, curriculum validity, and feasibility"
chains_well_with:
  - "place-based-inquiry-anchor"
  - "ecological-inquiry-anchor-designer"
  - "phenomenon-based-unit-anchor"
  - "culturally-responsive-teaching-designer"
  - "curriculum-knowledge-architecture-designer"
  - "learning-target-authoring-guide"
  - "assessment-validity-checker"
  - "systems-awareness-iceberg"
  - "mental-model-mapper"
teacher_time: "8 minutes"
tags: ["orchestrator", "composite-framework", "practitioner-framework", "place-based", "emerging-evidence", "curriculum", "pathways", "local", "community", "critical-pedagogy-of-place"]
---

# Place-Based Curriculum Orchestrator

## What This Skill Does

This orchestrator helps an educator design curriculum where a specific local place becomes a primary text for learning. It does not assume the educator already knows which place-based pathway fits. Before making a full design decision, it presents pathway options, recommends the best fit, explains tradeoffs, and asks for a pathway choice unless the user has already chosen one.

Use this when learning should be grounded in a creek, street, school ground, garden, neighbourhood, building, memorial, food system, local industry, community story, or other real place. The place should not be decorative. It should shape the questions, evidence, knowledge holders, learning activities, and possible action.

## Evidence Space and Strength of Evidence

This is a composite practitioner framework. It coordinates several evidence-informed pedagogical traditions, but the exact pathway architecture has not yet been directly evaluated as a complete intervention. Use it as a curriculum-design scaffold, not as a claim that this sequence reliably produces specified outcomes.

### Component Evidence

- **Place-Based Education** (moderate): Sobel (2004), Smith (2002), and Gruenewald (2003) provide a solid theoretical and practitioner literature base. Research shows benefits for engagement and local connection; experimental evidence is limited.
- **Culturally Responsive Pedagogy** (moderate): Castagno & Brayboy (2008) and Bang, Medin & Atran (2007) establish the importance of cultural framing in place-based and ecological inquiry. Well-evidenced in Indigenous education contexts.
- **Critical Pedagogy of Place** (moderate): Gruenewald (2003) integrates critique with place-based learning; educational research supports but direct classroom effect studies are limited.
- **Component skills** (varies): place-based-inquiry-anchor, ecological-inquiry-anchor-designer, curriculum-knowledge-architecture-designer, and assessment-validity-checker each carry their own evidence ratings.

### Synthesis Evidence

The orchestration pathway — including the five named pathway options, routing logic, handoff structure, and stop/slow checks — is an original synthesis by Gareth Manning. It should be treated as emerging evidence until tested with real educators and revised from classroom use.

### What This Skill Should Not Claim

Do not claim that this framework has been validated as a curriculum programme or guaranteed route to improved outcomes. Do not use it to bypass teacher judgement, local knowledge, cultural protocols, community relationships, or assessment validity checks.

### Appropriate Use

Use this skill as a design scaffold for place-based curriculum planning. It is most appropriate when an educator needs help choosing among plausible design routes and understanding the tradeoffs of each before investing in full unit design.

## Dependency Maintenance

This skill depends on place-based-inquiry-anchor, ecological-inquiry-anchor-designer, curriculum-knowledge-architecture-designer, culturally-responsive-teaching-designer, learning-target-authoring-guide, and assessment-validity-checker. Review this orchestrator whenever any chained skill changes its evidence strength, output schema, core quality gates, or major cautions. Do not strengthen the evidence claim of this composite framework unless the composite workflow itself has been tested. If a component skill is deprecated or substantially revised, this orchestration pathway must be reviewed before use.

## Pathway Principle

A place-based orchestrator should route, not bulldoze. It should make the available pathways visible to the educator so they can choose consciously.

If `pathway_choice` is not provided, return the **Pathway Options Menu** first, plus a recommended option and the question: "Which pathway should I develop into a full design?" If the user explicitly asks for a full design immediately, proceed with the recommended pathway but label it as provisional.

## Pathway Options

### 1. Place-First Inquiry
Use when the educator has a specific place and wants to discover what the place can teach. Begin with direct encounter and observation, then map curriculum around what emerges.

Typical chain: `place-based-inquiry-anchor` → `curriculum-knowledge-architecture-designer` → `learning-target-authoring-guide` → `assessment-validity-checker`.

### 2. Curriculum-First Localisation
Use when required content or standards are fixed and the educator wants to ground them locally. Begin with the curriculum, then identify which local place can reveal it authentically.

Typical chain: `curriculum-knowledge-architecture-designer` → `place-based-inquiry-anchor` or `ecological-inquiry-anchor-designer` → `learning-target-authoring-guide` → `assessment-validity-checker`.

### 3. Critical Place Inquiry
Use when the place involves identity, power, history, access, land, culture, equity, or contested stories. This pathway includes appreciation and critique.

Typical chain: `place-based-inquiry-anchor` → `culturally-responsive-teaching-designer` → `source-credibility-evaluation-protocol` or `historical-document-set-curator` → `assessment-validity-checker`.

### 4. Ecological Place Inquiry
Use when the local place is a living system: pond, creek, tree, garden, hedgerow, soil, school grounds, coast, or urban ecosystem.

Typical chain: `ecological-inquiry-anchor-designer` → `outdoor-learning-sequence-designer` → `learning-target-authoring-guide` → optional `agency-circles-for-systems-action`.

### 5. Place + Systems Pathway
Use when the place issue involves recurring patterns, social structures, human decisions, mental models, or agency questions. Compassionate systems awareness tools are optional and should be used because the context needs them, not by default.

Typical chain: `place-based-inquiry-anchor` → `systems-awareness-iceberg` or `aspirational-systems-iceberg` → `mental-model-mapper` → `agency-circles-for-systems-action`.

## Prompt

```text
You are a place-based curriculum orchestrator. Your first responsibility is to make pathway options visible before committing to a design. Do not assume the educator knows the pathways.

Inputs:
Starting point: {{starting_point}}
Learner stage: {{learner_stage}}
Subject/curriculum content: {{subject_or_curriculum_content}}
Local place: {{local_place}}
Community knowledge holders: {{community_knowledge_holders}}
Constraints: {{constraints}}
Pathway choice: {{pathway_choice}}

Step 1: Present pathway options unless pathway_choice is already provided.
Include:
- Place-First Inquiry
- Curriculum-First Localisation
- Critical Place Inquiry
- Ecological Place Inquiry
- Place + Systems Pathway
For each pathway, state what it is for, what it produces, and when not to use it.

Step 2: Recommend the best-fit pathway based on the input. Explain why, and name the assumptions behind the recommendation.

Step 3: If no pathway_choice was provided, ask the educator to choose before producing the full design. If the user explicitly requested a full design anyway, continue with the recommended pathway and label it provisional.

Step 4: Once a pathway is selected, orchestrate the skill chain. For every step, specify:
- skill/tool to use
- purpose
- input it needs
- output it should produce
- handoff to the next step
- do-not-proceed-if check

Step 5: Produce the curriculum design sequence in teacher-usable language.

Return:

## Place-Based Curriculum Pathway Options
[Menu of pathways, with recommendation and choice prompt if needed]

## Recommended Pathway
[Best fit, assumptions, and alternatives]

## Orchestrated Skill Chain
[Step-by-step chain with handoffs]

## Place-Based Curriculum Design
[Only if a pathway is selected or provisional design is explicitly requested]

## Stop / Slow Down Checks
- [ ] Is the place a primary text, not a decorative hook?
- [ ] Are local/community knowledge holders treated as knowledge partners, not content props?
- [ ] Are cultural, Indigenous, historical, or access issues handled with humility?
- [ ] Does the design avoid asking students to act before they understand the place?
- [ ] Does assessment match the actual learning, not just the final product?
- [ ] Are student action and adult/community responsibility clearly distinguished?
```

## Common Pitfalls

1. Treating place as a theme rather than a source of knowledge.
2. Starting from action before encounter, observation, and inquiry.
3. Mapping curriculum onto a place in a forced way.
4. Extracting community stories without reciprocity.
5. Using compassionate systems tools automatically even when the inquiry is mainly ecological, historical, or conceptual.
6. Omitting assessment validity because the unit feels authentic.

## Known Limitations

1. **Cannot assess community relationships.** This orchestrator cannot determine whether proposed local knowledge holders or community partners are willing to participate, appropriate to involve, or safe to engage. That requires prior relationship-building which the skill cannot substitute.
2. **Does not provide cultural competency protocols.** The skill flags when cultural, Indigenous, or historical sensitivity is required (Critical Place Inquiry pathway) but cannot replace specialist cultural guidance or community consultation. A flag is not a process.
3. **Assessment validity is flagged, not verified.** The stop/slow check includes assessment alignment, but checking whether assessment truly measures intended learning requires use of assessment-validity-checker as a separate step.
4. **Degrades with unfamiliar places.** When the teacher does not know the local place well, the skill cannot generate meaningful design from thin input. Direct encounter, local research, and community knowledge must precede or run alongside this orchestration.

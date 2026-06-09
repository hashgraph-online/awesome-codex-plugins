---
# AGENT SKILLS STANDARD FIELDS (v2)
name: hexagon-complexity-mapper
description: "Map a complex topic by placing factors on hexagonal tiles where adjacency signals a claimed relationship. Use when students need to surface hidden connections in a system before analysis or action."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS
skill_id: "systems-thinking/hexagon-complexity-mapper"
skill_name: "Hexagon Complexity Mapper"
domain: "systems-thinking"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Hodgson, A. (1992). Hexagons for systems thinking. European Journal of System Dynamics, 59(1), 220–230."
  - "Meadows, D. (2008). Thinking in Systems. Chelsea Green. (systemic structure, feedback, unintended consequences)"
  - "Senge, P. (1990). The Fifth Discipline. Doubleday. (mental models, systems archetypes, seeing wholes)"
  - "H3Uni Hexagon Mapping tutorial and facilitation guides (CC BY-SA 4.0, practitioner method)"
input_schema:
  required:
    - field: "topic_or_challenge"
      type: "string"
      description: "The complex topic, issue, or challenge students are mapping — specific enough to generate 8–20 distinct factors"
    - field: "context"
      type: "string"
      description: "School, community, ecological, or curriculum context that grounds the mapping"
  optional:
    - field: "student_level"
      type: "string"
      description: "Year group or age range, to calibrate vocabulary and abstraction"
    - field: "mapping_question"
      type: "string"
      description: "Specific question to focus the mapping — e.g. 'What factors are shaping this situation?'"
    - field: "prior_scoping_statement"
      type: "string"
      description: "A scoping statement from scoping-for-transformative-learning-inquiry, if already completed"
    - field: "existing_evidence"
      type: "string"
      description: "Data, stories, observations, or student work already available about this topic"
output_schema:
  type: "object"
  fields:
    - field: "mapping_question"
      type: "string"
      description: "The focused question guiding the hexagon map"
    - field: "factor_list"
      type: "array"
      description: "All factors surfaced for student hexagon tiles"
    - field: "clusters"
      type: "array"
      description: "Named clusters with member factors and the story each cluster tells"
    - field: "named_relationships"
      type: "array"
      description: "At least three specific relationships between hexagons or clusters, with direction and explanation"
    - field: "boundary_hexagons"
      type: "array"
      description: "Factors at the edge of the map representing external forces or entry points for change"
    - field: "map_insights"
      type: "array"
      description: "What the completed map reveals that was not obvious before mapping"
    - field: "quality_gate_results"
      type: "object"
      description: "Results of structural quality checks on the map"
    - field: "next_step_options"
      type: "array"
      description: "Suggested follow-on skills based on map structure"
chains_well_with:
  - "systems-awareness-iceberg"
  - "mental-model-mapper"
  - "three-horizons-learning-transition-mapper"
  - "leverage-and-response-design"
  - "agency-circles-for-systems-action"
  - "place-based-inquiry-anchor"
teacher_time: "15 minutes"
tags: ["systems-thinking", "hexagon-mapping", "complexity", "relationships", "h3uni", "visual-facilitation", "emerging-evidence", "student-inquiry"]
---

# Hexagon Complexity Mapper

## What This Skill Does

Guides students through a hexagon mapping exercise in which they identify factors shaping a complex topic, write each on a hexagonal tile, and arrange the tiles so that adjacency — physical touching — signals a claimed relationship between two factors. The arrangement is not sorting into categories. It is a collective act of relationship-claiming. When two hexagons touch, students are asserting "these two things affect each other in some way" and must be able to explain how.

This distinction is critical. Hexagon mapping is not a brainstorming exercise with a prettier shape. It is a tool for surfacing the hidden connective tissue of complex situations: which factors cluster together because they are mutually reinforcing, which sit at the boundary of the system as external forces, and which hold the map together by appearing in multiple clusters.

The skill produces a shared visual map that becomes the input for subsequent tools such as Three Horizons mapping, systems awareness iceberg work, or agency circles.

## Evidence Space and Strength of Evidence

This skill encodes the H3Uni Hexagon Mapping method, a practitioner framework developed by Anthony Hodgson. It is not a validated classroom intervention.

### Component Evidence

- **Hodgson (1992) hexagonal systems thinking** (emerging): Hodgson's paper describes hexagons as a tool for qualitative systems mapping, particularly for surfacing relationships that are invisible in list-based or hierarchical representations. The paper provides theoretical grounding for the adjacency = relationship principle but does not include classroom evaluation data.
- **Meadows (2008) systemic structure** (strong): Meadows' account of systemic structure — stocks, flows, feedback loops, and leverage points — provides the theoretical framework within which hexagon mapping is meaningful. Understanding that complex behaviours emerge from structure, not from individual factors in isolation, is the rationale for relationship-based mapping.
- **Senge (1990) mental models and systems archetypes** (moderate): Senge's work on learning organisations establishes that mental models filter which factors and relationships people see. Hexagon mapping externalises and makes those mental models visible and collectively revisable.
- **H3Uni Hexagon Mapping facilitation guides** (practitioner framework): H3Uni's Resource Library includes step-by-step facilitation guides and tutorials for hexagon mapping with adult groups in policy and strategy contexts. These are practitioner resources, not peer-reviewed studies.

### Synthesis Evidence

The application of hexagon mapping to school-age students and classroom inquiry contexts is a classroom adaptation. The facilitation sequence, quality gates, student worksheet prompts, and teacher moves encoded in this skill were developed at REAL School Budapest by Gareth Manning, drawing on H3Uni's open facilitation guides. This synthesis has not been independently evaluated.

H3Uni methods are published under CC BY-SA 4.0 by H3Uni, founded by Anthony Hodgson and Bill Sharpe. H3Uni's formal operations concluded May 2026; the Resource Library is maintained by Future Stewards as an open commons.

### What This Skill Should Not Claim

H3Uni hexagon mapping was designed for adult facilitators working with policy practitioners, strategy teams, and professional groups. The classroom adaptation here does not claim peer-reviewed evidence for improved student outcomes, deeper systems thinking, or transferable complexity-navigation skills. Teachers should treat this as a theoretically grounded and professionally field-tested method under classroom adaptation — not as an evidence-based intervention with verified effects.

### Appropriate Use

Use this skill when students need to externalise and negotiate their collective understanding of a complex situation before analysis or action planning. It is most useful after a scoping exercise has defined what the group is investigating, and before tools that require a shared model of the situation (Three Horizons mapping, agency circles, systems iceberg). Avoid using it as a warm-up brainstorm or as a categorisation tool — the relationship logic must be actively maintained throughout.

## Input Schema

The teacher must provide:
- **Topic or challenge:** A complex issue specific enough to generate 8–20 distinct factors. Example: "What is shaping our school's relationship with technology?" or "What factors are influencing student wellbeing in this year group?"
- **Context:** Where this inquiry is happening and why it matters.

Optional:
- **Student level:** Year group or age, to calibrate language, abstraction, and number of hexagons expected.
- **Mapping question:** A specific question to anchor the exercise. If not provided, the skill will generate one from the topic.
- **Prior scoping statement:** If students have completed a scoping exercise, include the statement so the mapping question aligns with it.
- **Existing evidence:** Relevant data, observations, student responses, or community input to draw on.

## Prompt

```text
You are facilitating a hexagon complexity mapping exercise. Students will identify factors shaping a complex topic, write each on a hexagonal tile, and arrange tiles so that touching hexagons signal a claimed relationship.

CRITICAL PRINCIPLE: Adjacency is the meaning. When two hexagons touch, students are asserting "these two factors affect each other." This is not a sorting or categorisation exercise. Every placement is a relationship claim that students should be able to explain.

Inputs:
Topic or challenge: {{topic_or_challenge}}
Context: {{context}}
Student level: {{student_level}}
Mapping question: {{mapping_question}}
Prior scoping statement: {{prior_scoping_statement}}
Existing evidence: {{existing_evidence}}

Step 1 — Form the mapping question:
If a mapping question was provided, use it. If not, generate one that asks what factors are shaping the topic — not what solutions are needed. The question should be broad enough to invite diverse factors and specific enough to be answerable with evidence. Format: "What factors are shaping [topic] in [context]?"

Step 2 — Factor generation:
Generate 12–18 factors for the topic. Each factor should be:
- Specific (not vague like "society" or "money")
- Expressible in 2–4 words on a hexagon tile
- A genuine mix of: people and groups; structures and systems; events and patterns; values and beliefs; resources and constraints; environmental and material conditions
Label this: "Suggested starting factors — students should add, remove, and rename these."

Step 3 — Clustering guidance:
Provide step-by-step instructions for the class:
1. Spread all tiles loosely and read them together before touching them.
2. Move tiles that clearly belong near each other. Ask: "What makes these two belong together?" — students must name the relationship, not just a shared theme.
3. Build clusters by adding tiles with a relationship to existing cluster members.
4. Name each cluster with a phrase capturing the story it tells, not a category label. Example: "trust erodes when accountability is unclear" not "accountability."
5. After clustering, add arrows between clusters where one cluster strongly influences another.
6. Identify boundary hexagons — tiles at the edge representing forces outside the group's direct control.

Step 4 — Relationship naming:
Identify at least three specific relationships. Each should state:
- Factor A
- Factor B
- How A affects B, or how they affect each other
- Whether the relationship is reinforcing (more A → more B) or balancing (A limits B)
- Evidence level: "we observed this," "we believe this," or "we're guessing"

Step 5 — Quality check:
Apply these gates:
- REJECT if the map has fewer than 6 hexagons (topic too narrow or question too simple)
- FLAG if all hexagons touch all others (no structure found — ask students to re-examine which connections are strongest and which are absent)
- FLAG if there are no boundary hexagons (ask what forces from outside the group's control are shaping the situation)
- FLAG if students cannot name 3 specific relationships (tiles placed by category, not relationship — return to clustering Step 2)

Step 6 — Map insights:
Based on map structure, identify:
- Which cluster is most central (connected to the most other clusters)?
- Which factor appears in multiple clusters (a bridge factor)?
- Which factors at the boundary are entry points for change or external forces?
- What does the map reveal that a simple list would have hidden?

Return exactly:

## Hexagon Map: [Topic]

**Mapping question:** [question]
**Context:** [brief context]

### Suggested Factors
[12–18 factors, one per line, with note that students should revise these]

### Clustering Guidance
[Step-by-step instructions for the class]

### Named Relationships
| Factor A | Factor B | How they relate | Reinforcing or balancing? | Evidence level |
|---|---|---|---|---|
[At least 3 rows]

### Cluster Stories
[For each cluster: cluster name (story-phrase), member factors, what the cluster reveals]

### Boundary Hexagons
[Factors at the edge — what they are and what they suggest]

### Map Insights
[What the completed map structure reveals]

### Quality Gate Results
- [ ] Map has 6+ hexagons: [pass/flag]
- [ ] Clusters based on relationships, not just themes: [pass/flag/note for teacher]
- [ ] Boundary hexagons present: [pass/flag]
- [ ] At least 3 specific relationships named: [pass/flag]
- [ ] No cluster contains 8+ tiles without a sub-story: [pass/flag]

### Next Step Options
[Suggest follow-on skills by name: systems-awareness-iceberg if a power or structural cluster is central; three-horizons-learning-transition-mapper if the map has a time dimension; leverage-and-response-design if students want to identify intervention points]
```

## Common Pitfalls

1. **Running it as a brainstorm.** Hexagon mapping loses its distinctive value if students generate factors without making relationship claims. The arrangement phase is the analytical work, not decoration.
2. **Using category names instead of relationship stories.** A cluster named "Social Factors" has not been mapped. A cluster named "peer pressure shapes what risks feel safe to take" has.
3. **Accepting adjacency without explanation.** If a student places two hexagons touching and cannot explain how they relate, the placement is a guess, not a relationship claim. Ask before moving on.
4. **Skipping boundary hexagons.** Factors at the system boundary often reveal the most important leverage points: what cannot be changed directly, and what enters the system from outside.
5. **Using the map to confirm existing beliefs.** A map that looks exactly like what the teacher expected should be treated with suspicion. Ask: "What surprised us? What is missing from this map?"

## Known Limitations

1. **Relationship claims are hypotheses.** The map represents student beliefs about the system, not verified causal structure. Named relationships should be treated as hypotheses requiring evidence.
2. **Physical format matters.** This skill produces guidance and suggested factors; it does not replace physical hexagonal tiles, cards, or a digital equivalent. The tactile, moveable quality of the medium is part of the method's value.
3. **Works poorly in isolation.** Hexagon mapping produces a shared model, not an action plan. Without follow-on tools (Three Horizons, agency circles, iceberg) the map becomes an artefact rather than an analytical tool.
4. **Degrades with very large groups.** In classes larger than 20, multiple small-group maps with a gallery comparison phase are more productive than a single whole-class map.

## Verification Checklist

- [ ] The mapping question is specific enough to generate diverse, non-obvious factors.
- [ ] Suggested factors include a genuine mix of people, structures, values, events, and material conditions.
- [ ] Clustering guidance explicitly states that adjacency = relationship, not category membership.
- [ ] At least 3 specific relationships are named with direction and evidence level.
- [ ] Boundary hexagons are identified and interpreted.
- [ ] All four quality gates are applied and reported.
- [ ] Next step options reference real skills in the library by their skill name.

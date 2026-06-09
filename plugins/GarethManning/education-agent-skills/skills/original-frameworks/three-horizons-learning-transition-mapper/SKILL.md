---
# AGENT SKILLS STANDARD FIELDS (v2)
name: three-horizons-learning-transition-mapper
description: "Map a scoped topic across three coexisting horizons — current system under strain (H1), preferred future (H3), and transition innovations sorted as H2+ or H2- — to understand change dynamics and identify responsible next actions."
disable-model-invocation: false
user-invocable: true
effort: high

# EXISTING FIELDS
skill_id: "original-frameworks/three-horizons-learning-transition-mapper"
skill_name: "Three Horizons Learning Transition Mapper"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Curry, A., & Hodgson, A. (2008). Seeing in multiple horizons: connecting futures to strategy. Journal of Futures Studies, 13(1), 1–20."
  - "Sharpe, B., Fazey, I., Hodgson, A., Leicester, G., & Lyon, A. (2016). Three horizons: A pathways practice for transformation. Ecology and Society, 21(2), 47."
  - "Sharpe, B., & Hodgson, A. (2019). Anticipation in three horizons. In R. Poli (Ed.), Handbook of Anticipation. Springer."
  - "H3Uni Three Horizons tutorials and facilitation guides (CC BY-SA 4.0, practitioner method)"
input_schema:
  required:
    - field: "scoped_topic"
      type: "string"
      description: "The inquiry topic, ideally from a completed scoping statement — specific enough to generate concrete evidence for each horizon"
    - field: "value_dimension"
      type: "string"
      description: "The value or quality the group cares about — what goes on the vertical axis. Examples: ecological health, student wellbeing, learning depth, belonging, fairness, community resilience"
  optional:
    - field: "student_level"
      type: "string"
      description: "Year group or age range"
    - field: "existing_evidence"
      type: "string"
      description: "Data, observations, or student work already available about the current situation"
    - field: "h3_seeds"
      type: "string"
      description: "Pockets of the preferred future already visible somewhere — real examples, prototypes, or inspiring cases"
    - field: "prior_hexagon_map"
      type: "string"
      description: "Key clusters or insights from a prior hexagon mapping exercise, if available"
output_schema:
  type: "object"
  fields:
    - field: "h1_map"
      type: "object"
      description: "Current system under strain: evidence of dysfunction, persistence factors, what H1 still provides"
    - field: "h3_map"
      type: "object"
      description: "Preferred future pattern: values, norms, relationships; pockets already visible"
    - field: "h2_map"
      type: "object"
      description: "Transition activity sorted as H2+ (grows toward H3) and H2- (extends H1 in new language)"
    - field: "transition_story"
      type: "string"
      description: "3–5 sentence narrative of what is declining, emerging, contested, and where action might help"
    - field: "h2_plus_opportunities"
      type: "array"
      description: "Specific H2+ innovations worth supporting or learning from"
    - field: "quality_gate_results"
      type: "object"
      description: "Results of structural quality checks on the three horizons map"
    - field: "next_step_options"
      type: "array"
      description: "Suggested follow-on skills based on map insights"
chains_well_with:
  - "scoping-for-transformative-learning-inquiry"
  - "hexagon-complexity-mapper"
  - "dilemma-navigation-for-education-design"
  - "systems-awareness-iceberg"
  - "agency-circles-for-systems-action"
  - "place-based-inquiry-anchor"
  - "regenerative-project-design-orchestrator"
teacher_time: "20 minutes"
tags: ["h3uni", "three-horizons", "futures-thinking", "transition", "h2-plus", "h2-minus", "original-framework", "emerging-evidence", "systems-change", "programme-planning"]
---

# Three Horizons Learning Transition Mapper

## What This Skill Does

Guides students through a Three Horizons mapping exercise that helps them understand how a current system is changing, what kind of future they want to grow, and which innovations are genuinely moving toward that future. The skill produces a structured three-horizon map with: evidence that the current dominant pattern is under strain (Horizon 1); a description of the preferred future pattern with grounded examples (Horizon 3); and a sorted list of transition innovations distinguishing H2+ (grows the preferred future) from H2- (extends the old pattern in new language).

Three Horizons is not a timeline. The three horizons coexist in the present: H1 elements dominate now, H3 pockets already exist now, and H2 innovations are contested terrain now. The skill encodes a facilitation logic that makes this coexistence visible and analytically useful.

## Evidence Space and Strength of Evidence

This skill encodes the H3Uni Three Horizons method, a practitioner framework for futures thinking and transformative change facilitation.

### Component Evidence

- **Curry & Hodgson (2008) multiple horizons** (emerging): This foundational paper describes the Three Horizons framework as a tool for strategic futures thinking. It provides conceptual grounding for the H1/H2/H3 distinctions and the H2+/H2- classification. The paper is theoretical and practitioner-oriented, not a controlled study.
- **Sharpe et al. (2016) pathways practice** (emerging): This ecology and society paper describes Three Horizons as a participatory transformation pathway tool and documents its use in professional and community contexts. It provides the most systematic academic account of the method, including the H2+/H2- distinction and the facilitation sequence. The paper does not include randomised or comparative study designs.
- **Sharpe & Hodgson (2019) anticipation framework** (emerging): This chapter positions Three Horizons within the broader literature on anticipation and future consciousness, connecting it to cognitive and sociological accounts of how groups develop shared futures thinking.
- **H3Uni Three Horizons tutorials and facilitation guides** (practitioner framework): H3Uni's Resource Library includes step-by-step facilitation guides for Three Horizons mapping with adult groups in policy, ecology, and organisational contexts. These are practitioner resources, not peer-reviewed evaluations.

### Synthesis Evidence

The classroom adaptation — including the facilitation sequence, student worksheet prompts, quality gates, and H2+/H2- distinction encoded in this skill — was developed for school-age students at REAL School Budapest by Gareth Manning, drawing on H3Uni's open facilitation guides and the academic papers above. This adaptation has not been independently evaluated. The core intellectual framework is H3Uni's; the classroom operationalisation is practitioner-synthesised.

H3Uni methods are published under CC BY-SA 4.0 by H3Uni, founded by Anthony Hodgson and Bill Sharpe. H3Uni's formal operations concluded May 2026; the Resource Library is maintained by Future Stewards as an open commons.

### What This Skill Should Not Claim

H3Uni Three Horizons was designed for adult facilitators working with policy practitioners, strategy teams, and professional groups. The classroom adaptation here does not claim peer-reviewed evidence for improved student futures thinking, better transition design outcomes, or transferable systems-change capability. Teachers should treat this as a theoretically grounded and professionally field-tested method under classroom adaptation — not as a validated educational intervention.

### Appropriate Use

Use this skill after a scoping exercise and, where possible, after hexagon mapping. The map works best when students have already thought carefully about what they are investigating and have some shared understanding of the system's structure. Avoid using it as a standalone first activity — without prior scoping, students tend to fill H1 with complaints and H3 with fantasies rather than grounded structural analysis.

## Input Schema

The teacher must provide:
- **Scoped topic:** The inquiry topic, ideally from a completed scoping statement. Should be specific enough that students can give concrete evidence for H1 and name real pockets of H3.
- **Value dimension:** What value or quality the group cares about and wants on the vertical axis. This is not a moral judgement about H1 being bad — it is a shared declaration of what the group is trying to protect or grow.

Optional:
- **Student level:** Year group or age range, to calibrate language and abstraction.
- **Existing evidence:** Data, observations, student surveys, stories, or community input about the current situation.
- **H3 seeds:** Specific examples of the preferred future already existing somewhere.
- **Prior hexagon map:** Key clusters or insights from a hexagon mapping exercise if students have already completed one.

## Prompt

```text
You are facilitating a Three Horizons mapping exercise. Students will map a complex topic across three coexisting patterns: the current dominant system under strain (H1), the preferred future pattern they want to grow (H3), and transition innovations (H2) sorted as H2+ (grows toward H3) or H2- (extends H1 in new language).

CRITICAL SEQUENCE: Always map in this order: H1 → H3 → H2. Never H1 → H2 → H3. Without mapping H3 first, it is impossible to distinguish H2+ from H2-. H2 innovations can only be classified once students know what future they are testing them against.

CRITICAL FRAMING: H1 is not "bad" and H3 is not "good." H1 elements persist in any real system and supply functions that must not be lost. H3 pockets already exist in the present. Frame the map as change dynamics, not moral categories.

Inputs:
Scoped topic: {{scoped_topic}}
Value dimension: {{value_dimension}}
Student level: {{student_level}}
Existing evidence: {{existing_evidence}}
H3 seeds: {{h3_seeds}}
Prior hexagon map: {{prior_hexagon_map}}

Step 1 — Map Horizon 1 (current pattern under strain):
H1 is the dominant current pattern: the dominant assumptions, practices, structures, metrics, and relationships that currently govern the topic. The vertical axis measures the value dimension. H1 is declining not because it is evil but because it is losing fit with changing conditions or values.

Ask: What evidence shows the current pattern is under strain? What keeps H1 in place even as it loses fit? Who benefits from H1 continuing? What does H1 still provide that we need?

Generate:
- Evidence of H1 strain: specific, observable examples showing the value dimension is being compromised
- H1 persistence factors: the structures, incentives, habits, or beliefs that sustain H1 even under pressure
- What H1 still provides: valuable functions any transition must preserve

Step 2 — Map Horizon 3 (preferred future pattern):
H3 is the pattern of life the group wants to grow: the values, norms, relationships, and practices that would represent genuine improvement in the value dimension. H3 is not a fantasy — it must be grounded in pockets already visible somewhere.

Ask: What would this system look like if the value dimension were genuinely flourishing? Where can we already see pockets of this future — in other schools, communities, projects, or places? What values and norms characterise H3?

Generate:
- H3 pattern description: what the preferred future looks, feels, and works like
- H3 pockets: real examples already existing somewhere that embody elements of H3
- H3 values: the shared values or principles this future is built on

Step 3 — Map Horizon 2 (transition innovations, sorted as H2+ or H2-):
H2 innovations are the experiments, projects, practices, and actors responding to pressure between H1 and H3. Some grow the preferred future (H2+). Others extend the old pattern in new language — they look like change but reinforce H1's core logic (H2-).

For each H2 item, test: Does this innovation genuinely move toward H3, or does it adapt H1 to survive? H2- items often use H3 language (sustainability, wellbeing, innovation) while leaving H1 structures intact.

For each H2 item generate:
- Description of the innovation or experiment
- Classification: H2+ or H2-
- Reasoning: why it grows H3 or why it extends H1

Step 4 — Tell the transition story:
Write a narrative (3–5 sentences) describing: what is declining in H1, what is emerging in H3, which H2 innovations are genuinely transitional, what is contested, and where the group might focus action.

Step 5 — Quality check:
Apply these gates:
- FLAG if H3 is empty or contains only vague aspirations with no grounded pockets (cannot distinguish H2+ from H2- without a concrete H3)
- FLAG if no H2 items are classified as H2+ or H2- (H2 listed without analysis)
- FLAG if H1 contains only complaints or blame without structural analysis (H1 needs evidence of strain AND persistence factors)
- REJECT if the output frames H1 as "bad" and H3 as "good" without nuance
- FLAG if H3 has no real-world pockets — aspiration only with no connection to present reality

Return exactly:

## Three Horizons Map: [Topic] — [Value Dimension]

**Scoped topic:** [topic]
**Value dimension:** [what the group cares about protecting or growing]

---

### Horizon 1 — Current Pattern Under Strain

**What H1 looks like:**
[Description of the dominant current pattern]

**Evidence of strain:**
- [Specific, observable example]

**What keeps H1 in place:**
- [Persistence factor — structure, incentive, habit, or belief]

**What H1 still provides:**
- [Function or value that any transition must preserve]

---

### Horizon 3 — Preferred Future Pattern

**What H3 looks like:**
[Description of the preferred future — grounded, not utopian]

**Pockets of H3 already visible:**
- [Real example — a school, community, project, or practice already embodying elements of H3]

**H3 values:**
- [Shared values or norms characterising this future]

---

### Horizon 2 — Transition Activity

| Innovation or Experiment | H2+ or H2-? | Reasoning |
|---|---|---|
| [name] | H2+ | [grows toward H3 because...] |
| [name] | H2- | [extends H1 in new language because...] |

**H2+ opportunities worth supporting:**
- [Key H2+ innovations with brief explanation]

---

### Transition Story
[3–5 sentence narrative: what is declining, what is emerging, what is contested, where action might help]

---

### Quality Gate Results
- [ ] H3 is grounded with at least one concrete pocket: [pass/flag]
- [ ] H2 items are classified as H2+ or H2-: [pass/flag]
- [ ] H1 includes structural analysis, not only complaints: [pass/flag]
- [ ] Map avoids moral framing of H1 as bad, H3 as good: [pass/flag]
- [ ] H3 is a pattern of life, not a list of innovations: [pass/flag]

### Next Step Options
[dilemma-navigation-for-education-design if the map surfaces a genuine tension between values; agency-circles-for-systems-action if students are ready to act; regenerative-project-design-orchestrator if a project design is needed]
```

## Common Pitfalls

1. **Mapping in the wrong sequence (H1 → H2 → H3).** Without H3 in place, students cannot classify H2 items. They will list innovations without being able to say which ones are genuinely transitional.
2. **H3 as a fantasy wish list.** H3 should be grounded in pockets already visible somewhere in the world. An H3 with no real examples is harder to act toward and harder to test innovations against.
3. **H2- as obviously bad.** H2- innovations are not necessarily dishonest — they often represent real attempts at improvement constrained by existing structures. The H2- classification is analytical, not a moral judgement.
4. **H1 as a list of complaints.** A strong H1 explains why the pattern persists, not only what is wrong with it. Without understanding H1's persistence factors, students will underestimate the difficulty of transition.
5. **H1 as "the past" and H3 as "the future."** All three horizons exist simultaneously in the present. This is not a historical timeline.

## Known Limitations

1. **H2+/H2- classification is interpretive.** Whether an innovation is H2+ or H2- depends on the value dimension chosen and the H3 vision held. Different groups with different values will produce different classifications. This is a feature — it makes value differences visible.
2. **Requires a clear value dimension.** Without an agreed vertical axis, the map lacks analytical structure. Groups that cannot agree on a value dimension may need a values clarification step first.
3. **Produces understanding, not action.** The Three Horizons map reveals transition dynamics; it does not produce a project plan. Follow-on skills are needed to move from map to action.
4. **Quality of H3 limits H2 analysis.** A vague H3 produces ambiguous H2 classification. The map's analytical value depends on the specificity and groundedness of the H3 vision.

## Verification Checklist

- [ ] The facilitation sequence follows H1 → H3 → H2.
- [ ] H1 includes both evidence of strain AND persistence factors.
- [ ] H3 is grounded in at least one concrete real-world pocket.
- [ ] Every H2 item is classified as H2+ or H2- with explicit reasoning.
- [ ] The map avoids moral framing (H1 ≠ bad, H3 ≠ good).
- [ ] A transition story is produced naming what is declining, emerging, and contested.
- [ ] All five quality gates are applied and reported.
- [ ] Next step options reference real skills in the library by name.

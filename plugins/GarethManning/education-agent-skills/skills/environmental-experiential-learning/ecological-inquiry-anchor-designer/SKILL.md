---
# AGENT SKILLS STANDARD FIELDS (v2)
name: ecological-inquiry-anchor-designer
description: "Design an inquiry sequence anchored in a local ecosystem that embeds science or geography curriculum content. Use when teaching through local living systems like gardens, ponds, or hedgerows."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "environmental-experiential-learning/ecological-inquiry-anchor-designer"
skill_name: "Ecological Inquiry Anchor Designer"
domain: "environmental-experiential-learning"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Sobel (1996) — Beyond Ecophobia: reclaiming the heart in nature education"
  - "Sobel (2004) — Place-Based Education: connecting classrooms and communities"
  - "Orr (1992) — Ecological Literacy: education and the transition to a postmodern world"
  - "Kimmerer (2013) — Braiding Sweetgrass: Indigenous wisdom, scientific knowledge, and the teachings of plants"
  - "Chawla (1998) — Significant life experiences revisited: a review of research on sources of environmental sensitivity"
input_schema:
  required:
    - field: "local_ecosystem"
      type: "string"
      description: "The specific local ecosystem or living system that anchors the inquiry — a garden, pond, hedgerow, tree, patch of waste ground, window box"
    - field: "curriculum_objective"
      type: "string"
      description: "The science or geography curriculum content the inquiry must address"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "time_frame"
      type: "string"
      description: "How long the inquiry runs — single lesson, a week, a term, a year"
    - field: "school_grounds"
      type: "string"
      description: "What outdoor or growing spaces the school has"
    - field: "community_expertise"
      type: "string"
      description: "Local experts — gardeners, ecologists, farmers, park rangers"
    - field: "student_prior_experience"
      type: "string"
      description: "Students' existing relationship with nature and outdoor environments"
output_schema:
  type: "object"
  fields:
    - field: "ecological_inquiry"
      type: "object"
      description: "The complete inquiry design — anchored in a specific local ecosystem, addressing curriculum objectives through direct ecological investigation"
    - field: "inquiry_question"
      type: "string"
      description: "The driving question that emerges from the ecosystem and connects to the curriculum"
    - field: "investigation_activities"
      type: "array"
      description: "What students do — direct observation, data collection, long-term monitoring, ecological interventions"
    - field: "ecological_literacy_outcomes"
      type: "object"
      description: "What students understand about ecological systems — beyond curriculum objectives, the deeper ecological literacy"
    - field: "stewardship_dimension"
      type: "object"
      description: "How the inquiry leads to caring for the ecosystem — knowledge creates responsibility"
chains_well_with:
  - "outdoor-learning-sequence-designer"
  - "place-based-inquiry-anchor"
  - "phenomenon-based-unit-anchor"
  - "biophilic-learning-environment-designer"
  - "critical-thinking-task-designer"
teacher_time: "4 minutes"
tags: ["ecological-literacy", "Sobel", "Orr", "place-based", "environmental-education", "inquiry", "stewardship"]
---

# Ecological Inquiry Anchor Designer

## What This Skill Does

Designs a sustained ecological inquiry anchored in a specific local ecosystem — a pond, garden, hedgerow, tree, or even a window box — connecting curriculum science objectives to direct investigation of living systems that students can observe, monitor, and care for over time. The approach draws on Sobel's (1996, 2004) place-based education and his critique of "ecophobia" (frightening children with global environmental catastrophe before they have developed love for local nature), and Orr's (1992) concept of ecological literacy (understanding how natural systems work, not just knowing facts about nature). The critical principle is that ecological understanding comes from RELATIONSHIP with specific living systems — sustained observation of one pond teaches more about ecology than reading about ten biomes. The output includes an inquiry design, a driving question, investigation activities, ecological literacy outcomes (beyond the curriculum), and a stewardship dimension where students take responsibility for the ecosystem they've studied. AI is specifically valuable here because designing an inquiry that addresses curriculum objectives THROUGH authentic ecological investigation requires mapping scientific concepts onto what a specific local ecosystem can reveal — ensuring the ecology is real, not contrived.

## Evidence Foundation

Sobel (1996) argued that environmental education should begin with LOVE of local nature, not FEAR of global destruction. He documented how premature exposure to environmental catastrophe (rainforest destruction, species extinction, climate change) before children have developed emotional bonds with local nature produces "ecophobia" — anxiety, helplessness, and disengagement rather than stewardship. His prescription: ages 4–7, explore the home environment; ages 8–11, explore the local neighbourhood and its ecosystems; ages 12–15 and beyond, engage with broader social and environmental issues. Start local, start positive, start with relationship. Sobel (2004) extended this into place-based education, arguing that the curriculum should grow FROM the local environment rather than being mapped ONTO it. Orr (1992) defined ecological literacy as understanding how natural systems sustain life — the flows of energy, cycles of matter, interdependencies of species, and resilience of ecosystems. He argued that ecological illiteracy is the most dangerous form of ignorance because it enables humans to destroy the systems that sustain them without understanding what they're doing. Kimmerer (2013), writing from an Indigenous (Potawatomi) perspective, described a relationship with the living world that is both scientific and reciprocal — learning from plants and ecosystems is inseparable from caring for them. Chawla (1998) reviewed research on "significant life experiences" — the formative experiences that lead adults to care about the environment — finding that the most common factor was direct, extended experience of nature in childhood, not environmental education classes or campaigns.

## Input Schema

The teacher must provide:
- **Local ecosystem:** The specific living system. *e.g. "The school pond — about 2m × 3m, established 5 years ago, has frogspawn in spring, dragonflies in summer, some algae buildup" / "A large oak tree in the school grounds — estimated 150 years old, visible from our classroom window" / "Three raised beds in the school garden — currently growing herbs and vegetables" / "A patch of 'waste ground' behind the school fence — overgrown, wild, officially neglected but ecologically interesting"*
- **Curriculum objective:** What must be learned. *e.g. "Year 4 Science: living things and their habitats — identify local habitats and the organisms that live there" / "Year 7 Science: ecosystems — food chains, food webs, interdependence" / "Year 8 Geography: ecosystems — how ecosystems function, human impact"*

Optional (injected by context engine if available):
- **Student level:** Year group
- **Time frame:** Duration of inquiry
- **School grounds:** Available outdoor spaces
- **Community expertise:** Local experts
- **Student prior experience:** Existing nature connection

## Prompt

```
You are an expert in ecological education and place-based inquiry, with deep knowledge of Sobel's (1996, 2004) place-based education and ecophobia framework, Orr's (1992) ecological literacy, Kimmerer's (2013) reciprocal relationship with living systems, and Chawla's (1998) research on significant life experiences. You understand that ecological understanding is not a set of facts but a WAY OF SEEING — an ability to perceive the connections, dependencies, and cycles in living systems. This understanding comes from sustained relationship with specific ecosystems, not from textbook descriptions of generic biomes.

CRITICAL PRINCIPLES:
- **Start with love, not fear (Sobel, 1996).** Children need to fall in love with a specific pond, tree, or garden BEFORE they can meaningfully engage with abstract environmental issues. Don't begin with "ecosystems are under threat" — begin with "look at what lives in our pond."
- **The ecosystem is the teacher.** The curriculum objective is met THROUGH the ecosystem, not mapped onto it. If the objective is "food chains," the students don't learn about food chains and then look at the pond — they investigate the pond and discover the food chain that's actually there.
- **Long-term observation reveals what short visits cannot.** An ecosystem changes through seasons, through weather, through years. A single visit shows a snapshot; a term of weekly observations shows a living system. Design the inquiry for sustained engagement, not a one-off trip.
- **Reciprocity, not extraction (Kimmerer, 2013).** Students don't just TAKE knowledge from the ecosystem (observe, collect data, leave). They give back — through care, stewardship, and respect. The inquiry includes a stewardship dimension: what can we do FOR this ecosystem?
- **Every ecosystem is complex enough.** A school pond is not a "simple" ecosystem. It contains hundreds of species, multiple trophic levels, seasonal cycles, water chemistry, decomposition processes, and inter-species relationships. A single tree supports an entire community. Don't dismiss small or familiar ecosystems as educationally insufficient.

Your task is to design an ecological inquiry for:

**Local ecosystem:** {{local_ecosystem}}
**Curriculum objective:** {{curriculum_objective}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, infer from the curriculum objective.
**Time frame:** {{time_frame}} — if not provided, design for a term-long inquiry with weekly observations.
**School grounds:** {{school_grounds}} — if not provided, use the described ecosystem.
**Community expertise:** {{community_expertise}} — if not provided, suggest who might help.
**Student prior experience:** {{student_prior_experience}} — if not provided, assume limited but not absent nature experience.

Return your output in this exact format:

## Ecological Inquiry: [Ecosystem] × [Curriculum Objective]

**Ecosystem:** [The specific local living system]
**Curriculum objective:** [What students must learn]
**Driving question:** [The question that emerges from the ecosystem and connects to the curriculum]

### Why This Ecosystem

[What makes this specific ecosystem educationally rich — what it can teach that a textbook cannot]

### Inquiry Design

**Phase 1 — Meeting the ecosystem**
[How students first encounter the ecosystem — observation, wonder, questions]

**Phase 2 — Investigating**
[What students investigate — specific activities, data collection, long-term monitoring]

**Phase 3 — Understanding**
[How students make sense of what they've found — connecting observations to ecological concepts]

**Phase 4 — Stewardship**
[How students give back — caring for the ecosystem based on what they've learned]

### Investigation Activities

[Detailed activities — what students do, what data they collect, what tools they use]

### Curriculum Connections

[How the inquiry addresses the specific curriculum objective — with evidence from the ecosystem itself]

### Ecological Literacy Outcomes

[What students understand about HOW ecosystems work — beyond the specific curriculum objective]

### Stewardship Plan

[Specific actions students take to care for the ecosystem — informed by their investigation]

**Self-check before returning output:** Verify that (a) the inquiry starts with love and wonder, not fear, (b) the ecosystem drives the inquiry rather than the curriculum being mapped onto it, (c) sustained observation is built in, (d) stewardship follows naturally from investigation, and (e) the curriculum objective is genuinely addressed through the ecological inquiry.
```

## Example Output

**Scenario:** *Local ecosystem: "The school pond — about 2m × 3m, dug 5 years ago by a previous Year 6 class. It has pond plants (water lilies, iris, water mint), frogspawn appears in spring, dragonflies are seen in summer, there's a growing algae problem (green water), and we've noticed fewer frogs this year than last. It's in the school conservation area, which also has a log pile, a wildflower strip, and a bird feeder." / Curriculum objective: "Year 7 Science: ecosystems — food chains, food webs, interdependence, and the impact of changes to the ecosystem" / Time frame: "One term — approximately 12 weeks, with one session per week (plus the regular Science lessons where concepts are taught)"*

---

## Ecological Inquiry: The School Pond × Ecosystems and Interdependence

**Ecosystem:** School pond — 2m × 3m, 5 years old, established plants, frog population, algae issue, declining biodiversity indicators
**Curriculum objective:** Year 7 Science — food chains, food webs, interdependence, and the impact of changes to the ecosystem
**Driving question:** "Our pond is going green and we're seeing fewer frogs. What's happening, and can we help?"

### Why This Ecosystem

This pond is a complete ecosystem in miniature. It contains:
- **Producers:** Algae, pond plants (lilies, iris, water mint)
- **Primary consumers:** Water fleas (Daphnia), pond snails, mayfly larvae, mosquito larvae
- **Secondary consumers:** Dragonfly larvae, water boatmen, diving beetles, newts (if present)
- **Tertiary consumers:** Frogs (adult), herons (if visiting)
- **Decomposers:** Bacteria, fungi in the sediment

It has a REAL problem — algae overgrowth and declining frog population — which is a genuine ecological puzzle. The algae bloom may be caused by nutrient enrichment (eutrophication) from leaf fall, soil runoff, or excess feeding if the pond was previously stocked. The declining frog population may be connected (algae reduces oxygen, making the pond inhospitable) or may have a separate cause (loss of surrounding habitat, predation, disease). This is not a textbook problem — it's a real investigation with a real answer that students can discover.

### Inquiry Design

**Phase 1 — Meeting the Pond (Weeks 1–2)**

*Week 1: First encounter.*
Students visit the pond. No clipboards, no worksheets. Just look. Sit by the pond for 10 minutes in silence. Then: "What did you notice? What did you see moving? What questions do you have?" Teacher records questions on a large sheet.

Expected questions: "Why is the water green?" "Where are the frogs?" "What's that bug on the surface?" "Is the pond dying?"

The green water and missing frogs are genuine hooks — students notice them immediately. The inquiry question emerges from observation, not from the teacher.

*Week 2: Baseline survey.*
Students conduct a biodiversity survey. Using pond-dipping nets and identification keys, they sample invertebrates, identify species (or species groups), and record what they find. They also note: water colour, water clarity (can they see the bottom?), plant coverage, and any visible animals. This is the baseline against which change will be measured.

**Phase 2 — Investigating (Weeks 3–8)**

*Week 3: Building the food web.*
Using the species found in Week 2, students construct the ACTUAL food web of THIS pond — not a textbook food web but one based on what they've observed. "We found Daphnia. What do Daphnia eat? (Algae.) What eats Daphnia? (Dragonfly larvae, fish if present.) What eats dragonfly larvae? (Frogs, birds.)" The food web is drawn on a large display and stays up all term — it's a working document that gets updated as new species are found.

*Weeks 4–5: The algae investigation.*
The driving question narrows: "Why is our pond going green?" Students design and conduct an investigation:
- Test water quality: pH, nitrate levels (using simple test strips, £5 from an aquarium shop), water clarity (Secchi disk — students can make one from a weighted white disc on a string)
- Compare: take a water sample from the pond and from the school tap. What's different? The nitrate test will likely show elevated nitrates in the pond (the cause of algae growth)
- Hypothesis: "If nitrates are high, what's producing them?" Students investigate: leaf litter decomposing in the pond, soil runoff from adjacent garden beds, bird droppings from the feeder nearby. Each is a testable hypothesis.

*Weeks 6–7: The frog question.*
"Why are there fewer frogs?" Students research frog life cycles and habitat requirements: frogs need clean water for breeding (algae reduces dissolved oxygen), vegetated pond margins for cover, and surrounding habitat for foraging. Students assess: does our pond still provide these? The log pile provides foraging habitat. But has the algae made the water less suitable for tadpoles?

*Week 8: Interdependence mapping.*
Students revisit their food web. The teacher introduces the concept of INTERDEPENDENCE: "If the algae takes over and covers the surface, what happens to the plants underneath? (They can't photosynthesise — they die.) If the plants die, what happens to the invertebrates that live in them? (They lose habitat.) If the invertebrates decline, what eats them? (The frogs.) So the algae problem might be CONNECTED to the frog problem." Students trace the cascade through their food web — this is interdependence made visible through THEIR pond.

**Phase 3 — Understanding (Weeks 9–10)**

Students synthesise their findings:
- The food web shows how energy flows through the pond ecosystem
- The algae investigation shows how a change in ONE factor (nutrient levels) can cascade through the system
- The frog question shows interdependence in action — the health of one species depends on the health of the whole system
- The concept of ECOSYSTEM BALANCE becomes tangible: this pond was balanced when it was first dug, and something has shifted

Students write an "Ecosystem Health Report" for the school — summarising what they found, explaining the science, and recommending actions.

**Phase 4 — Stewardship (Weeks 11–12)**

Based on their investigation, students design and implement an intervention:
- If the problem is leaf litter: install a pond net in autumn to prevent leaves entering
- If the problem is runoff: create a planted buffer zone between the garden beds and the pond
- If the problem is nutrient accumulation: partial water change (removing some algae-rich water and replacing with clean water) and introducing barley straw (a traditional, evidence-supported method for reducing algae)
- Ongoing: establish a "Pond Monitoring Team" that checks water quality and species monthly — the inquiry doesn't end when the unit ends

### Investigation Activities

| Week | Activity | What Students Do | Data Collected |
|---|---|---|---|
| 1 | Silent observation | Sit, watch, record questions | Question list, initial sketches |
| 2 | Biodiversity survey | Pond-dip, identify species | Species list, abundance estimates |
| 3 | Food web construction | Research feeding relationships, build web | Physical food web display |
| 4 | Water quality testing | Test pH, nitrate, clarity | Water quality data (quantitative) |
| 5 | Algae source investigation | Test hypotheses about nutrient sources | Comparative data, observations |
| 6 | Frog habitat assessment | Assess breeding and foraging habitat | Habitat checklist, condition rating |
| 7 | Comparison with a healthy pond | Research or visit a comparison site | Comparative species/water data |
| 8 | Interdependence mapping | Trace cascading effects through food web | Annotated food web with impact arrows |
| 9–10 | Ecosystem Health Report | Synthesise and write | Written report with evidence |
| 11–12 | Stewardship intervention | Plan and implement improvement action | Action plan, before/after data plan |

### Curriculum Connections

| Curriculum Objective | How the Pond Inquiry Addresses It |
|---|---|
| Food chains | Students construct a real food chain from species found in THEIR pond |
| Food webs | The full food web is built from observed organisms, not textbook examples |
| Interdependence | The algae-frog connection demonstrates cascade effects in a living system |
| Impact of changes | The algae bloom IS a change to the ecosystem — students investigate its causes and effects |
| Human impact | Students discover that human actions (garden runoff, bird feeder placement) may have caused the problem — and that human stewardship can address it |

### Ecological Literacy Outcomes

Beyond the curriculum, students develop:
1. **Systems thinking.** The pond is not a collection of individual organisms — it is a SYSTEM where everything is connected. Changing one element affects others in ways that are not always obvious.
2. **Seasonal awareness.** Through weekly visits, students notice that the pond changes through the term — species appear and disappear, plants grow and die back, water levels change. Ecosystems are dynamic, not static.
3. **Ecological reciprocity.** Students learn FROM the pond and give back TO the pond. This is Kimmerer's principle: knowledge creates responsibility. Students who understand the pond's ecology are motivated to care for it.
4. **The value of long-term observation.** A single visit gives a snapshot. Twelve weeks gives a story. Students learn that ecological understanding requires patience and repeated observation.

### Stewardship Plan

Students design their intervention based on evidence:
1. **Identify the cause.** Their investigation determines whether the algae is caused by nutrient runoff, leaf litter, or other factors.
2. **Research solutions.** For each cause, research ecologically appropriate interventions (not chemical — biological and structural).
3. **Implement.** With teacher and caretaker support, carry out the intervention.
4. **Monitor.** Establish ongoing monitoring: monthly water quality tests, termly species surveys. Next year's Year 7 continues the monitoring, comparing their data to this year's baseline. The pond becomes a long-term ecological study site.

---

## Known Limitations

1. **Ecological inquiry requires access to a real ecosystem.** Schools without ponds, gardens, or accessible natural areas face genuine constraints. However, Sobel's principle is that ANY living system — even a window box, a compost bin, or a patch of grass growing through a crack in the playground — is ecologically complex enough for investigation. The inquiry can be scaled to whatever ecosystem is available.

2. **The evidence base for ecological education is primarily qualitative.** Chawla (1998) and Sobel (1996, 2004) draw on qualitative research traditions — significant life experience narratives, case studies, and practitioner accounts. There are fewer RCTs or large-scale quantitative studies demonstrating academic attainment gains from ecological inquiry. The evidence for engagement, environmental awareness, and stewardship behaviours is stronger than the evidence for science test performance.

3. **Long-term inquiry requires institutional support.** A term-long weekly investigation needs timetable protection, outdoor access in all weather, and support from school leadership. If the inquiry is cancelled every time it rains or the field is muddy, the sustained observation principle is undermined. Teachers need to advocate for the time and conditions that make ecological inquiry possible.

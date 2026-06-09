---
# AGENT SKILLS STANDARD FIELDS (v2)
name: seeds-regenerative-inquiry-cycle
description: "Design a SEEDS regenerative inquiry cycle connecting place-based learning to ecological awareness for young learners. Use when building early childhood or primary inquiry around ecosystems and community."
disable-model-invocation: true
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "original-frameworks/seeds-regenerative-inquiry-cycle"
skill_name: "SEEDS Regenerative Inquiry Cycle"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Manning (2025) — SEEDS cycle, published in All Thoughts Subject to Change (Substack)"
  - "Manning (2025) — Metabolising Regeneration (regenerative vs restorative vs sustainable spectrum)"
  - "Kimmerer (2013) — Braiding Sweetgrass (bio-empathy, reciprocity)"
  - "Vervaeke (2019) — Relevance realisation (philosophical underpinning for the Sense stage)"
  - "Sobel (2004) — Place-based education (external validation of underlying principles)"
  - "Reggio Emilia documentation pedagogy (aligned assessment approach)"
input_schema:
  required:
    - field: "learning_group"
      type: "string"
      description: "Which age group — early childhood (5-8) or primary (8-12)"
    - field: "place_context"
      type: "string"
      description: "The specific place, ecosystem, or community that anchors the inquiry — where learning happens and what it connects to"
  optional:
    - field: "existing_problem_or_potential"
      type: "string"
      description: "A known issue or opportunity, if identified — SEEDS may begin from problem or from possibility"
    - field: "time_available"
      type: "string"
      description: "Term length, year-long, or shorter cycle"
    - field: "community_connections"
      type: "string"
      description: "People, organisations, or ecosystems available to the inquiry"
    - field: "documentation_approach"
      type: "string"
      description: "How learning will be made visible — learning stories, portfolios, observations"
output_schema:
  type: "object"
  fields:
    - field: "seeds_overview"
      type: "object"
      description: "Summary of the cycle, place anchor, and regenerative intent"
    - field: "sense_stage"
      type: "object"
      description: "Attunement activities, bio-empathy practices, baseline data gathering, knowledge gap identification"
    - field: "envision_stage"
      type: "object"
      description: "Ideation sequence, expert engagement plan, criteria-based reality testing, assessment checkpoints"
    - field: "experiment_stage"
      type: "object"
      description: "Prototyping and action plan, adaptation mechanisms, formative assessment approach"
    - field: "design_to_last_stage"
      type: "object"
      description: "Stewardship structure, care routines, handoff plan, named steward or successor"
    - field: "share_stage"
      type: "object"
      description: "Impact assessment (honest — positive, negative, intended, unintended), storytelling approach, connection back to Sense"
    - field: "documentation_plan"
      type: "object"
      description: "How learning is made visible throughout — portfolios, learning stories, observations"
    - field: "known_limitations"
      type: "object"
      description: "Honest framing about evidence base, time requirements, tension with standard school timelines"
chains_well_with:
  - "place-based-inquiry-anchor"
  - "reggio-documentation-protocol"
  - "ecological-inquiry-anchor-designer"
  - "ubuntu-collective-knowledge-task-designer"
  - "critical-thinking-task-designer"
teacher_time: "6 minutes"
tags: ["SEEDS", "regenerative", "inquiry", "place-based", "Manning", "bio-empathy", "stewardship", "cyclical", "documentation"]
---

# SEEDS Regenerative Inquiry Cycle

## What This Skill Does

This skill encodes an original practitioner framework developed by Gareth Manning, educator, curriculum designer, and learning systems designer. Unlike skills in other domains, it is not drawn from peer-reviewed research traditions. It is grounded in serious engagement with learning science, original curriculum design work, and active classroom testing. It is included because the methodology is coherent, transferable, and genuinely useful — and because intellectual honesty requires distinguishing practitioner frameworks from research-validated approaches.

SEEDS designs a five-stage regenerative inquiry cycle for early childhood and primary contexts — a learning process that grounds student inquiry in real places, real systems, and real care. SEEDS stands for **Sense → Envision → Experiment → Design to Last → Share**. Unlike linear project frameworks, SEEDS is cyclical — Share connects back to Sense, and each stage overlaps and recurses. Unlike most project-based learning frameworks, SEEDS begins with attunement and bio-empathy rather than a problem statement, and ends with stewardship structures rather than a presentation. The quality of attention at the beginning determines the quality of action at the end. It is better to stay in Envision and become knowledgeable than to act unknowingly and cause harm.

The framework draws on Kimmerer's (2013) ethic of reciprocity ("This is our work. To discover what we can give"), Vervaeke's relevance realisation as a philosophical anchor for the Sense stage, Reggio Emilia documentation pedagogy for the assessment approach, and place-based education principles (Sobel, 2004) for the grounding in real places. It was inspired by but is distinct from Green School Bali's 4S model (Freud) — acknowledging the catalyst while being clear that SEEDS is original development with a significantly different assessment philosophy. The regenerative spectrum matters: restorative (fixing damage) is the minimum; regenerative (increasing the capacity of the system to thrive) is the aim.

## Evidence Foundation

Manning (2025) developed the SEEDS cycle as a regenerative alternative to conventional PBL frameworks, published in *All Thoughts Subject to Change* (Substack). The framework addresses three limitations of standard project-based learning: (1) most PBL begins with a problem statement, which frames the world as broken and the student as fixer — SEEDS begins with attunement, which frames the world as complex and the student as participant; (2) most PBL ends with a presentation, which reduces the project to a performance — SEEDS ends with stewardship, which embeds the project in ongoing care; (3) most PBL assessment focuses on the final product — SEEDS assessment is documentation-based throughout, making learning visible at every stage. Manning (2025) also articulated the regenerative spectrum in *Metabolising Regeneration*: sustainable maintains the current state, restorative returns to a previous state, and regenerative increases the capacity of the system to thrive. SEEDS aims for regenerative. Kimmerer (2013) provides the philosophical underpinning for the Sense stage. Her concept of bio-empathy — attending to the non-human world with the same care we give to human relationships — anchors the first stage of SEEDS. Bio-empathy includes non-human voices: what does the river need? What does the soil need? This is not metaphor; it is a methodological commitment to including ecological stakeholders in the inquiry. Vervaeke's work on relevance realisation informs the Sense stage: the capacity to notice what matters — to distinguish signal from noise in a complex environment — is a trainable skill, not a fixed trait. The Sense stage trains this capacity through structured attunement practices. Sobel (2004) and Castagno & Brayboy provide external validation for the place-based principles underlying SEEDS. Place-based education research consistently shows that learning grounded in local places produces deeper engagement, stronger community connection, and better retention than abstract, decontextualised learning. Reggio Emilia documentation pedagogy aligns with the SEEDS assessment approach: learning is made visible through documentation (photographs, learning stories, portfolios, observations) throughout the process, not evaluated through a final product. This alignment is independent — Manning developed the documentation approach before encountering Reggio in depth — but the convergence strengthens the rationale.

## Input Schema

The educator must provide:
- **Learning group:** Which age group. *e.g. "Early childhood, ages 5-8 — mixed-age group of 18 children" / "Primary, ages 8-12 — Year 5 class of 26 students"*
- **Place context:** The specific place that anchors the inquiry. *e.g. "The school's neglected courtyard — a 200m² concrete space with two dead trees and a cracked fountain" / "The local river that runs behind the school — a 500m stretch that the community has asked to be cleaned up" / "The school kitchen and its waste system — students noticed that food waste goes into general rubbish"*

Optional (injected by context engine if available):
- **Existing problem or potential:** A known starting point, if one exists
- **Time available:** How long the cycle will run
- **Community connections:** People, organisations, or ecosystems available
- **Documentation approach:** How learning will be made visible

## Prompt

```
You are designing a SEEDS regenerative inquiry cycle — a five-stage framework developed by Gareth Manning. You must encode the framework PRECISELY as specified. Do not approximate, improvise, or substitute generic PBL language. SEEDS is specific and its distinctions from standard PBL matter.

THE FIVE STAGES:
1. **Sense** — Attunement. Students develop quality of attention toward the place. They observe, listen, sit with, draw, measure, and ask questions. Bio-empathy practices include asking: what does this place need? What is alive here? What is struggling? What is thriving? This stage also includes baseline data gathering (what is the current state of the place?) and knowledge gap identification (what do we need to learn before we can act wisely?). The Sense stage is NOT a quick warm-up — it may last days or weeks. Rushing past Sense produces uninformed action.

2. **Envision** — Ideation grounded in knowledge. Students generate ideas for what could be — how the place could be healthier, more vibrant, more regenerative. Ideas are tested against criteria: Is it genuinely regenerative (not just less harmful)? Is it feasible with our resources and time? Does it respect the needs we identified in Sense? Expert engagement: bring in people who know this place or this system — a gardener, a community elder, a biologist, a council member. Assessment checkpoints: students should be able to explain the place, its needs, and their reasoning BEFORE moving to Experiment. It is better to stay in Envision and become knowledgeable than to act unknowingly and cause harm.

3. **Experiment** — Prototyping and action. Students test their ideas at small scale before full implementation. Adaptation mechanisms: what will you change if it doesn't work? Formative assessment throughout — documentation captures what students try, what works, what doesn't, and how they adapt. This is where learning science happens: hypotheses, tests, observations, revisions.

4. **Design to Last** — Stewardship, not presentation. The question is not "How will we present this?" but "How will this continue after we're done?" Stewardship structures: who will care for this next term? Next year? Care routines: what needs to happen daily, weekly, seasonally? Handoff plan: how is knowledge transferred to the next group? Named steward or successor: a specific person, group, or structure that takes responsibility. "Design to Last" is the stage that distinguishes SEEDS from conventional PBL — it embeds learning in ongoing responsibility rather than ending it with a product.

5. **Share** — Honest impact assessment and storytelling. Impact assessment must be honest: positive, negative, intended, AND unintended effects. Not a celebration — a reckoning with what actually happened. Storytelling approach: how do we communicate what we learned and what we did, so others can build on it? Connection back to Sense: Share feeds into the next cycle. What do we notice NOW about this place? What has changed? What needs attention next? The cycle is regenerative because it doesn't end — it spirals.

CRITICAL DISTINCTIONS (encode these in the output):
- SEEDS is CYCLICAL, not linear — Share feeds back into Sense
- Begins with QUALITY OF ATTENTION, not identification of a problem
- Bio-empathy includes NON-HUMAN voices — not just human stakeholder empathy
- Assessment is DOCUMENTATION-BASED throughout, not product-focused at the end
- "Design to Last" is NOT the same as "present" — stewardship is the point
- The REGENERATIVE SPECTRUM matters: restorative is minimum, regenerative is the aim
- It is BETTER TO STAY IN ENVISION and become knowledgeable than to act unknowingly and cause harm

Your task is to design a SEEDS cycle for:

**Learning group:** {{learning_group}}
**Place context:** {{place_context}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Existing problem or potential:** {{existing_problem_or_potential}} — if not provided, the Sense stage will surface the inquiry direction.
**Time available:** {{time_available}} — if not provided, design for a full term (10-12 weeks).
**Community connections:** {{community_connections}} — if not provided, identify the connections that would strengthen the inquiry and suggest how to find them.
**Documentation approach:** {{documentation_approach}} — if not provided, recommend a documentation approach appropriate for the age group.

Return your output in this exact format:

## SEEDS Regenerative Inquiry Cycle: [Place Context]

**Place anchor:** [The place, ecosystem, or community]
**Learning group:** [Age range and context]
**Regenerative intent:** [One sentence — what regenerative outcome this cycle aims for]
**Cycle duration:** [How long]

### SEEDS Overview

[Summary of the cycle — what will happen across the five stages, how they connect, and why this place is the right anchor for regenerative inquiry with this group]

### Stage 1: Sense — Attunement

**Duration:** [How long this stage should last — do not rush it]
**Core question:** "What is alive here? What does this place need?"

**Attunement activities:**
[Specific activities that develop quality of attention — observation, sensory engagement, sitting with the place]

**Bio-empathy practices:**
[Activities that extend empathy to non-human elements — what does the soil need? What is the water telling us?]

**Baseline data gathering:**
[What to measure, observe, and document about the current state]

**Knowledge gap identification:**
[What do students need to learn before they can act wisely? What expertise is needed?]

**Documentation during Sense:**
[How learning is made visible at this stage — photographs, drawings, observations, questions recorded]

### Stage 2: Envision — Grounded Ideation

**Duration:** [How long]
**Core question:** "What could this place become? What would genuinely regenerative look like?"

**Ideation sequence:**
[How students generate and develop ideas — grounded in what they learned in Sense]

**Expert engagement plan:**
[Who to bring in and why — people who know this place or this system]

**Reality testing criteria:**
[How to test whether ideas are genuinely regenerative, feasible, and respectful of the place's needs]

**Assessment checkpoint:**
[What students should be able to explain before moving to Experiment — if they can't, stay in Envision]

### Stage 3: Experiment — Prototyping and Action

**Duration:** [How long]
**Core question:** "Does this work? What needs to change?"

**Prototyping plan:**
[Small-scale tests before full implementation]

**Adaptation mechanisms:**
[What to do when things don't work — how to revise, pivot, or return to Envision]

**Formative assessment approach:**
[How learning is documented and assessed throughout — not just at the end]

### Stage 4: Design to Last — Stewardship

**Duration:** [How long]
**Core question:** "How will this continue after we're done?"

**Stewardship structure:**
[Who will care for this? What does ongoing maintenance look like?]

**Care routines:**
[Daily, weekly, and seasonal care tasks]

**Handoff plan:**
[How knowledge and responsibility transfer to the next group]

**Named steward or successor:**
[A specific person, group, or structure that takes ongoing responsibility]

### Stage 5: Share — Honest Impact Assessment

**Duration:** [How long]
**Core question:** "What actually happened — intended AND unintended?"

**Impact assessment:**
[Honest reckoning — positive effects, negative effects, intended outcomes, unintended outcomes]

**Storytelling approach:**
[How students communicate what they learned and did — for others to build on]

**Connection back to Sense:**
[How Share feeds into the next cycle — what do we notice NOW? What needs attention next?]

### Documentation Plan

[How learning is made visible across ALL five stages — the specific documentation tools, routines, and products]

### Known Limitations

[Honest framing — this is a practitioner framework, not a peer-reviewed methodology. Include: evidence base limitations, time requirements, tension with standard school timelines, and where teacher judgment is essential]

**Self-check before returning output:** Verify that (a) all five SEEDS stages are present and distinct, (b) the cycle is framed as cyclical not linear, (c) bio-empathy includes non-human voices, (d) Design to Last specifies stewardship not presentation, (e) Share includes honest impact assessment, (f) documentation is embedded throughout not just at the end, and (g) the regenerative spectrum is referenced.
```

## Example Output

**Scenario:** *Learning group: "Primary, ages 8-12 — mixed-age group of 22 students" / Place context: "The school's neglected courtyard — a 200m² concrete space with two dead planters, a cracked bench, and a drain that floods in heavy rain. The space is currently unused except as a cut-through. The head teacher has agreed the students can work on it" / Time available: "Full term, 10 weeks, with 3 hours per week dedicated to the cycle" / Community connections: "A parent who is a landscape architect, a local community garden 500m away, the school caretaker who knows the drainage history"*

---

## SEEDS Regenerative Inquiry Cycle: School Courtyard

**Place anchor:** The school's neglected 200m² courtyard
**Learning group:** Mixed-age primary, ages 8-12, 22 students
**Regenerative intent:** Transform a dead concrete space into a living system that students, soil organisms, and the school community actively sustain — not just a garden, but a functioning micro-ecosystem with a stewardship culture
**Cycle duration:** 10 weeks (30 hours total)

### SEEDS Overview

This cycle takes a neglected courtyard — currently concrete, cracked, and ignored — and asks students to develop a relationship with it before changing it. The temptation will be to jump to planting. SEEDS resists that temptation. Students spend the first three weeks in Sense and Envision: observing the space, investigating its systems (drainage, sun exposure, soil beneath the concrete, existing life), identifying what the space needs, and developing a regenerative vision grounded in knowledge. Only then do they Experiment — testing ideas at small scale. Design to Last ensures the courtyard doesn't become another neglected project after the term ends. Share honestly assesses what was achieved and what wasn't, feeding into the next cycle.

### Stage 1: Sense — Attunement

**Duration:** 2.5 weeks (weeks 1-2, half of week 3)
**Core question:** "What is alive here? What does this place need?"

**Attunement activities:**
- **Silent sit (week 1, session 1).** Students sit in the courtyard for 15 minutes in silence. No phones, no notebooks initially. Just sit. After 15 minutes: "What did you notice? What surprised you?" Record observations. Repeat on three different days at different times — morning, midday, afternoon — to notice how light, sound, and activity change.
- **Sensory mapping (week 1, session 2).** In pairs, students create a sensory map of the courtyard: what they SEE (concrete, cracks, weeds in cracks, a drain, a wall), HEAR (traffic from the road, birds on the roof, wind), FEEL (temperature of concrete vs. shade, roughness of bench), SMELL (damp near the drain, nothing from the planters). This trains quality of attention.
- **Life audit (week 2).** Students systematically search for every living thing in the courtyard: weeds in cracks, moss on the wall, insects, spiders, birds visiting. Document each with a photograph and drawing. The courtyard is not dead — it is neglected. What is already surviving here?

**Bio-empathy practices:**
- **"What does the rain think of this place?"** (week 2). When it rains, students observe where water goes. Does it pool? Does it drain? Does it nourish anything? Ask: if you were the rain, would you want to land here? Where would you go? This is not fantasy — it is a way of attending to the water system with empathy.
- **"What would the soil say?"** Students investigate whether there is soil under the concrete (ask the caretaker about the courtyard's history). If concrete were removed in one area, what might grow? What organisms live in soil? What do they need?

**Baseline data gathering:**
- Measure the courtyard: area, sun exposure (track shadows at 9am, 12pm, 3pm), drainage patterns, temperature (concrete surface vs. shaded wall)
- Photograph from four fixed points — these become the "before" images for the impact assessment
- Interview the caretaker: What is the drainage history? When was the courtyard last used? What's under the concrete?
- Soil test: if there is exposed soil anywhere (cracks, planter edges), test pH and structure

**Knowledge gap identification:**
Students generate a "What we need to learn" list:
- How do drainage systems work?
- What plants survive in partial shade on poor soil?
- How do you remove concrete safely?
- What makes a micro-ecosystem self-sustaining?
- What does "regenerative" mean (vs. just "less bad")?

**Documentation during Sense:**
- Learning journals: each student keeps a courtyard journal with observations, drawings, questions, and data
- Photographs: weekly photos from the four fixed points
- Class "wonder wall": questions posted on a shared board, sorted into "we can answer" and "we need help with"

### Stage 2: Envision — Grounded Ideation

**Duration:** 1.5 weeks (second half of week 3, week 4)
**Core question:** "What could this place become? What would genuinely regenerative look like?"

**Ideation sequence:**
- **Individual vision drawings (week 3).** Each student draws their vision for the courtyard. No constraints yet — dream big. Then share in small groups: what's similar? What's different?
- **Regenerative spectrum lesson (week 3).** Teach the distinction: SUSTAINABLE means it stays the same. RESTORATIVE means it goes back to how it was. REGENERATIVE means it becomes MORE alive than before — the system's capacity to thrive increases. Ask: which is our courtyard project aiming for? (Regenerative.)
- **Group synthesis (week 4).** Combine individual visions into 3-4 group proposals. Each proposal must answer: What will be alive here that isn't alive now? How will it sustain itself? Who will care for it?

**Expert engagement plan:**
- **Landscape architect parent (week 3 or 4):** Invite to review group proposals. Ask them: Is this feasible? What are we not thinking about? What would a professional do differently?
- **Community garden visit (week 4):** Take students to the local community garden. Ask the gardeners: How did you start? What failed? What do you wish you'd known? How do you sustain it?
- **School caretaker (ongoing):** The caretaker is a critical stakeholder — they will live with whatever the students create. Their practical knowledge of the space is irreplaceable.

**Reality testing criteria:**
Each group proposal is tested against:
1. Is it genuinely regenerative? (Does it increase the capacity of the space to support life, or just make it look nicer?)
2. Is it feasible with our time, budget, and skills? (Can 22 students actually do this in 6 weeks?)
3. Does it respect what we learned in Sense? (Does it address the drainage, the sun exposure, the existing life?)
4. Can it last? (Will it survive the summer holidays without us?)

**Assessment checkpoint:**
Before moving to Experiment, each student must be able to explain: (a) what the courtyard is like now and why, (b) what their group proposes and why it's regenerative (not just nice), and (c) what they still need to learn. If they cannot, the group stays in Envision until they can.

### Stage 3: Experiment — Prototyping and Action

**Duration:** 3 weeks (weeks 5-7)
**Core question:** "Does this work? What needs to change?"

**Prototyping plan:**
- **Week 5: Small-scale tests.** Before transforming the whole courtyard, test key elements at small scale. If the plan includes planting: plant one test area and observe for a week. If the plan includes removing concrete: test removing one section and see what's underneath. If the plan includes a water feature: test the drainage with a bucket experiment first.
- **Weeks 6-7: Implementation.** Based on test results, implement the agreed plan. Divide into working teams: planting team, construction team (raised beds, seating), documentation team (photographing, measuring, recording). Rotate teams so all students experience all aspects.

**Adaptation mechanisms:**
- **Weekly review (end of each session):** What's working? What isn't? What do we need to change? Document decisions and rationale.
- **Pivot protocol:** If something fails (plants die, drainage doesn't work, concrete won't come up), return to Envision with new information. Failure is data, not defeat.

**Formative assessment approach:**
- Documentation continues: photographs, journal entries, and data collection at every session
- Skills assessment: can students use tools safely? Can they follow a planting plan? Can they measure and record accurately?
- Collaboration assessment: are students working interdependently? Who is contributing what?

### Stage 4: Design to Last — Stewardship

**Duration:** 1.5 weeks (week 8, first half of week 9)
**Core question:** "How will this continue after we're done?"

**Stewardship structure:**
- **Courtyard Committee:** A rotating group of 4 students (refreshed each half-term) responsible for weekly checks. Older students (ages 10-12) serve first and train younger students to take over.
- **Teacher sponsor:** One teacher agrees to oversee the committee — not to do the work, but to ensure the committee functions.

**Care routines:**
- **Daily:** Check water levels for any planted areas (assigned to a daily classroom rota, not the committee alone)
- **Weekly:** Committee walks the courtyard with a checklist — plants healthy? Seating clean? Drainage clear? Any damage? Report to the class.
- **Seasonally:** Spring planting, autumn cleanup, winter protection for vulnerable plants. These tasks are scheduled into next term's calendar NOW, not left to chance.

**Handoff plan:**
- **Courtyard Guide:** Students create a physical guide (laminated, stored in the courtyard) that explains: what's planted where, what it needs, what to do each season, and who to contact if something goes wrong.
- **Next-group induction:** The current group presents the courtyard to the NEXT group of students who will inherit it — explaining the history, the design choices, and the care routines. This is the real "presentation" — not to impress, but to transfer responsibility.

**Named steward or successor:**
The first Courtyard Committee (4 named students) + the teacher sponsor. The committee structure is designed to outlast any individual — new members are inducted each half-term.

### Stage 5: Share — Honest Impact Assessment

**Duration:** 1 week (second half of week 9, week 10)
**Core question:** "What actually happened — intended AND unintended?"

**Impact assessment:**
Students conduct an honest audit:
- **Positive intended effects:** What did we plan to achieve that we actually achieved? (More life, better drainage, a usable space)
- **Positive unintended effects:** What good things happened that we didn't plan? (Younger students started using the space for reading; a bird nested in the new planting)
- **Negative intended effects:** Did any of our deliberate actions cause harm? (Did removing concrete expose roots? Did new planting displace existing weeds that were supporting insects?)
- **Negative unintended effects:** What went wrong that we didn't anticipate? (The raised bed blocks the caretaker's access route; one plant species is actually invasive)

This is NOT a celebration. It is a reckoning. Honest impact assessment is the foundation of regenerative practice — you cannot improve what you refuse to see.

**Storytelling approach:**
Students create a visual timeline of the cycle — from the first silent sit to the stewardship handoff — using their photographs, journal excerpts, and data. The timeline tells the REAL story, including failures and pivots, not a polished success narrative. This timeline is displayed in the courtyard itself — so future students see the process, not just the product.

**Connection back to Sense:**
In the final session, students return to the courtyard and sit in silence for 15 minutes — just as they did in week 1. Then: "What do you notice NOW that you didn't notice in week 1? What has changed? What still needs attention?" These new observations feed into the next cycle. The SEEDS cycle does not end — it spirals.

### Documentation Plan

**Throughout all five stages:**
- **Student journals:** Each student maintains a courtyard journal — observations, drawings, data, questions, reflections. This is their personal documentation and a key assessment artefact.
- **Fixed-point photography:** Weekly photographs from four fixed points in the courtyard — creates a visual record of change over the 10 weeks.
- **Class documentation wall:** A physical or digital display updated weekly showing: current stage, key observations, decisions made, and questions being investigated.
- **Learning stories (teacher-authored):** The teacher writes 2-3 learning stories per week — narrative accounts of significant learning moments, with photographs. These are the primary assessment documents, aligned with Reggio documentation pedagogy.

---

## Known Limitations

1. **SEEDS is an original practitioner framework, not a peer-reviewed methodology.** It has been developed and tested in specific educational contexts (Manning's work at REAL School Budapest and related projects) but has not been subjected to controlled experimental evaluation. The underlying principles align with peer-reviewed research (place-based education, documentation pedagogy, formative assessment), but the specific SEEDS framework and its five-stage structure are Manning's original design.

2. **SEEDS requires significant time — more than most school timetables allow.** A full SEEDS cycle at the depth described above requires 10-12 weeks with dedicated time each week. Schools with rigid timetables, subject-specific teaching, and exam pressure may find it difficult to allocate this time. Shorter adaptations are possible (6-week cycles with reduced Sense and Envision stages) but they sacrifice the attunement that makes SEEDS distinctive.

3. **The Sense stage feels slow — and may face resistance.** Teachers accustomed to action-oriented PBL may want to skip Sense or reduce it to a single lesson. Students may feel frustrated: "When do we actually DO something?" The Sense stage is deliberately slow because the quality of attention at the beginning determines the quality of action at the end. This requires trust from both teacher and students that the slowness is productive.

4. **Bio-empathy is philosophically grounded but methodologically imprecise.** Asking "What does the soil need?" is a generative prompt for inquiry, not a scientific method. It can produce genuine ecological insight (the soil needs organic matter, moisture, microbial life) or vague anthropomorphism (the soil is "sad"). The teacher's role is to guide students from empathic prompts toward scientific investigation — using the empathy as a doorway, not a destination.

5. **Stewardship depends on institutional continuity.** The Design to Last stage requires that the school sustain the stewardship structure — the Courtyard Committee, the care routines, the seasonal calendar — beyond the original group of students. If the school doesn't commit to this continuity, the courtyard will revert to neglect, and students will learn that their work doesn't matter. The teacher must have institutional support before committing to the stewardship promise.

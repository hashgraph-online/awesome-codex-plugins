---
# AGENT SKILLS STANDARD FIELDS (v2)
name: outdoor-learning-sequence-designer
description: "Design a structured outdoor learning sequence embedding curriculum objectives in an available outdoor space. Use when planning lessons in school grounds, parks, or local natural environments."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "environmental-experiential-learning/outdoor-learning-sequence-designer"
skill_name: "Outdoor Learning Sequence Designer"
domain: "environmental-experiential-learning"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Education Endowment Foundation (2019) — Outdoor Adventure Learning systematic review"
  - "Rickinson, Dillon, Teamey, Morris, Choi, Sanders & Benefield (2004) — A Review of Research on Outdoor Learning"
  - "Waite (2011) — Children learning outside the classroom: from birth to eleven"
  - "Beames, Higgins & Nicol (2012) — Learning Outside the Classroom: theory and guidelines for practice"
  - "Mannion, Mattu & Wilson (2015) — Teaching, learning and play in the outdoors"
input_schema:
  required:
    - field: "learning_objective"
      type: "string"
      description: "The specific curriculum content or skill students will learn — what the outdoor activity is FOR, educationally"
    - field: "outdoor_space"
      type: "string"
      description: "The available outdoor space — school grounds, local park, woodland, field, playground, garden"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "class_size"
      type: "string"
      description: "Number of students and available adult support"
    - field: "time_available"
      type: "string"
      description: "How long the outdoor session lasts"
    - field: "weather_constraints"
      type: "string"
      description: "Season, typical weather, any constraints"
    - field: "risk_factors"
      type: "string"
      description: "Known risks — traffic, water, terrain, student needs"
output_schema:
  type: "object"
  fields:
    - field: "outdoor_sequence"
      type: "object"
      description: "The complete outdoor learning sequence — indoor preparation, outdoor activity, indoor follow-up"
    - field: "learning_design"
      type: "object"
      description: "How the outdoor element serves the learning objective — what can be learned outside that cannot be learned inside"
    - field: "safety_framework"
      type: "object"
      description: "Risk-benefit assessment, safety procedures, adult roles"
    - field: "indoor_outdoor_continuity"
      type: "object"
      description: "How the indoor and outdoor elements connect — the outdoor learning is not a separate activity but part of a coherent sequence"
chains_well_with:
  - "ecological-inquiry-anchor-designer"
  - "place-based-inquiry-anchor"
  - "biophilic-learning-environment-designer"
  - "awe-wonder-experience-designer"
teacher_time: "4 minutes"
tags: ["outdoor-learning", "EEF", "Rickinson", "outside-classroom", "fieldwork", "nature", "experiential"]
---

# Outdoor Learning Sequence Designer

## What This Skill Does

Designs a structured outdoor learning sequence where the outdoor element serves a specific curriculum learning objective — not as a reward, a change of scene, or a general wellbeing activity, but as a learning experience that exploits what the outdoor environment uniquely offers. The critical principle from Rickinson et al.'s (2004) review is that outdoor learning is most effective when it has clear learning intentions, is connected to indoor learning (preparation before, follow-up after), and involves students in active inquiry using the outdoor environment as a primary resource. The output includes the complete sequence (indoor preparation, outdoor activity, indoor follow-up), a learning design explaining why the outdoor element serves the objective better than an indoor alternative, a safety framework, and indoor-outdoor continuity planning. AI is specifically valuable here because designing effective outdoor learning requires simultaneously considering curriculum alignment (what are students learning?), environmental opportunities (what does this specific space offer?), practical logistics (safety, weather, timing), and pedagogical design (how to structure the activity for maximum learning) — a multi-dimensional planning challenge.

## Evidence Foundation

The Education Endowment Foundation (2019) conducted a systematic review of outdoor adventure learning, finding moderate but consistent positive effects on academic outcomes (particularly for disadvantaged pupils) and stronger effects on non-cognitive outcomes including self-confidence, self-efficacy, motivation, and teamwork. Critically, the EEF found that structured outdoor learning with clear learning objectives produced better outcomes than unstructured outdoor time. Rickinson et al. (2004) produced the most comprehensive review of outdoor learning research, identifying three key contexts: fieldwork and outdoor visits (linked to school subjects), outdoor adventure education (residential, team-building), and school grounds and community projects. They found that well-designed fieldwork improved long-term memory of subject content, developed practical inquiry skills, and increased engagement — but that poorly designed outdoor activities (unclear purpose, weak connection to curriculum) produced little learning benefit beyond enjoyment. Waite (2011) focused on younger children, showing that outdoor environments naturally support active, sensory, exploratory learning that is constrained by indoor classrooms. Beames, Higgins & Nicol (2012) proposed a "pedagogy of place" for outdoor learning, arguing that the physical environment should be the starting point for planning — not the curriculum content mapped onto an outdoor location, but the learning opportunities the location itself offers. Mannion, Mattu & Wilson (2015) documented effective outdoor learning in Scottish schools, emphasising that the best outdoor learning sequences include three phases: anticipation (preparation), encounter (the outdoor experience), and recollection (reflection and follow-up).

## Input Schema

The teacher must provide:
- **Learning objective:** What students will learn. *e.g. "Measuring angles and distances — Year 7 Mathematics" / "Understanding habitats and adaptation — Year 4 Science" / "Descriptive writing using sensory detail — Year 6 English" / "Map skills and compass use — Year 8 Geography"*
- **Outdoor space:** What's available. *e.g. "School playing field — flat grass area, some trees around the perimeter, a pond in the conservation area" / "Local woodland — 15-minute walk from school, paths, stream, varied terrain" / "School playground — tarmac, benches, some planters, view of the local area"*

Optional (injected by context engine if available):
- **Student level:** Year group
- **Subject area:** The curriculum subject
- **Class size:** Numbers and adult support
- **Time available:** Duration of outdoor session
- **Weather constraints:** Season and conditions
- **Risk factors:** Known hazards

## Prompt

```
You are an expert in outdoor learning design, with deep knowledge of the Education Endowment Foundation's (2019) systematic review of outdoor adventure learning, Rickinson et al.'s (2004) comprehensive review of outdoor learning research, Waite's (2011) research on children learning outside the classroom, Beames, Higgins & Nicol's (2012) pedagogy of place, and Mannion, Mattu & Wilson's (2015) three-phase outdoor learning model. You understand that outdoor learning is most effective when it is STRUCTURED (clear learning objectives, not just "go outside"), CONNECTED (linked to indoor learning before and after), and EXPLOITS THE UNIQUE FEATURES OF THE OUTDOOR ENVIRONMENT (teaches something that cannot be taught as well indoors).

CRITICAL PRINCIPLES:
- **The outdoor element must serve the learning objective.** If the lesson could be taught just as effectively indoors, there is no educational reason to go outside. The outdoor environment must offer something the classroom cannot: real specimens, authentic contexts, spatial scale, sensory experience, or direct observation of phenomena.
- **Three-phase design: preparation → encounter → reflection.** Following Mannion et al. (2015), the outdoor session is the middle of a sequence, not a standalone activity. Indoor preparation builds the knowledge and skills students need to learn effectively outdoors. The outdoor encounter is the core learning experience. Indoor follow-up consolidates, analyses, and extends what was learned outside.
- **Active inquiry, not passive observation.** Students should DO something outdoors, not just look at things. Collect data. Measure. Sketch. Sample. Record. Compare. The outdoor environment is a laboratory, not a museum.
- **Safety through risk-benefit analysis, not risk elimination.** Outdoor learning involves risks (weather, terrain, traffic, water). The approach is not to eliminate all risk (which would also eliminate the learning) but to assess the BENEFITS against the risks and manage the risks to an acceptable level. A child who never encounters managed risk never develops risk assessment skills.
- **Weather is a feature, not a bug.** Rain, wind, cold, and heat are learning conditions, not cancellation conditions. "There's no such thing as bad weather, only bad clothing" (Norwegian proverb). Design the session to work in the weather that's likely, not just in ideal conditions.

Your task is to design an outdoor learning sequence for:

**Learning objective:** {{learning_objective}}
**Outdoor space:** {{outdoor_space}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for a general school-age context.
**Subject area:** {{subject_area}} — if not provided, infer from the learning objective.
**Class size:** {{class_size}} — if not provided, design for 30 students with one teacher and one teaching assistant.
**Time available:** {{time_available}} — if not provided, design for a 60-minute session (including transition time).
**Weather constraints:** {{weather_constraints}} — if not provided, design for a temperate climate with a rain contingency.
**Risk factors:** {{risk_factors}} — if not provided, include standard outdoor risk assessment guidance.

Return your output in this exact format:

## Outdoor Learning Sequence: [Learning Objective]

**Learning objective:** [What students will learn]
**Outdoor space:** [Where]
**Why outdoors?** [Specifically what the outdoor environment offers that the classroom cannot]

### Phase 1 — Preparation (Indoor)

[What students need to know, practise, or prepare before going outside — builds the knowledge needed for the outdoor activity to be effective]

### Phase 2 — Encounter (Outdoor)

**Setup:** [How to organise students, distribute equipment, establish boundaries]
**Activity:** [Step-by-step outdoor learning activity — what students do, in what order]
**Teacher role:** [What the teacher does during the outdoor activity — circulating, questioning, managing]
**Key questions to ask outdoors:** [Specific questions that direct students' attention to the learning objective]

### Phase 3 — Reflection (Indoor)

[How to consolidate the outdoor learning — what students do with the data/observations/experiences they collected outside]

### Safety Framework

**Risk-benefit assessment:**
| Risk | Likelihood | Severity | Benefit | Management |
|---|---|---|---|---|
| [Risk 1] | [L/M/H] | [L/M/H] | [What learning benefit justifies this risk] | [How to manage it] |

**Weather contingency:** [What to do if weather changes — adapt, not cancel]
**Adult roles:** [Who does what — teacher, TA, parent helpers]

### Indoor-Outdoor Continuity

[How the three phases connect — the outdoor session is not a separate event but the middle of a coherent learning sequence]

### Equipment and Resources

[What's needed — kept practical and minimal]

**Self-check before returning output:** Verify that (a) the outdoor element serves the learning objective specifically, (b) the three-phase design is complete, (c) students are actively inquiring outdoors, not passively observing, (d) the safety framework uses risk-benefit analysis, and (e) the indoor and outdoor phases are connected.
```

## Example Output

**Scenario:** *Learning objective: "Descriptive writing using sensory detail — Year 6 English. Students need to write descriptions that use all five senses, specific vocabulary, and figurative language (similes, metaphors, personification). Current work is weak — descriptions are generic and rely on sight alone." / Outdoor space: "School grounds — a conservation area with a small pond, trees (including a large oak), a meadow area, and a sensory garden planted by Year 3 last year. Also the main playground (tarmac) and the school building itself." / Time available: "60 minutes for the outdoor session; preparation and follow-up in normal English lessons either side." / Weather constraints: "March — could be sunny, cold, rainy, or any combination. Unpredictable."*

---

## Outdoor Learning Sequence: Sensory Description Writing — Year 6

**Learning objective:** Writing descriptions that use all five senses, specific vocabulary, and figurative language
**Outdoor space:** School conservation area — pond, trees, meadow, sensory garden
**Why outdoors?** The classroom is a sensory desert — the same sounds (chair scraping, clock ticking), the same smells (whiteboard markers, lunch from the hall), the same textures (desk, pencil, paper). Students cannot write rich sensory descriptions if they have nothing to sense. The outdoor environment provides authentically complex sensory input: the smell of damp earth, the sound of wind through branches, the texture of bark, the sight of light on water, the taste of wild garlic (if present and safe). Students who EXPERIENCE sensory richness write more specifically than students who are told to "imagine sensory detail."

### Phase 1 — Preparation (Indoor, 30 minutes, previous lesson)

**Mini-lesson: Sensory vocabulary audit.**
Give students a chart with five columns: See, Hear, Touch, Smell, Taste. Challenge: "Describe this classroom using ALL five senses. Write at least three specific details per sense." Students will find that: sight is easy, hearing is possible, touch is limited, smell is limited, taste is almost impossible. This reveals the problem: generic environments produce generic descriptions.

**Model text analysis.** Read a short extract of powerful descriptive writing (e.g., from a Robert Macfarlane nature essay or a Ted Hughes poem). Students identify: which senses are used? Which details are SPECIFIC (not just "green" but "the sharp green of new nettles")? Which use figurative language?

**Preparation for outdoor session:** Issue "Sensory Field Notebooks" — folded A4 with sections for each sense. Explain the task: "Tomorrow you will be a writer in the field. Your job is to COLLECT sensory details like a scientist collects specimens. You will take them back to the classroom and use them to write."

### Phase 2 — Encounter (Outdoor, 60 minutes)

**Setup (5 minutes):**
Walk to the conservation area. At the entrance, stop. "Before you write ANYTHING, stand still for 60 seconds. Close your eyes. Listen. What can you hear?" This transition from indoor to outdoor is deliberate — it slows students down and shifts their attention from social chatter to environmental awareness.

**Activity 1 — Sensory stations (30 minutes):**
Students rotate through five stations, spending 5–6 minutes at each. At each station they record in their Sensory Field Notebook.

| Station | Location | Sensory Focus | Task |
|---|---|---|---|
| 1: The Listening Post | Under the oak tree | Hearing | Close your eyes for 2 minutes. Write every sound you hear — near and far, loud and quiet. Be SPECIFIC: not "bird" but "two sharp, rising notes, then a pause, then three more." |
| 2: The Texture Trail | Along the hedge/tree line | Touch | Touch 5 different natural surfaces (bark, leaf, soil, stone, moss). For each: write exactly what it feels like. Use a simile: "the bark felt like..." |
| 3: The Smell Map | Sensory garden | Smell | Crush a leaf gently between your fingers. Smell the soil. Smell the air. Write: what does this place smell like? Can you describe a smell without using another smell? (This is HARD — which is the point.) |
| 4: The Sight Snapshot | By the pond | Sight (but SPECIFIC) | Choose one small area (no bigger than your hand). Describe EXACTLY what you see — colours, shapes, movement, light. The rule: no generic words. Not "green" but WHICH green? Not "water" but what does the water look like right now? |
| 5: The Whole Place | Meadow area | All senses combined | Stand in the meadow. Write a "panoramic description" — sweep from left to right and describe what you experience through ALL senses. This is the combination: sight + sound + smell + touch + (if applicable) taste. |

**Activity 2 — Figurative language hunt (15 minutes):**
After the stations, gather the class: "Now find ONE thing in this environment that reminds you of something completely different. The pond that looks like a mirror. The branches that reach like fingers. The wind that whispers. Find YOUR comparison and write it down with the REASON — why does it remind you of that?"

**Teacher role:** Circulate between stations. Ask the KEY questions (below). Read over shoulders. Identify students whose writing is still generic ("the tree was brown") and redirect: "Closer. WHICH brown? Touch it. Close your eyes. Now describe." Also identify students whose writing is exceptional and note it for sharing in Phase 3.

**Key questions to ask outdoors:**
- "Close your eyes. What do you hear NOW that you didn't notice before?"
- "You wrote 'the bark was rough.' Rough like sandpaper? Rough like a cheese grater? Rough like your dad's chin? WHICH rough?"
- "What does this smell remind you of? Can you capture that in words?"
- "If you had to describe this place to someone who has never been here, what ONE detail would you choose?"

**Wrap-up (10 minutes):** Return to classroom. "Don't lose your notebooks. Everything you collected outside is the raw material for tomorrow's writing."

### Phase 3 — Reflection (Indoor, 45 minutes, next lesson)

**Step 1 — Mining the field notes (10 minutes):** Students review their Sensory Field Notebooks. Highlight their three BEST details — the most specific, the most vivid, the most surprising. Share with a partner: "Which of my details is strongest?"

**Step 2 — Drafting (25 minutes):** Students write a descriptive passage about the conservation area using their field notes as the primary source material. Requirements: at least three senses used, at least two figurative language devices, no generic vocabulary (teacher provides a "banned words" list: nice, good, big, small, pretty, green — use MORE SPECIFIC alternatives).

**Step 3 — Peer review (10 minutes):** Swap descriptions. Partner reads and answers: "Which ONE detail made you feel like you were THERE? Where could the description be more specific?"

### Safety Framework

**Risk-benefit assessment:**

| Risk | Likelihood | Severity | Benefit | Management |
|---|---|---|---|---|
| Slipping on wet ground | Medium (March) | Low | Access to authentic sensory environment; rain ADDS sensory detail | Remind students to wear appropriate footwear. Walk, don't run. Highlight wet areas. |
| Pond — falling in | Low | Medium | Pond station provides rich visual and auditory detail (water surface, reflections, sounds) | Clear boundary markers 1 metre from pond edge. Adult stationed at pond. Students observe from bank only. |
| Allergic reaction (plants, pollen) | Low | Medium | Direct sensory engagement with plants | Check medical records before the session. Students with hay fever or plant allergies adapt the smell station (observe, don't crush leaves). Carry antihistamines if prescribed. |
| Cold / rain | High (March) | Low | Weather IS sensory material — rain sounds, wet smells, cold touch are writing material | Require coats. Brief session to 45 min if very cold. Rain plan: go out anyway — rain produces better sensory writing than sunshine. Only cancel for storm or lightning. |

**Weather contingency:** Light rain — proceed, bring clipboards with covers. Heavy rain — shorten to 30 minutes, focus on the most sheltered stations. Lightning — postpone.

**Adult roles:** Teacher circulates and questions. TA manages transitions between stations and monitors the pond area. If parent helpers available: one per station to prompt reluctant writers.

### Indoor-Outdoor Continuity

The three phases form ONE learning sequence:
- **Preparation** builds the analytical vocabulary (sensory categories, figurative language types) students need to collect useful data outdoors
- **Encounter** provides the raw sensory material that cannot be generated indoors — real smells, real textures, real sounds
- **Reflection** transforms raw sensory data into crafted writing — the outdoor notes are the EVIDENCE, the indoor lesson is the COMPOSITION

The outdoor session is not "a fun trip" with writing attached. The writing depends on the outdoor experience. Without the field notes, students have nothing to write from.

### Equipment and Resources

- Sensory Field Notebooks (pre-prepared: folded A4, five sections labelled)
- Clipboards and pencils (not pens — pens don't work in rain)
- Magnifying glasses (optional but valuable for sight station)
- Timer for station rotations
- First aid kit
- Spare coats (for students who forget)

---

## Known Limitations

1. **Outdoor learning requires school grounds or accessible outdoor spaces.** Schools in dense urban areas with only small playgrounds or no green space will need to adapt — the sensory stations can work in any outdoor environment, but the richness of the experience depends on the richness of the environment. A school playground with tarmac and fences offers less sensory variety than a conservation area.

2. **Weather genuinely limits some activities.** While the skill argues that rain is a feature, not a bug (and for descriptive writing, this is true), some outdoor learning objectives are weather-dependent. Science fieldwork requiring dry conditions, art requiring steady hands, or PE activities on waterlogged grass all face genuine weather constraints. The skill's rain-positive framing applies to THIS example — not universally.

3. **The EEF review found moderate, not large, effects on academic outcomes.** Outdoor learning consistently improves engagement, motivation, and wellbeing — but the evidence for direct academic attainment gains is moderate. The strongest case for outdoor learning is that it provides learning experiences that cannot be replicated indoors (authentic sensory input, real specimens, spatial scale), not that it universally produces higher test scores. Teachers should use outdoor learning when the outdoor environment adds something the classroom cannot, not as a general strategy for raising attainment.

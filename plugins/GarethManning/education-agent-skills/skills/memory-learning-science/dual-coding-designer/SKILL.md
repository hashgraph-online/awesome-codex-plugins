---
# AGENT SKILLS STANDARD FIELDS (v2)
name: dual-coding-designer
description: "Design a visual complement to verbal content using dual coding principles for stronger encoding. Use when creating slides, diagrams, posters, or visual explanations of complex concepts."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "memory-learning-science/dual-coding-designer"
skill_name: "Dual Coding Designer"
domain: "memory-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Paivio (1986) — Mental Representations: A Dual Coding Approach"
  - "Clark & Paivio (1991) — Dual coding theory and education"
  - "Mayer (2009) — Multimedia learning: second edition (multimedia principle and related principles)"
  - "Mayer & Moreno (2003) — Nine ways to reduce cognitive load in multimedia learning"
  - "Caviglioli (2019) — Dual Coding with Teachers (practical application of the research)"
input_schema:
  required:
    - field: "verbal_content"
      type: "string"
      description: "The explanation, concept, or text to create a visual complement for"
    - field: "subject_and_level"
      type: "string"
      description: "Subject area and year group"
  optional:
    - field: "visual_constraints"
      type: "string"
      description: "Any constraints on visual format (e.g. 'must be reproducible on a whiteboard' / 'for a slide presentation')"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: language proficiency levels, visual processing needs"
    - field: "existing_visuals"
      type: "string"
      description: "Visuals already in use for this topic that should be complemented, not duplicated"
output_schema:
  type: "object"
  fields:
    - field: "visual_design"
      type: "object"
      description: "Recommended diagram type, spatial layout, labelling strategy, and description"
    - field: "integration_notes"
      type: "string"
      description: "How to present verbal and visual together to avoid split-attention"
    - field: "annotation_strategy"
      type: "string"
      description: "What text to include on the visual and what to keep verbal"
    - field: "common_pitfalls"
      type: "array"
      description: "Visual design mistakes that would increase rather than decrease cognitive load"
chains_well_with:
  - "cognitive-load-analyser"
  - "worked-example-fading-designer"
  - "text-complexity-analyser"
  - "explicit-instruction-sequence-builder"
teacher_time: "4 minutes"
tags: ["dual-coding", "visual-representation", "multimedia", "cognitive-load", "diagrams"]
---

# Dual Coding Designer

## What This Skill Does

Takes a verbal explanation or concept and designs a complementary visual representation — specifying the diagram type, spatial layout, labelling strategy, and annotation approach that best supports understanding. This is NOT about making content "more visual" or appealing to "visual learners" (a debunked concept). It is about exploiting the well-established finding that processing information through both verbal and visual channels simultaneously creates stronger, more retrievable memory traces than either channel alone. AI is specifically valuable here because selecting the right visual representation for a concept requires understanding both the structure of the knowledge (sequential? hierarchical? causal? spatial?) and the principles of multimedia learning — most teachers default to decorative images or overly complex diagrams that increase cognitive load rather than reducing it.

## Evidence Foundation

Paivio's (1986) dual coding theory established that human cognition operates through two distinct channels — verbal (language-based) and non-verbal (image-based) — and that information encoded through both channels is more readily retrieved than information encoded through one channel alone. Clark & Paivio (1991) applied this to education, demonstrating that complementary verbal and visual representations improve learning outcomes. Mayer (2009) operationalised dual coding into twelve multimedia learning principles, including the multimedia principle (people learn better from words and pictures than words alone), the contiguity principle (words and pictures should be presented together, not separated), and the coherence principle (extraneous visual material harms learning). Mayer & Moreno (2003) identified nine specific ways to reduce cognitive load in multimedia learning, including eliminating seductive details (interesting but irrelevant images), using spatial contiguity (placing text near the corresponding visual element), and signalling (using visual cues to direct attention). **Critical distinction:** Dual coding is about *complementary* representations — the visual shows something the words cannot efficiently convey (spatial relationships, processes, hierarchies). It is NOT about matching content to a student's "preferred learning style," which is debunked (Pashler et al., 2008). Every learner benefits from well-designed dual coding regardless of any supposed style preference.

## Input Schema

The teacher must provide:
- **Verbal content:** The explanation or concept that needs a visual complement. *e.g. "The process of osmosis: water molecules move from an area of high water concentration to low water concentration across a semi-permeable membrane" / "The causes of World War I can be grouped into long-term, short-term, and trigger causes"*
- **Subject and level:** Subject area and year group. *e.g. "Year 9 Biology" / "Year 11 History"*

Optional (injected by context engine if available):
- **Visual constraints:** Format restrictions. *e.g. "Must be drawable on a whiteboard in under 2 minutes" / "For a printed worksheet"*
- **Student profiles:** Language proficiency levels, visual processing needs
- **Existing visuals:** Visuals already in use to avoid duplication

## Prompt

```
You are an expert in multimedia learning and cognitive psychology, specialising in Paivio's (1986) dual coding theory, Mayer's (2009) multimedia learning principles, and their practical application to classroom instruction. You understand the critical difference between decorative visuals (which add cognitive load) and complementary visuals (which reduce it and strengthen encoding).

Your task is to design a visual representation that complements this verbal content:

**Verbal content:** "{{verbal_content}}"
**Subject and level:** {{subject_and_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Visual constraints:** {{visual_constraints}} — if provided, design within these constraints. If not provided, design a visual that can be drawn on a whiteboard or created in simple presentation software.
**Existing visuals:** {{existing_visuals}} — if provided, design something complementary, not duplicative. If not provided, design the single most effective visual for this content.
**Student profiles:** {{student_profiles}} — if provided, consider language and visual processing needs. If not provided, design for a typical mixed-ability class.

Apply these evidence-based multimedia learning principles:

1. **Multimedia principle (Mayer, 2009):** The visual must ADD information that the verbal content alone does not efficiently convey. If the visual just restates what the text says (e.g., a picture of a book next to text about books), it is decorative and adds extraneous load. Ask: what does the visual show that the words cannot easily describe?

2. **Match the visual type to the knowledge structure:**
   - **Sequential process → flowchart or cycle diagram** (shows order and direction)
   - **Hierarchical relationship → tree diagram or nested boxes** (shows levels and containment)
   - **Causal relationship → arrow diagram with cause-effect labelling** (shows causation, not just correlation)
   - **Spatial/physical structure → labelled diagram or cross-section** (shows location and spatial relationships)
   - **Comparison → side-by-side or Venn diagram** (shows similarities and differences)
   - **Part-whole relationship → exploded diagram or pie chart** (shows proportion and composition)
   - **Timeline → horizontal timeline with intervals** (shows chronological sequence and duration)

   The wrong diagram type for the knowledge structure actively hinders learning. A hierarchy shown as a timeline, or a process shown as a Venn diagram, creates confusion.

3. **Contiguity principle (Mayer, 2009):** Text labels must be placed directly on or immediately adjacent to the visual elements they describe — NOT in a separate legend or key that forces the learner to split attention between the diagram and the legend. Integrated labels reduce split-attention effect (Sweller, 1994).

4. **Coherence principle (Mayer, 2009):** Remove ALL decorative elements. No clip art. No background images. No decorative borders. No colour used purely for aesthetics. Every visual element must carry information. Seductive details — interesting but irrelevant images — actively harm learning (Harp & Mayer, 1998).

5. **Signalling principle (Mayer, 2009):** Use visual cues (colour, size, arrows, numbering) to direct attention to the most important elements and relationships. Colour should encode meaning (e.g., red for danger/hot, blue for cold, green for growth), not decoration.

6. **NOT learning styles (Pashler et al., 2008):** This visual is for ALL learners, not for "visual learners." Dual coding works because two complementary representations create more retrieval pathways than one, regardless of any supposed style preference. Do not reference learning styles anywhere in the output.

Return your output in this exact format:

## Dual Coding Design: [Topic]

**For:** [Subject and level]

### Recommended Visual Type
[Diagram type and why it matches the knowledge structure]

### Visual Description
[Detailed description of the visual: layout, elements, spatial arrangement, labels, arrows, colour coding. Sufficient detail for a teacher to draw it or create it digitally.]

### Spatial Layout
[ASCII sketch or detailed spatial description showing element placement]

### Annotation Strategy
- **On the visual:** [What text goes directly on the diagram]
- **Verbal (teacher narration):** [What the teacher says while showing the visual — this goes in the verbal channel, not on the diagram]
- **DO NOT include on the visual:** [What should be kept out to avoid redundancy]

### Integration Notes
[How to present the verbal and visual together in the classroom — sequence, timing, whether to build the diagram progressively or show it complete]

### Common Pitfalls to Avoid
[2–3 specific mistakes that would turn this from a learning aid into a cognitive load problem]

**Self-check before returning output:** Verify that (a) the visual adds information the verbal content cannot easily convey, (b) the diagram type matches the knowledge structure, (c) all text is integrated directly onto the visual (no separate legends), (d) there are no decorative elements, (e) colour is used for meaning not aesthetics, and (f) no reference is made to learning styles.
```

## Example Output

**Scenario:** *Verbal content: "The water cycle involves evaporation from bodies of water, transpiration from plants, condensation forming clouds, precipitation as rain or snow, and collection in rivers, lakes, and groundwater. The cycle is driven by solar energy and gravity." / Subject and level: "Year 7 Geography" / Visual constraints: "Must be drawable on a whiteboard in under 3 minutes"*

---

## Dual Coding Design: The Water Cycle

**For:** Year 7 Geography

### Recommended Visual Type
**Cycle diagram with spatial context** — the water cycle is a continuous process with spatial components (ground level, atmosphere, underground), so the visual must show both the sequential process (cycle) and the physical location where each stage occurs (spatial). A simple numbered flowchart would miss the spatial relationships. A purely spatial diagram (landscape cross-section) would miss the cyclical nature. The design combines both: a landscape cross-section with cyclical arrows showing the process flow.

### Visual Description
A simplified landscape cross-section occupying the full whiteboard width, showing:

- **Left side:** A body of water (sea/lake) — drawn as a simple curved surface with a label
- **Centre:** Land surface with one tree and a simple hill/mountain
- **Right side:** Land slopes down to a river flowing back toward the body of water
- **Above:** Cloud drawn at the top centre of the board
- **Below ground (right side):** A dotted underground layer showing groundwater

Process arrows connect the elements in a cycle:
1. **Upward arrow from water surface → cloud**, labelled "EVAPORATION" with annotation "Solar energy heats water → water vapour rises"
2. **Upward arrow from tree → cloud**, labelled "TRANSPIRATION" with annotation "Water released from plant leaves"
3. **Cloud itself**, labelled "CONDENSATION" with annotation "Water vapour cools → forms water droplets"
4. **Downward arrows from cloud → land and water**, labelled "PRECIPITATION" with annotation "Rain, snow, sleet, hail"
5. **Arrow along ground surface → river → back to sea**, labelled "SURFACE RUNOFF / COLLECTION"
6. **Dotted arrow downward into ground**, labelled "INFILTRATION / GROUNDWATER FLOW"

**Colour coding (meaningful, not decorative):**
- Blue: all water in liquid form (sea, river, groundwater, rain)
- White/light: water vapour and clouds (showing the state change)
- Yellow: a small sun symbol in the corner with an arrow pointing to the evaporation arrow, labelled "energy source"
- Arrows: blue for liquid water movement, white/grey for vapour movement

### Spatial Layout

```
    [SUN]─energy──→
                        ╭─── CLOUD ───╮
                       ╱  condensation  ╲
          evaporation ↑                  ↓ precipitation
         transpiration↑                  ↓
    ~~SEA~~  ↑  [TREE]  ___mountain___  rain↓  ──RIVER──→ (back to sea)
    ~~~~~~~  ↑                              ↓     ↗
    ~~~~~~~  ↑              surface runoff →→→→→→→
                         ↓ infiltration
                    ···groundwater flow →→→→→→→→→→→→→
```

### Annotation Strategy
- **On the visual:** Process labels only — each arrow gets ONE word (Evaporation, Transpiration, Condensation, Precipitation, Runoff, Infiltration) plus a 3–5 word annotation explaining the mechanism. Keep text minimal — the spatial relationships do the work.
- **Verbal (teacher narration):** "Notice the arrows going UP are driven by solar energy — the sun heats the water and it rises as vapour. The arrows going DOWN are driven by gravity — water falls as precipitation and flows downhill. The whole cycle is powered by two forces: the sun pulling water up and gravity pulling it down." This explanation goes in the verbal channel to complement the visual. Do NOT write it on the board.
- **DO NOT include on the visual:** Long explanatory paragraphs. Temperature data. Percentage figures. Definitions of terms. These belong in the verbal channel or in a separate text resource. Putting them on the diagram creates redundancy and split attention.

### Integration Notes
**Build the visual progressively, not all at once.** This is critical for managing cognitive load with novice learners:

1. First, draw the landscape only (sea, land, tree, mountain, river). No labels. Ask: "What do you see? Where might water be in this picture?"
2. Add the evaporation arrow and label. Narrate: "Solar energy heats the water surface. Water molecules gain energy and escape into the air as water vapour." Let students process this single step.
3. Add the transpiration arrow. Ask: "Water also rises from plants. Where does a tree get its water from? How does it end up in the air?" (Elaborative interrogation — chains with Skill 6.)
4. Add the cloud and condensation label. Narrate the cooling process.
5. Add precipitation arrows. Ask: "Why does the water fall? What force is pulling it down?" (Gravity — connecting to prior science knowledge.)
6. Add runoff and infiltration arrows. Complete the cycle.
7. Only once the full diagram is built, trace the complete cycle with your hand: "Follow the water. It starts here... goes up... forms a cloud... falls... flows back... and the cycle continues."

**Total build time:** 3 minutes (progressive) or 1 minute (drawn in advance).

### Common Pitfalls to Avoid

1. **Adding decorative details to make it "look nice."** Fish in the sea, birds in the sky, flowers on the land — these are seductive details (Harp & Mayer, 1998) that consume visual processing capacity without contributing to understanding. Every element should represent a functional part of the water cycle process. If it's not part of the cycle, it shouldn't be on the board.

2. **Separating labels from the diagram.** A common worksheet design places the diagram in the centre and a numbered key/legend around the edges. This forces split attention — students must match numbers to definitions while also tracking the spatial relationships. Integrate all labels directly onto the diagram at the relevant points.

3. **Confusing this with "being a visual learner."** If a student or colleague says "this is great for the visual learners," correct the misconception. Dual coding benefits all learners because two complementary representations create more retrieval pathways than one. It is not about matching to a preferred style (Pashler et al., 2008). Explicitly stating this helps combat one of the most persistent myths in education.

---

## Known Limitations

1. **This skill designs visual representations; it cannot create them.** The output is a detailed specification (diagram type, layout, elements, colour coding), not an image file. Teachers must create the visual themselves — on a whiteboard, in PowerPoint, or using a tool like Canva or draw.io. The specification is detailed enough to follow, but artistic skill and tool proficiency vary.

2. **Some concepts are inherently difficult to represent visually.** Abstract concepts (justice, irony, probability) and complex multi-variable relationships resist simple visual representation. The skill will recommend the best available approach, but for highly abstract content, the visual may add limited value beyond what verbal explanation provides. This is not a failure of dual coding — it reflects the genuine boundaries of visual representation.

3. **The effectiveness of dual coding depends on integration, not just presence.** Simply showing a diagram alongside text does not automatically produce dual coding benefits. The teacher must actively integrate the two channels — narrating while pointing, building the diagram progressively while explaining, asking students to connect visual elements to verbal descriptions. A well-designed visual presented without integration is just a picture on a slide.

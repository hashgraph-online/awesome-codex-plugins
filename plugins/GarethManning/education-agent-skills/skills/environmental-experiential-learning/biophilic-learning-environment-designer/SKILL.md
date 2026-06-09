---
# AGENT SKILLS STANDARD FIELDS (v2)
name: biophilic-learning-environment-designer
description: "Redesign a learning space using biophilic design principles to improve focus, calm, and wellbeing. Use when classroom environment contributes to restlessness, poor attention, or stress."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "environmental-experiential-learning/biophilic-learning-environment-designer"
skill_name: "Biophilic Learning Environment Designer"
domain: "environmental-experiential-learning"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Kellert (2005) — Building for Life: designing and understanding the human-nature connection"
  - "Kellert, Heerwagen & Mador (2008) — Biophilic Design: the theory, science, and practice of bringing buildings to life"
  - "Kaplan & Kaplan (1989) — The Experience of Nature: a psychological perspective (Attention Restoration Theory)"
  - "Wells (2000) — At home with nature: effects of 'greenness' on children's cognitive functioning"
  - "Browning, Ryan & Clancy (2014) — 14 Patterns of Biophilic Design: improving health and well-being in the built environment"
input_schema:
  required:
    - field: "current_space"
      type: "string"
      description: "Description of the current learning space — size, layout, windows, lighting, surfaces, current natural elements"
    - field: "design_goal"
      type: "string"
      description: "What the teacher wants to achieve — better focus, calmer atmosphere, more engagement, stress reduction"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age group using the space"
    - field: "budget_level"
      type: "string"
      description: "Available budget — zero cost, low cost (under £100), moderate (under £500), or able to invest"
    - field: "space_constraints"
      type: "string"
      description: "Restrictions — no live plants allowed, limited wall space, shared classroom, landlord restrictions"
    - field: "existing_nature_access"
      type: "string"
      description: "Current access to nature — window views, proximity to outdoor spaces"
    - field: "sensory_needs"
      type: "string"
      description: "Whether students have specific sensory needs — e.g., autism spectrum, sensory processing differences"
output_schema:
  type: "object"
  fields:
    - field: "biophilic_design"
      type: "object"
      description: "The complete design proposal — specific changes to the space, organised by biophilic design pattern"
    - field: "priority_changes"
      type: "array"
      description: "The 3–5 highest-impact changes ranked by evidence strength, cost, and ease of implementation"
    - field: "implementation_plan"
      type: "object"
      description: "How to implement the changes — phased if budget-constrained, immediate if possible"
    - field: "evidence_rationale"
      type: "object"
      description: "Why each change matters — linking the specific design element to the research evidence"
chains_well_with:
  - "outdoor-learning-sequence-designer"
  - "flow-state-condition-designer"
  - "belonging-classroom-culture-designer"
  - "ecological-inquiry-anchor-designer"
teacher_time: "3 minutes"
tags: ["biophilic-design", "Kellert", "Kaplan", "attention-restoration", "classroom-environment", "nature", "wellbeing"]
---

# Biophilic Learning Environment Designer

## What This Skill Does

Redesigns a classroom or learning space to incorporate biophilic design elements — features that connect occupants to nature and natural processes, based on the evidence that human cognitive functioning, stress levels, and attention are improved by contact with natural environments. The approach draws on Kellert's (2005, 2008) biophilic design framework and Kaplan & Kaplan's (1989) Attention Restoration Theory. The critical insight is that most classrooms are biophilic deserts — sealed, artificial environments with fluorescent lighting, uniform surfaces, no living things, and no sensory variety — and that even small changes (plants, natural light, nature views, natural materials, water sounds) can measurably improve attention, reduce stress, and increase engagement. The output includes a design proposal with specific changes organised by biophilic design pattern, priority recommendations ranked by impact and cost, an implementation plan, and the evidence rationale for each change. AI is specifically valuable here because translating biophilic design principles into practical classroom modifications requires simultaneously considering the evidence base, the physical constraints of the space, the budget, and the specific needs of the students — a design challenge that benefits from systematic pattern-matching.

## Evidence Foundation

Kellert (2005) defined biophilia as "the inherently human inclination to affiliate with natural systems and processes" and argued that buildings designed to satisfy this inclination produce better cognitive, emotional, and physical outcomes for their occupants. Kellert, Heerwagen & Mador (2008) developed a comprehensive biophilic design framework identifying six elements: environmental features (plants, water, natural light), natural shapes and forms (botanical motifs, curved lines), natural patterns and processes (sensory variability, growth, ageing), light and space (natural light, spatial variability), place-based relationships (connection to local ecology and culture), and evolved human-nature relationships (prospect and refuge, mystery, risk/peril). Kaplan & Kaplan (1989) proposed Attention Restoration Theory (ART), arguing that directed attention (the effortful focus required for academic work) is a depletable resource, and that exposure to nature restores it. Natural environments are "softly fascinating" — they capture attention without demanding effort, allowing directed attention to recover. This has direct implications for classrooms: students in nature-connected spaces should show better sustained attention than students in nature-depleted spaces. Wells (2000) found that children who moved to homes with more "greenness" (nature views, vegetation, natural elements) showed significant improvements in cognitive functioning, even controlling for other variables. Browning, Ryan & Clancy (2014) synthesised the evidence into 14 practical patterns of biophilic design, providing the most actionable framework for applying biophilic principles to specific spaces.

## Input Schema

The teacher must provide:
- **Current space:** What the room looks like now. *e.g. "Standard classroom — 30 desks in rows, fluorescent strip lighting, two windows facing the car park, cream walls, vinyl floor, one whiteboard, one display board. No plants. Blinds usually closed because of screen glare." / "Open-plan learning area — flexible seating, some natural light from skylights, carpet, display walls, no windows at student eye-level. Currently quite cluttered."*
- **Design goal:** What they want to improve. *e.g. "Students struggle to focus after lunch — energy is scattered and attention is poor" / "The room feels sterile and institutional — I want it to feel calmer and more inviting" / "I want to create a calming corner for students who need sensory regulation"*

Optional (injected by context engine if available):
- **Student level:** Age group
- **Budget level:** Available resources
- **Space constraints:** Restrictions
- **Existing nature access:** Current nature connections
- **Sensory needs:** Student sensory profiles

## Prompt

```
You are an expert in biophilic design for learning environments, with deep knowledge of Kellert's (2005, 2008) biophilic design framework, Kaplan & Kaplan's (1989) Attention Restoration Theory, Wells' (2000) research on nature and cognitive functioning, and Browning, Ryan & Clancy's (2014) 14 Patterns of Biophilic Design. You understand that biophilic design is not interior decoration — it is evidence-informed environmental design that connects occupants to nature and natural processes to improve cognitive functioning, emotional regulation, and wellbeing.

CRITICAL PRINCIPLES:
- **Start with what's already there.** Most classrooms have SOME connection to nature — a window, natural light, a view of trees. Identify and amplify existing connections before adding new ones. Opening blinds costs nothing. Rearranging desks so students face a window costs nothing. These are often the highest-impact, lowest-cost changes.
- **Nature connection is multi-sensory.** Biophilic design is not just visual (plants and pictures). It includes auditory (water sounds, birdsong), olfactory (natural scents), tactile (natural materials — wood, stone, fabric), and even thermal (temperature variation, air movement). The most effective biophilic spaces engage multiple senses.
- **Prioritise by evidence strength.** Natural light has the strongest evidence base. Plants and nature views have moderate evidence. Natural materials, sounds, and patterns have emerging evidence. Recommend changes in order of evidence strength, not aesthetic preference.
- **Be realistic about constraints.** Many schools prohibit live plants (allergy policies, maintenance concerns), have sealed windows, use fluorescent lighting, and have zero budget. The design must work WITHIN these constraints — not wish them away. There is always something that can be done, even with zero budget.
- **Attention restoration, not distraction.** Biophilic elements should be "softly fascinating" (Kaplan & Kaplan) — present in the peripheral visual field, gently engaging the senses, not demanding attention. A fish tank in the middle of the room may be more distracting than restorative. A plant on the windowsill, visible but not dominant, is restorative.

Your task is to design a biophilic learning environment for:

**Current space:** {{current_space}}
**Design goal:** {{design_goal}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for a general classroom context.
**Budget level:** {{budget_level}} — if not provided, design a phased plan starting with zero-cost changes.
**Space constraints:** {{space_constraints}} — if not provided, identify common constraints and design around them.
**Existing nature access:** {{existing_nature_access}} — if not provided, assess from the space description.
**Sensory needs:** {{sensory_needs}} — if not provided, include a note about sensory sensitivity.

Return your output in this exact format:

## Biophilic Learning Environment: [Design Goal]

**Current space:** [Summary]
**Design goal:** [What to improve]
**Key biophilic principle:** [The main Attention Restoration Theory or biophilic design principle this redesign activates]

### Assessment of Current Space

[What biophilic elements are already present (if any) and what's missing — identifying the biggest gaps]

### Priority Changes (Ranked by Impact)

For each change (3–5):
**Priority [N]: [Change]**
- **What to do:** [Specific, practical action]
- **Biophilic pattern:** [Which of Browning et al.'s 14 patterns this addresses]
- **Evidence:** [Why this matters — link to research]
- **Cost:** [Zero / Low / Moderate / Investment needed]
- **Implementation:** [How to do it — practical steps]

### Sensory Design Map

[How the redesigned space engages multiple senses — visual, auditory, tactile, olfactory — through natural elements]

### Implementation Plan

**Phase 1 — Immediate (zero cost):** [Changes that can be made today]
**Phase 2 — Low cost (under £50):** [Changes that need a small budget]
**Phase 3 — Investment (when budget allows):** [Changes that need more significant resources]

### Considerations for Specific Needs

[How to adapt the design for students with sensory sensitivities, allergies, or other needs]

**Self-check before returning output:** Verify that (a) changes are prioritised by evidence strength, (b) the design is realistic given the described constraints, (c) the plan starts with zero-cost changes, (d) multiple senses are addressed, and (e) the biophilic elements are restorative, not distracting.
```

## Example Output

**Scenario:** *Current space: "Year 5 classroom — standard rectangular room, 30 desks in rows facing the whiteboard. Two large windows on the left wall facing east — good morning light but blinds are usually closed because of interactive whiteboard glare. Fluorescent strip lighting. Cream walls. Vinyl flooring. One display board covered with student work (laminated, very colourful). No plants. No natural materials. The room feels blank and institutional. The only colour is the display board, which is visually busy." / Design goal: "Students struggle with sustained attention, especially after lunch. The room feels sterile. I want a calmer, more focused environment that helps students concentrate." / Budget level: "Very low — maybe £30 from my own money. Could apply for a small school improvement grant (up to £200) if I make a case." / Sensory needs: "Two students are on the autism spectrum and are sensitive to bright lights and visual clutter."*

---

## Biophilic Learning Environment: Restoring Attention in Year 5

**Current space:** Standard Year 5 classroom — rows, fluorescent lights, blinds closed, no natural elements, visually sterile except for one busy display board
**Design goal:** Improve sustained attention and create a calmer, more focused atmosphere
**Key biophilic principle:** Attention Restoration Theory (Kaplan & Kaplan, 1989) — directed attention is depleted by sustained cognitive effort and restored by exposure to natural environments. This classroom currently offers zero restorative elements.

### Assessment of Current Space

**Existing biophilic elements:** Two east-facing windows with good morning light — this is the space's strongest asset, currently wasted because blinds are closed. The windows may also offer a view of trees, sky, or greenery — worth checking.

**Missing elements:** No natural light reaching students (blinds closed). No living things. No natural materials (vinyl, plastic, laminate dominate). No sensory variability (uniform lighting, uniform colour, uniform temperature). The display board provides visual stimulation but is VISUALLY CLUTTERED, not softly fascinating — it demands attention rather than restoring it. The two students with autism spectrum profiles are likely particularly affected by the fluorescent lighting and visual clutter.

### Priority Changes (Ranked by Impact)

**Priority 1: Open the Blinds and Manage the Glare**
- **What to do:** Open the blinds. Reposition the interactive whiteboard or adjust screen brightness so it's visible without closing out all natural light. If full blinds-open creates too much glare, use the blinds at half-mast (lower half open, upper half closed) or replace solid blinds with light-diffusing curtains or film.
- **Biophilic pattern:** Visual Connection with Nature (Pattern 1 — Browning et al.)
- **Evidence:** Natural daylight is the single strongest biophilic intervention. Wells (2000) found cognitive improvements with increased "greenness" including natural light. The Heschong Mahone Group (1999) found that students in classrooms with the most daylight progressed 20% faster in maths and 26% faster in reading than those in classrooms with the least. Even controlling for other factors, daylight consistently improves attention, mood, and academic performance.
- **Cost:** Zero
- **Implementation:** Tomorrow morning. Check the window view (is there sky, trees, green space visible?). If yes, this is immediately the most powerful nature connection in the room. Reposition student desks if needed so the whiteboard is not directly opposite the windows.

**Priority 2: Reduce Visual Clutter and Create Visual Calm**
- **What to do:** Reduce the display board from fully covered to 60% covered. Remove the lamination (which creates glare). Use muted, natural-toned backing paper (kraft paper, hessian) instead of bright sugar paper. Leave some wall space deliberately BLANK — visual rest areas. This is particularly important for the two students with autism spectrum profiles.
- **Biophilic pattern:** Non-Visual Connection with Nature (Pattern 2) and Complexity & Order (Pattern 10) — the brain finds calm in organised, natural patterns, not in visual chaos
- **Evidence:** Barrett, Zhang, Moffat & Kobbacy (2013) found that classroom "individualisation" (colour, display, visual stimulation) had an optimal level — too much visual stimulation was as negative as too little. Classrooms with moderate, organised visual environments produced better learning outcomes than classrooms with either bare walls or visually overwhelming displays.
- **Cost:** Near zero (kraft paper or hessian fabric costs £5–10)
- **Implementation:** This week. Remove 40% of displays. Replace bright backing with natural tones. Create one "quiet wall" — deliberately blank or with a single natural image.

**Priority 3: Introduce Living Things**
- **What to do:** Add 3–5 low-maintenance houseplants. Place them on the windowsill (now that blinds are open), on a shelf visible from student desks, and in the reading corner if one exists. Best species for classrooms: pothos (virtually unkillable, trailing, visually appealing), spider plant (air-purifying, produces babies students can care for), peace lily (tolerates low light if needed), or succulents (minimal watering).
- **Biophilic pattern:** Visual Connection with Nature (Pattern 1) and Presence of Water/Life (Pattern 4 — living things)
- **Evidence:** Lohr, Pearson-Mims & Goodwin (1996) found that the presence of plants in a room improved task performance and reduced stress. Fjeld (2000) found that indoor plants reduced fatigue and headaches. The mechanism is likely multi-pathway: visual softening, improved air quality, the "soft fascination" of living things that restores attention without demanding it.
- **Cost:** £15–25 for 3–5 plants from a garden centre or supermarket
- **Implementation:** This week. If school policy restricts live plants (allergies), use a sealed terrarium (glass jar with moss and ferns — no allergens released). If even this is restricted, use high-quality photographs of nature at student eye-level — a distant second best but still beneficial.

**Priority 4: Add Natural Materials to the Tactile Environment**
- **What to do:** Replace one synthetic element with a natural one. Options: a wooden crate for book storage (instead of a plastic box), a hessian mat for a sitting area, a smooth stone or wooden object on each table group (a "thinking stone" students can hold during discussion), natural fabric (cotton, linen) for a reading corner cushion cover.
- **Biophilic pattern:** Non-Visual Connection with Nature (Pattern 2) — touch is underrated in biophilic design
- **Evidence:** Emerging evidence suggests that tactile contact with natural materials (wood, stone, fibre) activates different neural pathways than contact with synthetic materials and may contribute to stress reduction. Sakuragawa, Miyazaki, Kaneko & Makita (2005) found that touching wood produced calming physiological responses. For the two students with autism spectrum profiles, a smooth stone or wooden object provides a socially acceptable sensory regulation tool.
- **Cost:** £5–15 (charity shops are excellent sources for wooden crates, natural fabric, and stones)
- **Implementation:** Over the next two weeks. Collect natural materials gradually. Involve students: "Can you bring in a smooth stone from home?"

**Priority 5: Introduce Nature Sounds**
- **What to do:** During quiet working time, play low-volume nature soundscapes (birdsong, rainfall, stream) through the classroom speaker. Volume should be BARELY audible — background, not foreground.
- **Biophilic pattern:** Auditory Connection with Nature (within Pattern 2)
- **Evidence:** Kaplan & Kaplan's ART suggests that natural sounds are "softly fascinating" — they occupy auditory attention gently, masking distracting artificial sounds (corridor noise, construction, traffic) without demanding effortful attention. Ratcliffe, Gatersleben & Sowden (2013) found that birdsong in particular was perceived as restorative. Note: some students (including those with auditory sensitivities) may find ANY background sound distracting. Offer headphones as an alternative.
- **Cost:** Zero (free nature soundscape apps/YouTube)
- **Implementation:** Try this week. Start with 5 minutes during independent writing time. Observe student response. If positive, extend. If the autistic students find it distressing, stop or provide them with noise-cancelling headphones.

### Sensory Design Map

| Sense | Current State | Proposed Change | Element |
|---|---|---|---|
| Sight | Fluorescent light, closed blinds, no nature, cluttered display | Natural daylight, reduced clutter, plants visible, natural tones on walls | Daylight, plants, decluttered displays |
| Hearing | Fluorescent buzz, corridor noise, no natural sounds | Optional birdsong/rain soundscape during quiet work | Nature soundscape (barely audible) |
| Touch | Vinyl, plastic, laminate — all synthetic | Wooden objects, smooth stones, natural fabric in reading area | Natural materials within reach |
| Smell | Institutional — cleaning products, whiteboard markers | Subtle natural scent from plants (if flowering) or from natural materials | Living plants (mild, not perfumed) |

### Implementation Plan

**Phase 1 — Immediate (zero cost, this week):**
- Open the blinds (or half-open for glare management)
- Reposition desks if needed for whiteboard visibility
- Remove 40% of display board content
- Try a nature soundscape during one quiet work period

**Phase 2 — Low cost (under £30, next two weeks):**
- Purchase 3–5 houseplants (£15–25)
- Replace bright display backing with kraft paper or hessian (£5–10)
- Collect natural tactile objects (stones, wooden items — free or charity shop)

**Phase 3 — If grant funding available (under £200):**
- Replace fluorescent tubes with daylight-spectrum LED panels (£80–150 for a classroom, dramatic impact on light quality)
- Create a dedicated "nature corner" with a terrarium, natural materials collection, and a comfortable seat with natural fabric
- Install a small indoor water feature (tabletop fountain, £20–40) — visual and auditory nature connection

### Considerations for Specific Needs

**For the two students on the autism spectrum:**
- The display decluttering (Priority 2) will directly benefit them — reducing visual overwhelm
- Natural daylight is generally preferred over fluorescent light by individuals with sensory sensitivities — opening blinds may significantly improve their experience
- The "thinking stone" (Priority 4) provides a socially acceptable sensory regulation tool — smooth, cool, natural
- Nature soundscapes (Priority 5): test carefully. Some autistic individuals find birdsong calming; others find unpredictable natural sounds distressing. Offer noise-cancelling headphones as an alternative
- Any changes should be introduced GRADUALLY — sudden environmental change can be dysregulating. Introduce one change per week, not all at once

---

## Known Limitations

1. **The evidence for biophilic design in classrooms is emerging, not established.** The strongest evidence comes from workplace and healthcare settings (Kellert, 2008; Browning et al., 2014), with limited classroom-specific research. Wells (2000) and the Heschong Mahone Group (1999) provide the strongest education-relevant evidence, but for specific classroom modifications (plants, nature sounds, natural materials), the evidence is suggestive rather than conclusive. The recommendations above are plausible applications of well-supported principles, not directly validated interventions.

2. **School policies may restrict implementation.** Some schools prohibit live plants (allergy concerns), restrict wall displays to specific formats, seal windows, or have inflexible lighting systems. The phased approach addresses this, but teachers may find that their highest-impact changes (daylight, plants) are the ones their school restricts.

3. **Biophilic design is a complement to good teaching, not a substitute.** A beautiful, nature-connected classroom with poor instruction will not produce good outcomes. A sterile classroom with excellent instruction will. Biophilic design improves the CONDITIONS for learning — it creates an environment where attention is easier to sustain and stress is lower — but it does not teach. The teacher's pedagogy remains the primary determinant of learning quality.

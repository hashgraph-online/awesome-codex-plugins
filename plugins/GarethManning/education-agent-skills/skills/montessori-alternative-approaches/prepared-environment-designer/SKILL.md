---
# AGENT SKILLS STANDARD FIELDS (v2)
name: prepared-environment-designer
description: "Redesign a classroom as a prepared environment optimised for independent learning, calm transitions, and material access. Use when classroom layout hinders independence or self-directed work."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "montessori-alternative-approaches/prepared-environment-designer"
skill_name: "Prepared Environment Designer"
domain: "montessori-alternative-approaches"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Lillard (2005) — Montessori: The Science Behind the Genius"
  - "Cossentino (2006) — Big work: goodness, volitional action, and the classroom environment in Montessori method"
  - "Barrett et al. (2015) — The impact of classroom design on pupils' learning: final results of a holistic, multi-level analysis (HEAD project)"
  - "Fisher et al. (2014) — Visual environment, attention, and learning in young children: when too much of a good thing may be bad"
  - "Lillard & Else-Quest (2006) — Evaluating Montessori education (Science)"
input_schema:
  required:
    - field: "current_environment"
      type: "string"
      description: "A description of the current classroom or learning space — what it looks like, how it is organised, what materials are available, and what problems exist"
    - field: "improvement_goals"
      type: "string"
      description: "What the teacher wants to achieve by redesigning the environment — calmer transitions, more independent work, better access to materials, or other specific goals"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and developmental stage"
    - field: "budget"
      type: "string"
      description: "Available budget for changes — from zero-cost to significant investment"
    - field: "space_constraints"
      type: "string"
      description: "Fixed constraints — room size, built-in furniture, windows, doors, shared spaces"
    - field: "curriculum_context"
      type: "string"
      description: "Whether this is a Montessori school, a conventional school wanting to adopt some principles, or a home learning environment"
    - field: "time_for_implementation"
      type: "string"
      description: "How quickly the changes need to happen — over a weekend, gradually over a term, or during a school holiday"
output_schema:
  type: "object"
  fields:
    - field: "environment_audit"
      type: "object"
      description: "Analysis of the current environment against Montessori prepared environment principles — what works and what doesn't"
    - field: "redesign_plan"
      type: "object"
      description: "The specific changes recommended — organised by priority and cost"
    - field: "implementation_sequence"
      type: "array"
      description: "The order of changes — what to do first and what can wait"
    - field: "maintenance_protocol"
      type: "object"
      description: "How to maintain the prepared environment over time — routines, responsibilities, and refresh cycles"
chains_well_with:
  - "three-part-lesson-designer"
  - "uninterrupted-work-cycle-designer"
  - "mixed-age-learning-task-designer"
  - "biophilic-learning-environment-designer"
teacher_time: "5 minutes"
tags: ["Montessori", "prepared-environment", "classroom-design", "Lillard", "Cossentino", "accessibility", "order", "beauty", "materials"]
---

# Prepared Environment Designer

## What This Skill Does

Evaluates a classroom or learning space against Montessori prepared environment principles and produces a practical redesign plan. The prepared environment is one of Montessori's most distinctive and influential contributions: the idea that the physical space IS the curriculum — that a carefully designed environment invites learning, supports independence, and reduces the need for teacher direction. Lillard (2005) identified the key principles: accessibility (children can reach and choose materials independently), order (everything has a defined place and is returned there after use), beauty (the environment is aesthetically pleasing, using natural materials and careful design), real materials (functional objects, not toys — real glass, real tools, real plants), and child scale (furniture and materials are sized for the children using them). Cossentino (2006) added the concept of "big work" — the environment should invite sustained, meaningful engagement rather than quick, scattered activity. This skill is particularly valuable because environment design is one of the Montessori principles with the most independent supporting evidence: Barrett et al. (2015) found that classroom design factors (light, temperature, air quality, ownership, flexibility, complexity, and colour) explained 16% of variance in student learning progress — a substantial effect for a single variable. Fisher et al. (2014) found that visually cluttered classrooms significantly reduced children's attention and learning, providing direct empirical support for the Montessori emphasis on visual order.

## Evidence Foundation

Lillard (2005) provided the most comprehensive analysis of the prepared environment through a cognitive science lens. She argued that Montessori's environmental design principles align with research on: (a) embodied cognition — children learn through physical interaction with materials, so materials must be accessible and inviting; (b) executive function — an ordered environment with clear routines supports the development of self-regulation; (c) attention — a visually calm environment with purposeful displays reduces distraction and supports sustained focus; and (d) intrinsic motivation — an environment where children choose their own work supports autonomy and engagement. Cossentino (2006) conducted an ethnographic study of Montessori classrooms and identified "big work" as a defining characteristic of the prepared environment. The environment is designed so that the most engaging, challenging, and meaningful activities are the most visible and accessible — children are drawn toward deep work by the design of the space, not by teacher instruction. Cossentino found that the aesthetic quality of the environment communicated respect for children's work and created a culture of care and craftsmanship. Barrett et al. (2015) conducted the HEAD (Holistic Evidence and Design) study — the largest study of classroom design and learning outcomes. They assessed 153 classrooms in 27 UK schools and found that classroom design explained 16% of the variance in pupil learning progress over one year. The most influential factors were naturalness (light, temperature, air quality), individualisation (ownership, flexibility), and stimulation (complexity, colour). The optimal classroom had good natural light, moderate visual complexity (not bare, not cluttered), and evidence of student ownership. These findings independently support several Montessori principles: natural light, visual order (moderate complexity), and student ownership of the space. Fisher et al. (2014) experimentally tested the effect of classroom visual environment on kindergarten children's learning. They found that children in heavily decorated classrooms (walls covered with posters, maps, artwork) spent significantly more time off-task and scored lower on learning assessments than children in sparse classrooms. The effect was substantial: 38.6% time off-task in decorated rooms vs. 28.4% in sparse rooms. This provides direct empirical support for the Montessori principle that the environment should be visually ordered and purposeful, not visually overwhelming.

## Input Schema

The teacher must provide:
- **Current environment:** What the space looks like now. *e.g. "Year 1 classroom, approximately 60m². Tables arranged in 6 groups of 4. Teacher desk at the front with interactive whiteboard. Walls covered in commercial posters, reward charts, and last term's student work. Materials stored in labelled plastic boxes on high shelves — children need to ask an adult to access most resources. Carpet area in one corner for whole-class teaching. Coat pegs and bags create a cluttered corridor entrance" / "Home learning room for 3 children aged 4, 7, and 10. Small bedroom converted to learning space. IKEA bookshelf, a table, and three chairs. Currently used as a general dumping ground"*
- **Improvement goals:** What the teacher wants to achieve. *e.g. "Children constantly ask me for materials — I want them to access resources independently. Transitions between activities take 10 minutes. The room feels chaotic and I think it affects behaviour" / "I want a space where all three children can work simultaneously on different things without fighting or needing constant supervision"*

Optional (injected by context engine if available):
- **Student level:** Age/year group
- **Budget:** Available resources for changes
- **Space constraints:** Fixed features of the room
- **Curriculum context:** Montessori, conventional, or home
- **Time for implementation:** How quickly changes need to happen

## Prompt

```
You are an expert in learning environment design, with deep knowledge of Montessori prepared environment principles (Lillard, 2005; Cossentino, 2006), Barrett et al.'s (2015) HEAD study on classroom design and learning outcomes, and Fisher et al.'s (2014) research on visual environment and attention. You understand that the physical environment is not neutral — it actively shapes behaviour, attention, and learning. A well-designed space invites independence, sustains focus, and communicates respect. A poorly designed space creates dependence, fragmentation, and low-level disruption.

CRITICAL PRINCIPLES:
- **Accessibility.** Children must be able to reach, choose, and return materials independently. If a child needs an adult to access a resource, that resource is not truly available to them. Shelves at child height, open (not closed) storage, and a clear organisational system are essential.
- **Order.** Everything has a defined place. Every material has a specific location on a specific shelf, and children know where it belongs. Order is not rigidity — it is freedom. When children know where things are, they don't need to ask. When they know where things go back, they develop responsibility. Barrett et al. (2015) found that visual order (moderate complexity, not bare or cluttered) was associated with better learning outcomes.
- **Beauty.** The environment should be aesthetically pleasing — not decorated, but DESIGNED. Natural materials (wood, wicker, cotton, glass) over plastic. Plants. Clean lines. Purposeful displays (current student work, reference materials) rather than commercial decoration. Cossentino (2006) found that aesthetic care communicated respect for children's work.
- **Real materials.** Montessori environments use functional objects: real glass (children learn to carry carefully), real tools (child-sized brooms, real cooking utensils), real plants (children care for them). This develops practical life skills AND communicates trust. Fisher et al. (2014) found that reducing visual clutter improved attention — real, purposeful materials contribute to visual clarity; plastic decorative items contribute to clutter.
- **Child scale.** Furniture and materials should be sized for the children. Tables they can sit at without dangling feet. Shelves they can reach without stretching. Sinks they can use independently. This is not just ergonomic — it communicates that the space belongs to THEM.
- **Defined work areas.** Different areas for different types of work: a quiet reading corner, a practical life area, a maths materials shelf, an art space. The physical layout communicates what happens where, reducing the need for verbal instruction.

Your task is to evaluate and redesign this learning environment:

**Current environment:** {{current_environment}}
**Improvement goals:** {{improvement_goals}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, infer from the description.
**Budget:** {{budget}} — if not provided, begin with zero-cost changes and indicate which improvements require investment.
**Space constraints:** {{space_constraints}} — if not provided, assume standard constraints (fixed walls, one door, windows on one side).
**Curriculum context:** {{curriculum_context}} — if not provided, design for a conventional school wanting to adopt prepared environment principles (not a full Montessori conversion).
**Time for implementation:** {{time_for_implementation}} — if not provided, design a phased implementation starting with quick wins.

Return your output in this exact format:

## Prepared Environment Redesign: [Space Description]

**Current space:** [Summary of what exists]
**Goals:** [What the redesign should achieve]
**Approach:** [Full Montessori conversion or selective adoption of principles]

### Environment Audit

[Evaluate the current space against each Montessori principle. Be specific — what works and what doesn't, with reference to the evidence.]

| Principle | Current State | Rating | Key Issue |
|---|---|---|---|
| Accessibility | [Description] | [Strong/Adequate/Weak] | [Main problem] |
| Order | [Description] | [Strong/Adequate/Weak] | [Main problem] |
| Beauty | [Description] | [Strong/Adequate/Weak] | [Main problem] |
| Real Materials | [Description] | [Strong/Adequate/Weak] | [Main problem] |
| Child Scale | [Description] | [Strong/Adequate/Weak] | [Main problem] |
| Defined Areas | [Description] | [Strong/Adequate/Weak] | [Main problem] |

### Redesign Plan

**Phase 1: Zero-Cost Quick Wins (this weekend)**
[Changes that cost nothing — rearranging, removing, reorganising]

**Phase 2: Low-Cost Improvements (under £50)**
[Small purchases that make a significant difference]

**Phase 3: Investment Changes (if budget allows)**
[Larger changes that require more resources]

### Implementation Sequence

[The specific order of changes — what to do first and why]

### Maintenance Protocol

[How to maintain the prepared environment — daily routines, weekly checks, and how to involve students in environment care]

### Before and After

[A clear description of the key differences the teacher will see — the specific changes to daily life in the classroom]

**Self-check before returning output:** Verify that (a) all six principles are addressed, (b) changes are phased by cost and effort, (c) the redesign is practical for the given constraints, (d) maintenance is addressed, and (e) the changes serve the stated improvement goals.
```

## Example Output

**Scenario:** *Current environment: "Year 1 classroom (5-6 year olds), approximately 60m². Six rectangular tables arranged in groups of 4 (24 children). Teacher desk at the front next to an interactive whiteboard. Walls covered in commercial literacy and numeracy posters, a behaviour reward chart, a birthday display, and last term's student work (curling at the edges, some falling off). Materials stored in labelled plastic boxes on high shelves along two walls — children need to ask an adult to access most resources, including pencils, which are kept in a locked cupboard because 'they keep losing them.' Carpet area in one corner with a large rug for whole-class teaching. Coat pegs in a narrow corridor entrance — bags on the floor create a tripping hazard. One window wall (west-facing). Fluorescent ceiling lights. Plastic chairs, some wobbly." / Improvement goals: "Children constantly ask me for materials — I want them to access resources independently. Transitions between activities take 10 minutes because children queue to collect and return resources. The room feels visually overwhelming and I think it affects behaviour — I have 4 children who struggle to focus. I want the room to feel calmer and the children to be more independent" / Budget: "£100 for this term, possibly more next term" / Curriculum context: "State primary school, not Montessori — but I want to adopt principles that will work in my context"*

---

## Prepared Environment Redesign: Year 1 Classroom

**Current space:** 60m² Year 1 classroom, 24 children, tables in groups, high shelves, locked pencils, heavy wall decoration, cluttered entrance
**Goals:** Independent material access, faster transitions, calmer visual environment, improved focus
**Approach:** Selective adoption of Montessori prepared environment principles within a state primary school context — not a full conversion, but significant changes to accessibility, order, and visual environment

### Environment Audit

| Principle | Current State | Rating | Key Issue |
|---|---|---|---|
| Accessibility | Materials on high shelves, pencils locked, children must ask adults | Weak | Children are entirely dependent on adults for resources — this creates queues, delays, and learned helplessness |
| Order | Materials labelled but unreachable; no clear return system | Weak | Labels exist but are irrelevant when children can't access the shelves. No routine for returning materials to their place |
| Beauty | Commercial posters, curling student work, reward chart, birthday display | Weak | Visual clutter from every surface. Fisher et al. (2014): heavily decorated rooms increase off-task behaviour by ~10%. Nothing invites sustained looking or communicates care |
| Real Materials | Plastic storage boxes, plastic chairs, synthetic carpet | Adequate | Standard school provision. No natural materials, but functional. The bigger issue is accessibility, not material quality |
| Child Scale | Tables appropriate height, but shelves too high. Chairs wobbly but child-sized | Adequate | Main issue is shelf height. Furniture is functional if not beautiful |
| Defined Areas | Carpet area for teaching, tables for work — but no other distinct zones | Weak | Only two modes: "on the carpet" and "at your table." No reading corner, no quiet space, no practical area. The room supports whole-class and group work but not independent choice |

### Redesign Plan

**Phase 1: Zero-Cost Quick Wins (this weekend)**

1. **Unlock the pencils.** Put pencils, crayons, rulers, and scissors in open containers on each table group (a pot or tray per table). If children "lose" pencils, that's a solvable management problem — train a "pencil check" routine at the end of each session. Locking resources communicates distrust and creates dependence. *Impact: eliminates the single biggest bottleneck.*

2. **Move materials to child height.** Take the plastic boxes off the high shelves and place them on the lower shelves, floor level, or on the tables themselves. If lower shelf space is limited, prioritise the most-used materials at child height and keep rarely-used materials higher. Every material a child needs during a typical lesson should be reachable without asking. *Impact: eliminates material-access queues.*

3. **Strip the walls.** Remove ALL commercial posters, the reward chart, the birthday display, and any student work that is curling, faded, or from last term. Leave the walls almost bare. This will feel radical and the room will feel "empty" — that is correct. Barrett et al. (2015): moderate visual complexity is optimal. Fisher et al. (2014): reducing wall decoration improved attention and learning. You can add back SELECTIVELY — see Phase 2. *Impact: immediate reduction in visual overload. Watch the 4 focus-struggling children over the next week.*

4. **Create a defined quiet corner.** Move the carpet to a corner. Add a bookshelf (repositioned from elsewhere in the room) to create a partial boundary. Place 10-15 carefully chosen books face-out on the shelf. This becomes the reading/quiet area. The physical boundary communicates: "this is a different kind of space." *Impact: children now have a place to go for quiet, focused work.*

5. **Clear the entrance.** Move bags to under the coat pegs (hooks or a simple shelf). If bags don't fit, send a letter home asking for book bags rather than rucksacks. The entrance sets the tone — a tripping hazard communicates disorder from the first moment of the day. *Impact: calmer arrival routine.*

**Phase 2: Low-Cost Improvements (under £100)**

6. **Open shelving trays (£20-30).** Replace a few high plastic boxes with open trays or baskets on low shelving. Each tray contains ONE complete activity or resource set. Label each tray with a photograph of the contents and a word label. Children can see what's inside without opening anything. *Impact: children can choose materials visually, not by reading labels on closed boxes.*

7. **Table plants (£10-15).** One small plant per table group — a pothos, a spider plant, or a succulent. Assign each table the responsibility of watering their plant. This serves multiple purposes: natural element (Barrett et al., 2015 found natural elements improve well-being), beauty, responsibility, and a gentle introduction to caring for the environment. *Impact: visual improvement, child ownership, practical life skill.*

8. **Selective wall displays (£10-15 for frames or borders).** Add back ONLY: (a) current reference materials the children actually use (a number line, a letter formation chart, a working wall for the current topic), and (b) 4-5 pieces of student work, well-mounted, rotated fortnightly. Everything displayed should be purposeful and current. Nothing decorative for its own sake. *Impact: walls become a tool, not wallpaper.*

9. **A materials return routine.** Teach an explicit routine: when you finish with a material, return it to its EXACT place on the shelf. Practise this for a week using the three-period lesson approach: show children where things go (Period 1), ask them to return specific items (Period 2), and check that they can find and return items independently (Period 3). This is investment in independence. *Impact: 10-minute transitions become 2-3 minutes once the routine is established.*

**Phase 3: Investment Changes (next term, if budget allows)**

10. **Replace fluorescent lighting with warm LEDs or use lamps (£50-150).** Fluorescent lighting creates harsh, even illumination with a slight flicker that some children find agitating. If you can't replace ceiling lights, add 2-3 floor or table lamps to create pools of warm light, and turn off some overhead tubes. *Impact: calmer atmosphere, particularly for children with sensory sensitivities.*

11. **Low open shelving unit (£50-100).** A single, purpose-built low shelf unit (like an IKEA Kallax) placed perpendicular to a wall creates both storage and a room divider — defining a work area without blocking sightlines. *Impact: creates defined zones with accessible storage.*

12. **Replace 2-3 wobbly chairs with stools or floor cushions (£30-50).** Offer CHOICE of seating: standard chair, stool, or floor cushion. Some children focus better when they can move slightly (stool) or sit lower (cushion). This is child-scale thinking applied to seating. *Impact: addresses the needs of children who struggle with sitting still on standard chairs.*

### Implementation Sequence

| Weekend/Week | Action | Effort | Expected Impact |
|---|---|---|---|
| This weekend | Unlock pencils, move materials to child height, strip walls, create quiet corner, clear entrance | 3-4 hours | Immediate: calmer visual environment, faster material access |
| Week 1 | Teach materials return routine (daily 5-min practice) | 5 min/day for 5 days | Transitions shorten dramatically by end of week |
| Week 2 | Observe and adjust — note which materials need repositioning, which children need extra routine practice | Observation only | Data-driven refinement |
| Week 3-4 | Add table plants, selective wall displays, open trays | £40-50, 2 hours setup | Visual warmth returns (purposefully, not randomly) |
| Next half term | Lighting changes, shelving unit, seating options | £100-150 | Deeper environmental quality improvement |

### Maintenance Protocol

**Daily (children do this):**
- End-of-session tidy: every child returns their materials to the correct place. This takes 2-3 minutes once routinised. A "shelf monitor" checks that each shelf looks correct.
- Plant check: is the table plant watered and healthy?

**Weekly (teacher does this):**
- Quick shelf audit: are materials in the right places? Is anything broken, missing, or no longer needed?
- Display check: is the working wall current? Should any student work be rotated?

**Half-termly (teacher + children):**
- Room review: "What's working in our classroom? What isn't? What should we change?" Involve children in environment decisions — Montessori's principle of child ownership extends to the space itself.
- Material rotation: remove materials that are no longer being used (completed topic resources) and introduce new ones. A smaller, curated selection is better than an overwhelming quantity.

### Before and After

**Before:** Children queue at the teacher's desk to ask for pencils. Walls scream with colour from every surface. Transitions take 10 minutes as 24 children simultaneously try to access materials from high shelves. The room feels busy and chaotic. Four children struggle to focus.

**After:** Pencils are on every table — children pick them up and begin working. Walls are calm: a number line, a working wall, and five well-mounted pieces of student work. Materials are on low shelves — children choose what they need and return it after use. Transitions take 2-3 minutes because children know where everything goes. There is a quiet reading corner where children can choose to work. Plants on each table add life. The room feels purposeful and calm.

The biggest change is not visual — it is behavioural. Children who previously asked permission for everything now act independently. The teacher who previously managed logistics now teaches.

---

## Known Limitations

1. **The prepared environment evidence is stronger for general classroom design principles than for Montessori-specific design.** Barrett et al. (2015) and Fisher et al. (2014) support the principles of visual order, natural light, and moderate complexity — but their studies were conducted in conventional classrooms, not Montessori environments. Lillard (2005) and Cossentino (2006) provide Montessori-specific evidence, but this is largely qualitative and observational rather than experimental. The combination of general classroom design research and Montessori-specific analysis provides a strong rationale, but the prepared environment as a complete system has not been tested in a randomised controlled trial.

2. **Environment design effects are difficult to isolate from instructional effects.** Lillard et al.'s (2006) study found positive outcomes for Montessori programmes, but these programmes combine prepared environments with specific instructional practices (three-period lessons, mixed-age grouping, uninterrupted work cycles). The specific contribution of the environment cannot be separated from the contribution of the instruction.

3. **School policies may limit environmental changes.** Many schools have policies about display requirements (literacy working walls, maths displays, behaviour charts), health and safety (real glass may be prohibited), and furniture (standardised tables and chairs from a central procurement system). The redesign plan above should be adapted to work within these constraints rather than fighting them.

4. **The initial transition may temporarily increase disorder.** When children who are used to asking for permission are suddenly given open access to materials, there may be a period of overuse, messiness, or testing of boundaries. This is normal and temporary. The materials return routine (Phase 2, step 9) addresses this, but teachers should expect a 1-2 week adjustment period.

---
# AGENT SKILLS STANDARD FIELDS (v2)
name: emergent-project-design-scaffold
description: "Scaffold an emergent project from observed children's interests using Reggio-inspired approaches. Use when following children's fascinations into deeper inquiry in early years or primary settings."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "global-cross-cultural-pedagogies/emergent-project-design-scaffold"
skill_name: "Emergent Project Design Scaffold"
domain: "global-cross-cultural-pedagogies"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Rinaldi (2006) — In Dialogue with Reggio Emilia: listening, researching and learning"
  - "Malaguzzi (1993) — For an education based on relationships"
  - "Helm & Katz (2016) — Young Investigators: the project approach in the early years (3rd edition)"
  - "Wien (2008) — Emergent Curriculum in the Primary Classroom: interpreting the Reggio Emilia approach in schools"
  - "Edwards, Gandini & Forman (2012) — The Hundred Languages of Children (3rd edition)"
input_schema:
  required:
    - field: "children_interest"
      type: "string"
      description: "The emerging interest, question, or fascination observed in the children — what has captured their attention"
    - field: "teacher_observations"
      type: "string"
      description: "What the teacher has noticed — children's questions, theories, experiments, and representations related to the interest"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age group"
    - field: "curriculum_connections"
      type: "string"
      description: "Curriculum areas the interest naturally connects to"
    - field: "available_resources"
      type: "string"
      description: "Materials, spaces, and community resources that could support the investigation"
    - field: "project_duration"
      type: "string"
      description: "How long the project might run — a week, several weeks, a term"
    - field: "team_context"
      type: "string"
      description: "Whether the teacher is working alone or in a team"
output_schema:
  type: "object"
  fields:
    - field: "project_scaffold"
      type: "object"
      description: "The emergent project design — not a fixed plan but a flexible scaffold that responds to children's developing inquiry"
    - field: "provocations"
      type: "array"
      description: "Experiences, materials, and questions designed to deepen and extend children's inquiry"
    - field: "curriculum_mapping"
      type: "object"
      description: "How the emerging project connects to curriculum objectives — natural connections, not forced ones"
    - field: "documentation_plan"
      type: "object"
      description: "How to document the project's evolution — capturing children's learning journey"
    - field: "decision_points"
      type: "array"
      description: "Moments where the teacher will observe and decide: extend this direction, introduce a new provocation, or allow the project to wind down"
chains_well_with:
  - "reggio-documentation-protocol"
  - "awe-wonder-experience-designer"
  - "agency-scaffold-generator"
  - "place-based-inquiry-anchor"
teacher_time: "4 minutes"
tags: ["Reggio-Emilia", "emergent-curriculum", "project-approach", "Rinaldi", "Malaguzzi", "provocations", "early-years", "primary"]
---

# Emergent Project Design Scaffold

## What This Skill Does

Designs a flexible scaffold for an emergent project — a sustained investigation driven by children's interests, questions, and theories, following the Reggio Emilia approach to curriculum. Unlike predetermined projects (where the teacher plans the topic, activities, and outcomes in advance), emergent projects begin with children's genuine interests and develop through a cycle of observation, provocation, documentation, and response. The teacher's role is not to plan the journey but to SCAFFOLD it — providing materials, provocations, and environments that deepen and extend the children's inquiry while connecting it to curriculum objectives. The critical principle from Rinaldi is that the teacher is a researcher alongside the children, genuinely curious about where the investigation will lead. The output includes a project scaffold (not a fixed plan but a flexible framework with decision points), provocations designed to deepen inquiry, curriculum connections, a documentation plan, and identified decision points where the teacher observes and responds. AI is specifically valuable here because designing provocations that are genuinely responsive to children's current thinking requires understanding both the developmental trajectory of children's ideas and the range of materials, experiences, and questions that can move thinking forward.

## Evidence Foundation

Rinaldi (2006) described emergent curriculum as "a process of negotiated learning" — the curriculum emerges from the intersection of children's interests, teachers' knowledge, and the environment. The teacher does not abandon planning but plans DIFFERENTLY: instead of planning activities in advance, the teacher plans provocations (materials, experiences, questions) that respond to what children are currently investigating. Malaguzzi (1993) articulated the environment as the "third teacher" — alongside the adult teacher and the child's peers, the physical environment provokes, supports, and documents learning. Emergent projects require thoughtful environmental design: materials that invite investigation, spaces that support collaboration, and displays that document and sustain the project's evolution. Helm & Katz (2016) provided practical guidance for the "project approach" in early years and primary settings, describing three phases: Phase 1 (beginning the project — identifying the interest, sharing initial knowledge, developing questions), Phase 2 (developing the project — investigating, representing, revisiting), and Phase 3 (concluding the project — sharing, reflecting, celebrating). Wien (2008) adapted Reggio principles for primary classrooms, demonstrating that emergent curriculum is not limited to early childhood but can be practised at any level when teachers are willing to follow children's questions. Edwards, Gandini & Forman (2012) documented how Reggio educators plan "progettazione" — not lesson plans but intentional design of environments, provocations, and encounters that might catalyse investigation, combined with careful documentation that informs the next step.

## Input Schema

The teacher must provide:
- **Children's interest:** What has captured their attention. *e.g. "The children found a bird's nest in the school garden and are fascinated by how it was built — they keep going back to look at it, drawing it, and asking questions about the bird that made it" / "Year 1 children are obsessed with maps after finding an old map of the school grounds — they want to make their own maps of everything" / "Several children are deeply engaged with building — constructing increasingly complex structures and testing whether they stand up"*
- **Teacher observations:** What the teacher has noticed. *e.g. "Three children spent 20 minutes examining the nest, pointing at the different materials woven into it. One child said 'the bird is like a builder.' Another asked 'how did the bird carry all these sticks?' I've noticed children collecting sticks and leaves and trying to weave them together during outdoor play." / "Children are drawing maps of their bedrooms, the playground, and their journey to school. They argue about whether the map is 'right' — 'No, the swings aren't there, they're THERE!' — which shows they're grappling with representation and perspective."*

Optional (injected by context engine if available):
- **Student level:** Age group
- **Curriculum connections:** Relevant curriculum areas
- **Available resources:** Materials, spaces, community resources
- **Project duration:** Expected length
- **Team context:** Solo or team

## Prompt

```
You are an expert in emergent curriculum and project-based investigation in the Reggio Emilia tradition, with deep knowledge of Rinaldi's (2006) concept of negotiated learning, Malaguzzi's (1993) hundred languages and environment as third teacher, Helm & Katz's (2016) project approach phases, Wien's (2008) emergent curriculum in primary settings, and Edwards, Gandini & Forman's (2012) account of Reggio progettazione. You understand that emergent projects are NEITHER unplanned ("let the children do whatever they want") NOR predetermined ("I've planned a bird project for this half-term"). They are intentionally scaffolded — the teacher observes, documents, interprets, and then designs provocations that deepen the children's inquiry in directions that are both child-led and educationally rich.

CRITICAL PRINCIPLES:
- **Start from the child's question, not the teacher's topic.** The interest is the children's — not a theme the teacher has chosen. The teacher's role is to recognise the interest, take it seriously, and provide opportunities for it to develop. If the teacher redirects the interest to fit a pre-planned topic, it ceases to be emergent.
- **Provocations, not lessons.** The teacher does not teach about birds — they provide a magnifying glass, books about nest construction, materials for building, and the question: "Could YOU build a nest that's as strong as the bird's?" A provocation invites investigation; a lesson delivers content. Provocations open possibilities; lessons close them.
- **The project is a conversation, not a delivery.** The project develops through a cycle: children investigate → teacher documents → teacher interprets → teacher designs provocation → children investigate further. Each step responds to the previous one. If the teacher plans all the provocations in advance, they are not responding — they are delivering.
- **Curriculum connections are found, not forced.** An emergent project on nest-building naturally connects to science (materials, habitats), technology (construction, engineering), literacy (stories about birds, information texts, children's own writing), mathematics (measurement, shape), and art (observation drawing, sculpture). These connections should be identified and used — but the investigation should not be distorted to "cover" a curriculum objective that doesn't fit.
- **Projects have a natural lifespan.** Not all interests sustain a long project. Some last a week and wind down; others last a term and keep deepening. The teacher should be attentive to the project's energy — extending it when children are engaged and allowing it to conclude gracefully when interest wanes.

Your task is to design an emergent project scaffold for:

**Children's interest:** {{children_interest}}
**Teacher observations:** {{teacher_observations}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for early years or Key Stage 1.
**Curriculum connections:** {{curriculum_connections}} — if not provided, identify natural connections.
**Available resources:** {{available_resources}} — if not provided, suggest accessible resources.
**Project duration:** {{project_duration}} — if not provided, design with decision points that allow the project to last 1–4 weeks depending on children's engagement.
**Team context:** {{team_context}} — if not provided, design for a solo practitioner.

Return your output in this exact format:

## Emergent Project: [Interest]

**Children's interest:** [What has captured their attention]
**Teacher's guiding question:** [What the teacher is curious about — what they want to understand about children's thinking through this project]
**Potential duration:** [Flexible estimate]

### Phase 1 — Launching the Investigation

[How to begin — sharing what children already know, surfacing their questions, creating the conditions for investigation]

### Phase 2 — Provocations and Investigations

For each provocation (3–5):
**Provocation [N]: [What the teacher offers]**
- **What:** [The material, experience, or question]
- **Why:** [What this provocation might reveal or develop — connected to the teacher's observations]
- **Watch for:** [What to observe — children's responses, theories, new questions]
- **If children respond by...:** [Possible next steps depending on children's response]

### Phase 3 — Deepening and Representing

[How children represent their understanding through multiple "languages" — drawing, building, writing, dramatic play, discussion]

### Phase 4 — Sharing and Concluding

[How the project is shared and celebrated — with the class, with families, with the school]

### Curriculum Connections

[Natural connections to curriculum areas — what children are learning through the project]

### Decision Points

[Specific moments where the teacher pauses, documents, and decides: continue this direction, introduce a new provocation, or allow the project to wind down]

### Documentation Plan

[How to document the project's journey — what to capture and how to use it]

**Self-check before returning output:** Verify that (a) the project begins from children's genuine interest, (b) provocations respond to observed thinking, (c) the scaffold is flexible with decision points, (d) curriculum connections are natural, and (e) the project has a plan for concluding, not just beginning.
```

## Example Output

**Scenario:** *Children's interest: "Reception children (ages 4–5) found a bird's nest in the school garden after it fell from a tree during a storm. They are fascinated by how it was built — examining the materials (twigs, moss, feathers, string, a piece of plastic bag), asking questions about the bird that made it, and trying to build their own nests during outdoor play." / Teacher observations: "Three children spent 20 minutes examining the nest with a magnifying glass. One said 'the bird is like a builder — she made a house!' Another asked 'how did the bird carry all these sticks with no hands?' A third pointed to the plastic bag piece and said 'the bird went shopping!' Several children have been collecting sticks, leaves, and string from the garden and trying to weave them into nests. The attempts keep falling apart, which is frustrating some children and motivating others to try differently." / Available resources: "School garden, outdoor area, art materials, clay, magnifying glasses, iPad for photos, access to a local nature reserve with a ranger"*

---

## Emergent Project: The Nest Builders

**Children's interest:** How birds build nests — materials, methods, and the remarkable skill of building without hands
**Teacher's guiding question:** "What do the children understand about how structures are built, and how will their understanding develop as they try to build structures themselves?"
**Potential duration:** 2–4 weeks, depending on sustained interest

### Phase 1 — Launching the Investigation

**Day 1 — Gathering what we know:**
Bring the nest (carefully) into the classroom. Place it on a table with magnifying glasses and invite children to examine it. In a group conversation, ask: "What do you notice?" Record children's observations on a large piece of paper (the teacher writes; children talk).

Then: "What questions do you have about this nest?" Record questions. Expected questions (based on observations so far):
- How did the bird build it?
- What is it made from?
- How did the bird carry the sticks?
- Where did the bird find the string?
- Why did it use plastic?
- Is the bird sad that the nest fell?

Display the observations and questions on the wall. These are the starting point of the investigation — the children's questions drive the project.

**Day 2 — What do we already know? What do we want to find out?**
Create a simple documentation panel: "What We Know About Nests" (children's current knowledge) alongside "What We Want to Find Out" (their questions). This makes the inquiry visible and creates a reference point that children can revisit throughout the project.

### Phase 2 — Provocations and Investigations

**Provocation 1: The Nest Material Investigation**
- **What:** Carefully deconstruct a section of the nest (or a second nest, if available) and lay out the individual materials: twigs, moss, feathers, string, plastic. Provide magnifying glasses and drawing materials. Ask: "What is the nest made of? Why do you think the bird chose THESE materials?"
- **Why:** The teacher observed that children are interested in the materials but haven't yet considered WHY the bird chose them. This provocation focuses attention on material properties — strength, flexibility, warmth, waterproofing.
- **Watch for:** Do children describe materials by their properties ("this one is bendy," "this one is soft") or only by their names ("it's a stick")? Property-based descriptions indicate emerging understanding of material science.
- **If children respond by examining properties:** Extend with a sorting challenge — "Can you sort these into groups? What's your rule for sorting?"
- **If children focus on where the materials came from:** Extend with a garden investigation — "Can you find these materials in OUR garden?"

**Provocation 2: The Building Challenge**
- **What:** Set up a "Nest Building Workshop" outdoors. Provide natural materials (sticks, grass, leaves, mud, feathers) and a challenge: "Can you build a nest that holds an egg?" Use a small wooden egg or ball as a test object. Work in pairs or small groups.
- **Why:** Children's earlier attempts at building kept falling apart. This provocation gives them focused time, specific materials, and a test criterion (does it hold the egg?). The frustration of structural failure is productive — it drives problem-solving and theory revision.
- **Watch for:** How children approach the problem — do they start randomly or with a plan? Do they imitate the real nest's structure? When the nest fails, do they try the same approach again or change their strategy? Listen for engineering language: "We need to make it tighter," "It needs to go round and round."
- **If children succeed:** Ask: "What made YOUR nest work? What did the bird do that you did too?" This connects their experience back to the bird's nest.
- **If children struggle:** Introduce a new provocation — show a video clip of a bird building a nest (BBC nature footage). Watch slowly. "What is the bird doing? How does she use her beak? What pattern is she following?"

**Provocation 3: Drawing the Nest (Close Observation)**
- **What:** Provide fine drawing pencils and place the nest in the centre of a small group. Ask: "Can you draw the nest EXACTLY as you see it — every stick, every piece of moss?" This is observational drawing, not creative expression.
- **Why:** Drawing demands close observation. Children who draw the nest will notice structural features they missed when just looking — the way sticks are interlocked, the layering of different materials, the circular shape. Drawing is a form of investigation.
- **Watch for:** What structural features appear in the drawings? Do children draw individual sticks or a general shape? Do they notice the weaving/interlocking pattern? The drawings reveal what children are SEEING, which indicates what they understand about the structure.
- **If children notice the interlocking pattern:** This is a key structural insight. Extend: provide weaving materials (strips of fabric, pipe cleaners) and a weaving frame. "Can you make materials interlock like the bird did?"

**Provocation 4: Expert Encounter**
- **What:** Arrange a visit from the nature reserve ranger (or a visit to the reserve). Children prepare questions in advance. The ranger shows different types of nests, explains how birds build, and if possible, shows birds in the garden or reserve.
- **Why:** The children have investigated the nest themselves and formed theories. Meeting an expert provides new information that they can compare with their own theories. The expert should ANSWER children's questions, not deliver a lecture — the children's inquiry drives the encounter.
- **Watch for:** How children reconcile the expert's information with their own theories. Do they update their ideas? Do they challenge the expert? ("But we tried that and it didn't work!") Both responses are valuable — they show children engaged in genuine inquiry.
- **If the encounter raises new questions:** These become the next phase of investigation. "The ranger said birds use mud as glue — can WE use mud as glue?"

### Phase 3 — Deepening and Representing

Children represent their learning through multiple languages:

**Drawing and painting:** Observational drawings of the nest, paintings of birds building, illustrated "instructions" for building a nest (a form of procedural writing)

**Construction:** Nest-building using increasingly varied materials. Some children may move from natural materials to experimenting with other materials — "What if we used playdough instead of mud?" This is engineering inquiry.

**Dramatic play:** Create a "bird building site" in the role-play area — hard hats, clipboards, "building plans" (children's drawings), and nest-building materials. Children act out the construction process, which reveals their understanding of sequence and method.

**Language and literacy:** Dictated stories ("The Bird Builder"), labels for a nest display, a class book of "What We Learned About Nests," letters to the bird ("Dear Bird, we found your nest and we are looking after it")

**Mathematics:** Measuring sticks used in the nest ("the longest stick is ___ cm"), counting materials, comparing nest sizes (if multiple nests are available), patterns in weaving

### Phase 4 — Sharing and Concluding

**The Nest Exhibition:** Display the documentation of the project in the school entrance or classroom — photographs of children investigating, their exact words, their drawings, their constructed nests alongside the real nest. Include the journey: "First we thought... then we discovered... now we understand..."

**Family invitation:** Invite families to visit the exhibition. Children explain their project to their families — this is the most powerful assessment: can the child explain what they learned to someone who wasn't there?

**Returning the nest:** If appropriate, return the nest to the garden — or create a permanent display. Discuss with children: "The bird might build a new nest. Should we help? How?"

**Natural conclusion:** The project ends when children's interest moves to a new focus. This might be after 2 weeks or 4 weeks. The teacher recognises the winding down (fewer children choosing nest activities, energy shifting elsewhere) and helps the group mark the ending with the exhibition.

### Curriculum Connections

| Curriculum Area | What Children Learn Through the Project |
|---|---|
| Science (Living things and habitats) | Bird habitats, nest construction, material properties, observation skills |
| Design & Technology | Building structures, testing, iterating, material selection for purpose |
| Mathematics | Measuring, counting, pattern, shape (circular nest, interlocking pattern) |
| Literacy | Vocabulary development, procedural writing (how to build a nest), storytelling, labelling, information texts |
| Art | Observational drawing, sculpture (nest construction as art), attention to detail |
| PSHE | Respect for nature, teamwork, persistence when building fails, caring for living things |

### Decision Points

| When | What to Observe | Decision |
|---|---|---|
| End of Week 1 | Are children still choosing nest-related activities? Are new questions emerging? | If yes: introduce Provocation 3 or 4. If interest is waning: begin winding down. |
| After the Building Challenge | Did the challenge generate new questions or frustration? | If new questions: follow them. If frustration without curiosity: provide more support or a different entry point. |
| After the Expert Encounter | Did new information spark new inquiry? | If yes: extend the project. If the encounter "answered everything": the project may be ready to conclude. |
| When a new interest emerges | Are children's questions shifting to a new topic? | Allow the transition. The nest project can conclude naturally as a new interest takes over. |

### Documentation Plan

Document throughout using the Reggio Documentation Protocol:
- **Daily:** 2–3 photographs + 2–3 verbatim quotes (captured in notebook, expanded at the end of the day)
- **Weekly:** Select the most revealing evidence. Create a mini-panel: "This week we discovered..." Display at children's eye level for revisiting.
- **Throughout:** Collect children's drawings and constructions (photographed if 3D). Annotate with children's explanations.
- **End of project:** Compile into a project book or digital portfolio. This becomes part of the class's "group memory" and a resource for professional reflection.

---

## Known Limitations

1. **Emergent curriculum requires a teacher who is comfortable with uncertainty.** There is no predetermined endpoint, no guaranteed "coverage" of curriculum objectives, and no way to know in advance where the project will go. Teachers accustomed to detailed planning may find this uncomfortable. The scaffold above provides structure — but within that structure, the teacher must be willing to follow the children's lead.

2. **Accountability systems can conflict with emergent approaches.** Schools that require detailed medium-term plans submitted in advance cannot easily accommodate emergent curriculum. The curriculum connections identified above show that emergent projects DO address curriculum objectives — but not in a predictable, plannable sequence. Teachers may need to advocate for flexibility within their school's planning requirements.

3. **Not all interests sustain a project.** Some children's fascinations are momentary — intense for a day and then gone. The teacher's skill lies in distinguishing a momentary fascination from a sustained interest that can sustain an investigation. The decision points above help — if interest wanes after Week 1, the project is concluded rather than artificially extended.

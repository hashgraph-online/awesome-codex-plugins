---
# AGENT SKILLS STANDARD FIELDS (v2)
name: curriculum-knowledge-architecture-designer
description: "Map the epistemic structure of a subject to determine knowledge types and inform curriculum sequencing. Use when designing courses, restructuring programmes, or analysing knowledge architecture."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "curriculum-assessment/curriculum-knowledge-architecture-designer"
skill_name: "Curriculum Knowledge Architecture Designer"
domain: "curriculum-assessment"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Bernstein (1999) — Vertical and horizontal discourse: hierarchical vs horizontal knowledge structures"
  - "Bernstein (2000) — Pedagogy, Symbolic Control and Identity: recontextualisation and the pedagogic device"
  - "Muller (2009) — Forms of knowledge and curriculum coherence: conceptual vs contextual coherence"
  - "Maton (2009) — Cumulative and segmented learning: curriculum structures and knowledge-building"
  - "Maton (2013) — Making semantic waves: semantic gravity and density as tools for cumulative learning"
  - "Maton (2014) — Knowledge and Knowers: Legitimation Code Theory (Semantics dimension)"
  - "Young (2008) — Bringing Knowledge Back In: powerful knowledge and social realist curriculum theory"
  - "Wheelahan (2010) — Why Knowledge Matters in Curriculum: access to theoretical knowledge as social justice"
  - "Bianchi, Pisiotis & Cabrera Giraldez (2022) — GreenComp: European Sustainability Competence Framework"
  - "Bacigalupo et al. (2016) — EntreComp: Entrepreneurship Competence Framework"
  - "Sala et al. (2020) — LifeComp: European Framework for Personal, Social and Learning to Learn"
input_schema:
  required:
    - field: "curriculum_input_type"
      type: "string"
      description: "The type of curriculum input: 'course', 'scope-and-sequence', or 'project-brief'"
    - field: "domain_or_subject"
      type: "string"
      description: "Name and brief description of the subject or domain"
    - field: "learner_stage"
      type: "string"
      description: "Age range or year group"
    - field: "learning_goals"
      type: "string"
      description: "Intended outcomes — 3-5 sentences describing what students should know, understand, and be able to do"
  optional:
    - field: "existing_curriculum_documents"
      type: "string"
      description: "From context engine: text of curriculum documents, unit plans, or scope-and-sequence"
    - field: "competency_framework"
      type: "string"
      description: "From context engine: the school's competency or dispositional framework in use"
    - field: "prior_knowledge_baseline"
      type: "string"
      description: "From context engine: what students already know and can do before this curriculum begins"
output_schema:
  type: "object"
  fields:
    - field: "epistemic_diagnosis"
      type: "object"
      description: "Which knowledge types are present, approximate proportions, and reasoning"
    - field: "knowledge_architecture_map"
      type: "object"
      description: "For each type: hierarchical prerequisite chains, horizontal conceptual hubs and lenses, or dispositional progression bands"
    - field: "mixed_architecture_notes"
      type: "string"
      description: "Where types interact, overlap, or create tension in this specific curriculum. When a dispositional goal is identified, flag whether it is knowledge-contingent — i.e. whether it requires a sufficient hierarchical and horizontal knowledge base before it can meaningfully develop. Examples: critical thinking, ecological literacy, regenerative mindset, entrepreneurial thinking. For knowledge-contingent dispositions, identify which specific hierarchical and horizontal elements are prerequisites for the disposition to be operable. State explicitly: the disposition cannot develop authentically until these prerequisites are in place."
    - field: "teaching_sequencing_implications"
      type: "string"
      description: "What the architecture means for content ordering and pacing"
    - field: "assessment_implications"
      type: "object"
      description: "Which elements are auto-assessable vs require teacher judgment and why. When horizontal knowledge is present, flag whether critical thinking is being deliberately developed through explicit instruction in disciplinary thinking standards, or whether it is assumed to emerge through exposure to horizontal content. Research (Bailin et al. 1999; Willingham 2007) is clear that disciplinary content does not automatically develop critical thinking — it must be taught explicitly within the discipline. If the curriculum identifies critical thinking as a goal but does not include explicit teaching of what good thinking looks like in this domain, flag this as a design gap."
    - field: "ai_tutoring_design_implications"
      type: "string"
      description: "How this architecture should inform an intelligent tutoring system or AI teacher assistant"
chains_well_with:
  - "learning-target-authoring-guide"
  - "competency-framework-mapper"
  - "scope-and-sequence-designer"
  - "d2r-project-cycle-designer"
teacher_time: "5 minutes"
tags: ["knowledge-structure", "curriculum-architecture", "Bernstein", "epistemic-design", "hierarchical", "horizontal", "dispositional", "mixed-architecture", "AI-tutoring"]
---

# Curriculum Knowledge Architecture Designer

## What This Skill Does

Takes a curriculum input — a single course, a subject scope and sequence, or a real-world project brief — and diagnoses the epistemic architecture of the knowledge domain. It determines whether the domain is primarily Hierarchical, Horizontal, Dispositional, or a mixed architecture, then constructs the appropriate knowledge structure map for each type present, and outputs concrete implications for teaching sequence, assessment design, and AI tutoring architecture. Most real curricula — especially project-based and real-world learning designs — are mixed architectures. The skill diagnoses proportion and interaction, not forcing a single type. AI is specifically valuable here because epistemic diagnosis requires simultaneously applying sociological theory (Bernstein's knowledge structures), curriculum design expertise (sequencing and assessment logic), and competency framework literacy (dispositional progression) — a combination that is rare in any single educator and time-consuming to work through manually.

## Evidence Foundation

Bernstein (1999) distinguished two forms of discourse — horizontal discourse (everyday, context-specific knowledge) and vertical discourse (systematic, principled knowledge) — and within vertical discourse identified two knowledge structures. **Hierarchical knowledge structures** are coherent, explicitly principled, and hierarchically integrated: new theory subsumes and generalises prior knowledge, creating a cumulative progression where lower-level concepts must be mastered before higher-level ones are accessible. The natural sciences are the paradigmatic example. **Horizontal knowledge structures** are organised as a series of specialised languages or lenses, each with its own modes of inquiry and criteria for valid knowledge. Development occurs through accumulation of new perspectives rather than integration. The humanities and social sciences are paradigmatic. Bernstein (2000) extended this framework through the concept of recontextualisation — how knowledge is transformed as it moves from its field of production into pedagogic contexts — which directly informs how curriculum designers must think about knowledge type when making sequencing decisions.

Muller (2009) applied Bernstein's framework to curriculum coherence, distinguishing **conceptual coherence** (characteristic of hierarchical knowledge — curricula where knowledge builds cumulatively on prior knowledge) from **contextual coherence** (characteristic of segmental curricula — where each segment is adequate to a specific context but segments do not necessarily build on one another). This distinction has direct implications for sequencing: conceptually coherent curricula have a logic that is difficult to reorder, while contextually coherent curricula can be entered from multiple points.

Maton (2009, 2013, 2014) developed Legitimation Code Theory's Semantics dimension, providing two analytical tools: **semantic gravity** (the degree to which meaning is tied to a specific context — stronger SG means more contextual, weaker SG means more abstract and transferable) and **semantic density** (the degree to which meaning is condensed into terms or symbols). Maton (2013) introduced the concept of **semantic waves** — the pedagogic practice of moving between concrete examples (high SG, low SD) and abstract principles (low SG, high SD) — showing that curricula and teaching that create these waves enable cumulative knowledge-building, while those that remain flat (always contextual or always abstract) produce segmented learning. This provides a diagnostic tool for identifying where in a curriculum conceptual unpacking and repacking are needed.

Young (2008) argued that curriculum theory must take seriously which knowledge matters — introducing the concept of **powerful knowledge**: specialised, systematic, discipline-based knowledge that gives learners access to explanatory frameworks they cannot acquire through everyday experience. Wheelahan (2010) extended this argument to show that competency-based curricula that strip knowledge down to contextual skills without theoretical grounding deny students access to the conceptual structures that enable social participation — making knowledge architecture a question of equity, not merely pedagogy.

The **dispositional knowledge** category draws on competency framework literature. Unlike hierarchical and horizontal structures (which describe how propositional knowledge is organised), dispositional knowledge is constituted by developing capacities, orientations, and enacted competencies — it exists only in enactment. The EU competency frameworks provide the most rigorous articulations: GreenComp (Bianchi, Pisiotis & Cabrera Giraldez, 2022) defines twelve sustainability competences including agency, systems thinking, and values literacy; EntreComp (Bacigalupo et al., 2016) defines fifteen entrepreneurship competences including self-awareness, creativity, and learning through experience across an eight-level progression model; LifeComp (Sala et al., 2020) defines nine personal, social, and learning-to-learn competences including self-regulation, collaboration, and critical thinking. These frameworks share a common characteristic: progression is qualitative and developmental, described through bands rather than prerequisite chains, and assessment requires teacher judgment of enacted capability rather than testing of propositional knowledge.

## Input Schema

The teacher must provide:
- **Curriculum input type:** What kind of input are you providing? *e.g. "course" / "scope-and-sequence" / "project-brief"*
- **Domain or subject:** Name and brief description. *e.g. "Year 9 Science — forces, energy, and motion" / "Design and Regeneration project — smart water systems for a local wetland" / "IB History — causes and consequences of 20th-century authoritarian states"*
- **Learner stage:** Age range or year group. *e.g. "12–14 years" / "Year 10" / "Grade 7–8"*
- **Learning goals:** What students should know, understand, and be able to do — 3–5 sentences. *e.g. "Students will understand how forces cause changes in motion, apply Newton's laws to real-world situations, design and test a simple machine, and communicate scientific reasoning through written argument."*

Optional (injected by context engine if available):
- **Existing curriculum documents:** Text of curriculum documents, unit plans, or scope-and-sequence
- **Competency framework:** The school's dispositional or competency framework
- **Prior knowledge baseline:** What students already know and can do

## Prompt

```
You are an expert in curriculum epistemology and knowledge structure analysis, with deep knowledge of Bernstein's (1999, 2000) theory of knowledge structures, Muller's (2009) work on curriculum coherence, and Maton's (2009, 2013, 2014) Legitimation Code Theory — particularly the Semantics dimension (semantic gravity and semantic density). You also understand competency framework design (GreenComp, EntreComp, LifeComp) and the distinction between propositional knowledge structures and dispositional development.

Your task is to diagnose the epistemic architecture of the following curriculum input and produce a complete knowledge architecture analysis.

**Curriculum input type:** {{curriculum_input_type}}
**Domain or subject:** {{domain_or_subject}}
**Learner stage:** {{learner_stage}}
**Learning goals:** {{learning_goals}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Existing curriculum documents:** {{existing_curriculum_documents}} — if not provided, work from the domain, subject description, and learning goals.
**Competency framework:** {{competency_framework}} — if not provided, identify any dispositional elements from the learning goals.
**Prior knowledge baseline:** {{prior_knowledge_baseline}} — if not provided, assume typical prior knowledge for this learner stage.

Apply the following framework. You MUST use the exact three knowledge types defined below. Most real curricula contain more than one type — your diagnosis must identify ALL types present, estimate their approximate proportion, and explain how they interact.

## The Three Knowledge Types

**1. Hierarchical Knowledge Structure (Bernstein, 1999)**
Knowledge is coherent, systematically principled, and organised so that lower-level concepts must be mastered before higher-level ones are accessible. Development is through integration, where new theory subsumes and generalises prior knowledge. The curriculum logic is cumulative — sequencing is constrained by prerequisite relationships. Conceptual coherence (Muller, 2009) holds: content cannot be freely reordered without loss.

Indicators: prerequisite chains exist; concepts build in abstraction; mastery of prior concepts is necessary for later ones; errors at lower levels propagate upward; the subject has a canonical sequencing logic.

Examples: mathematics, formal logic, music theory, programming fundamentals, chemistry, physics.

**2. Horizontal Knowledge Structure (Bernstein, 1999)**
Knowledge is organised as a series of specialised languages or lenses, each with its own modes of inquiry and criteria for valid knowledge. Content can be entered from multiple points; development is through accumulation of new perspectives rather than integration. Disciplinary thinking skill develops progressively even though content is not strictly prerequisite-ordered. Contextual coherence (Muller, 2009) allows curriculum segments to be reordered, though analytical sophistication still develops cumulatively.

Indicators: multiple valid interpretive lenses exist; content can be studied in various orders; "thinking like a historian/philosopher/sociologist" develops across the curriculum rather than through a fixed sequence; new units add perspectives rather than building on prior units.

Examples: history, literature, philosophy, geography, sociology, art criticism.

**3. Dispositional Knowledge Structure**
Knowledge is constituted by developing capacities, orientations, and enacted competencies. The knowledge cannot be separated from the learner's growing capability — it exists only in enactment. Progression is qualitative and developmental, requiring teacher judgment rather than automated assessment. Competency frameworks (GreenComp, EntreComp, LifeComp) provide the most rigorous articulations of this type.

Indicators: the learning goal describes who the student is becoming, not just what they know; progression is described in developmental bands (emerging → developing → extending) rather than prerequisite chains; assessment requires observation of enacted behaviour over time; the competency cannot be tested through a single task.

Examples: agency, collaboration, ecological literacy, entrepreneurial thinking, self-regulation, creative confidence, regenerative mindset.

## Diagnosis Process

Step 1: Read the curriculum input carefully. For each learning goal, determine which knowledge type(s) it belongs to.

Step 2: Estimate the approximate proportion of each type present (as percentages that sum to 100%). Explain your reasoning — which specific goals or content areas belong to which type.

Step 3: For each type present, build the appropriate knowledge structure map:
- **Hierarchical:** Identify the key prerequisite chains. Order concepts topologically — which concepts must come before which. Flag any concepts where the prerequisite relationship is hard (cannot proceed without it) vs soft (easier with it but possible without).
- **Horizontal:** Identify the conceptual hubs (central themes, phenomena, or questions) and the lenses or perspectives that orbit each hub. Show how analytical sophistication develops across the curriculum even though content is not prerequisite-ordered.
- **Dispositional:** Define progression band descriptors across 4 levels: Emerging → Developing → Competent → Extending. Each level must describe what the learner DOES (observable behaviour), not what they "understand" internally. Include indicators that distinguish between levels.

Step 4: Analyse the mixed architecture — where do types interact, overlap, or create tension? Where does a hierarchical prerequisite chain intersect with a dispositional development goal? Where does a horizontal lens require hierarchical foundational knowledge?

Step 5: Derive implications for teaching, assessment, and AI tutoring.

Return your output in this exact format:

## Knowledge Architecture Analysis: [Domain/Subject Name]

**Input type:** [course / scope-and-sequence / project-brief]
**Learner stage:** [age/year]
**Learning goals:** [Summarised]

### 1. Epistemic Diagnosis

**Architecture type:** [Mixed / Primarily Hierarchical / Primarily Horizontal / Primarily Dispositional]
**Proportions:** [e.g. 40% Hierarchical, 35% Horizontal, 25% Dispositional]

**Reasoning:**
[For each knowledge type present, explain which specific learning goals or content areas belong to it and why. Reference the indicators from the framework above.]

### 2. Knowledge Architecture Map

#### Hierarchical Elements
[If present: prerequisite chains with topological ordering. Show which concepts must come before which. Mark hard vs soft prerequisites. Use a visual chain format.]

#### Horizontal Elements
[If present: conceptual hubs and the lenses/perspectives that orbit them. Show how analytical thinking develops across the curriculum.]

#### Dispositional Elements
[If present: progression band descriptors across 4 levels — Emerging, Developing, Competent, Extending — with observable indicators at each level for each dispositional competency identified.]

### 3. Mixed Architecture Notes

[Where do types interact? Where does tension arise? Be specific to THIS curriculum.]

### 4. Teaching & Sequencing Implications

[What does the architecture mean for how content should be ordered and paced? Which elements have constrained sequencing (hierarchical) vs flexible sequencing (horizontal)? Where must dispositional development run as a continuous thread rather than being assigned to specific lessons?]

### 5. Assessment Implications

**Auto-assessable elements (suitable for AI/automated assessment):**
[List specific elements and explain why they are auto-assessable — typically hierarchical elements with clear right/wrong answers or demonstrable procedures.]

**Teacher-judgment elements (require human assessment):**
[List specific elements and explain why they require teacher judgment — typically dispositional elements and sophisticated horizontal analysis.]

**Mixed elements (partial automation possible):**
[Elements where AI can assess some dimensions but teacher judgment is needed for others.]

### 6. AI Tutoring Design Implications

[How should this architecture inform an intelligent tutoring system or AI teacher assistant? Consider:
- For hierarchical elements: adaptive sequencing, prerequisite checking, targeted practice
- For horizontal elements: perspective-prompting, analytical scaffolding, exposure to multiple lenses
- For dispositional elements: reflection prompts, portfolio tracking, teacher dashboards (NOT automated grading)
- For mixed architectures: how the tutoring system should handle the transitions between types]

**Self-check before returning output:** Verify that (a) all three knowledge types have been considered, not just the dominant one, (b) proportions are justified with specific references to learning goals, (c) the architecture map uses the correct format for each type (prerequisite chains for hierarchical, hubs-and-lenses for horizontal, progression bands for dispositional), (d) mixed architecture notes are specific to THIS curriculum rather than generic, (e) assessment implications distinguish clearly between auto-assessable and teacher-judgment elements, and (f) AI tutoring implications are practical and architecture-specific.
```

## Example Output

**Scenario:** *Curriculum input type: "project-brief" / Domain or subject: "Design to Regenerate (D2R) — Smart Water Systems: students investigate water quality and flow in a local degraded wetland, design sensor-based monitoring solutions, and propose a regeneration plan that integrates ecological science, technology, and community engagement" / Learner stage: "12–14 years (Year 7–8)" / Learning goals: "Students will understand water cycle processes and water quality science (pH, dissolved oxygen, turbidity, nutrient loading). They will learn basic electronics and sensor technology to design a water monitoring prototype. They will apply systems thinking to analyse the wetland as an interconnected ecological, social, and economic system. They will develop agency and collaboration as regenerative practitioners — taking responsibility for a real place and working with community stakeholders. They will communicate findings and proposals to a genuine audience (local council or environmental group)."*

---

## Knowledge Architecture Analysis: D2R Smart Water Systems

**Input type:** project-brief
**Learner stage:** 12–14 years (Year 7–8)
**Learning goals:** Water cycle and water quality science; basic electronics and sensor technology; systems thinking applied to a wetland ecosystem; agency and collaboration as regenerative practitioners; communication to authentic audiences.

### 1. Epistemic Diagnosis

**Architecture type:** Mixed — all three knowledge types are present in significant proportions.
**Proportions:** 40% Hierarchical, 30% Horizontal, 30% Dispositional

**Reasoning:**

**Hierarchical (40%):** Two distinct prerequisite chains are present. First, the water quality science strand: students must understand the water cycle before they can understand water quality indicators, and must understand indicators before they can interpret field data. pH, dissolved oxygen, turbidity, and nutrient loading each have a conceptual prerequisite structure — you cannot meaningfully interpret a dissolved oxygen reading without understanding that oxygen dissolves in water, that living organisms consume it, and that temperature affects saturation. Second, the electronics and sensor technology strand: students must understand basic circuits before sensor function, and sensor function before prototype design. These are classically hierarchical — errors at lower levels propagate upward (a student who does not understand what pH measures cannot interpret pH data), and sequencing is constrained by the prerequisite structure.

**Horizontal (30%):** The systems thinking and communication strands operate as horizontal knowledge. Analysing the wetland as an ecological, social, and economic system requires applying multiple disciplinary lenses — ecological science, economics, social geography, ethics — to the same phenomenon. There is no single correct order for these lenses; each adds a new perspective rather than building on the previous one. A student might analyse the wetland's ecological function first and economic value second, or vice versa — both orderings are valid. However, the sophistication of systems analysis develops cumulatively: early analyses will be single-lens ("the wetland filters water"), while later analyses will be multi-lens and integrative ("the wetland's water-filtering function has ecological value, economic value to downstream users, and cultural significance to the local community — and these values are in tension because economic development upstream degrades the filtering function"). This is characteristic of Bernstein's horizontal knowledge structure: content can be entered from multiple points, but analytical thinking develops progressively.

**Dispositional (30%):** Agency, collaboration, and regenerative mindset are dispositional learning goals. These are not propositional knowledge that can be taught and tested — they are capacities that develop through enactment. A student does not "know" agency; they increasingly demonstrate it through taking initiative, persisting through difficulty, and owning responsibility for outcomes. Collaboration is not a skill to be mastered in a lesson but a disposition that develops qualitatively over time — from compliance (doing assigned group tasks) through coordination (dividing work effectively) to genuine co-construction (building ideas together that no individual could produce alone). Regenerative mindset — the orientation toward understanding and restoring living systems rather than merely extracting from them — is the deepest dispositional goal, requiring sustained experience and reflection rather than instruction.

### 2. Knowledge Architecture Map

#### Hierarchical Elements

**Prerequisite Chain 1: Water Quality Science**

```
Water cycle fundamentals (evaporation, condensation, precipitation, runoff, infiltration)
    ↓ [hard prerequisite]
Properties of water (solubility, temperature effects, pH scale)
    ↓ [hard prerequisite]
Water quality indicators (pH, dissolved oxygen, turbidity, nutrient loading)
    ├── pH: acid-base chemistry basics → pH scale → environmental pH ranges
    ├── Dissolved oxygen: gas solubility → temperature dependence → biological demand
    ├── Turbidity: suspended particles → light penetration → measurement methods
    └── Nutrient loading: nitrogen/phosphorus cycle basics → eutrophication process → threshold levels
        ↓ [hard prerequisite]
Field data interpretation (reading measurements, comparing to standards, identifying patterns)
    ↓ [soft prerequisite — possible but harder without]
Evidence-based conclusions (claim-evidence-reasoning from water quality data)
```

**Prerequisite Chain 2: Sensor Technology**

```
Basic circuits (voltage, current, components, simple circuit construction)
    ↓ [hard prerequisite]
Sensor principles (how sensors convert physical properties to electrical signals)
    ↓ [hard prerequisite]
Specific sensor types (pH probe, DO sensor, turbidity sensor — how each works)
    ↓ [soft prerequisite]
Prototype design (selecting sensors, connecting to microcontroller, basic data logging)
    ↓ [soft prerequisite]
Data validation (checking sensor readings against known standards, calibration concepts)
```

**Sequencing constraint:** Chain 1 and Chain 2 are largely independent until they converge at field data collection, where students use the sensors (Chain 2) to collect the water quality data (Chain 1). Both chains must reach their respective convergence points before fieldwork begins.

#### Horizontal Elements

**Central Hub: The Wetland as a System**

```
                        ┌── Ecological lens: biodiversity, habitat function,
                        │   food webs, nutrient cycling, ecosystem services
                        │
                        ├── Hydrological lens: water flow, catchment dynamics,
                        │   upstream/downstream relationships, flood regulation
                        │
The Wetland ────────────├── Economic lens: land value, water treatment costs,
as a System             │   ecosystem service valuation, development pressure
                        │
                        ├── Social lens: community relationships to the wetland,
                        │   Indigenous/local knowledge, recreational and cultural value
                        │
                        └── Ethical lens: intergenerational responsibility,
                            rights of nature, competing stakeholder interests
```

**Analytical sophistication develops across these lenses:**

| Stage | What the student does |
|-------|----------------------|
| Single-lens | Analyses the wetland through one perspective at a time: "The wetland is important because it is home to many species." |
| Multi-lens | Applies two or more lenses to the same feature: "The wetland filters water (ecological function) which saves the council money on water treatment (economic value)." |
| Integrative | Identifies tensions and trade-offs between lenses: "Developing the upstream land would increase economic output but degrade the wetland's filtering capacity, which would increase water treatment costs downstream — so the economic argument for development is weaker than it first appears." |
| Systemic | Sees the whole system dynamically: "The wetland's ecological, economic, and social values are interdependent — degrading one degrades all. A regeneration plan must address the system, not just individual components." |

**Sequencing flexibility:** Lenses can be introduced in any order. However, the ecological and hydrological lenses provide more productive entry points for 12–14-year-olds because they connect to observable, concrete phenomena (you can see biodiversity, you can measure water flow), while economic and ethical lenses are more abstract and benefit from having concrete data to reason about.

#### Dispositional Elements

**Competency 1: Agency as a Regenerative Practitioner**

| Level | Observable indicators |
|-------|----------------------|
| **Emerging** | Participates when directed. Completes assigned tasks related to the wetland investigation. Relies on teacher to define problems and next steps. Shows interest but waits for instruction before acting. |
| **Developing** | Identifies problems or opportunities independently: "I noticed the water is discoloured near the drain outlet — we should test there." Takes initiative on specific tasks within the project. Begins to express ownership: "our wetland" rather than "the wetland." |
| **Competent** | Drives investigation forward without prompting. Makes decisions about what to investigate next and justifies them. Takes responsibility for project outcomes: "Our data wasn't reliable enough — we need to recalibrate and resample." Seeks out information and resources independently. |
| **Extending** | Acts as a steward: connects the project to longer-term action beyond the classroom. Contacts community stakeholders independently. Identifies what the project cannot address and what should happen next. Demonstrates sustained commitment to the place beyond the project timeline. |

**Competency 2: Collaboration**

| Level | Observable indicators |
|-------|----------------------|
| **Emerging** | Works alongside others. Shares materials and space. Contributes when asked. May default to working alone or dividing tasks to avoid genuine interaction. |
| **Developing** | Coordinates effectively: divides tasks based on strengths, meets deadlines, communicates progress. Listens to others' ideas and incorporates them. Resolves minor disagreements without teacher intervention. |
| **Competent** | Co-constructs ideas: builds on others' contributions to produce something no individual could create alone. Actively seeks out perspectives different from their own. Adjusts their approach based on what the team needs — sometimes leading, sometimes supporting. |
| **Extending** | Facilitates group thinking: draws out quieter members, synthesises diverse viewpoints, navigates genuine disagreement productively. Reflects on and articulates how the collaboration shaped the outcome: "We wouldn't have seen the connection between the drainage pattern and the algae bloom if Priya hadn't suggested mapping both datasets together." |

**Competency 3: Regenerative Mindset**

| Level | Observable indicators |
|-------|----------------------|
| **Emerging** | Understands that the wetland is damaged and that humans caused the damage. Frames the problem as "fixing what's broken" — a deficit orientation. |
| **Developing** | Begins to see the wetland as a living system with its own capacity for recovery. Shifts from "fixing" to "supporting recovery." Asks questions about what the wetland needs rather than only what humans want from it. |
| **Competent** | Designs proposals that work with ecological processes rather than imposing human solutions. Considers the wetland's needs alongside human needs. Recognises that regeneration is ongoing, not a one-time fix. |
| **Extending** | Articulates a regenerative philosophy: understands that humans are part of the system, not separate from it. Proposes solutions that create conditions for the system to regenerate itself. Connects the specific wetland project to broader patterns of ecological degradation and regeneration. |

### 3. Mixed Architecture Notes

**Hierarchical-Horizontal interaction:** The systems thinking strand (horizontal) requires foundational science knowledge (hierarchical) to function. A student cannot apply an ecological lens to the wetland without understanding water quality indicators, and cannot apply an economic lens without understanding ecosystem services — which requires the ecological understanding first. This creates a partially constrained sequence within what is otherwise a flexible horizontal structure: the ecological lens should come before the economic lens, not because of content logic within the horizontal structure, but because of prerequisite dependencies from the hierarchical strand.

**Hierarchical-Dispositional interaction:** The sensor technology chain (hierarchical) and agency (dispositional) interact in a productive tension. The hierarchical strand provides structured, teachable skills (circuit building, sensor operation) that give students concrete competence — and competence fuels agency. A student who can build and operate a water sensor has a tangible capability that empowers action. However, if the hierarchical strand is taught in isolation (as a traditional electronics unit), the agency development stalls because the skills feel disconnected from purpose. The architecture requires that the hierarchical teaching is embedded within the project context so that skill acquisition is experienced as empowerment for action, not as abstract instruction.

**Horizontal-Dispositional interaction:** Systems thinking (horizontal) and regenerative mindset (dispositional) are deeply intertwined. The ability to see multiple perspectives on the wetland (horizontal) feeds the development of a regenerative orientation (dispositional) — you cannot develop a regenerative mindset without first seeing the system as interconnected. Conversely, a growing regenerative orientation motivates deeper systems analysis. These two types reinforce each other and should not be separated in instruction.

**Key tension:** Assessment of the hierarchical elements (water quality science, electronics) can be standardised and criterion-referenced. Assessment of the dispositional elements (agency, collaboration, regenerative mindset) cannot — it requires sustained observation and professional judgment. A project assessment framework that weights both equally must accommodate fundamentally different modes of evidence. There is a risk that the easily-measured hierarchical elements dominate assessment simply because they are easier to assess, marginalising the dispositional goals that are arguably the most important outcomes of a D2R project.

### 4. Teaching & Sequencing Implications

**Constrained sequence (hierarchical):** The water quality science chain must be taught before fieldwork — students cannot collect meaningful data without understanding what they are measuring. The sensor technology chain must reach "specific sensor types" before field deployment. These two chains should converge approximately one-third of the way through the project, creating a natural transition from classroom-based instruction to field-based inquiry.

**Flexible sequence (horizontal):** The systems thinking lenses can be introduced in any order after the ecological lens (which depends on the hierarchical science foundation). A productive sequence for 12–14-year-olds: ecological → hydrological → social → economic → ethical. This moves from concrete and observable to abstract and evaluative. However, a teacher who knows their students' strengths might reorder — a class with strong community connections might start with the social lens.

**Continuous thread (dispositional):** Agency, collaboration, and regenerative mindset cannot be taught in specific lessons — they develop across the entire project. The teaching implication is that every lesson must include opportunities for students to exercise these dispositions, and the teacher must notice and name them when they appear. A dedicated reflection protocol at the end of each week — "Where did you show agency this week? Where did collaboration change the outcome?" — makes the dispositional development visible and intentional.

**Pacing:** The hierarchical elements front-load — most of the direct instruction happens in the first third of the project. The horizontal elements build across the middle third as students apply multiple lenses to their field data. The dispositional elements are present throughout but become most visible in the final third when students take ownership of their regeneration proposals and present to authentic audiences.

### 5. Assessment Implications

**Auto-assessable elements (suitable for AI/automated assessment):**
- Water quality indicator knowledge (Can the student correctly explain what pH, dissolved oxygen, turbidity, and nutrient loading measure? — testable via structured questions)
- Data interpretation (Can the student read a data table and identify whether readings are within healthy ranges? — testable via data interpretation tasks)
- Basic circuit knowledge (Can the student identify components and explain circuit function? — testable via diagram-based tasks)
- Sensor function (Can the student explain how a specific sensor converts a physical property to a signal? — testable via structured explanation)

These elements have clear right/wrong answers or demonstrable procedural correctness. AI can assess them reliably, provide immediate feedback, and adapt difficulty.

**Teacher-judgment elements (require human assessment):**
- Agency development (Requires observation over time — a single task cannot reveal whether a student is taking initiative or following instructions. Teacher must observe patterns across multiple sessions.)
- Collaboration quality (Requires observation of group dynamics. AI cannot distinguish between a student who is silently contributing ideas in a group discussion and one who is disengaged.)
- Regenerative mindset (Requires interpretation of student reasoning and values orientation. A student's regeneration proposal might use the right language but miss the deeper shift from "fixing" to "supporting recovery" — detecting this requires professional judgment.)
- Quality of systems analysis at the integrative and systemic levels (Whether a student's multi-lens analysis genuinely identifies tensions and interdependencies vs merely listing different perspectives requires interpretive judgment.)

**Mixed elements (partial automation possible):**
- Evidence-based conclusions from water quality data (AI can check whether the student has cited data and whether the claim is consistent with the evidence, but cannot fully assess the quality of scientific reasoning in open-ended responses.)
- Communication to non-specialist audiences (AI can check for jargon, reading level, and structural elements, but cannot fully assess whether the communication would actually persuade a council member.)
- Multi-lens analysis at the single-lens and multi-lens levels (AI can check whether multiple lenses are named and applied, but the quality of integration requires judgment.)

### 6. AI Tutoring Design Implications

**For hierarchical elements — adaptive sequencing and mastery checking:**
An AI tutoring system should implement prerequisite checking before advancing students through the water quality and sensor technology chains. If a student cannot demonstrate understanding of pH (what it measures, what the scale means, what healthy ranges look like), the system should not advance them to field data interpretation tasks that require pH understanding. Targeted practice with immediate feedback is appropriate: "This water sample has a pH of 4.2. Is this within the healthy range for a freshwater wetland? Explain why or why not." The system should track mastery at each node in the prerequisite chain and flag students who are advancing without foundational understanding.

**For horizontal elements — perspective-prompting and analytical scaffolding:**
An AI tutor should prompt students to apply lenses they haven't yet considered: "You've analysed the wetland's ecological value. Now consider: what economic value does the wetland provide to the local community?" The system should scaffold analytical sophistication by modelling integrative thinking: "You've described the ecological and economic values separately. Can you identify a connection or tension between them?" The system should NOT impose a single correct interpretation — horizontal knowledge admits multiple valid analyses. Assessment should flag analytical depth (single-lens vs integrative) for teacher review rather than marking right/wrong.

**For dispositional elements — reflection prompts and teacher dashboards, NOT automated grading:**
An AI system must NOT attempt to grade agency, collaboration, or regenerative mindset. These require sustained observation of enacted behaviour that an AI tutoring system cannot access. Instead, the system should:
- Prompt regular self-reflection: "Describe a moment this week when you made a decision about the project without being told what to do. What did you decide? What happened?"
- Surface student reflections to a teacher dashboard so the teacher can track developmental trajectory over time
- Provide the dispositional progression bands as a shared vocabulary for teacher-student conferences
- Flag when a student's self-reflections suggest a shift between levels (e.g., language shifting from "the teacher told us to" to "I decided to")

**For the mixed architecture — handling transitions between types:**
The AI system must recognise that this project requires transitions between knowledge types within single sessions. A student might move from interpreting sensor data (hierarchical — right/wrong) to analysing what the data means for the wetland ecosystem (horizontal — multiple valid interpretations) to reflecting on their role as a regenerative practitioner (dispositional — developmental, no right answer). The tutoring system should shift its mode accordingly: directive and corrective for hierarchical elements, prompting and exploratory for horizontal elements, and reflective and non-evaluative for dispositional elements. A single pedagogical mode applied across all three types will be inappropriate for at least two of them.

---

## Known Limitations

1. **The three-type framework is a simplification.** Bernstein's original distinction was between hierarchical and horizontal knowledge structures within vertical discourse. The dispositional category is not Bernstein's — it draws on competency framework literature and represents a pragmatic extension for curriculum design purposes. Scholars working within Bernstein's framework may disagree with treating dispositional knowledge as a separate structural type rather than as a feature of horizontal discourse. The framework is offered as a design tool, not as a contribution to sociological theory.

2. **Proportions are approximate and contestable.** Estimating that a curriculum is "40% hierarchical, 30% horizontal, 30% dispositional" implies a precision that the framework cannot deliver. The proportions are interpretive judgments — a different analyst might assess the same curriculum as 35/35/30 or 45/25/30. They are useful for surfacing the relative weight of different knowledge types and ensuring none is overlooked, not as exact measurements.

3. **The diagnostic is based on stated learning goals, not enacted curriculum.** A curriculum that states dispositional goals (agency, collaboration) may not actually develop them if the teaching and assessment prioritise only the hierarchical elements. The architecture analysis reveals what the curriculum CLAIMS to do; whether it actually does so depends on implementation. Teachers should use the analysis to check whether their assessment design and daily teaching practice genuinely address all the knowledge types their curriculum claims to include.

4. **Knowledge-contingent dispositions require prerequisite diagnosis, not just type labelling.** Some dispositional goals — particularly critical thinking, ecological literacy, regenerative mindset, and entrepreneurial thinking — cannot develop authentically without a sufficient hierarchical and horizontal knowledge base. The architecture diagnosis identifies that a dispositional goal is present; it does not automatically identify whether the prerequisites for that disposition to be operable are also present in the curriculum. When the diagnosis identifies a knowledge-contingent disposition, the teaching and assessment implications must include explicit identification of the hierarchical and horizontal elements that must be developed first. A curriculum that states "students will develop critical thinking" without ensuring sufficient domain knowledge to think critically with is not a curriculum that will achieve that goal.

5. **Dispositional progression bands describe typical development, not universal stages.** A student may demonstrate "Extending" agency in one context and "Emerging" in another. Dispositional development is context-sensitive and non-linear. The bands are guides for observation and feedback, not rigid classifications.

6. **The AI tutoring implications assume a system capable of mode-switching.** Most current AI tutoring systems are designed for hierarchical knowledge (adaptive practice with right/wrong feedback). The recommendations for horizontal and dispositional elements describe capabilities that most systems do not yet have. The implications are forward-looking — describing what an architecture-informed system SHOULD do, not what off-the-shelf systems currently can do.

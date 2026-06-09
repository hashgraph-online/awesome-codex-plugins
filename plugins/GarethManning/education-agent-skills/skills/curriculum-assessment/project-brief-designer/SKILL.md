---
# AGENT SKILLS STANDARD FIELDS (v2)
name: project-brief-designer
description: "Design a project-based learning brief with a driving question, milestones, and assessment criteria. Use when planning PBL units, inquiry projects, or extended investigations."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "curriculum-assessment/project-brief-designer"
skill_name: "Project Brief Designer (PBL)"
domain: "curriculum-assessment"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Barron & Darling-Hammond (2008) — Teaching for meaningful learning: a review of research on inquiry-based and cooperative learning"
  - "Krajcik & Shin (2014) — Project-based learning: design features and key practices"
  - "Larmer, Mergendoller & Boss (2015) — Setting the Standard for Project Based Learning"
  - "Thomas (2000) — A review of research on project-based learning"
  - "Hmelo-Silver, Duncan & Chinn (2007) — Scaffolding and achievement in problem-based and inquiry learning"
input_schema:
  required:
    - field: "project_topic"
      type: "string"
      description: "The subject content the project addresses — what students will learn about"
    - field: "learning_objectives"
      type: "string"
      description: "The specific knowledge and skills students should develop through the project"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "project_duration"
      type: "string"
      description: "How long the project runs — e.g. 2 weeks, 6 lessons, half a term"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject or subjects (for cross-curricular projects)"
    - field: "real_world_connection"
      type: "string"
      description: "A specific real-world context, audience, or problem the teacher wants the project connected to"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: class data including prior attainment, interests, specific needs"
    - field: "available_resources"
      type: "string"
      description: "Technology, materials, community connections, specialist support available"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: relevant curriculum standards the project must address"
output_schema:
  type: "object"
  fields:
    - field: "driving_question"
      type: "string"
      description: "An open-ended, authentic question that drives inquiry throughout the project"
    - field: "project_brief"
      type: "object"
      description: "The complete brief students receive — scenario, requirements, milestones, final product"
    - field: "milestone_sequence"
      type: "array"
      description: "Structured checkpoints with explicit instruction points, ensuring learning happens through the project"
    - field: "assessment_criteria"
      type: "object"
      description: "What will be assessed and how — including both process and product assessment"
    - field: "explicit_instruction_map"
      type: "array"
      description: "Where in the project explicit teaching is needed — PBL works WITH direct instruction, not instead of it"
chains_well_with:
  - "backwards-design-unit-planner"
  - "competency-unpacker"
  - "criterion-referenced-rubric-generator"
  - "differentiation-adapter"
  - "scaffolded-task-modifier"
  - "curriculum-knowledge-architecture-designer"
  - "critical-thinking-task-designer"
teacher_time: "5 minutes"
tags: ["PBL", "project-based-learning", "inquiry", "driving-question", "authentic-assessment", "milestones"]
---

# Project Brief Designer (PBL)

## What This Skill Does

Designs a complete project brief for project-based learning — including a driving question, real-world connection, structured milestones, explicit instruction points, and assessment criteria — that ensures students learn substantive content THROUGH the project rather than simply producing a product. The critical design principle is that effective PBL combines authentic, open-ended inquiry with structured teaching: the project provides the motivation and context; explicit instruction provides the knowledge and skills students need to succeed. The output is a ready-to-use project brief that a teacher can hand to students, plus a teacher-facing implementation guide that maps where direct instruction, formative assessment, and scaffolding are needed. AI is specifically valuable here because designing effective PBL requires simultaneously balancing authenticity (making the project feel real), rigour (ensuring substantive learning happens), structure (building in milestones that prevent drift), and differentiation (making the project accessible to all learners) — a multi-dimensional design challenge that takes significant expertise and time.

## Evidence Foundation

Barron & Darling-Hammond (2008) reviewed evidence on inquiry-based learning and identified the design features that distinguish effective projects from activities that are engaging but educationally shallow: effective PBL connects to meaningful real-world problems, requires disciplinary thinking (not just information gathering), includes structured milestones, and incorporates explicit instruction at the points where students need new knowledge or skills. They found that PBL is most effective when it supplements, not replaces, direct instruction — the project provides a context that makes instruction meaningful, and instruction provides the tools that make the project possible. Krajcik & Shin (2014) identified five key features of effective PBL: a driving question (authentic, open-ended, anchored in real-world issues), situated inquiry (investigation embedded in meaningful context), collaboration, learning technologies, and tangible artefacts. They emphasised that the driving question is the design centrepiece — it must be genuinely open (not a question with a predetermined answer), connected to students' lives, and rich enough to sustain extended investigation. Larmer, Mergendoller & Boss (2015) from the Buck Institute for Education established the "Gold Standard PBL" framework with seven essential design elements: a challenging problem or question, sustained inquiry, authenticity, student voice and choice, reflection, critique and revision, and a public product. Thomas (2000) reviewed PBL research and found positive effects on content knowledge and problem-solving but cautioned that poorly designed projects can be time-consuming without producing proportionate learning — structure and explicit instruction are the differentiating factors. Hmelo-Silver, Duncan & Chinn (2007) demonstrated that scaffolded inquiry outperforms unscaffolded inquiry — students need structured support, not just open-ended tasks.

## Input Schema

The teacher must provide:
- **Project topic:** What the project is about. *e.g. "Water quality in our local river" / "Designing a sustainable city" / "The impact of the Industrial Revolution on working people" / "Creating a campaign to reduce food waste in our school"*
- **Learning objectives:** What students should learn. *e.g. "Understand the causes and effects of water pollution, apply scientific testing methods, communicate findings to an audience" / "Analyse primary and secondary sources about working conditions, construct historical arguments using evidence"*
- **Student level:** Year group. *e.g. "Year 8" / "Year 10"*
- **Project duration:** How long. *e.g. "6 lessons over 3 weeks" / "Half a term (12 lessons)"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject(s)
- **Real-world connection:** Specific context the teacher wants
- **Student profiles:** Class data, interests, needs
- **Available resources:** Technology, materials, community links
- **Curriculum framework:** Standards to address

## Prompt

```
You are an expert in project-based learning design, with deep knowledge of Barron & Darling-Hammond's (2008) research on inquiry-based learning, Krajcik & Shin's (2014) five key features of effective PBL, and Larmer, Mergendoller & Boss's (2015) Gold Standard PBL framework. You understand that effective PBL is NOT simply "do a project" — it is a carefully designed learning experience where authentic inquiry and explicit instruction work together so that students learn substantive content THROUGH the project.

CRITICAL DESIGN PRINCIPLE: PBL effects are strongest when projects include explicit instruction, not instead of it (Barron & Darling-Hammond, 2008; Hmelo-Silver et al., 2007). Every project brief you design must include specific points where the teacher provides direct instruction, modelling, or scaffolding. A project without structured teaching is an activity, not PBL.

Your task is to design a project brief for:

**Project topic:** {{project_topic}}
**Learning objectives:** {{learning_objectives}}
**Student level:** {{student_level}}
**Project duration:** {{project_duration}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the topic and objectives.
**Real-world connection:** {{real_world_connection}} — if not provided, design an authentic connection that makes the project meaningful to students at this level.
**Student profiles:** {{student_profiles}} — if not provided, design for a mixed-ability class.
**Available resources:** {{available_resources}} — if not provided, assume standard classroom resources with internet access but no specialist equipment.
**Curriculum framework:** {{curriculum_framework}} — if not provided, align to the stated learning objectives.

Apply these evidence-based PBL design principles:

1. **Design a driving question (Krajcik & Shin, 2014):**
   - The driving question must be OPEN-ENDED — it should not have a single correct answer.
   - It must be AUTHENTIC — connected to real-world issues, audiences, or problems that matter beyond the classroom.
   - It must be FEASIBLE — students at this level can meaningfully investigate it within the time available.
   - It must REQUIRE the intended learning — students cannot answer the question without developing the knowledge and skills in the learning objectives.
   - Avoid pseudo-questions that have predetermined answers. "How can we reduce water pollution in our local river?" is open. "What are the three types of water pollution?" is not.

2. **Structure milestones with explicit instruction (Barron & Darling-Hammond, 2008; Hmelo-Silver et al., 2007):**
   - Break the project into 3–5 milestones, each with a clear deliverable.
   - At each milestone, identify: what students produce, what they need to know/be able to do, and WHERE EXPLICIT INSTRUCTION HAPPENS.
   - Instruction should be "just in time" — taught when students need it for the next phase of the project, not front-loaded as a lecture block followed by a project block.
   - Each milestone should include a formative check — how does the teacher know students are learning, not just producing?

3. **Ensure authentic audience and purpose (Larmer et al., 2015):**
   - The final product should be FOR someone — a real audience, a genuine purpose.
   - "Present your findings to the class" is weak. "Present your water quality report to the local council environmental officer" is strong.
   - If a real audience isn't available, create a realistic scenario that simulates one.

4. **Build in student voice and choice (Larmer et al., 2015):**
   - Students should have meaningful choices within the project — which aspect to investigate, how to present findings, which evidence to prioritise.
   - Choice should be structured, not unlimited — too much choice overwhelms; too little removes ownership.
   - The learning objectives are non-negotiable; the route to them includes choice.

5. **Design assessment for both process and product (Barron & Darling-Hammond, 2008):**
   - Assess the LEARNING, not just the PRODUCT. A beautiful poster with no substantive content should not score well.
   - Include process assessment: research logs, draft work, peer feedback, reflection.
   - Assessment criteria should be transparent from the start — students should know how they'll be assessed before they begin.
   - Product quality matters, but content understanding matters more.

6. **Include reflection and revision (Larmer et al., 2015):**
   - Build in structured reflection points: "What have you learned so far? What questions do you still have?"
   - Build in revision opportunities: students improve their work based on feedback before final submission.
   - Critique and revision is where much of the learning happens — not in the first draft.

Return your output in this exact format:

## Project Brief: [Project Title]

**Driving Question:** [The open-ended question that drives the project]
**For:** [Student level]
**Duration:** [Project duration]
**Subject:** [Subject area(s)]

### The Scenario

[A compelling, authentic description of the project context — who needs this, why it matters, what students will produce. Written in language appropriate for the student level. This is what students actually read.]

### What You Will Produce

[Clear description of the final product(s) and who the audience is]

### Milestones

For each milestone:
**Milestone [N]: [Name] — [Timing]**
- **What you produce:** [Deliverable]
- **What you'll need to learn:** [Knowledge/skills required]
- **Teacher instruction point:** [What the teacher explicitly teaches at this stage and why]
- **Formative check:** [How the teacher assesses learning at this stage]
- **Student choice:** [Where students have meaningful choice within this milestone]

### Assessment Criteria

**Your project will be assessed on:**
[Clear, transparent criteria — what counts, what doesn't, how much each element is worth]

**Process assessment (how you work):**
[What process elements are assessed — research quality, collaboration, reflection, revision]

**Product assessment (what you produce):**
[What product elements are assessed — content accuracy, argument quality, communication effectiveness]

### Explicit Instruction Map (Teacher Guide)

[For each milestone: what the teacher needs to teach, when, and how. This ensures the project includes genuine instruction, not just facilitation.]

### Differentiation Notes

[How the project can be adapted for different learners — extension challenges, support scaffolds, EAL modifications — while maintaining the same learning objectives]

### Known Design Choices

[Transparent notes about trade-offs in the design — what was prioritised, what was sacrificed, what the teacher should watch for]

**Self-check before returning output:** Verify that (a) the driving question is genuinely open-ended and requires the intended learning, (b) every milestone includes an explicit instruction point, (c) assessment criteria are transparent and prioritise content learning over product aesthetics, (d) student voice and choice are structured within each milestone, (e) the project includes reflection and revision opportunities, and (f) the project could not be completed without substantive learning — it's not possible to produce a good product by copying information without understanding it.
```

## Example Output

**Scenario:** *Project topic: "Water quality in our local river" / Learning objectives: "Understand the causes and indicators of water pollution, apply scientific testing methods (pH, dissolved oxygen, nitrate levels), evaluate evidence to draw conclusions, communicate scientific findings to a non-specialist audience" / Student level: "Year 8" / Project duration: "8 lessons over 4 weeks" / Subject area: "Science" / Real-world connection: "The local river has had reports of increased algae growth — a real local issue"*

---

## Project Brief: River Health Investigation

**Driving Question:** How healthy is our local river, and what should be done about it?
**For:** Year 8 Science
**Duration:** 8 lessons over 4 weeks
**Subject:** Science (with elements of Geography and Communication)

### The Scenario

In recent months, residents near the River Arden have noticed increasing amounts of green algae growing on the surface of the water, particularly near the Millbrook industrial estate. Some dog walkers have reported their dogs becoming ill after drinking from the river. The local parish council wants to understand what's happening — but they don't have scientific expertise.

They need a team of scientists to:
1. Test the water quality at different points along the river
2. Identify what's causing the problem
3. Explain their findings in plain language
4. Recommend what should be done

Your team has been commissioned to investigate. Your findings will be presented in a scientific report written for the parish council — people who care about the river but don't have a science background. Your report needs to be scientifically accurate AND understandable to non-scientists.

### What You Will Produce

**Final product:** A scientific report (800–1200 words) for the parish council that includes:
- Your water quality findings with data
- A clear explanation of what the data means
- An evidence-based conclusion about the river's health
- Specific recommendations for action

**Audience:** The parish council (non-specialist adults who need to make decisions based on your findings)

**Presentation:** Each team will deliver a 5-minute summary of their report to the class, with the teacher role-playing as a parish council member who asks questions.

### Milestones

**Milestone 1: Understanding Water Quality — Lessons 1–2**
- **What you produce:** A research summary (one page) identifying the key indicators of water quality and what affects them. Include at least 4 indicators and explain what "healthy" and "unhealthy" levels look like for each.
- **What you'll need to learn:** What water quality means scientifically, the key indicators (pH, dissolved oxygen, nitrate/phosphate levels, biological indicators), what causes pollution in rivers, and what eutrophication is.
- **Teacher instruction point:** Lesson 1 — direct instruction on water quality indicators. The teacher explains pH, dissolved oxygen, nitrates, and phosphates, using diagrams to show how excess nutrients cause algal blooms (eutrophication). This is essential knowledge that students cannot discover independently within the time available. Lesson 2 — teacher models how to read and interpret water quality data tables, demonstrating what "normal" ranges look like and how to spot concerning readings.
- **Formative check:** Exit ticket at end of Lesson 2: "A river sample shows pH 6.2, dissolved oxygen 4mg/L, and nitrate levels of 25mg/L. Is this river healthy? Explain your reasoning using at least two indicators." This checks whether students can interpret data, not just recall what indicators exist.
- **Student choice:** Teams choose which two indicators they will focus their investigation on (all must cover pH and dissolved oxygen; teams choose their additional focus areas based on interest).

**Milestone 2: Collecting and Recording Data — Lessons 3–4**
- **What you produce:** A completed data table with water quality measurements from at least 3 sampling points, recorded accurately with units and repeated measurements.
- **What you'll need to learn:** How to use testing equipment (pH meter, dissolved oxygen probe, nitrate test strips), how to design a fair test (controlling variables when sampling), how to record data accurately in tables.
- **Teacher instruction point:** Lesson 3 — teacher demonstrates each piece of testing equipment, modelling the correct procedure and common errors. Students practise with prepared samples before going to the river. This is a practical skill that requires explicit modelling — students cannot figure out how to use a dissolved oxygen probe by experimentation. Lesson 4 — brief instruction on fair testing: why we sample at the same depth, take repeated readings, and record conditions. This connects to the broader science skill of controlling variables.
- **Formative check:** Teacher circulates during data collection, checking: Are readings recorded with correct units? Are students taking repeat measurements? Can students explain WHY they're testing at multiple points along the river? (If students can't explain why, they're following a procedure without understanding the scientific reasoning.)
- **Student choice:** Teams choose their sampling points along the river (within the approved area) based on their hypothesis about where pollution might be worst. They must justify their choice scientifically.

**Milestone 3: Analysing Evidence and Drawing Conclusions — Lessons 5–6**
- **What you produce:** A data analysis document that includes: data presented in appropriate graphs/charts, a written interpretation of what the data shows, and a conclusion about the river's health supported by evidence.
- **What you'll need to learn:** How to select appropriate graph types for different data, how to identify patterns and anomalies in data, how to write evidence-based conclusions (claim → evidence → reasoning).
- **Teacher instruction point:** Lesson 5 — teacher models how to analyse water quality data using a sample dataset (NOT the students' own data). Demonstrates: choosing bar charts for comparing sites vs. line graphs for showing change along the river, identifying what the pattern means ("dissolved oxygen decreases as we move downstream from the industrial estate — this suggests..."), and distinguishing between correlation and cause. Lesson 6 — teacher provides a Claim-Evidence-Reasoning (CER) framework and models writing one conclusion paragraph, thinking aloud about how to connect data to a claim.
- **Formative check:** Each team submits a draft conclusion paragraph (just one) before the end of Lesson 6. The teacher reviews these overnight and provides targeted written feedback on whether the conclusion is supported by the evidence cited. This is the critical learning moment — can students use data to support a scientific argument?
- **Student choice:** Teams choose how to present their data visually (graph type, layout, which comparisons to highlight). They also choose which findings to emphasise in their conclusion based on what they judge to be most significant.

**Milestone 4: Communicating to a Non-Specialist Audience — Lessons 7–8**
- **What you produce:** The final report (800–1200 words) and a 5-minute presentation summary.
- **What you'll need to learn:** How to communicate scientific findings to non-specialists — translating technical language into accessible explanations without losing accuracy, structuring a report for a decision-making audience.
- **Teacher instruction point:** Lesson 7 — teacher shows two example paragraphs side by side: one written for scientists ("The elevated NO₃⁻ concentration of 28mg/L suggests anthropogenic eutrophication") and one written for the parish council ("The nitrate levels in the river are higher than they should be. Nitrates act like fertiliser for algae — when levels rise above 10mg/L, algae can grow out of control"). Students identify the differences and practise "translating" one paragraph of their own analysis. This is a specific communication skill that requires modelling.
- **Formative check:** Peer review in Lesson 7: each team reads another team's draft report and answers three questions: (1) Can you understand the findings without a science background? (2) Is there a clear recommendation? (3) What's one thing that needs more explanation? Teams then revise based on peer feedback before final submission in Lesson 8.
- **Student choice:** Teams choose the format and structure of their final report (within the word count) and choose how to deliver their presentation (all members speak, one presents while others handle questions, etc.).

### Assessment Criteria

**Your project will be assessed on:**

**Process assessment (30% of total mark):**
- Research quality (Milestone 1): Did you accurately identify and explain water quality indicators? (10%)
- Data collection (Milestone 2): Was your data recorded accurately, with repeat measurements and correct units? (10%)
- Reflection and revision: Did you improve your report based on peer feedback? What specific changes did you make and why? (10%)

**Product assessment (70% of total mark):**
- Scientific accuracy (25%): Are your findings correct? Are your conclusions supported by the data? Do you correctly explain the science of water pollution?
- Evidence-based argument (20%): Do you use your data as evidence? Is your reasoning clear? Does your conclusion follow from the evidence?
- Communication to audience (15%): Can a non-specialist understand your report? Have you translated scientific language without losing accuracy?
- Recommendations (10%): Are your recommendations specific, realistic, and based on your findings?

**Note:** Visual design of the report is NOT assessed. A plain-text report with excellent science scores higher than a beautifully designed report with weak science. Focus your time on understanding and argument, not decoration.

### Explicit Instruction Map (Teacher Guide)

| Lesson | Explicit Instruction | Purpose | Timing |
|--------|---------------------|---------|--------|
| 1 | Water quality indicators, eutrophication process | Foundational knowledge students need before investigating | 25 minutes direct instruction + 20 minutes guided research |
| 2 | Reading and interpreting water quality data tables | Procedural skill: how to make sense of numerical data | 15 minutes modelling + 30 minutes practice with sample data |
| 3 | Equipment demonstration and fair testing | Practical skill requiring modelling — cannot be self-taught safely | 20 minutes demonstration + 25 minutes supervised practice |
| 4 | Brief review of variables and sampling design | Connecting practical work to scientific method | 10 minutes instruction + field work |
| 5 | Data analysis: graph selection, pattern identification | Analytical skill: moving from data to meaning | 20 minutes modelling with sample dataset + 25 minutes guided analysis |
| 6 | CER framework for scientific conclusions | Writing skill: structuring evidence-based argument | 15 minutes modelling + 30 minutes drafting with feedback |
| 7 | Communicating science to non-specialists | Communication skill: audience awareness | 15 minutes modelling + 30 minutes revision |
| 8 | — (student presentations and final submission) | Assessment and celebration | — |

**Total explicit instruction time:** Approximately 120 minutes across 8 lessons. The remaining time is structured inquiry, collaborative work, and formative assessment. This is NOT "teacher talks for 2 lessons then students do a project for 6 lessons" — instruction is distributed throughout, delivered when students need it.

### Differentiation Notes

**Extension:** Students who complete milestones early can investigate additional indicators (biological indicators such as invertebrate diversity), compare their findings to published data for similar rivers, or write a second audience-specific version of their report (e.g., a version for Year 5 students studying rivers in Geography).

**Support:** Pre-teach water quality vocabulary in a brief session before Lesson 1. Provide a data recording template with units and column headers already filled in. Offer a report structure template with section headings and sentence starters for each paragraph. These scaffolds structure the output without reducing the analytical demand — the student still must interpret the data and draw conclusions.

**EAL:** Provide a glossary of key scientific terms with everyday-language definitions. Use visual diagrams of the eutrophication process alongside written explanations. Allow students to discuss findings in their first language before writing in English. Provide sentence frames for the CER paragraph: "Our data shows that ___. This suggests ___ because ___."

**ADHD:** Break each lesson's tasks into shorter segments with clear "done" checkpoints. Provide a visual timeline of the project milestones. During field work, assign a specific role (equipment manager, data recorder) to provide focus and structure.

### Known Design Choices

1. **The river scenario is based on a real local issue.** If the river/issue doesn't match your local context, adapt the scenario — the design principles work with any authentic environmental issue. The key requirement is that the problem is REAL (or realistically simulated), not contrived.

2. **The report is prioritised over the presentation.** The report carries 70% of the assessment; the presentation is a communication exercise, not a performance assessment. This avoids the validity threat of assessing public speaking confidence instead of scientific understanding (see Assessment Validity Checker).

3. **Visual design is explicitly excluded from assessment.** This is a deliberate choice to prevent students from investing time in decoration rather than science. It also removes a socioeconomic barrier (access to colour printing, design software) and an equity barrier (students with dyslexia or fine motor difficulties are not penalised).

4. **The project requires explicit instruction at every milestone.** This is the most important design feature. PBL research consistently shows that projects without structured teaching produce engagement without proportionate learning (Thomas, 2000). If you remove the instruction points, the project becomes an activity — students will produce reports by copying information from websites rather than by understanding the science.

5. **Four weeks is the minimum viable duration for this project.** Shorter timelines would require cutting data collection (which removes the authentic inquiry) or cutting the revision cycle (which removes a key learning opportunity). If time is limited, reduce the number of sampling points rather than cutting milestones.

---

## Known Limitations

1. **The quality of PBL depends heavily on the driving question.** The generated driving question is designed to be open-ended, authentic, and requiring the intended learning — but the teacher should evaluate whether it genuinely engages their specific students. A question that works in one context may fall flat in another. The teacher may need to adapt the driving question to connect with their students' interests and local context.

2. **Real-world connections require local knowledge.** The project brief generates a scenario based on the stated topic and real-world connection, but the teacher knows their community, local resources, and potential external partners better than any AI. The generated scenario should be treated as a strong starting point that benefits from local adaptation — replacing generic details with specific local names, places, and issues.

3. **PBL is not appropriate for all learning objectives.** Some content is better taught through direct instruction, practice, and retrieval — particularly foundational knowledge that students need before they can investigate (Hmelo-Silver et al., 2007). PBL works best for objectives that involve application, analysis, evaluation, and communication — not for objectives that are primarily about acquiring factual knowledge. The teacher should consider whether PBL is the right approach for the stated objectives before using this skill.

4. **The explicit instruction map is a guide, not a script.** The suggested instruction points indicate WHERE teaching is needed but cannot specify the exact teaching approach that will work for every class. The teacher must use their professional judgement about how much instruction to provide, how to respond to misconceptions that arise during the project, and when to pause the project for additional teaching that wasn't anticipated in the original design.

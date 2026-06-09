---
# AGENT SKILLS STANDARD FIELDS (v2)
name: interdisciplinary-real-world-connection-mapper
description: "Map curriculum connections across multiple subjects for a real-world problem or authentic context. Use when planning cross-curricular projects or connecting content to real issues."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "environmental-experiential-learning/interdisciplinary-real-world-connection-mapper"
skill_name: "Interdisciplinary Real-World Connection Mapper"
domain: "environmental-experiential-learning"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Barron & Darling-Hammond (2008) — Teaching for Meaningful Learning: a review of research on inquiry-based and cooperative learning"
  - "Drake & Burns (2004) — Meeting Standards Through Integrated Curriculum"
  - "Beane (1997) — Curriculum Integration: designing the core of democratic education"
  - "Rennie, Venville & Wallace (2012) — Integrating Science, Technology, Engineering, and Mathematics"
  - "Czerniak, Weber, Sandmann & Ahern (1999) — Literature review of science and mathematics integration"
input_schema:
  required:
    - field: "real_world_problem"
      type: "string"
      description: "The real-world problem, issue, or situation that requires multiple disciplines to address"
    - field: "primary_subject"
      type: "string"
      description: "The teacher's own subject — the discipline from which this connection is being initiated"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "available_subjects"
      type: "string"
      description: "Which other subject departments are willing or available to collaborate"
    - field: "curriculum_constraints"
      type: "string"
      description: "What curriculum content must be covered in each subject"
    - field: "time_frame"
      type: "string"
      description: "Duration of the integrated unit"
    - field: "school_timetable"
      type: "string"
      description: "Whether the timetable allows for cross-curricular collaboration or subjects are fully siloed"
output_schema:
  type: "object"
  fields:
    - field: "connection_map"
      type: "object"
      description: "A visual and descriptive map of how the real-world problem connects to multiple disciplines"
    - field: "disciplinary_contributions"
      type: "array"
      description: "What each subject contributes — specific knowledge and skills, with curriculum alignment"
    - field: "integration_points"
      type: "array"
      description: "Where and how subjects genuinely connect — not parallel teaching but actual integration"
    - field: "implementation_plan"
      type: "object"
      description: "How to implement — from single-teacher connections to full cross-curricular collaboration"
    - field: "assessment_approach"
      type: "object"
      description: "How to assess integrated understanding — not subject-by-subject but the ability to draw on multiple disciplines"
chains_well_with:
  - "phenomenon-based-unit-anchor"
  - "project-brief-designer"
  - "service-learning-project-designer"
  - "ecological-inquiry-anchor-designer"
teacher_time: "4 minutes"
tags: ["interdisciplinary", "cross-curricular", "Barron", "Drake", "integrated-curriculum", "real-world", "PBL"]
---

# Interdisciplinary Real-World Connection Mapper

## What This Skill Does

Maps the connections between a real-world problem or situation and the disciplinary knowledge required to address it, generating a practical curriculum integration plan that shows what each subject contributes, where subjects genuinely connect, and how to implement the integration within real school timetable constraints. The approach draws on Barron & Darling-Hammond's (2008) research on inquiry-based and meaningful learning, and Drake & Burns' (2004) framework for integrated curriculum design. The critical insight is that real-world problems are inherently interdisciplinary — climate change is not "science," homelessness is not "PSHE," a building project is not "mathematics" — and students who learn to draw on multiple disciplines to address complex problems develop deeper understanding than students who learn each discipline in isolation. However, integration must be GENUINE (each subject contributes something necessary) not FORCED (artificial connections that dilute both subjects). The output includes a connection map, disciplinary contributions with curriculum alignment, specific integration points, a practical implementation plan, and an assessment approach. AI is specifically valuable here because mapping a real-world problem to multiple curriculum standards simultaneously requires cross-referencing knowledge that spans multiple subject domains — a task that would take individual teachers hours of cross-departmental consultation.

## Evidence Foundation

Barron & Darling-Hammond (2008) reviewed research on inquiry-based and cooperative learning, finding that learning is deepened when students apply knowledge from multiple disciplines to authentic problems. They identified design principles for effective interdisciplinary work: the problem must be genuinely complex (requiring multiple lenses), each discipline's contribution must be substantive (not tokenistic), and the integration must be visible to students (they should understand WHY multiple subjects are needed). Drake & Burns (2004) proposed three levels of curriculum integration: multidisciplinary (subjects address the same theme but remain separate), interdisciplinary (common skills or concepts are emphasised across subjects), and transdisciplinary (the real-world context organises the learning, and subjects serve the context). They argued that integration is most effective at the transdisciplinary level but most practical at the interdisciplinary level — and that any level is better than complete isolation. Beane (1997) argued for curriculum integration as a democratic principle: real-world problems don't come in subject-shaped packages, and citizens need to draw on multiple knowledge domains to participate effectively in democratic life. Rennie, Venville & Wallace (2012) specifically studied STEM integration, finding that integration improved student engagement and perception of relevance but needed careful design to avoid "diluting" individual disciplines. Czerniak et al. (1999) reviewed science-mathematics integration, finding positive effects on student attitudes and moderate effects on achievement, but warned that poorly designed integration could weaken understanding in both subjects.

## Input Schema

The teacher must provide:
- **Real-world problem:** The authentic situation. *e.g. "Our school wants to reduce its energy consumption by 20% — how?" / "A local developer wants to build houses on the green space behind the school — should the council approve it?" / "Water quality in the local river is declining — what's causing it and what can be done?" / "Our community has a food waste problem — where does the waste come from and how can it be reduced?"*
- **Primary subject:** The teacher's discipline. *e.g. "I'm a Science teacher" / "I'm a Geography teacher" / "I'm a Maths teacher" / "I'm a DT teacher"*

Optional (injected by context engine if available):
- **Student level:** Year group
- **Available subjects:** Which departments can collaborate
- **Curriculum constraints:** Required content in each subject
- **Time frame:** Duration
- **School timetable:** Collaboration possibilities

## Prompt

```
You are an expert in interdisciplinary curriculum design, with deep knowledge of Barron & Darling-Hammond's (2008) research on meaningful learning, Drake & Burns' (2004) framework for integrated curriculum (multidisciplinary, interdisciplinary, transdisciplinary), Beane's (1997) democratic argument for curriculum integration, Rennie, Venville & Wallace's (2012) STEM integration research, and Czerniak et al.'s (1999) science-mathematics integration review. You understand that interdisciplinary teaching is NOT "themed weeks" where subjects coincidentally address the same topic — it is the deliberate design of learning where multiple disciplines genuinely contribute to understanding a complex real-world problem.

CRITICAL PRINCIPLES:
- **The problem must genuinely require multiple disciplines.** If the problem can be fully addressed by one subject, integration is unnecessary and artificial. A genuine interdisciplinary problem is one where removing any contributing subject leaves the understanding incomplete.
- **Each subject's contribution must be SUBSTANTIVE, not tokenistic.** "Let's do fractions about the environment" is tokenistic — Maths is being used as a surface-level illustration, not contributing substantive mathematical thinking. "Analyse the energy consumption data using percentage change to determine which areas of the school waste the most energy" is substantive — Maths provides analytical tools that are genuinely needed.
- **Integration points must be SPECIFIC and IDENTIFIED.** Vague integration ("these subjects relate to the same topic") produces parallel teaching, not integrated learning. Specific integration ("the Science investigation produces data that the Maths analysis uses to draw conclusions that the Geography contextualises") produces genuine cross-disciplinary understanding.
- **Start from where the school IS, not where it should be.** Full transdisciplinary integration requires timetable flexibility, team planning time, and cross-departmental collaboration. Many schools have none of these. The implementation plan must offer a spectrum: from single-teacher connections (a Science teacher referencing Maths concepts) to full cross-curricular projects (multiple departments coordinating a shared unit).
- **Integration should STRENGTHEN individual subjects, not dilute them.** The most common criticism of interdisciplinary teaching is that it produces shallow understanding of multiple subjects rather than deep understanding of one. Good integration does the opposite: students learn MORE deeply about supply-demand dynamics when they encounter them through a real economic problem, not less deeply.

Your task is to map the interdisciplinary connections for:

**Real-world problem:** {{real_world_problem}}
**Primary subject:** {{primary_subject}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for lower secondary (Years 7–9).
**Available subjects:** {{available_subjects}} — if not provided, identify the 3–4 most relevant subjects.
**Curriculum constraints:** {{curriculum_constraints}} — if not provided, identify natural curriculum alignment.
**Time frame:** {{time_frame}} — if not provided, design for a 2-week unit.
**School timetable:** {{school_timetable}} — if not provided, provide implementation options for both collaborative and siloed timetables.

Return your output in this exact format:

## Interdisciplinary Connection Map: [Problem]

**Real-world problem:** [The authentic situation]
**Primary subject:** [The teacher's discipline]
**Connected subjects:** [Other subjects that contribute]
**Integration level:** [Multidisciplinary / Interdisciplinary / Transdisciplinary — and why]

### Connection Map

[Visual or descriptive map showing how the problem connects to each subject — what each contributes]

### Disciplinary Contributions

For each subject (3–5):
**[Subject]: [What it contributes]**
- **Knowledge:** [Specific content students learn through this problem]
- **Skills:** [Disciplinary skills developed]
- **Curriculum alignment:** [How this addresses specific curriculum requirements]
- **Why this subject is necessary:** [What understanding would be missing without it]

### Integration Points

[Specific, identified points where one subject's output becomes another's input — the moments of genuine cross-disciplinary connection]

### Implementation Plan

**Option A — Single teacher (no cross-departmental collaboration needed):**
[How one teacher can make connections to other subjects within their own teaching]

**Option B — Coordinated teaching (subjects teach the same problem simultaneously but in their own lessons):**
[How 2–3 teachers coordinate timing and share the problem context]

**Option C — Full collaboration (subjects co-plan and co-teach):**
[How a full cross-curricular project could work if the school supports it]

### Assessment Approach

[How to assess integrated understanding — a task that requires drawing on multiple disciplines]

**Self-check before returning output:** Verify that (a) the problem genuinely requires multiple disciplines, (b) each subject's contribution is substantive, (c) integration points are specific and identified, (d) the implementation plan is realistic with multiple options, and (e) the integration strengthens rather than dilutes individual subjects.
```

## Example Output

**Scenario:** *Real-world problem: "Our school wants to reduce its energy consumption by 20% over the next year. The headteacher has asked students to investigate where energy is used, identify the biggest opportunities for reduction, and propose a realistic action plan." / Primary subject: "I'm a Science teacher — Year 9" / Available subjects: "Maths, Geography, and DT are all interested. English has said they could contribute if we need persuasive writing." / Time frame: "3 weeks — approximately 15 lessons across the involved subjects"*

---

## Interdisciplinary Connection Map: School Energy Reduction

**Real-world problem:** Reduce school energy consumption by 20% — investigate, analyse, and propose an action plan
**Primary subject:** Science (Year 9)
**Connected subjects:** Mathematics, Geography, Design & Technology, English
**Integration level:** Interdisciplinary — subjects maintain their disciplinary rigour but coordinate around a shared problem. Approaches transdisciplinary in the final proposal, which requires students to synthesise across all subjects.

### Connection Map

```
                    SCHOOL ENERGY PROBLEM
                           |
        ┌──────────┬───────┴───────┬──────────┐
        │          │               │          │
    SCIENCE     MATHS         GEOGRAPHY      DT
   (how energy  (data analysis  (energy in   (designing
    works,      and modelling)  context —    solutions —
    audit the                   global and   insulation,
    building)                   local)       lighting,
        │          │               │        controls)
        └──────────┴───────┬───────┴──────────┘
                           │
                       ENGLISH
                  (communicate the
                   proposal — persuade
                   the headteacher)
```

### Disciplinary Contributions

**Science: How does energy work in our school?**
- **Knowledge:** Forms of energy, energy transfer, thermal insulation, electricity consumption, heating systems. Students learn WHY the school uses energy (heating, lighting, computing, cooking) and the SCIENCE of how energy is wasted (heat loss through walls, windows, roof; standby power consumption; inefficient lighting).
- **Skills:** Scientific investigation (conducting an energy audit), measurement (temperature logging, electricity meter reading), hypothesis testing ("Which room loses heat fastest and why?")
- **Curriculum alignment:** Year 9 Physics — energy transfers, conservation of energy, thermal insulation, power and energy calculations
- **Why this subject is necessary:** Without Science, students cannot understand the physical mechanisms of energy use and loss. They might know the school uses lots of energy but not understand WHERE it goes or WHY — which means their proposals would be guesses, not engineering.

**Mathematics: How much energy and what would savings look like?**
- **Knowledge:** Percentage change (calculating a 20% reduction), data analysis (reading and interpreting energy bills), statistical representation (bar charts, line graphs of energy use over time), proportional reasoning (cost per unit, scaling savings estimates), financial modelling (cost of intervention vs. savings over time)
- **Skills:** Data collection and analysis, percentage calculations, creating and interpreting graphs, financial modelling (simple payback calculations)
- **Curriculum alignment:** Year 9 Maths — percentages, data handling, proportion, interpretation of real-world data sets
- **Why this subject is necessary:** Without Maths, the energy problem is described in vague terms ("we use too much"). With Maths, students can quantify: "Heating accounts for 62% of our energy bill. If we improve roof insulation, we could reduce heating costs by 18%, saving approximately £4,200 per year. The insulation would cost £12,000, so it pays for itself in 2.9 years." Numbers make the proposal credible and the decisions evidence-based.

**Geography: Energy in context — why does this matter?**
- **Knowledge:** Energy sources (where school electricity comes from — the national grid, fossil fuels, renewables), carbon footprint (converting energy use to CO2 emissions), global energy inequality (our school uses X kWh per student; a school in Kenya uses Y), sustainable development (SDG 7: affordable and clean energy)
- **Skills:** Geographical enquiry, comparison across scales (local school → national energy policy → global energy inequality), critical evaluation of data sources
- **Curriculum alignment:** Year 9 Geography — energy resources, sustainability, development, environmental management
- **Why this subject is necessary:** Without Geography, the energy problem is purely technical. Geography provides the CONTEXT: why does energy reduction matter beyond saving money? What are the environmental consequences of our energy use? How does our situation compare to schools in other countries? Geography transforms the project from an engineering exercise into a sustainability inquiry.

**Design & Technology: What solutions can we build?**
- **Knowledge:** Thermal insulation materials and properties, LED lighting design, basic electronics (timers, sensors, controls), sustainable design principles, material selection for environmental performance
- **Skills:** Design process (identify problem → research → design → prototype → test → evaluate), prototyping, technical drawing, material testing
- **Curriculum alignment:** Year 9 DT — materials, sustainability in design, systems and control
- **Why this subject is necessary:** Without DT, students can identify the problems but cannot design solutions. DT moves the project from analysis ("our school wastes energy") to action ("here is a prototype draught-excluding strip / motion-activated light switch / window insulation panel that we can actually install").

**English: How do we persuade the headteacher?**
- **Knowledge:** Persuasive writing techniques (ethos, pathos, logos), report writing (formal register, structured argument), presentation skills (pitching an idea to a decision-maker)
- **Skills:** Persuasive writing, audience awareness, formal register, structuring an argument with evidence
- **Curriculum alignment:** Year 9 English — writing for purpose and audience, persuasive techniques, non-fiction writing
- **Why this subject is necessary:** The students' proposal needs to CONVINCE the headteacher and governors. A technically brilliant proposal that is poorly communicated will fail. English provides the communication skills that make the other subjects' contributions actionable.

### Integration Points

| Integration Point | Subject A produces... | Subject B uses it to... |
|---|---|---|
| **Energy audit data** | Science conducts the audit (temperature readings, electricity meter data, heat loss observations) | Maths analyses the data (percentage breakdowns, graphs, trend analysis) |
| **Quantified savings** | Maths calculates potential savings from each intervention (in kWh and £) | DT uses the savings data to prioritise which solutions to design (highest impact first) |
| **Carbon context** | Geography calculates the carbon footprint of current energy use | Science uses this to explain the environmental impact of different energy sources |
| **Prototype performance** | DT tests prototype insulation materials and measures effectiveness | Science evaluates the results using energy transfer principles |
| **Final proposal** | ALL subjects contribute evidence and analysis | English structures the proposal as a persuasive document for the headteacher |

### Implementation Plan

**Option A — Single teacher (Science teacher works alone):**
Within Science lessons, the teacher:
- Conducts the energy audit as a scientific investigation (Weeks 1–2)
- Includes basic data analysis that references mathematical concepts: "We need to calculate percentage change — you've done this in Maths"
- References geographical context: "Our school's energy use contributes to carbon emissions — you may be studying this in Geography"
- Sets the persuasive proposal as homework: "Write a letter to the headteacher recommending ONE change, with evidence from your audit"

This requires no cross-departmental coordination. The Science teacher makes connections TO other subjects without requiring those subjects to participate.

**Option B — Coordinated teaching (4 subjects, synchronised timing):**
All four subjects teach the energy problem during the same 3-week period, in their own lessons:
- **Week 1:** Science conducts the energy audit. Maths begins analysing the school's energy bill data. Geography introduces energy in global context. DT begins researching insulation and lighting solutions.
- **Week 2:** Science shares audit data with Maths (via a shared spreadsheet). Maths analyses and visualises the data. Geography calculates carbon footprint using the data. DT designs prototype solutions based on Science and Maths findings.
- **Week 3:** DT tests prototypes. Maths calculates payback periods. English helps students write the formal proposal. ALL subjects contribute to the final presentation.

This requires: one 30-minute cross-departmental planning meeting before the unit, a shared digital folder for data, and approximate timetable synchronisation (Science audit in Week 1 must precede Maths analysis in Week 2).

**Option C — Full collaboration (team teaching, shared lessons):**
Subjects combine lessons for key sessions:
- Science + Maths co-teach the energy audit (Science provides the methodology, Maths provides the analytical tools)
- Geography + English co-teach the proposal writing (Geography provides the environmental context, English provides the communication framework)
- DT + Science co-teach the prototype testing (DT builds it, Science measures it)
- Final presentation is a combined session where student groups present to the headteacher (genuine audience)

This requires: timetable flexibility, shared planning time, and support from school leadership. It is the most powerful option but the hardest to organise.

### Assessment Approach

**The Energy Action Proposal (integrated assessment):**

Student groups produce a formal proposal to the headteacher recommending specific actions to reduce school energy use by 20%. The proposal must include:

1. **Evidence from the energy audit** (Science): What we measured, what we found, where energy is wasted
2. **Data analysis** (Mathematics): Quantified savings, graphs, payback calculations
3. **Environmental context** (Geography): Why this matters — carbon footprint, global context
4. **Proposed solutions with prototypes** (DT): What we recommend, how we designed it, test results
5. **Persuasive communication** (English): Formal register, structured argument, clear recommendations

The proposal is assessed on: accuracy of evidence, quality of analysis, depth of context, feasibility of solutions, and clarity of communication. Each subject assesses its disciplinary contribution; the integration is assessed by the quality of the overall proposal.

**The real test:** Does the headteacher accept the proposal? If students present to a genuine audience with real decision-making power, the assessment has authentic stakes.

---

## Known Limitations

1. **Cross-curricular integration is structurally difficult in secondary schools.** Subject timetables, departmental silos, separate planning time, and individual teacher accountability all work against integration. The three-option implementation plan above acknowledges this reality — Option A works in any school, Option C requires significant structural flexibility that many schools don't have.

2. **Integration can dilute individual subjects if poorly designed (Czerniak et al., 1999).** The most common failure mode is that subjects contribute superficially to the shared problem rather than substantively. "Let's do energy percentages in Maths" (one lesson, low challenge) is weaker than "analyse real school energy data using percentage change, statistical representation, and financial modelling" (multiple lessons, genuine mathematical thinking). Each subject must maintain its own standards within the integrated context.

3. **Not all real-world problems connect equally to all subjects.** The energy problem above connects naturally to Science, Maths, Geography, DT, and English. It does not connect well to Music, PE, or MFL. Forcing connections to subjects that don't naturally contribute weakens the integration. It is better to have four subjects genuinely integrated than eight subjects artificially connected.

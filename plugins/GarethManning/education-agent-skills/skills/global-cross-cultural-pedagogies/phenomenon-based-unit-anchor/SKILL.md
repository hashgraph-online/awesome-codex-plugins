---
# AGENT SKILLS STANDARD FIELDS (v2)
name: phenomenon-based-unit-anchor
description: "Anchor a multidisciplinary unit in a real-world phenomenon that requires multiple subject lenses to understand. Use when designing integrated or phenomenon-based units across disciplines."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "global-cross-cultural-pedagogies/phenomenon-based-unit-anchor"
skill_name: "Phenomenon-Based Unit Anchor"
domain: "global-cross-cultural-pedagogies"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Finnish National Agency for Education (2016) — National Core Curriculum for Basic Education (POPS 2016)"
  - "Lonka (2018) — Phenomenal Learning from Finland"
  - "Symeonidis & Schwarz (2016) — Phenomenon-based teaching and learning through the pedagogical lenses of phenomenology"
  - "Halinen (2018) — The new educational curriculum in Finland"
  - "Silander (2015) — Phenomenon-based learning in Espoo"
input_schema:
  required:
    - field: "phenomenon"
      type: "string"
      description: "The real-world phenomenon that anchors the unit — a complex, authentic situation that requires multiple subject lenses to understand"
    - field: "subjects_involved"
      type: "string"
      description: "Which subject areas or disciplines the phenomenon draws on"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "curriculum_links"
      type: "string"
      description: "Specific curriculum objectives the unit must address"
    - field: "unit_duration"
      type: "string"
      description: "How long the unit will last — 1 week, 2 weeks, a half-term module"
    - field: "school_context"
      type: "string"
      description: "Whether the school supports cross-curricular planning, timetable flexibility, team teaching"
    - field: "local_relevance"
      type: "string"
      description: "How the phenomenon connects to students' local community or lived experience"
output_schema:
  type: "object"
  fields:
    - field: "unit_design"
      type: "object"
      description: "The complete phenomenon-based unit — anchor phenomenon, driving questions, subject contributions, integration points"
    - field: "subject_contributions"
      type: "array"
      description: "What each subject area contributes to understanding the phenomenon — specific knowledge and skills"
    - field: "integration_points"
      type: "array"
      description: "Where and how the subjects connect — genuine integration, not just proximity"
    - field: "student_inquiry_pathway"
      type: "object"
      description: "How students investigate the phenomenon — questions, activities, evidence gathering"
    - field: "assessment_design"
      type: "object"
      description: "How to assess understanding of the phenomenon — demonstrating integrated understanding, not subject-by-subject testing"
chains_well_with:
  - "project-brief-designer"
  - "culturally-responsive-teaching-designer"
  - "place-based-inquiry-anchor"
  - "agency-scaffold-generator"
  - "curriculum-knowledge-architecture-designer"
teacher_time: "5 minutes"
tags: ["phenomenon-based-learning", "Finland", "POPS-2016", "Lonka", "cross-curricular", "interdisciplinary", "transversal-competences"]
---

# Phenomenon-Based Unit Anchor

## What This Skill Does

Designs a phenomenon-based learning unit anchored in a real-world phenomenon that requires multiple subject disciplines to understand — following the approach central to Finland's 2016 National Core Curriculum (POPS 2016). The critical insight from the Finnish model is that phenomena are not "topics" or "themes" — they are complex real-world situations that genuinely REQUIRE multiple disciplinary lenses because no single subject can fully explain them. A phenomenon like "water quality in our local river" requires science (chemistry of pollutants, ecology of aquatic life), geography (land use, water systems), mathematics (data analysis, measurement), and civic education (policy, community responsibility). The skill designs the unit so that each subject's contribution is necessary and the integration is genuine — subjects connect because the phenomenon demands it, not because the teacher artificially stitches them together. The output includes the unit design, each subject's contribution, specific integration points, a student inquiry pathway, and an assessment design that tests integrated understanding. AI is specifically valuable here because designing authentic phenomenon-based units requires simultaneously mapping curriculum objectives from multiple subjects onto a single phenomenon while ensuring genuine integration — a complex design challenge that benefits from systematic cross-referencing.

## Evidence Foundation

The Finnish National Agency for Education (2016) mandated that all schools include at least one extended "multidisciplinary learning module" per year, where students study a phenomenon through multiple subject lenses. The rationale was that real-world problems do not come in subject-shaped packages — climate change is not "science" or "geography" or "economics" but all of these simultaneously. Lonka (2018) documented the Finnish approach, emphasising that phenomenon-based learning (PBL — not to be confused with problem-based learning) is not the abandonment of subjects but their integration around authentic phenomena. Subjects still exist and are taught — but they are regularly brought together to address real-world complexity. Symeonidis & Schwarz (2016) grounded the approach in phenomenological philosophy, arguing that phenomena are experienced holistically before being analytically separated into disciplines — so learning should sometimes reverse the analytical separation and return to holistic engagement. Halinen (2018) described how the Finnish curriculum pairs subject-specific objectives with "transversal competences" (thinking and learning to learn, cultural competence, multiliteracy, ICT competence, working life competence, participation and involvement, taking care of oneself and managing daily life) that are developed through phenomenon-based modules. Silander (2015) documented early implementation in Espoo, showing that the most effective phenomenon-based units were those where the phenomenon was genuinely complex (requiring multiple disciplines) and locally relevant (connected to students' community), rather than artificial "themes" with forced subject connections.

## Input Schema

The teacher must provide:
- **Phenomenon:** The real-world situation. *e.g. "Water quality in our local river — why does it change through the year and what affects it?" / "Fast fashion — why are clothes so cheap and what does that cost?" / "Our school's carbon footprint — where does it come from and can we reduce it?" / "Migration to our city — why do people come, what changes, and how do communities respond?"*
- **Subjects involved:** Which disciplines. *e.g. "Science, Geography, Mathematics" / "Geography, Economics, Ethics, Textiles" / "Science, Mathematics, Citizenship" / "Geography, History, English, PSHE"*

Optional (injected by context engine if available):
- **Student level:** Year group
- **Curriculum links:** Specific objectives to address
- **Unit duration:** How long the unit runs
- **School context:** Timetable flexibility, team teaching capacity
- **Local relevance:** Connection to students' community

## Prompt

```
You are an expert in phenomenon-based learning as developed in the Finnish education system, with deep knowledge of the POPS 2016 curriculum reform, Lonka's (2018) documentation of the Finnish approach, Symeonidis & Schwarz's (2016) phenomenological grounding, Halinen's (2018) transversal competences framework, and Silander's (2015) implementation research. You understand that phenomenon-based learning is NOT "topic work" or "themed weeks" — it is rigorous, disciplinary learning organised around a real-world phenomenon that genuinely requires multiple subjects to understand.

CRITICAL PRINCIPLES:
- **The phenomenon must be GENUINELY complex.** A good phenomenon cannot be fully understood through one subject alone. If the "integration" requires forcing connections ("Let's do fractions about the rainforest!"), the phenomenon is wrong. Each subject must contribute something NECESSARY that the other subjects cannot provide.
- **Subjects contribute, they don't disappear.** Students still learn science AS science, maths AS maths. The phenomenon provides the context and motivation — but the disciplinary rigour is maintained. Students should learn subject content MORE deeply because the phenomenon gives it meaning, not less deeply because the integration is superficial.
- **Start with a question, not a topic.** "Water" is a topic. "Why does the water quality in our river change through the year, and what can we do about it?" is a driving question that generates genuine inquiry. The question should be real, open, and locally relevant.
- **Integration points must be genuine.** The subjects should connect at specific, identified points where one subject's contribution informs another's. "Science tells us about pollutants; Geography tells us where they come from; Maths helps us analyse the data" — each subject's contribution is genuinely needed at a specific point.
- **Assessment must be integrated.** If you test each subject separately at the end, you have not designed a phenomenon-based unit — you have designed parallel subject units on the same topic. The final assessment should require students to draw on multiple subjects simultaneously.

Your task is to design a phenomenon-based unit for:

**Phenomenon:** {{phenomenon}}
**Subjects involved:** {{subjects_involved}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for lower secondary (Years 7–9).
**Curriculum links:** {{curriculum_links}} — if not provided, identify appropriate curriculum areas.
**Unit duration:** {{unit_duration}} — if not provided, design for a 2-week module (approximately 10–12 lessons across subjects).
**School context:** {{school_context}} — if not provided, design for a standard timetable where subjects are taught separately but teachers coordinate.
**Local relevance:** {{local_relevance}} — if not provided, include a step where students connect the phenomenon to their own community.

Return your output in this exact format:

## Phenomenon-Based Unit: [Phenomenon]

**Driving question:** [The central question that animates the unit]
**Subjects:** [Which disciplines contribute]
**Duration:** [How long]
**Transversal competences developed:** [Which Finnish-style transversal competences this unit develops]

### Unit Overview

[One paragraph: what students investigate, how subjects contribute, what they produce]

### Subject Contributions

For each subject:
**[Subject]: [What this subject contributes]**
- **Knowledge:** [What students learn in this subject through the phenomenon]
- **Skills:** [What disciplinary skills students develop]
- **Why this subject is necessary:** [What understanding would be MISSING without this subject's contribution]

### Integration Map

[Where and how the subjects genuinely connect — specific points where one subject's output becomes another subject's input]

### Student Inquiry Pathway

**Week 1: [Phase name]**
[What students do — which subjects are active, what questions they investigate, what they produce]

**Week 2: [Phase name]**
[Continuation — how the inquiry deepens, how subjects come together]

### Assessment Design

[How to assess integrated understanding — not subject-by-subject testing but a task that requires drawing on multiple disciplines]

### Practical Considerations

[How to coordinate across subjects when teachers have separate timetables — meeting points, shared resources, communication]

**Self-check before returning output:** Verify that (a) the phenomenon genuinely requires multiple subjects, (b) each subject contributes something necessary that others cannot provide, (c) the integration points are genuine and specific, (d) the assessment requires integrated understanding, and (e) the unit is practically feasible within normal school structures.
```

## Example Output

**Scenario:** *Phenomenon: "Fast fashion — why are clothes so cheap, what does that cost environmentally and socially, and what could we do about it?" / Subjects involved: "Geography, Science, Mathematics, Ethics/PSHE" / Student level: "Year 8" / Unit duration: "2 weeks — approximately 10 lessons across the four subjects" / Local relevance: "The school is near a high street with several fast-fashion retailers — students shop there regularly"*

---

## Phenomenon-Based Unit: Fast Fashion

**Driving question:** Why are our clothes so cheap, what does that cheapness really cost, and what choices do we have?
**Subjects:** Geography, Science, Mathematics, Ethics/PSHE
**Duration:** 2 weeks (10 lessons across 4 subjects)
**Transversal competences developed:** Thinking and learning to learn, cultural competence and interaction, multiliteracy, participation and involvement

### Unit Overview

Students investigate the fast fashion phenomenon through four disciplinary lenses: Geography examines global supply chains (where clothes are made, why production moves to certain countries, the human geography of garment workers); Science investigates the environmental impact (textile chemistry, water pollution from dyes, microplastic shedding from synthetic fabrics, carbon footprint of transportation); Mathematics analyses the data (cost breakdowns, production volumes, waste statistics, comparison and interpretation of data sources); Ethics/PSHE explores the moral dimensions (consumer choice, worker rights, the tension between affordability and exploitation). The unit culminates in a student-produced "True Cost Label" — a redesigned clothing label that communicates the full environmental and human cost of a garment, using evidence from all four subjects.

### Subject Contributions

**Geography: Where do our clothes come from, and why?**
- **Knowledge:** Global supply chains, economic geography of manufacturing (why Bangladesh, Vietnam, Ethiopia), push-pull factors for factory location, urbanisation and working conditions in manufacturing zones
- **Skills:** Map skills (tracing supply chains), data interpretation (comparing wages and working conditions across countries), geographical enquiry
- **Why this subject is necessary:** Without Geography, students cannot understand WHY clothes are cheap — the spatial logic of global manufacturing, the race to the bottom in labour costs, the human geography of garment workers. Science can explain environmental damage but not the economic structures that cause it.

**Science: What does fast fashion do to the planet?**
- **Knowledge:** Properties of textile fibres (natural vs. synthetic), chemical processes in dyeing and finishing, water pollution (chemical effluent from factories), microplastic pollution (synthetic fibres released in washing), carbon emissions from global transportation
- **Skills:** Scientific enquiry (testing microplastic release from different fabrics), data collection, understanding chemical processes
- **Why this subject is necessary:** Without Science, students cannot understand the ENVIRONMENTAL cost. "Pollution" remains vague unless students understand the specific chemistry — what chemicals are in textile dyes, what happens when synthetic fibres enter waterways, why polyester takes 200 years to decompose.

**Mathematics: How big is the problem, and can we trust the numbers?**
- **Knowledge:** Percentages (cost breakdowns — what percentage of a £5 t-shirt goes to the worker?), large number sense (2.7 billion garments produced annually — how to comprehend this), data interpretation (reading and critiquing graphs from campaign organisations and industry reports)
- **Skills:** Calculating percentages, interpreting and comparing data from different sources, understanding statistical claims, creating data visualisations
- **Why this subject is necessary:** Without Mathematics, students cannot grasp the SCALE of the problem. "Lots of clothes are wasted" is vague. "In the UK, 350,000 tonnes of clothing goes to landfill each year — that's the weight of 35,000 double-decker buses" is specific and comprehensible. Mathematics also provides critical tools for evaluating competing claims from industry and campaign groups.

**Ethics/PSHE: What should we do about it?**
- **Knowledge:** Ethical frameworks (rights, consequences, fairness), consumer responsibility, the concept of "ethical consumption," tension between individual choice and systemic change, workers' rights (UN Declaration of Human Rights, ILO conventions)
- **Skills:** Ethical reasoning, constructing arguments, perspective-taking, evaluating competing values (affordability vs. sustainability vs. workers' rights)
- **Why this subject is necessary:** Without Ethics/PSHE, the unit produces knowledge without agency. Students learn that fast fashion causes harm but have no framework for deciding what to DO about it. Is it the consumer's responsibility? The company's? The government's? Is boycotting effective or does it harm the workers it intends to help? These are ethical questions that require ethical reasoning.

### Integration Map

| Integration Point | Subject A contributes... | Subject B uses it to... |
|---|---|---|
| **Supply chain mapping** | Geography maps the production journey of a t-shirt (cotton field → spinner → factory → ship → warehouse → shop) | Maths calculates the cost at each stage (what % of the retail price goes where?) |
| **Environmental evidence** | Science identifies specific pollutants from textile production | Geography maps where the pollution occurs (river systems near factories in producing countries, not consuming countries) |
| **Scale of the problem** | Maths analyses production and waste statistics | Ethics uses the data to evaluate moral responsibility ("If 87% of clothing fibre ends up in landfill or incineration, is this a design problem or a consumer problem?") |
| **Worker conditions** | Geography describes working conditions and wages in garment factories | Ethics examines these through a rights framework ("Does this violate Article 23 of the UDHR?") |
| **The True Cost Label** | ALL subjects contribute data and analysis | Students synthesise all four lenses into a single product |

### Student Inquiry Pathway

**Week 1: Understanding the Phenomenon**

*Geography (2 lessons):* Trace the supply chain of a specific garment. Students are given a clothing label ("Made in Bangladesh") and investigate the journey: where was the cotton grown? Where was it spun? Where was the garment sewn? How did it get to the UK? Students create a supply chain map and research working conditions at each stage. Homework: check the labels on 5 items in your wardrobe — where were they made?

*Science (2 lessons):* Investigate textile materials. Lesson 1: examine fabric samples under microscopes (cotton vs. polyester vs. nylon) — what are they made of? What are their properties? Lesson 2: design and conduct a simple experiment to test microplastic release — wash samples of synthetic fabric in water, filter, and examine under microscope. What do you find?

*Mathematics (1 lesson):* The £5 t-shirt breakdown. Students are given data on the cost structure of a fast-fashion t-shirt and calculate: what percentage goes to the cotton farmer, the factory worker, the shipping company, the retailer, the brand? Present the data as a pie chart. Discuss: "Does this distribution seem fair? What would have to change for the worker to earn a living wage?"

**Week 2: Analysing and Responding**

*Science (1 lesson):* Carbon footprint calculation. Students calculate the approximate carbon footprint of their investigated garment's journey (using simplified transport emission data from Geography's supply chain map). Compare: what's the carbon footprint of a locally-made garment vs. one shipped from Asia?

*Ethics/PSHE (2 lessons):* Lesson 1: The ethical debate. Present three positions: "Buy fewer, better clothes" (consumer responsibility), "Companies should pay living wages" (corporate responsibility), "Governments should regulate" (systemic change). Students evaluate each using ethical frameworks. Lesson 2: "Is boycotting ethical?" — if consumers stop buying from Bangladesh, factory workers lose their jobs. Students grapple with the unintended consequences of well-intentioned action.

*Mathematics (1 lesson):* Evaluating competing claims. Students are given two data sources: an industry report claiming "fast fashion has reduced clothing costs, benefiting low-income families" and a campaign report claiming "fast fashion produces 10% of global carbon emissions." Evaluate both: What data is being used? Is it reliable? Are the claims accurate? Students learn to read data critically.

*ALL subjects (1 lesson — combined or coordinated):* Create the "True Cost Label." Each student designs a label for a garment that communicates: where it was made and who made it (Geography), its environmental impact (Science), the cost breakdown (Maths), and an ethical rating (Ethics). The label must be evidence-based — every claim must be supported by data from the unit.

### Assessment Design

**The True Cost Label (integrated assessment):**

Students produce a "True Cost Label" for a garment of their choice (from their own wardrobe or a hypothetical garment). The label must include:

1. **Supply chain summary** (Geography): Where the garment was made, the journey it took, the conditions of the workers at each stage
2. **Environmental impact statement** (Science): The environmental cost — materials, chemicals, carbon, microplastics — with specific data
3. **Cost breakdown** (Mathematics): A visual representation of where the retail price goes, with percentages calculated and presented clearly
4. **Ethical assessment** (Ethics): An evaluation of the garment's ethical standing, using at least one ethical framework, including acknowledgement of tensions and trade-offs

**Assessment criteria:** The label is assessed holistically — not subject by subject. Criteria include: accuracy (is the evidence correct?), integration (do the four lenses connect to form a coherent picture?), criticality (does the student acknowledge complexity and trade-offs?), and communication (is the label clear and effective?).

Each contributing subject teacher assesses the accuracy of their disciplinary contribution, but the INTEGRATION is assessed jointly.

### Practical Considerations

**Coordination (the hardest part):** The four teachers need one 30-minute planning meeting before the unit and one during (to share what students have produced and adjust). A shared folder (digital or physical) where students store their evidence from each subject — each lesson's output feeds into the final label.

**Timetable:** The unit works within a normal timetable. Each subject teaches its lessons in its own slot. The only requirement is approximate synchronisation (Geography's supply chain lesson should come before Maths' cost breakdown, since the supply chain provides the data for the cost analysis). A simple shared timeline prevents subjects getting out of sequence.

**Resources:** Fabric samples (for Science microscope work), garment labels (students bring from home), data sets (cost breakdowns, production statistics — curated by teachers), access to simple mapping tools (for Geography supply chain maps).

---

## Known Limitations

1. **Phenomenon-based learning requires cross-subject coordination, which is structurally difficult in most schools.** The Finnish curriculum was designed with this in mind — Finnish schools typically have more timetable flexibility and a tradition of teacher collaboration. In schools with rigid timetables and limited planning time, coordination between subjects is the primary barrier. The unit design above minimises the coordination needed (one planning meeting, a shared folder, approximate synchronisation), but it still requires more collaboration than independent subject teaching.

2. **Not all subjects integrate naturally with all phenomena.** The fast fashion example integrates Geography, Science, Maths, and Ethics convincingly — each subject contributes something genuinely necessary. But forced integration ("Let's include Art by having students design a sustainable fashion collection") weakens the unit. It is better to have three genuinely integrated subjects than five artificially connected ones.

3. **Phenomenon-based learning complements subject teaching; it does not replace it.** The Finnish model includes phenomenon-based modules alongside subject-specific teaching — not instead of it. Students still need dedicated subject lessons to build the disciplinary knowledge and skills they bring to the phenomenon. A school that replaced all subject teaching with phenomenon-based learning would likely produce students with broad awareness but shallow disciplinary understanding.

---
# AGENT SKILLS STANDARD FIELDS (v2)
name: service-learning-project-designer
description: "Design a service-learning project connecting genuine community need with embedded curriculum learning. Use when planning community projects, civic engagement, or social action units."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "environmental-experiential-learning/service-learning-project-designer"
skill_name: "Service Learning Project Designer"
domain: "environmental-experiential-learning"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Billig (2000) — Research on K-12 school-based service learning: the evidence builds"
  - "Billig (2004) — Heads, hearts, and hands: the research on K-12 service learning"
  - "RMC Research Corporation (2007) — Impacts of Service Learning on Participating K-12 Students"
  - "Furco (2002) — Is service learning really better than community service?"
  - "Celio, Durlak & Dymnicki (2011) — A meta-analysis of the impact of service learning on students"
input_schema:
  required:
    - field: "community_need"
      type: "string"
      description: "The genuine community need or problem the project addresses — identified with or by the community, not assumed by the school"
    - field: "curriculum_connection"
      type: "string"
      description: "The specific curriculum content that connects to the service — what academic learning is embedded in the project"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "community_partner"
      type: "string"
      description: "The community organisation, group, or individuals the school is working with"
    - field: "project_duration"
      type: "string"
      description: "How long the project runs — a day, a week, a term, ongoing"
    - field: "school_context"
      type: "string"
      description: "Whether the school has a service learning tradition or this is new"
    - field: "student_voice"
      type: "string"
      description: "Whether students have a role in choosing the project or it's been decided"
output_schema:
  type: "object"
  fields:
    - field: "project_design"
      type: "object"
      description: "The complete service learning project — community need, curriculum connection, service activities, reflection structure, assessment"
    - field: "community_partnership"
      type: "object"
      description: "How the school and community partner collaborate — genuine partnership, not charity"
    - field: "curriculum_integration"
      type: "object"
      description: "How the academic learning is embedded in the service — what students learn THROUGH serving, not separately from it"
    - field: "reflection_structure"
      type: "object"
      description: "How students reflect on the experience — before, during, and after the service"
    - field: "assessment_plan"
      type: "object"
      description: "How to assess both the academic learning and the civic development"
chains_well_with:
  - "experiential-learning-cycle-designer"
  - "interdisciplinary-real-world-connection-mapper"
  - "ubuntu-collective-knowledge-task-designer"
  - "agency-scaffold-generator"
teacher_time: "4 minutes"
tags: ["service-learning", "Billig", "community", "civic-engagement", "experiential", "reflection", "social-responsibility"]
---

# Service Learning Project Designer

## What This Skill Does

Designs a service learning project that combines genuine community service with structured academic learning — ensuring that students both contribute meaningfully to their community AND learn curriculum content through the process. The critical distinction from Furco (2002) is that service learning is NOT community service (service without academic learning), NOT volunteerism (service without structured reflection), and NOT field trips (experience without service). Service learning integrates three elements: genuine community benefit, curriculum-connected academic learning, and structured reflection that bridges the two. The approach draws on Billig's (2000, 2004) research showing that the strongest academic effects occur when service is directly connected to curriculum objectives through explicit reflection — not when service and academics happen in parallel without connection. The output includes the complete project design, community partnership framework, curriculum integration plan, reflection structure (before, during, and after service), and assessment plan. AI is specifically valuable here because designing effective service learning requires simultaneously addressing community needs, curriculum requirements, logistical constraints, and the structured reflection that converts service experience into academic learning — a complex design challenge where any element missing undermines the whole.

## Evidence Foundation

Billig (2000) reviewed K-12 service learning research, finding moderate positive effects on academic achievement, civic responsibility, and personal-social development. Critically, she found that these effects depended on quality indicators: the service must address a genuine community need (not a manufactured one), the service must be connected to curriculum content through explicit instruction, and students must engage in structured reflection before, during, and after the service. Service without these quality indicators produced community benefit but minimal learning. Billig (2004) elaborated on the mechanisms: service learning works by providing authentic context for academic content (students see WHY the content matters), developing civic identity (students see themselves as community contributors), and building social-emotional skills (empathy, collaboration, responsibility). Furco (2002) drew a critical distinction: community service focuses on SERVICE (the primary beneficiary is the community), field education focuses on LEARNING (the primary beneficiary is the student), and service learning integrates both (the student and the community both benefit equally). If the service dominates and learning is an afterthought, it's community service. If the learning dominates and service is a pretext, it's field education. True service learning holds both in balance. RMC Research Corporation (2007) summarised the evidence, finding that high-quality service learning projects (with structured reflection, curriculum connection, and genuine community partnership) produced effects on academic engagement, civic responsibility, and social skills — but that low-quality projects (one-off service days, no reflection, no curriculum connection) produced no measurable effects. Celio, Durlak & Dymnicki (2011) conducted a meta-analysis of 62 studies, finding a mean effect size of d=0.27 for academic outcomes — modest but positive, and notably higher for projects with structured reflection.

## Input Schema

The teacher must provide:
- **Community need:** What the community needs. *e.g. "The local food bank is struggling with donations — families in our area are experiencing food poverty" / "Elderly residents in the care home near our school are isolated — many have no visitors" / "The local park has become littered and overgrown — the community wants to restore it" / "Younger students in the primary school next door are struggling with reading — they need more reading partners"*
- **Curriculum connection:** What students will learn. *e.g. "Persuasive writing and campaign design — Year 9 English" / "Data handling and analysis — Year 8 Maths" / "Ecosystems and biodiversity — Year 7 Science" / "Reading comprehension and fluency — Year 5 English"*

Optional (injected by context engine if available):
- **Student level:** Year group
- **Community partner:** The organisation or group
- **Project duration:** How long
- **School context:** Service learning tradition
- **Student voice:** How much choice students have

## Prompt

```
You are an expert in service learning design, with deep knowledge of Billig's (2000, 2004) research on K-12 service learning, Furco's (2002) distinction between service learning, community service, and field education, the RMC Research Corporation's (2007) quality indicators for effective service learning, and Celio, Durlak & Dymnicki's (2011) meta-analysis. You understand that service learning is NOT "doing something nice for the community and learning about it afterwards" — it is a carefully designed pedagogy where service and learning are INTEGRATED through structured reflection, each strengthening the other.

CRITICAL PRINCIPLES:
- **The community need must be GENUINE and identified WITH the community, not FOR them.** The school should not decide what the community needs and then offer it. Genuine partnership means asking: "What does your organisation need? How can our students help in a way that actually serves you?" If the service is designed primarily to benefit the students' learning and the community benefit is an afterthought, it's not service learning — it's field education wearing a charitable mask.
- **The curriculum connection must be DIRECT, not incidental.** "Students learn about food poverty" is incidental to helping at a food bank. "Students analyse food bank data to identify patterns in demand, use statistical methods to predict future need, and present findings to the food bank to improve their planning" is a direct curriculum connection — the academic work IS the service, and the service IS the academic work.
- **Reflection is the mechanism that connects service and learning.** Without reflection, service produces experience but not learning. Billig's research is clear: structured reflection — before service (what do we know? what do we expect?), during service (what are we noticing? what questions arise?), and after service (what did we learn? what changed?) — is what transforms service into education.
- **Reciprocity, not charity.** Service learning should position students and community members as PARTNERS, not as helpers and helped. The community contributes knowledge and expertise; the students contribute time and skills. Both benefit. A project where students feel sorry for the community and "help" them reinforces power imbalances. A project where students and community members work together on a shared problem develops civic partnership.
- **Quality over quantity.** A well-designed, deeply connected service learning project that lasts one week produces more learning than a superficial "service day" repeated monthly. Depth of service, depth of reflection, and depth of curriculum connection matter more than hours of service.

Your task is to design a service learning project for:

**Community need:** {{community_need}}
**Curriculum connection:** {{curriculum_connection}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, infer from the curriculum connection.
**Community partner:** {{community_partner}} — if not provided, suggest appropriate community partners.
**Project duration:** {{project_duration}} — if not provided, design for a 2–3 week project.
**School context:** {{school_context}} — if not provided, design as a standalone project.
**Student voice:** {{student_voice}} — if not provided, build in student choice where possible.

Return your output in this exact format:

## Service Learning Project: [Community Need] × [Curriculum Connection]

**Community need:** [The genuine need being addressed]
**Curriculum connection:** [The academic learning embedded in the service]
**Reciprocity statement:** [How both the community and students benefit — balanced, not charitable]

### Community Partnership

**Partner:** [The community organisation or group]
**Their need:** [What they actually need, in their terms]
**Their contribution:** [What they bring to the partnership — knowledge, expertise, access, perspective]
**Student contribution:** [What students bring — time, skills, energy, fresh perspective]
**Partnership principles:** [How the relationship is structured — respectful, reciprocal, genuine]

### Curriculum Integration

**Academic objectives:** [What students learn through the service — specific curriculum content and skills]
**How service IS learning:** [The mechanism — how the academic work is embedded in the service activity itself, not separate from it]
**How learning IS service:** [The mechanism — how the academic work produces something the community actually needs]

### Project Design

**Phase 1 — Investigation and preparation**
[How students learn about the community need, connect with the community partner, and prepare for service]

**Phase 2 — Service and learning**
[What students do — the integrated service-learning activities]

**Phase 3 — Reflection and sharing**
[How students reflect on the experience and share what they've learned — with the community and with the school]

### Reflection Structure

**Before service:** [What students reflect on before they begin — preconceptions, expectations, questions]
**During service:** [How students reflect while serving — journals, discussions, observations]
**After service:** [How students reflect after completing the service — what changed, what they learned, what questions remain]

### Assessment Plan

**Academic assessment:** [How curriculum learning is assessed — using evidence from the service]
**Civic development assessment:** [How civic skills and dispositions are assessed — not graded but documented]
**Community feedback:** [How the community partner assesses the service — did it genuinely help?]

**Self-check before returning output:** Verify that (a) the community need is genuine, (b) the curriculum connection is direct, (c) reflection is structured before, during, and after, (d) the relationship is reciprocal, and (e) both the community and students benefit meaningfully.
```

## Example Output

**Scenario:** *Community need: "The local food bank is struggling — demand has increased 40% in the last year, but they lack the data infrastructure to predict demand patterns, manage stock efficiently, or communicate their impact to funders. They need help analysing their distribution data and creating materials that communicate their impact." / Curriculum connection: "Year 9 Mathematics — data handling, statistical analysis, percentages, graphical representation, interpretation of real data sets" / Community partner: "The local food bank — a volunteer-run charity that distributes food parcels to approximately 200 families per week. The manager is willing to share anonymised distribution data and would welcome help with data analysis and impact reporting." / Project duration: "3 weeks"*

---

## Service Learning Project: Food Bank Data × Year 9 Mathematics

**Community need:** The local food bank needs data analysis capacity — they collect distribution data but cannot analyse it to predict demand, manage stock, or communicate their impact to funders
**Curriculum connection:** Year 9 Mathematics — statistical analysis, percentages, graphical representation, and interpretation of real data sets
**Reciprocity statement:** The food bank contributes real data, expert knowledge of food poverty, and the authentic context that makes mathematics meaningful. Students contribute analytical skills, time, and fresh perspectives. The food bank gets an impact report and data dashboard. Students get mathematical competence developed through genuine purpose.

### Community Partnership

**Partner:** The local food bank
**Their need (in their terms):** "We know demand is increasing but we can't show the funders exactly how much, or predict when we'll run out of specific items. We collect the data on paper forms but nobody has time to analyse it. If we could show the council and funders a clear picture of our impact, we'd be more likely to secure funding."
**Their contribution:** Anonymised distribution data (what was given to whom, when), expert knowledge of food poverty in the local area, the authentic context that makes the project meaningful, access to the food bank for a visit, willingness to present to students about their work.
**Student contribution:** Mathematical analysis skills (data cleaning, statistical analysis, graphical representation), time (dedicated Maths lessons for 3 weeks), and the production of an impact report and data dashboard that the food bank can actually use.
**Partnership principles:** The food bank is the CLIENT, not the charity case. Students are providing a professional service (data analysis) in response to a genuine need. The food bank manager reviews and approves all outputs before they are used externally. Students do not take photographs in the food bank or identify service users.

### Curriculum Integration

**Academic objectives:** Collect, organise, and analyse real data. Calculate percentages and percentage change. Create appropriate graphical representations (bar charts, line graphs, pie charts) of real data. Interpret statistical patterns and communicate findings clearly. All Year 9 data handling curriculum objectives are addressed through the food bank data.

**How service IS learning:** The academic work IS the service. Students are not "doing Maths and also helping the food bank" — they are doing Maths BY helping the food bank. The data analysis IS the useful service. Every percentage calculated, every graph drawn, every pattern identified serves the food bank's need for impact data. There is no separation between the Maths lesson and the service.

**How learning IS service:** The mathematical outputs (impact report, data dashboard, demand predictions) are genuinely useful to the food bank. The manager will use the impact report in funding applications. The demand predictions will help with stock ordering. The data visualisations will be displayed in the food bank to show volunteers and donors the impact of their work.

### Project Design

**Phase 1 — Investigation and Preparation (Week 1)**

*Lesson 1: Understanding the need.*
The food bank manager visits the school (or sends a video message). They explain: what the food bank does, who uses it, how demand has changed, and what they need from the students. Students ask questions. The manager shares the anonymised data set (paper forms or a spreadsheet).

Key moment: Students see the raw data and realise it's messy, incomplete, and real — nothing like textbook data sets. This IS the mathematical challenge: how do you make sense of imperfect, real-world data?

*Lesson 2: Data familiarisation.*
Students examine the data set in groups. What does it contain? What's missing? How is it organised? Students clean the data: identify missing entries, categorise items, create a usable spreadsheet. This is REAL data handling — the kind of data work that professionals do and that textbook exercises never include.

*Lesson 3: Planning the analysis.*
Each group takes responsibility for one analytical question:
- Group A: "How has demand changed over the last 12 months?" (percentage change, line graph)
- Group B: "What types of food are most in demand?" (frequency analysis, pie chart)
- Group C: "Are there seasonal patterns in demand?" (comparison across months, bar chart)
- Group D: "How many families are served per week, and is this increasing?" (average, trend line)
- Group E: "Where do referrals come from?" (categorical data, bar chart)

**Phase 2 — Service and Learning (Week 2)**

*Lessons 4–5: Analysis.*
Groups conduct their analysis. This is intensive Maths: calculating percentages, drawing graphs, interpreting patterns. The teacher circulates, teaches mini-lessons as needed (how to calculate percentage change, how to identify a trend, how to choose the right type of graph), and ensures mathematical rigour.

Critical difference from a textbook exercise: the data is REAL. The answer matters. If Group A calculates that demand has increased by 43%, this is not a textbook answer — it's a fact about their community that the food bank needs to know.

*Lesson 6: Visit to the food bank (if possible).*
Students visit the food bank. They see the operation: how food is sorted, how parcels are assembled, how families collect them. They meet volunteers. This puts the data in human context — the numbers represent people. After the visit, students return to their analysis with renewed motivation and understanding.

**Phase 3 — Reflection and Sharing (Week 3)**

*Lesson 7: Creating the impact report.*
Groups compile their analyses into a single impact report. Each group contributes their section (with data, graphs, and interpretation). The class collectively writes the introduction and conclusions. The report is formatted professionally — this is a document that the food bank will use in funding applications.

*Lesson 8: Presentation to the food bank.*
The food bank manager returns (or students visit the food bank). Students present their findings. The manager responds: "This is exactly what we needed. We can use this graph in our next funding application. Your demand prediction will help us plan stock orders."

*Lesson 9: Reflection and assessment.*
Structured final reflection (see below). Individual assessment task.

### Reflection Structure

**Before service (Lesson 1):**
- "What do you know about food banks? Who uses them and why?"
- "What preconceptions do you have about people who use food banks? Where do these come from?" (Challenging stereotypes about poverty — this is the civic learning dimension)
- "What do you expect the data to show? Make a prediction: has demand increased or decreased? By how much?"

**During service (Lessons 4–6):**
- "What surprised you in the data? Did anything challenge your expectations?"
- "How does the real data compare to textbook data? What's different? What makes it harder?"
- After the visit: "What did you see today that the data doesn't show? What can numbers capture and what can't they?"

**After service (Lesson 9):**
- "What mathematical skills did you use that you didn't realise you'd need?"
- "How did working with real data for a real purpose change how you approached the Maths?"
- "Has your understanding of food poverty changed? How? What questions do you still have?"
- "What does it mean that mathematical skills can help a community? Where else could data analysis make a difference?"

### Assessment Plan

**Academic assessment:**
Individual task: Students are given a new, unfamiliar data set (e.g., from a charity shop or homeless shelter). They must: clean the data, calculate key statistics, create appropriate graphs, identify patterns, and write a brief report. This tests TRANSFER — can they apply the skills learned through the food bank project to a new context?

**Civic development assessment (not graded, but documented):**
Students write a reflective paragraph: "What did this project teach me that a textbook couldn't?" The teacher looks for evidence of: empathy (understanding the human context behind the data), civic awareness (understanding community needs), and agency (belief that their skills can make a difference).

**Community feedback:**
The food bank manager provides written feedback: Was the analysis accurate? Was the report useful? Will they use it? This is the most meaningful assessment — not "did the students get the Maths right?" but "did their Maths produce something the community actually needs?"

---

## Known Limitations

1. **Service learning requires genuine community partnerships, which take time to develop.** The food bank project above assumes a willing community partner who can provide data, host visits, and give feedback. Finding and maintaining such partnerships is one of the biggest practical challenges of service learning. Schools new to service learning should start with one trusted community partner and build from there.

2. **The meta-analytic effect size for service learning on academic outcomes is modest (d=0.27 — Celio et al., 2011).** Service learning is not a high-impact academic strategy in the way that retrieval practice or feedback are. Its primary value is in integrating academic learning with civic development, authentic context, and motivation — not in raising test scores. Teachers should use service learning because it develops citizens AND teaches curriculum, not because it is the most efficient way to improve academic attainment.

3. **The distinction between service learning and charity is crucial and easy to get wrong.** If students feel sorry for food bank users and "help" them from a position of privilege, the project reinforces social hierarchies rather than challenging them. The reflection structure is designed to prevent this — but the teacher must be vigilant. The framing should be partnership, not pity: "We are providing data analysis skills that the food bank needs. They are providing us with real data and authentic purpose that we need. Both sides contribute, both sides benefit."

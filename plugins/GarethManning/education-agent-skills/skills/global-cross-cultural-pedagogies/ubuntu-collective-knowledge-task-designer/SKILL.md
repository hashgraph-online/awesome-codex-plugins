---
# AGENT SKILLS STANDARD FIELDS (v2)
name: ubuntu-collective-knowledge-task-designer
description: "Design learning tasks built on Ubuntu philosophy emphasising collective knowledge-building and mutual responsibility. Use when fostering collaboration that values community over individual competition."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "global-cross-cultural-pedagogies/ubuntu-collective-knowledge-task-designer"
skill_name: "Ubuntu Collective Knowledge Task Designer"
domain: "global-cross-cultural-pedagogies"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Mkabela (2005) — Using the Afrocentric method in researching indigenous African culture"
  - "Letseka (2012) — In defence of Ubuntu"
  - "Ramose (2002) — The philosophy of Ubuntu and Ubuntu as a philosophy"
  - "Venter (2004) — What is African philosophy of education?"
  - "Msila (2008) — Ubuntu and school leadership"
input_schema:
  required:
    - field: "learning_objective"
      type: "string"
      description: "The curriculum content or skill students need to learn"
    - field: "class_context"
      type: "string"
      description: "The class composition, community context, and how students currently relate to collaborative learning"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "current_task"
      type: "string"
      description: "The existing task that could be redesigned through an Ubuntu lens"
    - field: "community_connection"
      type: "string"
      description: "How the learning connects to or could involve the wider community"
    - field: "assessment_constraints"
      type: "string"
      description: "Whether the curriculum requires individual assessment, and how to balance this with collective learning"
output_schema:
  type: "object"
  fields:
    - field: "ubuntu_task_design"
      type: "object"
      description: "The redesigned task using Ubuntu principles — collective knowledge building, shared responsibility, community benefit"
    - field: "collective_knowledge_structure"
      type: "object"
      description: "How the task structures collective rather than individual knowledge building — each person's contribution is necessary for the whole"
    - field: "community_dimension"
      type: "object"
      description: "How the learning connects to or serves the wider community — not just individual achievement"
    - field: "individual_within_collective"
      type: "object"
      description: "How individual growth and accountability exist within the collective structure — not erased but reframed"
chains_well_with:
  - "culturally-responsive-teaching-designer"
  - "belonging-classroom-culture-designer"
  - "place-based-inquiry-anchor"
  - "agency-scaffold-generator"
teacher_time: "4 minutes"
tags: ["Ubuntu", "Mkabela", "African-philosophy", "collective-knowledge", "communalism", "community", "collaboration"]
---

# Ubuntu Collective Knowledge Task Designer

## What This Skill Does

Redesigns learning tasks through the lens of Ubuntu philosophy — the African concept of "umuntu ngumuntu ngabantu" (a person is a person through other persons) — so that knowledge building is genuinely collective rather than individual. Western education typically structures learning as individual acquisition: each student learns for themselves, is assessed alone, and succeeds or fails independently. Ubuntu philosophy proposes a fundamentally different epistemology: knowledge is communal, wisdom emerges through relationship, and a person's understanding is incomplete without the understanding of others. The skill redesigns academic tasks so that collective knowledge building is structural (the task cannot be completed alone — each person's contribution is genuinely necessary), the learning serves the community (not just the individual student), and individual growth exists WITHIN, not apart from, the collective. The output includes a redesigned task with collective knowledge structures, a community dimension, and a framework for individual accountability within collective learning. AI is specifically valuable here because designing genuinely collective tasks (not just group work relabelled) requires rethinking task structure at a fundamental level — ensuring that interdependence is authentic, not cosmetic.

## Evidence Foundation

Mkabela (2005) articulated an Afrocentric research methodology grounded in communal knowledge production, arguing that knowledge in African philosophical traditions is not a private commodity but a shared resource that belongs to the community. The individual learner's role is not to acquire knowledge for personal advantage but to contribute to the community's collective understanding. Letseka (2012) defended Ubuntu as a coherent philosophical framework with educational implications: education's purpose is to develop persons who understand themselves as fundamentally connected to others — "I am because we are." This is not collectivism that erases the individual but a relational ontology where individual identity is constituted through community. Ramose (2002) explored Ubuntu as a philosophy of be-ing (his hyphenation), arguing that human existence is inherently communal and that education should develop this communal orientation rather than competitive individualism. Venter (2004) examined African philosophy of education specifically, identifying key principles: communalism (the community's welfare takes precedence over individual advantage), respect for elders and knowledge holders, learning through participation in community life, and the integration of education with community service. Msila (2008) applied Ubuntu to school leadership, showing that schools organised around Ubuntu principles — shared responsibility, communal decision-making, collective accountability — produced more cohesive and supportive learning environments than schools organised around competitive individualism.

## Input Schema

The teacher must provide:
- **Learning objective:** What students need to learn. *e.g. "Understanding photosynthesis — Year 8 Science" / "Persuasive writing — Year 9 English" / "Local history — Year 7 History, investigating the history of our local area" / "Data handling — Year 6 Mathematics, collecting, presenting, and interpreting data"*
- **Class context:** Who the students are and how they currently work. *e.g. "Year 8, 30 students, mixed ability, tend to work individually and competitively — some students are reluctant to share work because they fear others will copy" / "Year 7, very collaborative but group work often results in uneven contribution — a few students do most of the work"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Student level:** Year group
- **Current task:** An existing task to redesign
- **Community connection:** Links to wider community
- **Assessment constraints:** Whether individual assessment is required

## Prompt

```
You are an expert in Ubuntu philosophy of education, with deep knowledge of Mkabela's (2005) Afrocentric epistemology, Letseka's (2012) defence of Ubuntu, Ramose's (2002) philosophy of be-ing, Venter's (2004) African philosophy of education, and Msila's (2008) Ubuntu in school leadership. You understand that Ubuntu is not merely a synonym for "group work" or "collaboration" — it represents a fundamentally different understanding of knowledge, personhood, and the purpose of education. In Ubuntu, knowledge is communal property, individual understanding is constituted through relationship, and education exists to serve the community, not just the individual.

CRITICAL PRINCIPLES:
- **Genuine interdependence, not cosmetic collaboration.** In typical group work, the task CAN be done alone — the group is convenient, not necessary. In an Ubuntu-designed task, the task CANNOT be completed by one person because each person's unique contribution (perspective, experience, knowledge) is structurally necessary. If one voice is missing, the collective knowledge is incomplete.
- **Knowledge as communal, not competitive.** The task must be designed so that sharing knowledge benefits everyone, not so that knowledge is a scarce resource to be hoarded. Remove structures that reward individual knowledge-holding (competitive grading, individual ranking) and replace them with structures that reward collective knowledge-growing.
- **Community benefit, not just individual achievement.** In Ubuntu, education serves the community. The task should produce something that benefits others beyond the individual students — knowledge shared with younger students, a resource for the community, a solution to a local problem. The question is not "What have I learned?" but "What have WE learned, and who else benefits?"
- **Individual identity WITHIN the collective.** Ubuntu does not erase individual identity — it locates it within community. Each student should have a distinct role, a unique contribution, and individual growth. But the individual's contribution is meaningful because of how it serves the whole — not in isolation.
- **Respect for all knowledge holders.** Ubuntu respects elders and those with experience as knowledge holders. The task can extend beyond the classroom to involve family members, community elders, or practitioners whose knowledge enriches the learning.

Your task is to redesign a learning task through Ubuntu principles for:

**Learning objective:** {{learning_objective}}
**Class context:** {{class_context}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the learning objective.
**Student level:** {{student_level}} — if not provided, infer from the learning objective.
**Current task:** {{current_task}} — if not provided, design a new task.
**Community connection:** {{community_connection}} — if not provided, suggest appropriate community links.
**Assessment constraints:** {{assessment_constraints}} — if not provided, design for a context where both individual understanding and collective contribution are valued.

Return your output in this exact format:

## Ubuntu Collective Knowledge Task: [Learning Objective]

**Learning objective:** [What students learn]
**Ubuntu principle:** [The specific Ubuntu principle most central to this task]
**Community benefit:** [How the learning serves others beyond the students themselves]

### Why Collective Knowledge Matters Here

[Brief explanation of why THIS learning objective benefits from collective rather than individual knowledge building — what is gained that individual learning cannot achieve]

### Task Design

**The collective task:** [What the class or group does together — structured so that each person's contribution is genuinely necessary]
**Individual contributions:** [What each student uniquely brings — their specific role, knowledge, or perspective]
**Knowledge integration:** [How individual contributions are woven together into collective understanding]

### Collective Knowledge Structure

[How the task ensures genuine interdependence — what mechanisms prevent the task from being completed by one person alone]

### Community Dimension

[How the learning connects to or serves the wider community — a practical, authentic community element]

### Individual Within Collective

[How individual learning and accountability exist within the collective structure — assessment approach that values both]

### Teacher's Role

[How the teacher facilitates collective knowledge building — different from facilitating group work]

**Self-check before returning output:** Verify that (a) the task requires genuine interdependence, not cosmetic collaboration, (b) knowledge sharing is structurally rewarded, (c) the learning serves someone beyond the individual students, (d) individual identity and contribution are maintained within the collective, and (e) the design is respectful and authentic, not a superficial application of Ubuntu terminology to standard group work.
```

## Example Output

**Scenario:** *Learning objective: "Local history — Year 7 History, investigating the history of our local area over the last 100 years" / Class context: "Year 7, 28 students, diverse community — families have been in the area for varying lengths of time, from multiple generations to recently arrived. Students tend to work individually. The school is in an area undergoing rapid change (new housing developments, changing demographics) and there's a mix of long-established and newer communities." / Community connection: "The school has good relationships with a local community centre, a care home, and several places of worship. There are community members who have lived in the area for 50+ years."*

---

## Ubuntu Collective Knowledge Task: Our Community's Story — A Collective History

**Learning objective:** Investigating local history — using primary and secondary sources, analysing change over time, understanding multiple perspectives on historical events
**Ubuntu principle:** "Umuntu ngumuntu ngabantu" — a person is a person through other persons. The history of our community is not any one person's story — it is the collective story of everyone who has lived here. No single person holds the complete history. The full story emerges only when many voices contribute.
**Community benefit:** The class produces a "Community Memory Archive" — a collection of oral histories, photographs, maps, and analysis that is donated to the local community centre and school library as a permanent resource for future students and residents.

### Why Collective Knowledge Matters Here

Local history is inherently collective. No single student — and no single textbook — holds the history of this community. The history exists in the PEOPLE: in the memories of long-term residents, in the experiences of recent arrivals, in the documents held by the council, the photographs in family albums, the stories told at dinner tables. A standard history task ("Research the history of our area using library resources") produces individual reports based on secondary sources. An Ubuntu approach recognises that the COMMUNITY is the primary source — and that building the history requires every student to contribute knowledge that only they can access (their family's story, their community's perspective, their cultural lens).

### Task Design

**The collective task:** The class builds a "Community Memory Archive" — a multi-layered history of the local area told through the voices of the people who live there. The archive includes:
- Oral history interviews (students interview family members, neighbours, and community elders)
- Annotated maps (showing how the area has changed, with personal annotations from residents)
- A timeline of significant local events, constructed from MULTIPLE perspectives (the same event may appear differently from different community viewpoints)
- A reflective analysis: "What has this community gained and lost over the last 100 years, and who decides?"

**Individual contributions:** Each student conducts at least one oral history interview with a family member or community contact, contributing a unique perspective that NO other student can provide. A student whose family has lived in the area for three generations brings long-term memory. A student whose family arrived recently brings the perspective of a newcomer — what drew them here, what they found, how they were received. A student from a particular faith community brings that community's story. EVERY story is necessary because the archive is incomplete without it.

**Knowledge integration:** Students bring their individual interviews and findings to "knowledge circles" (groups of 5–6). Each circle synthesises their contributions: What themes emerge? Where do the stories agree? Where do they differ? Circles then share with the whole class, and the class constructs a collective timeline where the SAME events are annotated with multiple perspectives. For example, the construction of a new housing estate might be remembered as "progress" by one family and as "the end of the green space where we played" by another.

### Collective Knowledge Structure

**Why one person cannot complete this alone:**
1. **Each student's family/community connection is unique.** Only Amara can interview her grandmother who ran a shop on the high street for 40 years. Only Jakub can interview his parents about their experience arriving from Poland in 2008. Only Priya can access the temple community's memory of building their first permanent place of worship. The knowledge is distributed across the community, accessed through relationships, not research.

2. **The synthesis requires multiple perspectives.** The collective timeline only reveals the complexity of local history when it includes multiple, sometimes contradicting, viewpoints. A history built from one perspective is partial. The Ubuntu principle is structural here: the collective understanding is greater than any individual contribution.

3. **The archive is too large for one person.** The physical product — interviews, maps, photographs, analysis — requires many hands. But more importantly, it requires many RELATIONSHIPS. The archive's value lies in the breadth of voices it contains.

### Community Dimension

**Serving the community, not just completing an assignment:**

1. **Oral history as gift and service.** The interviews are not just data collection — they are acts of recognition. Community elders' memories are valued, preserved, and honoured. For elderly residents in the local care home, being interviewed by a young person who genuinely wants to hear their story is meaningful in itself.

2. **The archive as community resource.** The finished archive is printed/digitised and donated to the community centre and school library. A "Community Memory Evening" invites interviewees and community members to see their stories presented. This is not a school assembly — it is a community event where knowledge is returned to the community that produced it.

3. **Ongoing resource.** Future Year 7 classes can add to the archive, making it a growing, living document of collective memory. The first class starts the tradition; subsequent classes extend it.

### Individual Within Collective

**Individual learning:**
- Each student develops historical skills: conducting an oral history interview (primary source creation), analysing testimony (reliability, perspective, bias), constructing a narrative from evidence
- Each student writes a personal reflection: "What did I learn from my interview that I couldn't have learned from a textbook? What did I learn from my classmates' interviews that I couldn't have learned from my own?"

**Individual accountability within the collective:**
- Each student is accountable for their interview (did they prepare questions, conduct the interview respectfully, transcribe key passages, bring findings to the group?)
- Each student contributes a written analysis of their interview to the archive
- Assessment is dual: the quality of the individual interview AND the quality of the individual's contribution to the collective synthesis. Neither is sufficient alone.

**Assessment approach:**
| Assessed Element | Individual or Collective | What It Shows |
|---|---|---|
| Oral history interview (preparation, conduct, transcription) | Individual | Historical enquiry skills, respect for sources |
| Written analysis of interview | Individual | Analytical skills, ability to draw historical conclusions |
| Contribution to knowledge circle synthesis | Observed by teacher | Ability to listen, integrate, contribute to collective understanding |
| Quality of the collective archive section | Collective (group-assessed) | Ability to synthesise multiple perspectives into coherent history |
| Personal reflection | Individual | Metacognitive awareness of collective vs. individual learning |

### Teacher's Role

The teacher in an Ubuntu task is not a "facilitator of group work" — they are a COMMUNITY CONNECTOR and KNOWLEDGE WEAVER:

1. **Before the task:** Contact the community centre and care home to arrange interview access. Send a letter to families explaining the project and inviting participation. Identify community members who would welcome being interviewed.

2. **During the task:** Model respectful interviewing. Help students prepare culturally appropriate interview approaches (some communities may have specific protocols for speaking with elders). Visit knowledge circles to listen and ask questions that deepen the synthesis: "I notice Amara's story and Jakub's story describe the same street but with completely different feelings about it. Why might that be?"

3. **During integration:** Help students navigate the complexity of contradictory perspectives. In Ubuntu, disagreement is not a problem to be resolved but a richness to be honoured: "Both stories are true. The history of this place contains both experiences."

4. **Community evening:** Help students present their archive with respect and gratitude. Ensure interviewees are honoured — their names, their stories, their contribution to the collective knowledge.

---

## Known Limitations

1. **Ubuntu is a philosophy, not a teaching technique.** Applying Ubuntu principles to classroom task design is an interpretation — it draws on the philosophical tradition but necessarily adapts it for a specific educational context. Teachers should understand Ubuntu as a rich philosophical framework, not reduce it to "fancy group work." Reading Letseka, Ramose, and Mkabela provides depth that a task template cannot.

2. **Ubuntu exists within specific cultural contexts.** While the principles of communal knowledge, relational identity, and collective responsibility have broad applicability, Ubuntu is rooted in specific Southern African philosophical traditions. Applying it in a UK or other Western classroom requires cultural sensitivity — it should be done WITH understanding of the philosophical tradition, not as cultural appropriation. Acknowledging the origin and treating the philosophy with respect is essential.

3. **Collective knowledge building takes more time than individual learning.** The archive task above takes significantly longer than a standard local history unit. The depth and community engagement it produces are worth the time, but teachers working within tight curriculum schedules may need to adjust. Not every task needs to be collective — Ubuntu principles can inform SOME tasks while others remain individual.

4. **Individual assessment systems can conflict with collective learning.** If the school requires individual grades for every piece of work, the collective dimension may be undermined. The assessment framework above attempts to honour both individual and collective contribution, but in systems that ultimately reduce everything to individual marks, the collective dimension may be devalued. This is a systemic limitation, not a design limitation.

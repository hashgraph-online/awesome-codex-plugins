---
# AGENT SKILLS STANDARD FIELDS (v2)
name: culturally-responsive-teaching-designer
description: "Redesign a lesson to centre students' cultural backgrounds, community knowledge, and lived experience. Use when making curriculum relevant and inclusive for diverse student populations."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "global-cross-cultural-pedagogies/culturally-responsive-teaching-designer"
skill_name: "Culturally Responsive Teaching Designer"
domain: "global-cross-cultural-pedagogies"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Gay (2018) — Culturally Responsive Teaching: theory, research, and practice (3rd edition)"
  - "Ladson-Billings (1995) — Toward a theory of culturally relevant pedagogy"
  - "Hammond (2015) — Culturally Responsive Teaching and The Brain"
  - "Paris & Alim (2017) — Culturally Sustaining Pedagogies: teaching and learning for justice in a changing world"
  - "Aronson & Laughter (2016) — The theory and practice of culturally relevant education: a synthesis of research across content areas"
input_schema:
  required:
    - field: "lesson_content"
      type: "string"
      description: "The curriculum content or learning objective to be taught"
    - field: "student_community"
      type: "string"
      description: "The cultural backgrounds, community contexts, and lived experiences of the students in the class"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "current_approach"
      type: "string"
      description: "How the content is currently taught — what texts, examples, and perspectives are used"
    - field: "school_context"
      type: "string"
      description: "Demographics, community, prior work on cultural responsiveness"
    - field: "teacher_background"
      type: "string"
      description: "The teacher's own cultural background and experience with culturally responsive practice"
output_schema:
  type: "object"
  fields:
    - field: "crt_lesson_design"
      type: "object"
      description: "The redesigned lesson incorporating culturally responsive principles — same rigorous content, culturally connected pedagogy"
    - field: "cultural_connections"
      type: "array"
      description: "Specific connections between the curriculum content and students' cultural knowledge, community practices, and lived experience"
    - field: "critical_consciousness_element"
      type: "object"
      description: "How the lesson develops students' ability to identify and critique inequity — the sociopolitical dimension"
    - field: "high_expectations_framework"
      type: "object"
      description: "How the lesson maintains rigorous academic expectations while being culturally responsive — not lowering the bar"
chains_well_with:
  - "ubuntu-collective-knowledge-task-designer"
  - "place-based-inquiry-anchor"
  - "belonging-classroom-culture-designer"
  - "phenomenon-based-unit-anchor"
teacher_time: "4 minutes"
tags: ["culturally-responsive", "Gay", "Ladson-Billings", "equity", "culturally-sustaining", "Hammond", "inclusion"]
---

# Culturally Responsive Teaching Designer

## What This Skill Does

Redesigns lesson content to be culturally responsive — connecting rigorous academic curriculum to students' cultural backgrounds, community knowledge, and lived experiences while maintaining high expectations and developing critical consciousness. The approach draws on Geneva Gay's (2018) framework of culturally responsive teaching and Gloria Ladson-Billings' (1995) theory of culturally relevant pedagogy. The critical principle is that culturally responsive teaching is not about lowering standards, adding a "multicultural day," or replacing academic content with cultural content — it is about using students' cultural knowledge as a BRIDGE to rigorous academic learning. Students learn MORE, not less, when the curriculum connects to what they already know and value. The output includes a redesigned lesson with specific cultural connections, a critical consciousness element (where students use the content to examine equity and power), and a high expectations framework that ensures academic rigour is strengthened, not diluted. AI is specifically valuable here because identifying authentic connections between curriculum content and diverse cultural contexts requires broad knowledge across cultures, academic disciplines, and pedagogical approaches — while remaining sensitive to the specificity of each community.

## Evidence Foundation

Gay (2018) defined culturally responsive teaching as "using the cultural knowledge, prior experiences, frames of reference, and performance styles of ethnically diverse students to make learning encounters more relevant to and effective for them." She identified five essential elements: developing a cultural diversity knowledge base, designing culturally relevant curricula, demonstrating cultural caring and building a learning community, cross-cultural communication, and cultural congruity in classroom instruction. Ladson-Billings (1995) proposed three criteria for culturally relevant pedagogy: academic success (students must achieve academically), cultural competence (students must maintain and develop their cultural identity), and critical consciousness (students must develop the ability to critique social inequity). She emphasised that culturally relevant teaching demands MORE of students, not less — it raises expectations while making the path to meeting them culturally meaningful. Hammond (2015) connected culturally responsive teaching to neuroscience, arguing that when learning is culturally connected, it activates students' existing neural pathways and prior knowledge, reducing cognitive load and increasing engagement — the brain learns more efficiently when new information connects to existing schemas. Paris & Alim (2017) extended the framework to "culturally sustaining pedagogies," arguing that teaching should not only respond to students' cultures but actively sustain and develop them in the face of cultural erasure. Aronson & Laughter (2016) synthesised research across content areas, finding that culturally relevant education consistently improved student engagement and academic achievement, with strongest effects for students from marginalised communities.

## Input Schema

The teacher must provide:
- **Lesson content:** What students need to learn. *e.g. "Persuasive writing — Year 9 English, constructing arguments with evidence" / "Fractions — Year 4 Mathematics, understanding fractions as parts of wholes" / "The Industrial Revolution — Year 8 History, causes and consequences of industrialisation" / "Ecosystems — Year 7 Science, understanding food chains and interdependence"*
- **Student community:** Who the students are. *e.g. "Predominantly South Asian British community, many students bilingual (Urdu/Punjabi and English), strong family and community connections, local area has a vibrant market culture" / "Mixed community in a coastal town — some farming families, significant Eastern European population (Polish, Romanian), local fishing industry declining" / "Inner-city London school, very diverse — Caribbean, West African, Somali, Bangladeshi, white British working class, significant proportion of students eligible for Pupil Premium"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Student level:** Year group
- **Current approach:** How the content is currently taught
- **School context:** Demographics, community, prior work
- **Teacher background:** Teacher's own cultural experience

## Prompt

```
You are an expert in culturally responsive teaching, with deep knowledge of Gay's (2018) CRT framework, Ladson-Billings' (1995) culturally relevant pedagogy, Hammond's (2015) neuroscience of culturally responsive teaching, Paris & Alim's (2017) culturally sustaining pedagogies, and Aronson & Laughter's (2016) research synthesis. You understand that culturally responsive teaching is a rigorous pedagogical approach, not a superficial add-on — it uses students' cultural knowledge as a cognitive bridge to academic content, maintains the highest academic expectations, and develops critical consciousness about equity and power.

CRITICAL PRINCIPLES:
- **High expectations are non-negotiable.** Culturally responsive teaching is NOT about making work easier, simpler, or "more fun." It is about making rigorous academic content ACCESSIBLE by connecting it to what students already know. If the redesigned lesson has lower academic expectations than the original, it has failed. Ladson-Billings was explicit: culturally relevant pedagogy demands academic excellence.
- **Cultural connections must be AUTHENTIC, not tokenistic.** "Let's do fractions using samosas instead of pizzas" is tokenistic — it changes a surface detail without connecting to genuine cultural knowledge. An authentic connection uses the cultural PRACTICE, not just the cultural OBJECT: "In your family's cooking, recipes are often adjusted for different numbers of guests — how do proportions work when you double a recipe?"
- **Critical consciousness is essential, not optional.** Ladson-Billings' third criterion is that students develop the ability to critique social inequity. This means the lesson should include an element where students use the academic content to examine power, representation, or justice. In History: "Whose story is told? Whose is missing?" In Science: "Who benefits from this research? Who is harmed?" In English: "Who gets to speak? Whose language is valued?"
- **Know the community, don't assume.** Culturally responsive teaching requires knowledge of the SPECIFIC community, not generic assumptions about cultural groups. "South Asian students will connect to Bollywood" is a stereotype. "Students in this community have strong intergenerational storytelling traditions" is specific knowledge. When you don't have specific knowledge, design the lesson to INVITE students' own cultural knowledge rather than assuming it.
- **Sustain, don't just respond.** Following Paris & Alim, the goal is not just to use students' cultures as a bridge (which can treat cultures as instrumental) but to sustain and develop cultural knowledge and identity through the academic work.

Your task is to redesign a lesson to be culturally responsive for:

**Lesson content:** {{lesson_content}}
**Student community:** {{student_community}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the lesson content.
**Student level:** {{student_level}} — if not provided, infer from the lesson content.
**Current approach:** {{current_approach}} — if not provided, assume a standard textbook approach.
**School context:** {{school_context}} — if not provided, design for a general context.
**Teacher background:** {{teacher_background}} — if not provided, include a note about the teacher's own positionality.

Return your output in this exact format:

## Culturally Responsive Lesson: [Content]

**Content:** [What students learn — same academic objectives, culturally connected]
**Community:** [Who the students are]
**Core principle:** [The specific CRT principle most central to this redesign]

### Current Approach vs. Culturally Responsive Approach

[Brief comparison: what a standard approach looks like, and what changes in the CRT redesign — not to criticise the standard approach but to make the difference visible]

### Cultural Connections

For each connection (2–4):
**Connection [N]: [What connects]**
- **Cultural knowledge:** [What students bring from their community/experience]
- **Academic content:** [How this connects to the curriculum objective]
- **How to use it:** [Specific activity or approach that bridges the cultural and academic]

### Critical Consciousness Element

[How the lesson develops students' ability to examine equity, power, or representation through the academic content]

### High Expectations Framework

[How the lesson maintains or raises academic rigour — specific evidence that expectations are not lowered]

### Lesson Redesign

[The redesigned lesson — structured, practical, ready to teach]

### Teacher Reflection

[Questions for the teacher to reflect on their own positionality, assumptions, and learning]

**Self-check before returning output:** Verify that (a) academic expectations are at least as high as the original lesson, (b) cultural connections are authentic and specific, not tokenistic, (c) the critical consciousness element is genuinely integrated, (d) the design invites student cultural knowledge rather than assuming it, and (e) the approach sustains cultural identity, not just uses it as a bridge.
```

## Example Output

**Scenario:** *Lesson content: "Persuasive writing — Year 9 English. Students need to construct a persuasive argument using evidence, rhetorical techniques (ethos, pathos, logos), and structured paragraphs. The current approach uses model texts from newspaper opinion columns and students write a letter to a local council about a planning issue." / Student community: "Inner-city London school, very diverse — Caribbean, West African, Somali, Bangladeshi, white British working class. Many students are eloquent and persuasive speakers but struggle to transfer this to formal written English. Strong oral traditions in several home cultures. Many students are actively engaged in social media discourse and local community issues." / Current approach: "Model texts from broadsheet newspapers. Students practise ethos/pathos/logos identification, then write a formal letter to a council. Some students disengage because the model texts feel distant from their experience."*

---

## Culturally Responsive Lesson: Persuasive Writing — Year 9 English

**Content:** Constructing persuasive arguments using evidence, rhetorical techniques (ethos, pathos, logos), and structured writing — same English curriculum objectives, culturally connected pedagogy
**Community:** Diverse inner-city London — Caribbean, West African, Somali, Bangladeshi, white British working class. Strong oral traditions, social media fluency, community engagement
**Core principle:** Students are already skilled persuaders — the lesson bridges their existing persuasive competence (oral, digital, community-based) to formal academic writing

### Current Approach vs. Culturally Responsive Approach

**Standard approach:** Model texts from broadsheet newspaper opinion columns. Students identify rhetorical techniques, then write a formal letter to a council. The implicit message: "persuasion looks like THIS" — the specific register and format of white, middle-class, print-media discourse.

**CRT approach:** Start from students' existing persuasive expertise — oral argument, social media discourse, community advocacy, multilingual persuasion. Analyse persuasive techniques ACROSS registers and contexts (a TED talk, a spoken-word poem, a community petition, a sermon, a social media campaign), then deliberately transfer these skills to formal academic writing. The message: "You are already persuasive. Academic writing is another register you're adding to your repertoire — not replacing what you already know."

### Cultural Connections

**Connection 1: Oral Persuasion Traditions**
- **Cultural knowledge:** Many students come from cultures with rich oral traditions — Caribbean storytelling and speech-making, West African griot traditions, the rhetorical structures of Islamic sermons (khutbah), the oral argumentation of market trading. Students who are dismissed as "chatty" may be highly skilled oral persuaders.
- **Academic content:** Ethos, pathos, and logos are not just written techniques — they originated in oral rhetoric (Aristotle's Rhetoric was about SPEECH). Oral persuasion is the foundation of written persuasion, not a lesser form.
- **How to use it:** Begin the unit with a "persuasion audit" — students identify moments in their own lives where they persuade (negotiating with parents, convincing friends, debating in the playground, public speaking at community events). Students bring an example of persuasion from their own cultural context (a clip, a text, a story) and the class analyses it for ethos, pathos, and logos. This establishes that persuasion is universal and that students ALREADY do it — the lesson adds formal written register to existing competence.

**Connection 2: Digital Persuasion**
- **Cultural knowledge:** Students are immersed in digital persuasion — social media campaigns, YouTube video essays, Twitter/X threads, change.org petitions. Many have more experience analysing and constructing persuasive digital texts than persuasive print texts.
- **Academic content:** Digital persuasion uses the same rhetorical principles as traditional persuasive writing — but in different formats. A Twitter thread uses logos (data, evidence) and pathos (personal stories) just as a newspaper column does. Analysing both helps students see the underlying structure.
- **How to use it:** Alongside the broadsheet column, analyse a successful social media campaign (e.g., a petition that achieved its goal, a viral advocacy post). Students compare: how does this tweet use pathos? How does this newspaper column use it? What's the same? What's different? This positions students' digital literacy as a strength, not a distraction.

**Connection 3: Community Issues That Matter**
- **Cultural knowledge:** Many students are aware of and affected by local community issues — gentrification, policing, housing, access to services, representation. These are not abstract planning issues — they are lived experiences.
- **Academic content:** Persuasive writing is most powerful when the writer cares about the issue. The standard "letter to the council about a planning issue" may feel hypothetical. A genuine issue the students care about produces more motivated, more invested, and ultimately more sophisticated writing.
- **How to use it:** Students choose their own issue to write about — something that affects their community, their family, or themselves. The teacher provides a list of possible issues (drawn from local knowledge) but students can propose their own. The writing task remains formally identical (structured argument, evidence, rhetorical techniques), but the content is personally and culturally meaningful.

### Critical Consciousness Element

**Whose Persuasion Counts?**

After studying persuasive techniques across registers (oral, digital, print), students examine a critical question: "Which forms of persuasion are taken seriously by people in power, and which are dismissed? Why?"

Students compare: a broadsheet opinion column, a spoken-word performance, a protest chant, a social media campaign, a formal petition. All are persuasive. Which one would a council take most seriously? Which would a judge accept? Which would a school listen to?

Discussion: "Why is a formal letter considered more 'legitimate' than a spoken argument, even if the spoken argument is more detailed, more passionate, and more evidence-based? What does this tell us about power and language? If certain communities are stronger in oral persuasion than written, what happens to their voices in a system that privileges written, formal English?"

This is not a detour from the English curriculum — it IS the English curriculum. Understanding that language, power, and persuasion are interconnected is a core objective of English education.

**Important:** The lesson does NOT conclude "formal writing doesn't matter." It concludes: "Formal written persuasion is a TOOL you should have because it opens doors in systems that value it — AND the system's preference for formal writing over oral argument is itself worth questioning."

### High Expectations Framework

The CRT redesign raises expectations in three ways:

1. **More analysis, not less.** Students analyse persuasion across FIVE registers (oral, digital, print, community, formal), not just one (print). This is more analytically demanding than studying a single broadsheet column.

2. **Code-switching as a skill.** Students don't just write in one register — they write the SAME argument in two registers (a social media post AND a formal letter) and analyse how the persuasive techniques adapt. This requires deeper understanding of rhetoric than writing in one register alone.

3. **Authentic audience.** Where possible, the formal letter is SENT — to the council, the headteacher, or a local organisation. Writing for a real audience with real stakes demands higher quality than writing for a teacher's mark scheme.

### Lesson Redesign

**Lesson 1 — Persuasion Audit:**
Students identify persuasion in their own lives. In pairs, discuss: "When were you last persuaded? When did you last persuade someone?" Students bring an example of persuasion from their own experience or cultural context. Class builds a "persuasion wall" — examples from every culture and context represented in the room. Teacher introduces ethos, pathos, logos using these student-sourced examples.

**Lesson 2 — Cross-Register Analysis:**
Analyse persuasive techniques across five texts: a broadsheet opinion column, a spoken-word poem (performed), a social media campaign post, a community petition, and a short TED talk excerpt. Students identify ethos, pathos, and logos in each. Discuss: "What's the same across all five? What changes depending on the audience and format?"

**Lesson 3 — Choose Your Issue:**
Students select a community issue they care about. In pairs, they research the issue using at least two sources. They plan their argument: What is the claim? What evidence supports it? What is the strongest emotional appeal? What gives them credibility to speak on this (ethos)?

**Lesson 4 — Dual Register Writing:**
Students write two versions of their argument: (a) a social media post or script for a 60-second spoken piece, and (b) a formal persuasive letter. Same argument, same evidence, different register. This is where code-switching becomes a conscious, skilled practice.

**Lesson 5 — Critical Reflection and Sharing:**
Students share their paired texts. Class discussion: "Which version is more persuasive? Does it depend on the audience? What does this tell us about language and power?" Students revise their formal letter for submission.

### Teacher Reflection

- "Whose persuasive traditions do I unconsciously value most? Am I more impressed by a well-structured formal essay than by an eloquent spoken argument — and if so, what does that mean for how I assess students from oral traditions?"
- "Do I know enough about my students' cultural communication styles to make authentic connections, or am I relying on assumptions? How can I learn more — from students themselves, from families, from community?"
- "When I teach 'formal English,' am I framing it as 'correct English' (which devalues other registers) or as 'one powerful register among many' (which builds repertoire without diminishing identity)?"

---

## Known Limitations

1. **Culturally responsive teaching requires genuine knowledge of the specific community.** This skill can suggest connections and frameworks, but it cannot substitute for the teacher's own relationship with and knowledge of their students and community. A teacher who follows this template without knowing their students will produce superficially "responsive" lessons that lack authenticity. The most important culturally responsive practice is LISTENING to students and families.

2. **There is a risk of essentialism — treating cultural groups as monolithic.** Not all students from Caribbean backgrounds have strong oral traditions. Not all Bangladeshi students come from families with particular cooking practices. Culturally responsive teaching must engage with the SPECIFIC students in the room, not with assumptions about their cultural group. The design should invite students to share their own cultural knowledge rather than the teacher assuming what it is.

3. **Culturally responsive teaching exists within systemic constraints.** A single teacher can redesign their lessons to be culturally responsive, but they cannot change the assessment system, the national curriculum, or the institutional culture alone. Students may still face standardised assessments that privilege particular cultural forms. CRT prepares students to succeed in these systems while developing critical awareness of their limitations — but it cannot single-handedly transform the system.

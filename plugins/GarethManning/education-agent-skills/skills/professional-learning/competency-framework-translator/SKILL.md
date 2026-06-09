---
# AGENT SKILLS STANDARD FIELDS (v2)
name: competency-framework-translator
description: "Translate an external competency framework like DigComp, GreenComp, or ISTE into classroom-ready activities. Use when implementing framework standards in specific teaching contexts."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "professional-learning/competency-framework-translator"
skill_name: "Competency Framework Translator"
domain: "professional-learning"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Wiggins & McTighe (2005) — Understanding by Design: translating standards into classroom practice"
  - "Marzano & Kendall (2007) — The New Taxonomy of Educational Objectives: operationalising competencies"
  - "European Commission (2022) — DigComp 2.2: the Digital Competence Framework for Citizens"
  - "Bianchi, Pisiotis & Cabrera (2022) — GreenComp: the European sustainability competence framework"
  - "UNESCO (2023) — Guidance for generative AI in education and research"
input_schema:
  required:
    - field: "framework_reference"
      type: "string"
      description: "The external competency framework to translate — name, specific competency area, and level/descriptor to work with"
    - field: "target_context"
      type: "string"
      description: "The teaching context — subject, year group, and what the teacher wants students to DO with this competency"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "framework_text"
      type: "string"
      description: "The actual text of the competency descriptor to translate — paste the official wording"
    - field: "integration_approach"
      type: "string"
      description: "Whether the competency will be taught standalone, embedded in subject content, or assessed as a cross-curricular outcome"
    - field: "assessment_needs"
      type: "string"
      description: "How the teacher needs to assess the competency — formative, summative, portfolio, observation"
output_schema:
  type: "object"
  fields:
    - field: "translated_competency"
      type: "object"
      description: "The competency rewritten as specific, observable indicators appropriate for the target context"
    - field: "progression_levels"
      type: "array"
      description: "3–4 levels showing what the competency looks like at developing, competent, and advanced stages"
    - field: "classroom_tasks"
      type: "array"
      description: "Specific tasks or activities that require students to demonstrate the competency"
    - field: "assessment_criteria"
      type: "object"
      description: "How to assess whether a student has developed the competency — observable indicators at each level"
chains_well_with:
  - "competency-unpacker"
  - "criterion-referenced-rubric-generator"
  - "backwards-design-unit-planner"
  - "project-brief-designer"
  - "curriculum-knowledge-architecture-designer"
  - "scope-and-sequence-designer"
teacher_time: "4 minutes"
tags: ["competency-frameworks", "DigComp", "GreenComp", "ISTE", "UNESCO-AI", "translation", "observable-indicators"]
---

# Competency Framework Translator

## What This Skill Does

Takes any external competency framework — DigComp (digital competence), GreenComp (sustainability), ISTE Standards, UNESCO AI competency framework, national curriculum frameworks, or any other competency-based system — and translates its abstract descriptors into classroom-ready observable indicators, progression levels, teaching tasks, and assessment criteria for a specific subject and year group. The critical problem this solves is that competency frameworks are written for policy audiences, not for teachers: "Critically evaluates the credibility and reliability of sources of data, information and digital content" (DigComp 2.2) is meaningful to a policy analyst but tells a Year 8 History teacher nothing about what to teach, what tasks to set, or how to assess. The output is a translation: the same competency, expressed as specific things students can DO at different levels, with tasks that make the competency visible and criteria that make it assessable. AI is specifically valuable here because this translation requires understanding both the framework's intent (what the competency is really asking for) and the classroom reality (what students at this age can be expected to do, in this subject, with these resources).

## Evidence Foundation

Wiggins & McTighe (2005) established the principle that standards and competencies must be "unpacked" into observable indicators before they can be taught and assessed. A competency statement is a destination; the teacher needs a map showing what the journey looks like at each stage. Without unpacking, teachers either teach to the abstract wording (which students can't understand) or interpret the competency so broadly that it loses its meaning. Marzano & Kendall (2007) provided a taxonomy for operationalising competencies — moving from retrieval (can the student recall the knowledge?) through comprehension (can they explain it?) to analysis (can they compare, classify, evaluate?) to knowledge utilisation (can they apply it in a new context?). This taxonomy provides the backbone for progression levels. The DigComp 2.2 framework (European Commission, 2022) is a worked example of a competency framework that explicitly acknowledges the need for contextualisation — it provides 8 proficiency levels but notes that these must be adapted for specific educational contexts. GreenComp (Bianchi et al., 2022) takes a similar approach, defining sustainability competencies at a high level but requiring schools to translate them into subject-specific learning. UNESCO's (2023) guidance on AI in education introduces competencies for AI literacy that are new to most curriculum frameworks and urgently need classroom-level translation. In all cases, the gap between framework and classroom is the problem this skill addresses.

## Input Schema

The teacher must provide:
- **Framework reference:** Which framework and which competency. *e.g. "DigComp 2.2 — Competency 1.2: Evaluating data, information and digital content" / "GreenComp — Competency area: Embracing complexity in sustainability" / "ISTE Standards for Students — Computational Thinker" / "UNESCO AI competency — Understanding AI ethics and responsible use"*
- **Target context:** Where this competency will be taught. *e.g. "Year 9 History — students evaluating online sources about the causes of WW1" / "Year 7 Geography — students understanding the interconnected causes of climate change" / "Year 10 Computer Science — students understanding bias in AI systems"*

Optional (injected by context engine if available):
- **Student level:** Year group
- **Subject area:** The curriculum subject
- **Framework text:** The official competency wording
- **Integration approach:** Standalone, embedded, or cross-curricular
- **Assessment needs:** How the teacher needs to assess

## Prompt

```
You are an expert in competency frameworks and curriculum translation, with deep knowledge of Wiggins & McTighe's (2005) principles for unpacking standards, Marzano & Kendall's (2007) taxonomy for operationalising competencies, and specific familiarity with major competency frameworks including DigComp 2.2, GreenComp, ISTE Standards, UNESCO AI competency frameworks, and national curriculum systems. You understand that competency frameworks serve a policy purpose but require TRANSLATION for classroom use — and that the quality of this translation determines whether the competency is meaningfully developed or merely name-checked.

CRITICAL PRINCIPLES:
- **Observable indicators, not abstract statements.** "Critically evaluates digital sources" is abstract. "Given two websites about the same topic, identifies which is more credible by checking the author's credentials, the publication date, and whether claims are supported by evidence" is observable. Every translated indicator must describe something a teacher can SEE a student doing.
- **Progression, not binary.** Competencies develop over time. The translation must show what the competency looks like at different levels — not just "has it" or "doesn't have it" but "developing → competent → advanced." Each level must be qualitatively distinct (not just "more of the same").
- **Subject-specific, not generic.** "Evaluating sources" looks different in History (checking provenance, bias, context) than in Science (checking methodology, peer review, sample size) than in Media Studies (checking ownership, funding, audience). The translation must be specific to the stated subject and context.
- **Tasks that REQUIRE the competency.** The best way to assess a competency is through tasks that cannot be completed without demonstrating it. Design tasks where the competency is not optional but essential.
- **Honest about what the framework actually asks for.** Some framework descriptors are vague or contradictory. Where this is the case, acknowledge the ambiguity and provide a clear interpretation that serves the teacher's context.

Your task is to translate:

**Framework reference:** {{framework_reference}}
**Target context:** {{target_context}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, infer from the target context.
**Subject area:** {{subject_area}} — if not provided, infer from the target context.
**Framework text:** {{framework_text}} — if not provided, use your knowledge of the framework. If you are uncertain about the exact wording, state this and provide your best interpretation.
**Integration approach:** {{integration_approach}} — if not provided, design for embedding in subject content (the most sustainable approach).
**Assessment needs:** {{assessment_needs}} — if not provided, design for formative assessment within lessons.

Return your output in this exact format:

## Competency Translation: [Framework — Competency Name]

**Framework:** [Which framework]
**Competency:** [Official name and reference]
**Translated for:** [Subject, year group, context]

### Original Framework Wording

[The official competency descriptor as written in the framework — or your best interpretation if not provided]

### Translation: What This Means in [Subject] for [Year Group]

[Plain-English translation: what this competency actually requires students to do in this specific subject and age group]

### Observable Indicators

For each level (3–4 levels):
**Level [N]: [Label — Emerging / Developing / Competent / Extending]**
- **The student can:** [Specific, observable actions — what you'd SEE them doing]
- **Evidence looks like:** [What their work, discussion, or behaviour would show]
- **The student cannot yet:** [What distinguishes this level from the next]

### Classroom Tasks

For each task (2–3):
**Task [N]: [Name]**
- **What students do:** [The task]
- **Why this task requires the competency:** [How it makes the competency visible]
- **What to look for:** [Observable indicators that the competency is being demonstrated]

### Assessment Criteria

[How to assess whether students are developing the competency — linked to the observable indicators at each level]

### Integration Notes

[How to embed this competency into existing subject teaching without creating a separate "competency lesson"]

### Framework Fidelity Check

[How well this translation represents the original framework intention — any interpretive choices made and why]

**Self-check before returning output:** Verify that (a) every indicator is observable — you can see or hear it, (b) progression levels are qualitatively distinct, (c) the translation is specific to the stated subject and year group, (d) tasks require the competency (it's not optional), (e) the translation is honest about any ambiguity in the original framework, and (f) integration is practical — embeddable in existing teaching.
```

## Example Output

**Scenario:** *Framework reference: "DigComp 2.2 — Competency 1.2: Evaluating data, information and digital content. At proficiency level 3 (intermediate): 'Can compare and critically evaluate the credibility and reliability of specific sources of data, information and digital content'" / Target context: "Year 9 History — students are researching the causes of WW1 using online sources. The teacher wants students to evaluate the credibility of the websites and sources they find, rather than simply copying from the first Google result." / Subject area: "History" / Integration approach: "Embedded in the WW1 research unit — not a standalone digital literacy lesson"*

---

## Competency Translation: DigComp 2.2 — Evaluating Digital Sources

**Framework:** DigComp 2.2 (European Digital Competence Framework)
**Competency:** 1.2 — Evaluating data, information and digital content (Proficiency Level 3)
**Translated for:** Year 9 History — evaluating online sources about the causes of WW1

### Original Framework Wording

"At proficiency level 3 (intermediate): Can compare and critically evaluate the credibility and reliability of specific sources of data, information and digital content." (European Commission, 2022)

### Translation: What This Means in History for Year 9

In Year 9 History, this means: when students research a historical topic online, they can evaluate whether a website or digital source is credible and reliable for historical purposes — checking who wrote it (and whether they have expertise), when it was published (and whether it's current), what evidence it cites (and whether the claims are supported), and whether it has a bias or purpose that affects its reliability. This is not a generic digital literacy skill — it is SOURCE EVALUATION as historians practise it, applied to digital sources. Historians ask: Who produced this? Why? What evidence supports it? Does it agree or disagree with other sources? Students should apply the same questions to websites.

### Observable Indicators

**Level 1: Emerging — Recognises that source credibility matters**
- **The student can:** Distinguish between different types of online source (website, blog, news article, social media post) and understand that not all sources are equally reliable. Can identify whether a source has a named author.
- **Evidence looks like:** When asked "Where did you find this information?", the student can name the source and its type. May note "I'm not sure if this is reliable" but cannot yet explain why.
- **The student cannot yet:** Evaluate credibility using specific criteria, or give reasons beyond "it looks trustworthy" or "it was the first result."

**Level 2: Developing — Identifies basic credibility markers**
- **The student can:** Check whether a website has a named author, identify whether the source is a personal blog vs. an educational site vs. a news article, and notice when a source makes claims without evidence.
- **Evidence looks like:** The student's research notes include the source URL AND the author/organisation name. When asked "Is this a good source?", the student can give at least one reason ("It's from a university" or "I can't find who wrote it").
- **The student cannot yet:** Compare two sources to evaluate which is more reliable, or identify subtle bias (e.g., a nationalist perspective on the causes of WW1).

**Level 3: Competent — Evaluates and compares sources**
- **The student can:** Compare two or more sources on the same topic and identify which is more credible, giving specific reasons. Can identify basic bias ("This website is run by a German heritage organisation — they might present the German perspective differently from a British source"). Can check whether claims are supported by evidence cited in the source.
- **Evidence looks like:** The student's research notes evaluate each source: "I'm using this source because [reason] but not this one because [reason]." In their written work, the student selects sources based on credibility, not just convenience (not just the first Google result).
- **The student cannot yet:** Recognise sophisticated bias (e.g., how source selection itself shapes a narrative), or evaluate the methodology behind the source's claims.

**Level 4: Extending — Critically evaluates credibility, bias, and purpose**
- **The student can:** Analyse the purpose and audience of a digital source ("This was written to commemorate the centenary of WW1 for a British audience — its purpose is memorial, not analytical, which affects what it includes and excludes"). Can cross-reference claims between multiple sources to check consistency. Can articulate why even credible sources may be incomplete or biased.
- **Evidence looks like:** The student's research explicitly addresses reliability: "Source A (BBC History) and Source B (Wikipedia) both state that the assassination of Archduke Franz Ferdinand triggered WW1, but Source C (a journal article) argues that the assassination was a catalyst, not a cause. Source C is more analytically useful because it distinguishes between triggers and causes."
- **The student cannot yet:** Evaluate primary sources in digital archives with full historiographical awareness (this is A-level/university level).

### Classroom Tasks

**Task 1: Source Showdown**
- **What students do:** Give students 4 websites about the causes of WW1 — one is a well-sourced educational site (e.g., BBC History), one is a personal blog with no citations, one is a nationalist heritage site with a clear perspective, and one is a Wikipedia article. Students must rank the 4 sources from most to least reliable FOR THEIR HISTORY ESSAY, and justify each ranking with specific evidence from the source.
- **Why this task requires the competency:** Students cannot complete the ranking without evaluating credibility, checking evidence, and comparing sources. Copying from any single source won't answer the question — the task requires evaluation.
- **What to look for:** Do students cite specific features of the source (author credentials, evidence, bias) or give vague reasons ("It looks professional")? Do they distinguish between different TYPES of unreliability (no evidence vs. biased evidence vs. outdated)?

**Task 2: The Research Log**
- **What students do:** During independent research on the causes of WW1, students complete a research log for every source they use. The log has four columns: Source (URL + author), Credibility Check (why I trust or don't trust this source), What I'm Using From It (specific information), and Limitations (what this source doesn't tell me or might get wrong).
- **Why this task requires the competency:** The research log makes source evaluation VISIBLE. A student who copies from the first Google result without evaluation will have an empty Credibility Check column — the gap is immediately visible to the teacher.
- **What to look for:** Are students filling in the Credibility Check column with specific reasons, or leaving it blank / writing "good source"? Are they noting limitations?

**Task 3: Fact-Check Challenge**
- **What students do:** Give students a short passage about WW1 from an unreliable source (contains 3 factual errors and 2 biased interpretations mixed with accurate information). Students must identify: what is accurate, what is inaccurate, and what is opinion presented as fact. They must use at least one other source to verify each claim.
- **Why this task requires the competency:** This task requires students to critically evaluate specific claims, cross-reference with other sources, and distinguish fact from interpretation — the core of the DigComp competency applied to historical content.
- **What to look for:** Can students identify errors and bias, or do they accept the passage uncritically? Do they cross-reference (using another source to check) or rely on their own assumptions?

### Assessment Criteria

| Criterion | Emerging | Developing | Competent | Extending |
|---|---|---|---|---|
| Identifies source characteristics | Distinguishes source types (blog, news, academic) | Names the source type and checks for author/evidence | Evaluates credibility based on author, evidence, and purpose | Analyses how purpose and audience shape the source's content |
| Compares sources | Recognises that sources may differ | Notes that different sources say different things | Ranks sources by reliability with specific reasons | Cross-references claims across multiple sources to identify consensus and disagreement |
| Detects bias | Understands that sources can be biased | Recognises obvious bias ("This is one-sided") | Identifies how bias affects specific claims ("This source blames Germany because...") | Explains how even balanced sources involve selection and framing |
| Uses evaluation in own work | Includes sources but does not evaluate them | Cites sources with basic credibility notes | Selects sources based on credibility and notes limitations | Integrates source evaluation into their argument ("According to the more reliable Source A...") |

### Integration Notes

This competency should NOT be taught as a standalone "digital literacy" lesson disconnected from History. Instead:
- **Lesson 1 of the WW1 unit:** Introduce the Source Showdown task as the class researches causes. Frame it as "historians' work" — evaluating sources is what historians DO.
- **Throughout the unit:** Require the Research Log for every independent research task. Check it as you circulate — a 30-second glance at the Credibility Check column tells you whether the student is evaluating or just copying.
- **End of unit:** The Fact-Check Challenge serves as both a historical knowledge check and a digital competency assessment.

The competency is developed THROUGH the subject content, not alongside it. Students learn to evaluate digital sources because they need to — they're researching WW1 and need reliable information. The digital competency and the historical skill reinforce each other.

### Framework Fidelity Check

The DigComp 2.2 descriptor at Level 3 ("can compare and critically evaluate the credibility and reliability of specific sources") is faithfully represented in this translation, with the following contextualisation:
- **"Credibility"** is interpreted through a History lens: author expertise, evidence citation, bias, purpose. In a Science context, credibility would emphasise methodology and peer review instead.
- **"Reliability"** is interpreted as consistency across sources and the strength of evidence — not just whether the source "looks trustworthy."
- **"Digital content"** is interpreted as websites and online resources encountered during research, not social media or messaging (which would be a different translation for a Media Studies context).

The translation is faithful to the DigComp intent but specific to the History classroom. A different subject would produce a different translation of the same competency.

---

## Known Limitations

1. **Competency frameworks are updated regularly.** DigComp has moved from 1.0 to 2.2; GreenComp is relatively new; UNESCO AI guidance will evolve. The translation is based on the current framework version — teachers should check that they're working with the most recent version and adapt if descriptors have changed.

2. **Some frameworks are deliberately vague.** Framework descriptors are written for multiple contexts (primary, secondary, vocational, adult education) and multiple countries. This generality is a feature, not a bug — but it means that translation inevitably involves interpretation. This skill is transparent about interpretive choices, but teachers should verify that the translation aligns with their school's or system's interpretation of the framework.

3. **Competency frameworks are not curricula.** A competency framework describes what students should be able to do but not how to teach it, when to teach it, or how to assess it. The translation provides these elements, but they are pedagogical decisions informed by the framework, not dictated by it. Teachers should adapt the tasks and criteria to fit their specific curriculum and students.

4. **Not all frameworks are equally well-evidenced.** DigComp and GreenComp are policy frameworks developed through stakeholder consultation, not through educational research trials. The competencies they describe are reasonable and important, but their specific descriptors and proficiency levels are not empirically validated in the way that, say, Hattie's effect sizes are. Teachers should treat framework descriptors as useful organising structures, not as scientifically established learning progressions.

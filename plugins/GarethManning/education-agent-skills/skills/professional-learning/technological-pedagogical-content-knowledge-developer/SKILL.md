---
# AGENT SKILLS STANDARD FIELDS (v2)
name: technological-pedagogical-content-knowledge-developer
description: "Develop TPACK for integrating a specific technology or AI tool into subject teaching with pedagogical alignment. Use when adopting new ed-tech, reviewing AI tools, or planning technology integration."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "professional-learning/technological-pedagogical-content-knowledge-developer"
skill_name: "Technological Pedagogical Content Knowledge Developer"
domain: "professional-learning"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Mishra & Koehler (2006) — Technological pedagogical content knowledge: A framework for teacher knowledge"
  - "Koehler & Mishra (2009) — What is technological pedagogical content knowledge?"
  - "Voogt et al. (2013) — Technological pedagogical content knowledge — a review of the literature"
  - "Chai, Koh & Tsai (2013) — A review of the quantitative measures of TPACK"
  - "Angeli & Valanides (2009) — Epistemological and methodological issues for the conceptualization of TPACK"
  - "Shulman (1986) — Those who understand: Knowledge growth in teaching — PCK foundation"
  - "Selwyn (2016) — Is Technology Good for Education? Critical perspective on ed-tech claims"
  - "Hattie (2009) — Visible Learning: technology effects are highly variable depending on implementation"
  - "Luckin et al. (2016) — Intelligence Unleashed: AI in education — opportunities and design requirements"
  - "Timperley et al. (2007) — Teacher Professional Learning and Development: content-specific PD"
input_schema:
  required:
    - field: "teaching_context"
      type: "string"
      description: "What the teacher is teaching: subject, topic, unit"
    - field: "technology_in_use"
      type: "string"
      description: "The specific technology or AI tool the teacher is integrating or considering"
    - field: "learner_stage"
      type: "string"
      description: "Age range or year group"
    - field: "teacher_background"
      type: "string"
      description: "Subject training, teaching experience, and technology confidence"
  optional:
    - field: "pck_output"
      type: "string"
      description: "From pedagogical-content-knowledge-developer if already run; TPACK builds on PCK and is more useful when PCK gaps are already identified"
    - field: "intended_learning_outcome"
      type: "string"
      description: "What the technology is supposed to help students achieve"
    - field: "school_technology_context"
      type: "string"
      description: "Devices available, platform constraints, student data privacy requirements"
output_schema:
  type: "object"
  fields:
    - field: "tpack_diagnosis"
      type: "object"
      description: "Assessment of the teacher's TPACK gaps across the three intersections: technology-content (does the teacher understand how this technology represents or distorts this content?), technology-pedagogy (does the teacher know how to use this technology to support good teaching moves?), and the full TPACK intersection (can the teacher make real-time decisions about when to use, adapt, or abandon the technology based on what students are doing?)"
    - field: "technology_content_knowledge"
      type: "object"
      description: "How this specific technology represents, models, or transforms this specific content: what it makes visible that is otherwise hard to see, what it obscures or distorts, and whether the representation is epistemically accurate for this domain"
    - field: "technology_pedagogy_alignment"
      type: "object"
      description: "Which pedagogical moves this technology supports well, which it undermines, and which are neutral; includes specific guidance on when to use it, when to step back to non-technological approaches, and what the technology cannot do that the teacher must do"
    - field: "ai_specific_guidance"
      type: "object"
      description: "If the technology is an AI tool: specific guidance on what the AI does well for this content and learner stage, where AI outputs require teacher verification, how to develop student critical evaluation of AI, and the autonomy-dependency risk for this topic"
    - field: "tpack_development_plan"
      type: "object"
      description: "Sequenced development plan building from existing PCK; what the teacher needs to learn about the technology, practise with the technology, and observe in student responses to the technology"
    - field: "ethical_and_equity_considerations"
      type: "object"
      description: "Data privacy implications for this learner stage, equity risks if technology access is uneven, and any content-specific ethical issues with this technology in this context"
chains_well_with:
  - "pedagogical-content-knowledge-developer"
  - "curriculum-knowledge-architecture-designer"
  - "critical-thinking-task-designer"
  - "lesson-observation-protocol-designer"
teacher_time: "10 minutes"
tags: ["TPACK", "technology-integration", "AI-in-education", "pedagogical-content-knowledge", "Mishra-Koehler", "professional-learning", "ed-tech"]
---

# Technological Pedagogical Content Knowledge Developer

## What This Skill Does

Takes a description of what a teacher is teaching, the technology they are integrating, and their background, then diagnoses their technological pedagogical content knowledge gaps and produces a development plan. TPACK (Mishra & Koehler, 2006) extends Shulman's PCK framework to account for technology: just as knowing a subject and knowing how to teach it are distinct capabilities, knowing how a technology works and knowing how to use it to teach a specific subject well to specific students is a third, distinct capability. A teacher who is technically proficient with an AI tool may still not know whether that tool's representation of historical causation is epistemically accurate, or whether using it for student writing undermines the metacognitive development the writing task was designed to produce. This skill addresses those intersections. It is most powerful when run after the pedagogical-content-knowledge-developer — TPACK gaps are harder to diagnose without first understanding PCK gaps, because the technology question is always "does this tool help or hinder the teaching of this specific content to these specific students?" and that question requires PCK to answer. The skill includes specific guidance for AI tools, which present distinct challenges: AI outputs may be fluent but epistemically incorrect, AI assistance may create dependency rather than capability, and students using AI for thinking tasks may perform the task without doing the thinking the task was designed to develop. These are TPACK questions, not just technology questions, and they require the teacher to understand both the content and the pedagogy to navigate well.

## Evidence Foundation

Mishra & Koehler (2006) proposed TPACK as a framework for understanding the knowledge teachers need to integrate technology effectively, building on Shulman's (1986) PCK. They identified seven knowledge domains at the intersections of content (C), pedagogy (P), and technology (T): content knowledge, pedagogical knowledge, technological knowledge, and the four intersections — PCK, TCK (technological content knowledge), TPK (technological pedagogical knowledge), and the full TPACK (the intersection of all three). The critical insight is that technology integration is not a generic skill: the right use of a simulation for teaching photosynthesis requires different knowledge than the right use of a simulation for teaching market dynamics, even if the simulation platform is identical. Technology integration that is content-blind — "use this tool for engagement" — is pedagogically empty.

Koehler & Mishra (2009) extended the framework, arguing that effective technology integration requires understanding the "wicked problem" of how technology, content, and pedagogy interact in specific contexts. There are no general solutions — only specific solutions for specific intersections. A teacher who has learned to use an AI tool effectively for writing scaffolding in English does not automatically know how to use the same tool for scientific explanation in biology, because the content demands, the epistemic standards, and the learning goals are different.

Voogt et al.'s (2013) review found consistent evidence that TPACK is a distinct and teachable construct, but noted significant variation in how it is measured and developed across studies. Chai, Koh & Tsai (2013) reviewed quantitative TPACK measures and found that self-report instruments often overestimate teacher TPACK — teachers rate their technology integration confidence higher than their actual ability to make content-specific technology decisions in practice. This suggests that TPACK development requires practice-based feedback, not just self-assessment.

Angeli & Valanides (2009) argued that TPACK should be treated as a unique body of knowledge that is more than the sum of its parts — not just the intersection of three separate domains but a qualitatively distinct form of knowing that emerges from experience with specific technology-content-pedagogy combinations. This reinforces the need for topic-specific TPACK development rather than generic technology training.

Hattie's (2009) meta-analysis found that technology in education has highly variable effects — effect sizes range from strongly negative to strongly positive depending on implementation. The meta-analytic average (d = 0.31) is modest, but the variation is enormous. This is precisely the TPACK insight: it is not the technology that determines outcomes but the teacher's knowledge of how to deploy it for specific content with specific students. A technology used well for the right content at the right time produces strong learning gains; the same technology used without TPACK may produce no gain or active harm.

Selwyn (2016) provides a necessary critical counterweight to technology enthusiasm in education. Many claims about educational technology are made by vendors rather than researchers, and the evidence base for specific tools is often thin or conflicted. Selwyn argues that the burden of proof that a technology improves learning for this content with these students should sit with the teacher using it, not with the marketing literature. This critical stance is part of TPACK: the disposition to ask "does this actually help my students learn this specific content?" rather than assuming technology is beneficial by default.

For AI tools specifically, Luckin et al. (2016) identified teacher understanding of AI capabilities and limitations as a prerequisite for effective use — a teacher who cannot evaluate whether an AI output is accurate for their domain cannot use AI tools safely or effectively in that domain. This is the technology-content knowledge intersection for AI: the teacher must know enough about both the AI and the content to evaluate whether the AI's representation of the content is trustworthy.

Timperley et al. (2007) found that effective professional development for technology integration, like all effective PD, must be content-specific and practice-connected. Generic technology training ("here is how this tool works") does not produce TPACK. Content-specific technology development ("here is how this tool represents this content, and here is where it gets it wrong") does.

## Input Schema

The educator must provide:
- **Teaching context:** What the teacher is teaching. *e.g. "Year 9 History — causes of World War One, including source analysis and historical argumentation" / "Year 10 Biology — natural selection and evolution" / "Year 8 Ethics — moral reasoning and the trolley problem"*
- **Technology in use:** The specific technology or AI tool. *e.g. "Claude (AI assistant) for student source analysis and argument construction" / "PhET simulations for modelling natural selection" / "Google Docs with AI writing suggestions for essay drafting"*
- **Learner stage:** Age range or year group. *e.g. "14-15 years" / "Year 9" / "Band D"*
- **Teacher background:** Subject training, experience, and technology confidence. *e.g. "Experienced history teacher, moderate technology confidence, first time using AI tools in the classroom" / "Primary generalist, high technology confidence, limited science content knowledge"*

Optional (injected by context engine if available):
- **PCK output:** From pedagogical-content-knowledge-developer if already run
- **Intended learning outcome:** What the technology is supposed to help students achieve
- **School technology context:** Devices, platforms, privacy constraints

## Prompt

```
You are an expert in technological pedagogical content knowledge development, drawing on Mishra & Koehler's (2006, 2009) TPACK framework, Shulman's (1986) foundational PCK work, Voogt et al.'s (2013) review, Angeli & Valanides's (2009) conceptualisation of TPACK as a unique knowledge domain, Hattie's (2009) evidence on technology effects, Selwyn's (2016) critical perspective on educational technology, and Luckin et al.'s (2016) work on AI in education. You understand that TPACK is content-specific, technology-specific, and context-specific — there is no general TPACK, only specific TPACK for specific intersections.

Your task is to diagnose the teacher's TPACK gaps and produce a development plan for the following teaching context.

**Teaching context:** {{teaching_context}}
**Technology in use:** {{technology_in_use}}
**Learner stage:** {{learner_stage}}
**Teacher background:** {{teacher_background}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**PCK output:** {{pck_output}} — if provided, use the PCK diagnosis as the foundation. TPACK builds on PCK. If not provided, note that the TPACK diagnosis may be incomplete without a prior PCK assessment.
**Intended learning outcome:** {{intended_learning_outcome}} — if provided, evaluate whether the technology actually serves this outcome.
**School technology context:** {{school_technology_context}} — if provided, factor constraints into the recommendations.

## Process

Follow these seven steps precisely. Each step produces a named section in the output.

**Step 1 — TPACK Diagnosis.**
Assess the teacher's knowledge across the three TPACK intersections. Be specific to this technology and this content.
- **Technology-Content Knowledge (TCK):** Does the teacher understand how this technology represents this content — accurately, approximately, or distortingly? Can they identify where the technology's representation of this content is epistemically sound and where it is not?
- **Technology-Pedagogy Knowledge (TPK):** Does the teacher know which of their pedagogical moves this technology supports, which it undermines, and which it is irrelevant to? Can they identify when the technology is helping students learn versus when it is helping students complete a task without learning?
- **Full TPACK:** Can the teacher make real-time judgments during a lesson about when the technology is serving student learning and when to step away from it? This is the integrated knowledge that emerges from experience with this specific combination.
Also identify TPACK strengths the teacher likely brings from their background.

**Step 2 — Technology-Content Analysis.**
Analyse how this specific technology represents this specific content.
- What does it make visible that is otherwise hard to see?
- What does it simplify in ways that may produce misconceptions?
- What does it omit that matters for this content at this learner stage?
- If the technology is an AI tool: how reliable are its outputs for this specific content domain? At what level of specificity does the teacher need to verify outputs before using them with students? What kinds of errors is this AI most likely to make in this domain?

**Step 3 — Pedagogy-Technology Alignment.**
Identify which pedagogical moves this technology supports well, which it actively undermines, and which are neutral. For each move:
- **Supports:** The technology enhances this pedagogical move — it does something the teacher cannot easily do without it.
- **Undermines:** The technology actively works against this pedagogical move — using the technology for this purpose will reduce learning.
- **Neutral:** The technology neither helps nor hinders — using it adds complexity without adding value.
Be specific: "undermines the productive struggle with evidence selection that is the core historical thinking skill" is useful. "May be distracting" is not.

**Step 4 — AI-Specific Guidance.**
Complete this step if the technology is an AI tool. Skip if not.
Address four questions:
1. **Reliability:** What does this AI do well for this content and this learner stage, and what does it do poorly or unreliably? Be specific to the content domain.
2. **Verification:** Which AI outputs require teacher verification before being used as content in this subject? What does verification look like for this domain?
3. **Student critical evaluation:** How should the teacher develop students' critical evaluation of AI outputs in this domain? Include a specific modelling move the teacher can use in the first lesson.
4. **Autonomy-dependency risk:** Is there a genuine danger that using this AI for this task will prevent students from developing the capability the task was designed to build? If so, how should the task be structured to mitigate this?

**Step 5 — Equity and Ethics.**
Identify the equity and ethical dimensions of this technology integration:
- Does uneven access to the technology create differential learning experiences?
- Does the technology collect or expose student data in ways that require disclosure or consent for this age group?
- Are there content-specific ethical issues — for example, using AI for tasks involving student emotional disclosure, or using analytics on behaviour students have not consented to have tracked?
- Does the technology create advantages for students who already have more technology access at home, widening rather than narrowing equity gaps?

**Step 6 — Dispositional TPACK.**
Describe the orientation the teacher needs to maintain effective TPACK in practice. This is not a one-time assessment but a continuous stance:
- The habit of asking "is this technology actually helping my students learn this specific content right now?" during every lesson
- The willingness to step away from the technology when it is not serving learning, even if the lesson was planned around it
- The critical disposition toward vendor claims and technology enthusiasm that Selwyn (2016) describes
- The recognition that TPACK is not a destination — it requires continuous evaluation as technology changes, content evolves, and students bring different prior experiences

**Step 7 — TPACK Development Plan.**
Produce a sequenced plan building from existing PCK. Organise into three phases:
- **Before using the technology with students:** What the teacher needs to learn about this technology's representation of this content. What low-stakes practice will build confidence. What to test before the first lesson.
- **During the first use:** What to observe in student responses to the technology. What adjustments to be ready to make. What signals that the technology is helping versus hindering.
- **After the first cycle:** How to evaluate whether the technology served the learning outcome. What to refine. When to consider abandoning the technology for this content.

Return your output in this exact format:

## TPACK Development Plan: [Technology] in [Topic]

**Teaching context:** [Summarised]
**Technology:** [Specific tool]
**Learner stage:** [Age/year]
**Teacher background:** [Summarised]
**Intended learning outcome:** [If provided; otherwise "Not specified"]

### 1. TPACK Diagnosis

**Technology-Content Knowledge (TCK):**
[Does the teacher understand how this technology represents this content?]

**Technology-Pedagogy Knowledge (TPK):**
[Does the teacher know which pedagogical moves this technology supports or undermines?]

**Full TPACK:**
[Can the teacher make real-time decisions about technology use based on student learning?]

**TPACK strengths:**
[What the teacher brings from their background]

### 2. Technology-Content Analysis

**What this technology makes visible:**
[Content this technology represents well]

**What this technology obscures or distorts:**
[Where the technology's representation is inaccurate or misleading for this content]

**Reliability assessment (for AI tools):**
[How reliable are outputs for this domain, and what verification is needed]

### 3. Pedagogy-Technology Alignment

| Pedagogical move | Technology effect | Explanation |
|---|---|---|
| [Move 1] | Supports / Undermines / Neutral | [Why] |
| [Move 2] | Supports / Undermines / Neutral | [Why] |
| [Move 3] | Supports / Undermines / Neutral | [Why] |

**Critical recommendation:**
[The most important thing the teacher must understand about how this technology interacts with their pedagogy for this content]

### 4. AI-Specific Guidance

[If applicable]

**Reliability for this domain:** [What the AI does well and poorly]
**Verification requirements:** [What must be checked and how]
**Student critical evaluation:** [How to model this — specific first-lesson move]
**Autonomy-dependency risk:** [Assessment and mitigation]

### 5. Equity and Ethics

**Access equity:** [Differential access risks]
**Data privacy:** [Requirements for this age group and this technology]
**Content-specific ethics:** [Any issues specific to this content domain]

### 6. Dispositional TPACK

[The ongoing critical stance the teacher needs to maintain]

### 7. TPACK Development Plan

**Before using with students:**
1. [Priority action]
2. [Second priority]
3. [Third priority]

**During first use:**
- [What to observe]
- [Adjustments to be ready for]
- [Signals of help vs hindrance]

**After first cycle:**
- [How to evaluate]
- [What to refine]
- [When to consider abandoning]

**Self-check before returning output:** Verify that (a) the diagnosis is specific to this technology AND this content, not generic technology advice, (b) the technology-content analysis identifies specific representational strengths and distortions, (c) the pedagogy-technology alignment identifies at least one pedagogical move the technology undermines, (d) the AI-specific guidance (if applicable) addresses autonomy-dependency risk directly, (e) the equity and ethics section is specific to this technology and this learner stage, (f) the dispositional section describes a critical ongoing stance not a one-time assessment, and (g) the development plan is sequenced and actionable.
```

## Example Output

**Scenario:** *Teaching context: "Year 9 History — causes of World War One, including source analysis and historical argumentation" / Technology in use: "Claude (AI assistant) — students will use Claude to help analyse primary sources and construct historical arguments about the Fischer thesis vs revisionist interpretation" / Learner stage: "14-15 years" / Teacher background: "Experienced history teacher with strong PCK for WWI topic, moderate technology confidence, first time using AI tools in the classroom" / Intended learning outcome: "Students develop historical thinking skills including source evaluation, evidence-based argumentation, and evaluation of competing historical interpretations"*

---

## TPACK Development Plan: Claude (AI Assistant) in Causes of WWI

**Teaching context:** Year 9 History — causes of WWI, source analysis, historical argumentation (Fischer vs revisionist)
**Technology:** Claude (AI assistant)
**Learner stage:** 14-15 years (Year 9)
**Teacher background:** Experienced history teacher, strong WWI PCK, moderate technology confidence, first time using AI in the classroom
**Intended learning outcome:** Historical thinking skills — source evaluation, evidence-based argumentation, evaluation of competing interpretations

### 1. TPACK Diagnosis

**Technology-Content Knowledge (TCK):**
The teacher likely does not know how Claude represents historical content. Key gaps:
- Does Claude reliably distinguish between Fischer's thesis and the revisionist position with historiographical accuracy? (It generally does for well-established historiographical debates, but may present synthesised summaries that smooth over the sharp disagreements between historians.)
- Can Claude accurately quote from primary sources? (No — large language models frequently fabricate or misattribute specific quotes and dates. The teacher must understand that Claude's paraphrases of primary sources are generally reliable but specific quotations must be verified.)
- Does Claude represent historical causation with appropriate complexity? (It tends toward balanced, diplomatic summaries rather than the sharp argumentative positions that characterise genuine historiographical debate. This may flatten the very debate the task is designed to explore.)

**Technology-Pedagogy Knowledge (TPK):**
The teacher likely has strong general pedagogical knowledge but does not know how AI tools interact with historical thinking pedagogy. Key gaps:
- The teacher may not recognise that using Claude to generate historical arguments removes the productive struggle with evidence that IS the core historical thinking skill. If students ask Claude "argue the Fischer thesis," they receive a fluent argument without doing the historical work of selecting evidence, weighing its significance, and constructing the argument themselves.
- The teacher may not know how to design an AI-integrated task that preserves the thinking demand — specifically, the difference between students using AI to do the thinking and students using AI to scaffold their own thinking.

**Full TPACK:**
The teacher has not yet used AI in the classroom and therefore lacks the experiential TPACK that comes from observing how students actually use the tool. They will not yet be able to make the real-time judgment: "this student is using Claude to think more deeply about the evidence" versus "this student is using Claude to avoid thinking about the evidence." This develops through experience but can be accelerated by knowing what to look for.

**TPACK strengths:**
- Strong PCK for WWI content — the teacher knows the historiography, the primary sources, and the student misconceptions. This is a significant advantage: they can evaluate whether Claude's historical content is accurate, which a teacher without this PCK could not.
- Strong pedagogical knowledge for historical thinking — the teacher knows how to design tasks that develop source evaluation and argumentation. The challenge is adapting these skills to an AI-mediated environment, not building them from scratch.

### 2. Technology-Content Analysis

**What Claude makes visible:**
- Claude can generate well-structured summaries of historiographical positions (Fischer, revisionist, post-revisionist) quickly, allowing students to access the debate faster than through reading alone. This is useful for providing context before students engage with primary sources.
- Claude can model the structure of a historical argument (claim → evidence → reasoning → qualification), giving students an example to compare their own work against.
- Claude can generate follow-up questions that push students to consider evidence they may have overlooked: "Have you considered the role of Russia's mobilisation in the Fischer debate?" This scaffolds the thinking without doing it.

**What Claude obscures or distorts:**
- Claude tends to present balanced, diplomatic syntheses of debates rather than the sharp, committed positions that characterise genuine historiography. Fischer's argument was not balanced — it was a provocative, evidence-based provocation that divided the historical profession. If Claude smooths this into "some historians blame Germany more, while others emphasise shared responsibility," it has distorted the intellectual force of the debate.
- Claude cannot evaluate the provenance of a primary source the way a historian does. It can describe what a source says but struggles to make the inferential leap: "The Kaiser's telegram to the Tsar may be sincere diplomacy or calculated performance — we cannot determine intent from the text alone." This is precisely the kind of historical thinking the task is designed to develop.
- Claude's "knowledge" of primary sources is derived from its training data, not from reading the original documents. It may present paraphrased versions of sources with subtle inaccuracies that a teacher without strong content knowledge would not catch.

**Reliability assessment:**
- **Reliable:** General summaries of the Fischer debate, the alliance system, the July Crisis sequence. These are well-established historical content that Claude handles accurately.
- **Approximately reliable:** Summaries of specific historians' positions. Claude captures the broad argument but may not represent the nuance or the specific evidence each historian relies on. Verify against the teacher's own knowledge.
- **Unreliable:** Specific primary source quotations, specific dates in the July Crisis (Claude may give slightly wrong dates), and claims about what specific documents "prove." The teacher must verify any specific factual claim Claude makes about primary sources before allowing it to be used as content with students.

### 3. Pedagogy-Technology Alignment

| Pedagogical move | Technology effect | Explanation |
|---|---|---|
| Source evaluation (provenance, reliability, utility) | **Undermines** | If students ask Claude to evaluate a source, they receive a competent evaluation without developing the skill of evaluation themselves. The source evaluation IS the thinking — outsourcing it to AI defeats the learning purpose. |
| Constructing evidence-based arguments | **Undermines** | If students use Claude to draft their Fischer-vs-revisionist argument, they produce a fluent product without doing the historical thinking the product is supposed to evidence. The argument construction IS the learning, not the argument itself. |
| Scaffolding argument structure | **Supports** | Claude can provide the structure of a historical argument (claim-evidence-reasoning-qualification) as a framework. Students can then fill the framework with their own content. This scaffolds without replacing the thinking. |
| Generating follow-up questions and counter-arguments | **Supports** | After a student has drafted their own argument, Claude can generate challenges: "A revisionist historian would respond to your claim by pointing to..." This pushes the student to engage with counter-evidence they may not have considered. |
| Providing historical context | **Supports** | Claude can provide background information (timeline of events, explanation of alliances) that students need before they can think critically. This is surface-level knowledge provision that frees class time for deeper thinking. |
| Evaluating the quality of historical reasoning | **Neutral to undermines** | Claude can assess whether an argument has a clear claim and evidence, but cannot reliably assess the QUALITY of historical reasoning — whether the student's use of evidence is genuinely historiographical or merely competent-sounding. The teacher must do this. |
| Developing intellectual humility about historical knowledge | **Undermines** | Claude presents information with confident fluency that may model certainty rather than the appropriate uncertainty that characterises genuine historical inquiry. If students see Claude as an authority rather than a tool to be evaluated, it undermines the disposition of intellectual humility the task is designed to cultivate. |

**Critical recommendation:**
Claude must be positioned as a tool students use AFTER they have done the thinking, not BEFORE or INSTEAD OF. The task sequence should be: (1) students engage with primary sources and construct their own argument without AI, (2) students then use Claude to challenge, extend, or refine their argument — asking it for counter-evidence, alternative interpretations, or structural feedback on their reasoning. This preserves the thinking demand while using AI productively. If the sequence is reversed — students ask Claude for an argument and then edit it — the historical thinking has not occurred.

### 4. AI-Specific Guidance

**Reliability for this domain:**
Claude performs well on synthesising established historiographical debates and providing factual overviews of WWI causes. It performs poorly on specific primary source quotations (may fabricate or misattribute), precise dates (may be slightly wrong), and nuanced historiographical distinctions (may flatten debates into balanced summaries). For this task, the teacher should treat Claude's factual claims about specific sources as unverified until checked, while treating its structural and analytical scaffolding as generally reliable.

**Verification requirements:**
Before the unit begins, the teacher should:
1. Ask Claude to summarise the Fischer thesis and the revisionist position. Check: does Claude represent Fischer's argument as genuinely provocative, or does it smooth it into a diplomatic summary? If the latter, the teacher needs to supplement with their own framing.
2. Ask Claude to quote from the key primary sources being used in the task (Kaiser's telegram, War Council minutes). Check: are the quotations accurate or fabricated? If fabricated, students must NOT be told to ask Claude for quotations — they must work from the sources provided by the teacher.
3. Ask Claude to evaluate a primary source's provenance. Check: does Claude assess the source historiographically, or does it produce a generic evaluation? If generic, this confirms that source evaluation must not be outsourced to Claude.

**Student critical evaluation — first lesson modelling move:**
In the first lesson using Claude, the teacher should model critical evaluation live in front of students. Procedure:
1. Ask Claude, in front of the class: "Was Germany primarily responsible for World War One?"
2. Read Claude's response aloud.
3. Ask students: "What does this response get right? What does it oversimplify? What evidence does it use, and is that evidence specific or vague?"
4. Point out: "Claude gives a balanced answer. But Fischer's argument was NOT balanced — it was a deliberate provocation. A balanced answer to this question is actually a distortion of the historiographical debate. What does that tell us about how to use Claude for history?"
This models the critical stance students need: AI produces fluent answers, but fluent does not mean historically accurate or historiographically faithful.

**Autonomy-dependency risk:**
This risk is HIGH for this task. The entire learning outcome — developing historical thinking through evidence-based argumentation — requires students to do the thinking themselves. If students use Claude to construct their Fischer-vs-revisionist argument, they are performing the task without doing the historical thinking the task was designed to develop. The product (a written argument) will exist, but the learning (the ability to evaluate evidence, weigh competing interpretations, and construct a defended position) will not have occurred.

Mitigation: Structure the task in two phases. Phase 1 (no AI): students read the sources, draft their argument by hand, and submit a first draft. Phase 2 (AI available): students use Claude to challenge their draft — asking it for counter-evidence, requesting feedback on their reasoning, or exploring an alternative interpretation. The teacher assesses the first draft (which shows the student's own thinking) and the revision (which shows their ability to engage with challenges and refine their reasoning).

### 5. Equity and Ethics

**Access equity:**
If Claude is used during class time on school devices, access is equitable during the lesson. However, students with AI access at home may refine their arguments further outside class, creating a differential advantage. Mitigation: assess the in-class first draft (pre-AI) as the primary evidence of historical thinking. The AI-assisted revision demonstrates a different skill (engaging with feedback) and should be assessed separately.

**Data privacy:**
Students aged 14-15 using Claude interact with a third-party AI platform. Requirements:
- School must have institutional terms of use that cover student data, or students must use the tool through a school-provisioned account that does not retain conversation data.
- Students should not be required to input personal information, emotional disclosures, or identifying details into the AI.
- The school's data protection officer (or equivalent) should be informed that student work is being processed by a third-party AI system.
- In jurisdictions covered by GDPR or similar frameworks, parental notification or consent may be required for this age group using third-party AI tools. The teacher should verify this with their school before proceeding.

**Content-specific ethics:**
The WWI topic does not involve personal disclosure, but the teacher should be aware that students may use AI to explore content related to war, violence, and mass death. Claude's responses to such queries are generally appropriate and contextualised, but the teacher should preview any AI-mediated engagement with sensitive historical content before assigning it.

### 6. Dispositional TPACK

The teacher needs to develop and maintain a continuous evaluative stance toward AI in their classroom — not a one-time setup but an ongoing practice:

- **In every lesson:** Ask "are my students using Claude to think more deeply, or to avoid thinking?" Look for the difference between a student who asks Claude "what evidence could someone use against my argument?" (productive use — extending thinking) and a student who asks Claude "write an argument about the Fischer thesis" (replacement use — avoiding thinking).
- **Between lessons:** Evaluate whether AI-generated student work is distinguishable from student-generated work. If it is not, the task design may need revision — the thinking demand may not be visible enough in the product.
- **Resist the sunk cost:** If the AI integration is not serving the learning outcome, be willing to remove it mid-unit. The technology should serve the history, not the other way around. An AI-free lesson in which students debate the Fischer thesis using only primary sources and their own reasoning may produce more historical thinking than an AI-mediated lesson that produces more polished but less genuinely argued responses.
- **Maintain Selwyn's critical stance:** When colleagues or administrators advocate for more AI use because it is "innovative," the teacher should ask: "Does it help my Year 9 students develop better historical thinking than they would without it?" If the answer is not clearly yes, the innovation argument is insufficient.

### 7. TPACK Development Plan

**Before using Claude with students:**
1. **Verify Claude's reliability on WWI content.** Run the three verification tests described in section 4. Know where Claude is accurate and where it is unreliable BEFORE students interact with it.
2. **Design the two-phase task structure.** Write the task so that Phase 1 (no AI) captures the student's own historical thinking, and Phase 2 (AI available) adds value without replacing the thinking. Prepare the Phase 2 prompt suggestions for students: "Ask Claude to challenge your argument," "Ask Claude what evidence a revisionist historian would use against your position."
3. **Prepare the first-lesson modelling move.** Script the live demonstration of critical evaluation described in section 4. Practise it once so it feels natural, not staged.

**During first use:**
- **Observe student queries.** Walk the room and look at what students are typing into Claude. Are they asking thinking-extending questions or task-completing questions? If most students are asking Claude to write their argument, pause the class and redirect: "I want you to ask Claude to CHALLENGE your argument, not to WRITE it."
- **Be ready to adjust access.** If Phase 1 drafts are significantly weaker than Phase 2 products, the AI may be doing the thinking. Consider restricting AI access to specific query types rather than open-ended use.
- **Note one student interaction that worked and one that did not.** After the lesson, record both. This builds the experiential TPACK that the skill cannot provide in advance.

**After first cycle:**
- **Compare Phase 1 and Phase 2 products.** If the quality improvement from Phase 1 to Phase 2 is in the reasoning (better engagement with counter-evidence, more nuanced qualification), the AI is serving the learning outcome. If the quality improvement is only in fluency and polish, the AI is serving the product but not the learning.
- **Ask students directly:** "Did using Claude help you think more carefully about the Fischer debate, or did it give you answers you could have reached yourself?" Student self-report is imperfect but informative.
- **Decide whether to continue.** If the AI integration produced better historical thinking (not just better-written arguments), refine the task design and continue. If it produced dependency or fluent but unthinking responses, consider restricting AI to specific uses (counter-argument generation, feedback on drafts) or removing it from this task entirely.

---

## Known Limitations

1. **TPACK is technology-specific and content-specific simultaneously.** This skill produces guidance for one technology integrated with one content area. A teacher integrating three different tools across two subjects needs the skill run separately for each combination. There is no general TPACK — only specific TPACK for specific intersections.

2. **Technology changes faster than the research base.** Evidence on AI tools in education is currently thin and moving quickly. The AI-specific guidance in this skill is based on first-principles reasoning from PCK research and general AI capability assessments rather than on replicated empirical studies of specific AI tools in specific content areas. Treat AI-specific guidance as informed professional judgment, not as research-backed certainty.

3. **This skill does not evaluate the technology itself — it evaluates the teacher's knowledge of how to use it.** A technology that is fundamentally inappropriate for a learning goal will not become appropriate through better TPACK. If the technology-content analysis reveals that the technology actively distorts the content or undermines the core learning, the right response may be not to use it — and no amount of TPACK development changes that conclusion.

4. **The equity and ethics section identifies risks but cannot resolve them.** Data privacy requirements vary by jurisdiction and are changing rapidly. For any technology collecting student data, the teacher and school must verify compliance with applicable law — this skill provides a checklist prompt, not legal advice.

5. **TPACK development requires practice with real students.** Like PCK, TPACK is ultimately built through teaching with the technology, observing student responses, and refining. This skill accelerates development by identifying the right questions to ask and the right things to observe, but it cannot substitute for the experiential learning that comes from actually teaching with the technology and noticing what happens.

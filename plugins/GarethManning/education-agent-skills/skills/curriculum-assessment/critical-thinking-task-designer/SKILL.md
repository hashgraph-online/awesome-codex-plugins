---
# AGENT SKILLS STANDARD FIELDS (v2)
name: critical-thinking-task-designer
description: "Design discipline-specific critical thinking tasks grounded in knowledge-contingent reasoning rather than generic skills. Use when embedding higher-order thinking into subject content."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "curriculum-assessment/critical-thinking-task-designer"
skill_name: "Critical Thinking Task Designer"
domain: "curriculum-assessment"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Bailin, Case, Coombs & Daniels (1999) — Common misconceptions of critical thinking: the intellectual resources framework"
  - "Bailin & Siegel (2003) — Critical thinking in philosophy of education"
  - "Willingham (2007) — Critical thinking: why is it so hard to teach?"
  - "McPeck (1981) — Critical Thinking and Education: domain-specificity of critical thinking"
  - "Ennis (1989) — Critical thinking and subject specificity"
  - "Paul & Elder (2006) — The Art of Socratic Questioning: disciplinary thinking standards"
  - "Perkins & Salomon (1989) — Are cognitive skills context-bound? Transfer and domain-contingency"
  - "Hattie (2009) — Visible Learning: effect sizes for thinking skills instruction"
  - "Maton (2013) — Making semantic waves: semantic gravity and cumulative knowledge-building"
  - "Bernstein (1999) — Vertical and horizontal discourse: disciplinary knowledge structures"
input_schema:
  required:
    - field: "curriculum_topic"
      type: "string"
      description: "The subject, unit, or concept students are currently studying"
    - field: "learner_stage"
      type: "string"
      description: "Age range or year group"
    - field: "discipline_or_subject"
      type: "string"
      description: "The subject area, because thinking standards are discipline-specific"
  optional:
    - field: "knowledge_baseline"
      type: "string"
      description: "What students already know about this topic; used to check knowledge sufficiency"
    - field: "existing_learning_targets"
      type: "string"
      description: "Any LTs this task should connect to"
    - field: "thinking_focus"
      type: "string"
      description: "If the teacher has a specific thinking move in mind (e.g. evaluating evidence, identifying assumptions, considering perspective)"
output_schema:
  type: "object"
  fields:
    - field: "knowledge_prerequisite_check"
      type: "object"
      description: "Assessment of whether students have sufficient domain knowledge for the critical thinking to be meaningful; flags if the knowledge base is insufficient and recommends what to establish first"
    - field: "disciplinary_thinking_standards"
      type: "object"
      description: "What good thinking looks like specifically in this discipline for this topic; not generic ('think carefully') but substantive ('in history, good thinking requires evaluating source provenance and corroborating claims across sources')"
    - field: "critical_thinking_task"
      type: "object"
      description: "The structured task itself: context/scenario, the thinking demand, and the specific question or prompt students respond to"
    - field: "intellectual_resources"
      type: "object"
      description: "The scaffolded support students need to do the thinking: background knowledge to activate or provide, key concepts to clarify, thinking heuristics to offer, and habits of mind to cultivate"
    - field: "assessment_guidance"
      type: "object"
      description: "Criteria for what quality thinking looks like in student responses; this is horizontal knowledge (better and worse reasoning, not right/wrong answers); rubric should assess quality of reasoning process, not correctness of conclusion"
    - field: "teacher_development_notes"
      type: "object"
      description: "What designing and running this task reveals about disciplinary thinking in this subject; framed as professional learning, not just lesson delivery"
chains_well_with:
  - "curriculum-knowledge-architecture-designer"
  - "kud-knowledge-type-mapper"
  - "coherent-rubric-logic-builder"
  - "learning-target-authoring-guide"
  - "ai-output-critical-audit-designer"
teacher_time: "10 minutes"
tags: ["critical-thinking", "disciplinary-thinking", "horizontal-knowledge", "knowledge-contingent", "task-design", "intellectual-resources", "Bailin", "Willingham", "domain-specific"]
---

# Critical Thinking Task Designer

## What This Skill Does

Takes a curriculum topic and produces a structured critical thinking task that embeds disciplinary thinking within subject content — with the intellectual resources students need to do the thinking scaffolded explicitly. Critical thinking is domain-contingent: you cannot think critically about something you know too little about, and what counts as good thinking in history is not the same as what counts as good thinking in science or ethics. This skill operationalises that insight. It does not produce generic "higher order thinking" tasks. It produces tasks where the thinking demand is specific to the discipline, the knowledge prerequisites are checked before the task is designed, and the criteria for good thinking are stated explicitly so students know what they are aiming for. The skill draws on Bailin et al.'s intellectual resources framework: a critical thinker needs background knowledge, operational knowledge of good thinking in the domain, knowledge of critical concepts, effective heuristics, and habits of mind. All five must be present or scaffolded for the task to actually develop critical thinking rather than merely demand it. AI is particularly valuable here because designing a good critical thinking task requires simultaneously knowing the content domain, the disciplinary thinking standards, the knowledge prerequisites, and the assessment logic — a combination that is rare in any single educator and that most lesson planning processes skip entirely. This skill also functions as teacher professional development: the act of specifying what good thinking looks like in your subject is itself a significant pedagogical insight that most teachers have never been asked to articulate.

## Evidence Foundation

The foundational insight is from Willingham (2007): critical thinking skills are not transferable in the way general skills are. A student who thinks critically in history may think naively in biology, because the standards for good thinking are discipline-specific. Teaching generic critical thinking skills — inference, analysis, evaluation — without grounding them in specific disciplinary content produces students who can name thinking moves but cannot execute them meaningfully. The implication: critical thinking must be developed *through* disciplines, not *alongside* them.

Bailin et al. (1999) provide the most useful operational framework. They define the critical thinker through five **intellectual resources** that must be present: **background knowledge** (you cannot think critically about something you do not know enough about), **operational knowledge of what good thinking looks like** in this domain, **knowledge of critical concepts** (evidence, argument, assumption, perspective), **effective heuristics** (thinking moves that work in this domain), and **habits of mind** (intellectual humility, tolerance for ambiguity, commitment to good reasoning). Generic critical thinking instruction typically provides only the third category — concepts — and assumes the others will follow. They do not.

McPeck (1981) argued that critical thinking is entirely domain-specific — there are no general thinking skills, only disciplinary ones. Ennis (1989) countered that some thinking skills transfer across domains. The domain-specificity debate has a pragmatic resolution for curriculum designers: some thinking skills are more transferable than others (identifying assumptions, considering alternative perspectives) but all require domain knowledge to execute meaningfully. The design implication is that critical thinking tasks should be embedded in specific content, with the domain knowledge explicitly checked or provided, and with the thinking standards stated in discipline-specific terms.

Bailin & Siegel (2003) extended this framework within philosophy of education, arguing that critical thinking is not a skill at all but a quality of reasoning that is constituted by the intellectual resources the thinker brings to bear. This reframing is important for task design: the goal is not to "teach critical thinking" as a skill but to ensure that students have the intellectual resources needed to think well about a specific topic, and then to create tasks that require those resources to be deployed.

Paul & Elder (2006) contributed the concept of disciplinary thinking standards — the specific criteria by which reasoning is judged within a discipline. In science, good thinking requires testable hypotheses, controlled variables, and evidence-based conclusions. In history, good thinking requires source evaluation, corroboration, and contextualisation. In ethics, good thinking requires identifying stakeholders, articulating principles, and considering consequences. These standards are not interchangeable, and a task that does not make the relevant standards explicit leaves students guessing at what "good thinking" means.

Hattie (2009) found that teaching thinking skills has a moderate effect size (d = 0.62), but with enormous variation depending on implementation. The evidence suggests that thinking skills instruction is effective when it is embedded in content, when the thinking standards are made explicit, and when students practise applying them to specific problems — precisely the conditions this skill is designed to create. Generic thinking skills instruction divorced from content produces much weaker effects.

Maton's (2013) semantic wave concept is relevant here: effective knowledge-building requires moving between abstract principles and concrete cases. A critical thinking task that stays only at the abstract level ("analyse the argument") without grounding it in specific content produces shallow thinking. A task that stays only at the concrete level ("describe what happened") without requiring students to apply analytical frameworks produces description, not thinking. A well-designed task moves students across the semantic wave: from concrete case to abstract principle and back to concrete application.

Perkins & Salomon (1989) demonstrated that transfer of cognitive skills is not automatic — it requires deliberate bridging. Students do not spontaneously apply thinking skills learned in one domain to another. This reinforces the design principle that critical thinking must be developed within each discipline separately, with explicit attention to which thinking moves are discipline-specific and which might transfer with deliberate teaching.

## Input Schema

The educator must provide:
- **Curriculum topic:** The subject, unit, or concept students are currently studying. *e.g. "Year 9 History — causes of World War One" / "Year 10 Biology — natural selection and evolution" / "Year 8 Ethics — the trolley problem and moral reasoning"*
- **Learner stage:** Age range or year group. *e.g. "14-15 years" / "Year 9" / "Band D"*
- **Discipline or subject:** The subject area. *e.g. "History" / "Biology" / "Ethics" / "Geography"*

Optional (injected by context engine if available):
- **Knowledge baseline:** What students already know about this topic
- **Existing learning targets:** Any LTs this task should connect to
- **Thinking focus:** A specific thinking move the teacher wants to emphasise

## Prompt

```
You are an expert in critical thinking pedagogy, with deep knowledge of Bailin et al.'s (1999) intellectual resources framework, Willingham's (2007) research on domain-specificity, McPeck's (1981) and Ennis's (1989) work on critical thinking and subject specificity, Paul & Elder's (2006) disciplinary thinking standards, Hattie's (2009) evidence on thinking skills instruction, and Maton's (2013) semantic wave concept. You understand that critical thinking is domain-contingent: it requires sufficient domain knowledge, discipline-specific thinking standards, and all five intellectual resources (background knowledge, operational knowledge, critical concepts, heuristics, habits of mind) to be present or scaffolded.

Your task is to design a structured critical thinking task for the following curriculum input.

**Curriculum topic:** {{curriculum_topic}}
**Learner stage:** {{learner_stage}}
**Discipline or subject:** {{discipline_or_subject}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Knowledge baseline:** {{knowledge_baseline}} — if not provided, state what the minimum knowledge base would need to be and flag this as an assumption.
**Existing learning targets:** {{existing_learning_targets}} — if provided, connect the task to these LTs.
**Thinking focus:** {{thinking_focus}} — if provided, use this as the primary thinking demand. If not provided, select the most productive thinking demand for this topic and discipline.

## Process

Follow these seven steps precisely. Each step produces a named section in the output.

**Step 1 — Knowledge Prerequisite Check.**
Before designing the task, assess whether students have sufficient domain knowledge for critical thinking to be meaningful. If a student cannot accurately describe the phenomenon they are asked to analyse, they cannot analyse it critically — they will produce opinion dressed as reasoning. State explicitly: what is the minimum knowledge base required for this task? If the knowledge baseline provided suggests students are not there yet, flag this and recommend what to establish first. Do not proceed to task design until this question is answered. If no knowledge baseline is provided, state the assumed prerequisites and flag this as an assumption the teacher must verify.

**Step 2 — Identify the Disciplinary Thinking Standard.**
What does good thinking look like specifically in this discipline and for this topic? Avoid generic standards. "Evaluates evidence" is generic. "In history: identifies the provenance of a source, explains how provenance affects reliability, and corroborates the claim across at least two independent sources" is disciplinary. State the standard in terms that a student could understand and a teacher could use to assess. Reference the discipline's conventions for valid reasoning — what counts as evidence, what counts as a strong argument, what distinguishes expert thinking from novice thinking in this field.

**Step 3 — Select the Thinking Demand.**
Choose one primary thinking move for this task. Options include but are not limited to: evaluating competing claims or interpretations, identifying assumptions underlying a position, analysing a case through multiple lenses, constructing and defending a reasoned argument, identifying the limits of a given explanation, or considering how context or perspective changes interpretation. One thinking demand, done well, produces more genuine critical thinking than five thinking demands done superficially. State the selected thinking demand and explain why it is the most productive choice for this topic and learner stage.

**Step 4 — Design the Task.**
Write the context or scenario students will think about. It should be concrete, discipline-specific, and genuinely open — there should be better and worse answers but not a single correct answer. Write the specific question or prompt. It should require the selected thinking move to answer well. It should not be answerable by recall alone. The task should move students across Maton's (2013) semantic wave: from concrete case to abstract principle and back to concrete application.

**Step 5 — Scaffold the Intellectual Resources.**
For each of Bailin et al.'s (1999) five intellectual resources, state what students need and how it will be provided or activated:

1. **Background knowledge:** What do students need to know, and is it already established or does it need to be provided in the task materials? If it needs to be provided, specify exactly what to include.
2. **Operational knowledge:** What does good thinking look like here, and has the teacher modelled it? If not, how should the standard be shared with students before they begin?
3. **Critical concepts:** Which concepts (evidence, assumption, perspective, causation — discipline-specific) are required, and do students have working definitions? If not, provide the definitions.
4. **Heuristics:** What thinking moves or protocols will help students approach this task? Provide 1-2 specific, actionable heuristics — not generic advice ("think carefully") but concrete moves ("ask: what would change my mind about this?").
5. **Habits of mind:** Which dispositions (intellectual humility, tolerance for ambiguity, willingness to revise) does this task cultivate, and how will the classroom environment support them? Note: these are dispositional — they cannot be assessed through this task but can be cultivated by it.

**Step 6 — Write the Assessment Guidance.**
State 3-4 criteria for quality thinking in student responses. These criteria assess the reasoning process, not the conclusion. A student who reaches an unconventional conclusion through rigorous reasoning should score higher than a student who reaches a conventional conclusion through poor reasoning. Make the criteria specific to this task and this thinking demand. Use the rubric scale Emerging / Developing / Competent / Extending if level descriptors are provided. These criteria become the input for the Coherent Rubric Logic Builder if a formal rubric is needed.

**Step 7 — Write the Teacher Development Notes.**
What does designing and running this task reveal about disciplinary thinking in this subject? What would a teacher who ran this task learn about what good thinking looks like in their discipline? Frame this as professional insight, not classroom management advice. This section is the reason the skill has value beyond individual lesson planning — it builds the teacher's own critical thinking about their subject.

Return your output in this exact format:

## Critical Thinking Task: [Topic]

**Discipline:** [Subject]
**Learner stage:** [Age/year]
**Thinking demand:** [Selected thinking move]
**Connected LTs:** [If provided; otherwise "None specified"]

### 1. Knowledge Prerequisite Check

**Minimum knowledge required:**
[List the specific knowledge elements students must have before this task is meaningful]

**Status:** [Sufficient / Insufficient / Assumed — based on knowledge baseline provided]

[If insufficient: what must be established first, and how]

### 2. Disciplinary Thinking Standard

**In [discipline], good thinking about [topic] requires:**
[State the standard in discipline-specific terms — what counts as evidence, what counts as a strong argument, what distinguishes expert from novice reasoning]

### 3. Thinking Demand

**Primary thinking move:** [Selected demand]
**Why this demand:** [Why it is the most productive choice for this topic and learner stage]

### 4. The Task

**Context:**
[The scenario or case students will think about — concrete, discipline-specific, genuinely open]

**Task materials provided to students:**
[Any documents, data, sources, or information students need — specify exactly what is given]

**The question:**
[The specific prompt — requiring the selected thinking move, not answerable by recall alone]

### 5. Intellectual Resources

| Resource | What students need | How it is provided or activated |
|---|---|---|
| Background knowledge | [Specific knowledge] | [Already established / provided in task materials / needs pre-teaching] |
| Operational knowledge | [What good thinking looks like here] | [How the standard is shared — teacher modelling, exemplar, explicit statement] |
| Critical concepts | [Discipline-specific concepts required] | [Working definitions provided / already established / needs explicit teaching] |
| Heuristics | [Specific thinking moves] | [Stated to students as protocol / modelled by teacher] |
| Habits of mind | [Dispositions cultivated] | [How the classroom environment supports them] |

### 6. Assessment Guidance

**Criteria for quality thinking** (assess reasoning process, not conclusion):

1. [Criterion 1 — specific to this task]
2. [Criterion 2]
3. [Criterion 3]
4. [Criterion 4 — if needed]

**What distinguishes Competent from Extending:**
[The specific quality of reasoning that separates meeting the standard from genuinely exceeding it]

### 7. Teacher Development Notes

[What this task reveals about disciplinary thinking in this subject — framed as professional insight]

**Self-check before returning output:** Verify that (a) the knowledge prerequisite check is specific and honest — not assumed to be sufficient without evidence, (b) the disciplinary thinking standard is genuinely discipline-specific, not generic, (c) the task is not answerable by recall alone, (d) all five intellectual resources are addressed with specific content, not generic placeholders, (e) the assessment criteria assess reasoning quality, not conclusion correctness, (f) the teacher development notes contain genuine disciplinary insight, and (g) the rubric scale uses Emerging / Developing / Competent / Extending wherever level descriptors appear.
```

## Example Output

**Scenario:** *Curriculum topic: "Year 9 History — causes of World War One" / Learner stage: "14-15 years" / Discipline or subject: "History" / Knowledge baseline: "Students have studied the alliance system (Triple Alliance and Triple Entente), the assassination of Archduke Franz Ferdinand and the July Crisis, imperial competition between European powers, and the growth of nationalism in the late 19th century" / Thinking focus: "Evaluating competing historical interpretations"*

---

## Critical Thinking Task: Causes of World War One

**Discipline:** History
**Learner stage:** 14-15 years (Year 9)
**Thinking demand:** Evaluating competing historical interpretations
**Connected LTs:** None specified

### 1. Knowledge Prerequisite Check

**Minimum knowledge required:**
- The alliance system: which countries were in the Triple Alliance and Triple Entente, and what the alliances committed them to
- The assassination of Archduke Franz Ferdinand: what happened, when, by whom, and the immediate political consequences (Austria-Hungary's ultimatum to Serbia)
- The July Crisis: the sequence of events between the assassination (28 June 1914) and the outbreak of general war (early August 1914) — specifically, which country mobilised when and why
- Imperial competition: what European powers were competing for (colonies, trade routes, prestige), and at least two specific examples of imperial rivalry
- Nationalism: how nationalist sentiment contributed to tensions — at minimum, the difference between unifying nationalism (e.g. Pan-Slavism) and state nationalism (e.g. French revanchism)
- At least a basic awareness that historians disagree about WHO or WHAT was most responsible for the war — the idea of historiographical debate, even if students do not yet know the specific positions

**Status:** Sufficient — the knowledge baseline covers all required elements. The one area to verify is whether students understand that historians actively disagree about causes, or whether they have been taught "the causes of WWI" as a settled list. If the latter, a brief introduction to historiographical debate is needed before the task.

### 2. Disciplinary Thinking Standard

**In history, good thinking about the causes of WWI requires:**

- **Source evaluation:** Assessing who wrote or said something, when, in what context, and for what purpose — and explaining how these factors affect the reliability and usefulness of the source for a specific claim. A historian citing a German government memo from July 1914 must consider that the memo was written during a diplomatic crisis and may reflect strategic positioning rather than genuine intent.
- **Corroboration:** Not relying on a single source or a single historian's interpretation. Claims about causation must be checked against multiple sources. If Fischer argues Germany deliberately planned war, the evidence he uses must be examined — and competing evidence from other historians must be considered.
- **Distinguishing causation types:** Proximate causes (the assassination, the July Crisis) are not the same as structural causes (alliance system, imperial competition, nationalism). Good historical thinking names which type of cause is being discussed and explains why the distinction matters.
- **Appropriate qualification:** Historical claims about causation should be qualified — "the evidence suggests" rather than "this proves." Good historical thinking acknowledges what the evidence can support and what it cannot.

### 3. Thinking Demand

**Primary thinking move:** Evaluating competing historical interpretations
**Why this demand:** At 14-15, students are ready to move beyond "listing causes" (recall) to engaging with the idea that historians disagree about which causes mattered most and why. This is the transition from treating history as a fixed narrative to treating it as an ongoing argument — the fundamental disciplinary shift. Evaluating competing interpretations requires students to assess the quality of reasoning, not just the content of claims, which is the core of historical critical thinking. It also requires them to hold two positions in mind simultaneously and make a reasoned judgment between them — a cognitive demand that is achievable at this age with appropriate scaffolding.

### 4. The Task

**Context:**
In 1961, the German historian Fritz Fischer published a book arguing that Germany bore primary responsibility for World War One — that Germany's leaders deliberately pursued a policy of aggression, using the assassination of Franz Ferdinand as a pretext to launch a war they had been planning. This was explosive. For decades, the accepted view had been that all major powers stumbled into war through a combination of alliances, miscalculation, and escalation — that no single country was primarily responsible. Fischer's argument divided historians and remains debated to this day.

**Task materials provided to students:**

**Source A — The Fischer Thesis (summarised):**
Fischer argued that Germany's leaders, particularly Chancellor Bethmann-Hollweg, pursued a "September Programme" of expansionist war aims. He pointed to evidence that Germany gave Austria-Hungary a "blank cheque" of unconditional support, knowing this would likely lead to a wider war. Fischer used German government documents from 1914 to argue that the decision for war was deliberate, not accidental.

**Source B — The Revisionist Position (summarised):**
Historians including Christopher Clark (*The Sleepwalkers*, 2012) have argued that all major powers share responsibility. Clark described the outbreak of war as a collective failure: Austria-Hungary's reckless ultimatum, Russia's premature mobilisation, France's encouragement of Russia, Britain's ambiguous signals — each power made decisions that escalated the crisis. Clark argued that focusing on German guilt distorts a picture in which multiple actors made catastrophic choices.

**Source C — Primary evidence:**
Telegram from Kaiser Wilhelm II to Tsar Nicholas II, 29 July 1914: "I am exerting my utmost influence to induce the Austro-Hungarian Government to deal straightly to arrive at a satisfactory understanding with you. I confidently hope that you will help me in my efforts to smooth over difficulties that may still arise. Your very sincere and devoted friend and cousin, Willy."

**Source D — Primary evidence:**
Extract from the minutes of the German Imperial War Council, 8 December 1912 (discovered by Fischer): "His Majesty the Kaiser said that... if Russia mobilised, there would be no alternative but war. He further said the Fleet must prepare for war against England... The Chief of the General Staff said that in his opinion war was inevitable — the sooner, the better."

**The question:**
Based on the evidence you have studied and the sources provided, which interpretation — Fischer's argument for German responsibility or the revisionist argument for shared responsibility — is better supported by the available evidence? In your answer:
- State which interpretation you find more convincing and why
- Use specific evidence from the sources AND from your own knowledge to support your position
- Explain what evidence the OTHER side uses that you find hardest to dismiss
- Identify at least one thing the evidence CANNOT tell us — a limit of what we can know about the causes of WWI

### 5. Intellectual Resources

| Resource | What students need | How it is provided or activated |
|---|---|---|
| Background knowledge | Alliance system, July Crisis sequence, imperial competition, nationalism — sufficient to evaluate whether the source evidence is consistent with broader patterns | Already established through prior teaching. Teacher should run a brief retrieval activity (5 minutes) at the start of the lesson: "List the alliance commitments and the July Crisis timeline from memory." This activates the knowledge and reveals gaps before the task begins. |
| Operational knowledge | What a good historical argument looks like — evidence-based, qualified, acknowledges counter-evidence, distinguishes between types of cause | Teacher models this before the task using a different example: take a simpler historical debate (e.g. "Was the Roman Empire's fall caused by barbarian invasion or internal decay?") and demonstrate what a strong evaluation of two positions looks like. 10 minutes. Students see the standard before they are asked to meet it. |
| Critical concepts | **Historical causation:** proximate causes (events that triggered the war) vs structural causes (conditions that made war possible). **Provenance:** who produced a source, when, and why — and how this affects what we can use it for. **Corroboration:** checking a claim against multiple sources. | Teacher provides working definitions on the board or a handout. Key question: "When we say 'cause' in history, do we mean 'the thing that triggered the event' or 'the condition that made the event possible'? Fischer is arguing about BOTH. Which type of cause does each piece of evidence support?" |
| Heuristics | **"What would change my mind?"** — After forming an initial position, students ask: what evidence would I need to see to switch to the other interpretation? This forces genuine engagement with the counter-argument rather than dismissal. **"What can this evidence NOT tell us?"** — For each source, students identify its limits. The Kaiser's telegram shows what he said to the Tsar, not what he actually intended. The War Council minutes show what was discussed, not what was decided. | Stated explicitly as two thinking protocols on the board. Teacher walks through one example of each before students begin: "Source C — the Kaiser's telegram — sounds conciliatory. But what can it NOT tell us? It cannot tell us whether Wilhelm was sincere or performing diplomacy for the record. That matters for how much weight we give it." |
| Habits of mind | **Intellectual humility:** the willingness to say "I'm not sure" or "the evidence is not conclusive." **Tolerance for ambiguity:** the ability to hold two plausible interpretations in mind without prematurely resolving the tension. **Willingness to revise:** changing your mind if the evidence warrants it. | Teacher sets the tone explicitly: "In history, saying 'I'm not sure which interpretation is better supported' is not a weakness — it's a sign of mature thinking, as long as you explain WHY you're not sure. I am more impressed by honest uncertainty than by false confidence." Establish that the task rewards quality of reasoning, not strength of conviction. |

### 6. Assessment Guidance

**Criteria for quality thinking** (assess reasoning process, not conclusion):

1. **Use of specific historical evidence.** Does the student cite specific evidence from the sources AND from their own knowledge? Vague references ("there is evidence that Germany wanted war") score lower than specific ones ("the War Council minutes from December 1912 show the Kaiser and his Chief of Staff discussing the inevitability of war — Fischer uses this to argue the decision was premeditated"). A student citing Fischer's position is not evidence — the evidence Fischer uses is.

2. **Quality of engagement with the counter-argument.** Does the student genuinely engage with the strongest version of the opposing interpretation, or do they dismiss it superficially? A student who writes "The revisionist argument is wrong because Germany started it" has not engaged. A student who writes "Clark's argument that all powers share responsibility is supported by Russia's premature mobilisation — this is the hardest evidence for Fischer's thesis to account for, because it suggests the escalation was not solely Germany's doing" has engaged meaningfully.

3. **Appropriate qualification of claims.** Does the student distinguish between what the evidence supports and what it does not? Claims like "this proves Germany was responsible" are over-stated — the evidence is not conclusive. Claims like "the War Council minutes suggest that at least some German leaders considered war desirable as early as 1912, though the minutes do not prove that this preference became policy" are appropriately qualified.

4. **Disciplinary accuracy of historical reasoning.** Does the student distinguish between proximate and structural causes? Between what a source says and what it means? Between what the evidence can and cannot support? Students who treat all evidence as equally weighted, or who do not consider provenance, are reasoning below the disciplinary standard.

**What distinguishes Competent from Extending:**
A Competent response evaluates both interpretations using specific evidence, engages with the counter-argument, and qualifies claims appropriately. An Extending response does all of this AND identifies a genuine limitation of the evidence base — something that NEITHER interpretation can fully explain given the available sources — and articulates what further evidence would be needed to resolve the debate. This represents the shift from evaluating within given frameworks to evaluating the frameworks themselves.

### 7. Teacher Development Notes

**What this task reveals about disciplinary thinking in history:**

Designing this task forces the teacher to confront a question most history teachers have never been asked explicitly: what is the difference between knowing about the causes of WWI and thinking historically about the causes of WWI? The answer is not obvious. A student who can list all four MAIN causes (alliances, imperialism, militarism, nationalism) and describe the July Crisis in detail has significant knowledge — but they may have no idea how to evaluate whether one cause matters more than another, or how to assess the quality of a historian's argument. The knowledge is necessary but not sufficient for thinking.

The disciplinary thinking standard — source evaluation, corroboration, distinguishing causation types, appropriate qualification — is not something most history curricula make explicit. Students are told to "evaluate sources" but rarely taught what evaluation means in history specifically: that provenance matters because it determines what a source can be used to support, that corroboration matters because no single source is sufficient for a causal claim, and that qualification matters because historical evidence is always incomplete. Making these standards explicit is itself a professional development exercise: the teacher must articulate what they do implicitly when they reason historically, which requires them to examine their own disciplinary thinking.

The Fischer debate is particularly revealing because it shows that historical knowledge is not settled. Students who have been taught "the causes of WWI" as a definitive list may find it disorienting that historians disagree fundamentally about the same events. This disorientation is productive — it is the moment where students begin to understand that history is an argument, not a narrative. But it requires the teacher to be comfortable with ambiguity, which in turn requires the teacher to understand the historiography well enough to guide students through genuine uncertainty rather than retreating to false certainty.

The "what would change my mind?" heuristic is worth noting as a transferable move. While the disciplinary thinking standards are history-specific, the habit of asking "what evidence would make me revise my position?" is a metacognitive move that transfers across disciplines. A teacher who runs this task in history and then asks their science or ethics colleagues to identify the equivalent heuristic in their disciplines is doing precisely the kind of cross-disciplinary professional learning that builds a school-wide culture of critical thinking — one discipline at a time, with the standards made explicit in each.

---

## Known Limitations

1. **Critical thinking tasks are only as good as the knowledge base that precedes them.** This skill includes a prerequisite check, but it cannot verify what students actually know — only what the teacher reports. A task designed for students who "know the alliance system" will fail if they know it only superficially. The teacher must be honest about knowledge sufficiency.

2. **The domain-specificity of thinking standards means this skill requires the teacher to have sufficient disciplinary understanding to validate the output.** The skill will produce a disciplinary thinking standard — but if that standard does not accurately reflect how experts actually reason in this domain, the task will develop pseudo-critical thinking rather than genuine disciplinary reasoning. The teacher is the quality check.

3. **One task does not develop critical thinking.** Critical thinking develops through repeated practice of disciplinary thinking across a sustained curriculum. A single well-designed task is evidence of what the curriculum should be doing consistently, not a standalone intervention. If this skill is used once per unit and the rest of the teaching is recall-based, critical thinking will not develop.

4. **The habits of mind component (intellectual humility, tolerance for ambiguity) is dispositional and cannot be developed through a single task or assessed through a rubric.** The task can cultivate these habits if the classroom culture supports them — but the classroom culture is outside the scope of this skill. If the assessment environment is controlling or high-stakes, students will perform reasoning for the rubric rather than engage in genuine thinking.

5. **Transfer between domains should not be assumed.** Running this skill in history does not mean students will think critically in science. Each discipline requires its own thinking standards to be made explicit. The appropriate response is to use this skill consistently across multiple subjects, not to assume that critical thinking developed in one domain transfers automatically.

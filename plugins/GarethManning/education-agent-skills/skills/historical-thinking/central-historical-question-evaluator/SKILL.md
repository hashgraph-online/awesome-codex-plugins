---
# AGENT SKILLS STANDARD FIELDS (v2)
name: central-historical-question-evaluator
description: "Evaluate a teacher-drafted central historical question for its capacity to drive genuine historical inquiry. Use when assessing whether a question will generate real evidence-weighing or produce shallow responses."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS
skill_id: "historical-thinking/central-historical-question-evaluator"
skill_name: "Central Historical Question Evaluator"
domain: "historical-thinking"
version: "1.0"
contributor: "Sean Hu"
evidence_strength: "strong"
evidence_sources:
  - "Reisman (2012) — Reading like a historian: a document-based history curriculum intervention in urban high schools"
  - "Wineburg, Martin & Monte-Sano (2011) — Reading like a historian: teaching literacy in middle and high school history classrooms"
  - "Wineburg & Martin (2004) — Reading and rewriting history"
  - "Wineburg (2007) — Unnatural and essential: the nature of historical thinking"
  - "Wineburg (2016) — Why historical thinking is not about history"
input_schema:
  required:
    - field: "draft_question"
      type: "string"
      description: "The teacher's draft central historical question — the question intended to drive a document-based lesson or unit"
    - field: "available_sources"
      type: "string"
      description: "Description of the primary and secondary sources students will use to investigate the question — number, types, and key tensions or perspectives represented"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current experience with document-based inquiry"
  optional:
    - field: "historical_topic"
      type: "string"
      description: "The broader topic or unit within which this question sits"
    - field: "learning_objectives"
      type: "string"
      description: "What the teacher wants students to learn or be able to do through investigating this question"
    - field: "previous_questions"
      type: "string"
      description: "Central questions from earlier lessons — to check for variety in question type and to build on what students have already practised"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: relevant curriculum standards or historical thinking framework in use"
output_schema:
  type: "object"
  fields:
    - field: "question_evaluation"
      type: "object"
      description: "Analysis of the draft question against criteria for productive historical inquiry — does it require evidence, permit multiple defensible answers, demand the use of historical thinking skills, and avoid retrievable-answer or opinion-only traps"
    - field: "strengths"
      type: "array"
      description: "What the draft question does well — specific features that will drive productive inquiry"
    - field: "threats"
      type: "array"
      description: "Specific problems with the draft question that may produce shallow, predictable, or non-historical responses — with explanations of why each is a threat"
    - field: "revised_question"
      type: "string"
      description: "If the draft question needs modification, a revised version with an explanation of what changed and why — if the draft question is strong, confirmation that no revision is needed"
    - field: "question_type_analysis"
      type: "string"
      description: "Classification of the question type and guidance on what kind of historical thinking it will demand"
chains_well_with:
  - "document-based-lesson-designer"
  - "historical-document-set-curator"
  - "historical-source-adapter"
  - "sourcing-skill-builder"
  - "corroboration-skill-builder"
  - "backwards-design-unit-planner"
  - "hinge-question-designer"
teacher_time: "2 minutes"
tags: ["historical-questions", "inquiry", "document-based-lessons", "historical-thinking", "lesson-design", "DIG"]
---

# Central Historical Question Evaluator

## What This Skill Does

Evaluates a teacher-drafted central historical question against criteria for productive historical inquiry and, if needed, suggests a revised version. The output includes an analysis of whether the question will drive genuine document-based investigation, identification of specific strengths and threats, a question type classification, and — where the draft has problems — a revised question with an explanation of what changed and why.

The central historical question is the engine of a document-based lesson. In the Reading Like a Historian curriculum (Reisman, 2012; Wineburg, Martin & Monte-Sano, 2011), every lesson is organised around a question that requires students to investigate primary sources: "Did Pocahontas rescue John Smith?", "Was Abraham Lincoln a racist?", "What caused the Dust Bowl?" These questions share specific features that distinguish them from textbook review questions or open-ended discussion prompts. They are answerable through evidence (not just opinion), they permit multiple defensible answers (not a single correct response), they require the use of historical thinking skills (sourcing, close reading, contextualisation, corroboration), and they are genuinely contested (historians disagree about them).

A poorly designed central question can undermine an otherwise well-constructed lesson. A question that has a single correct answer ("When did the Battle of Lexington take place?") requires retrieval, not inquiry. A question that is purely opinion-based ("Was slavery wrong?") invites moral assertion rather than evidence-based argument. A question that is too broad ("What happened in the American Revolution?") provides no analytical focus. This skill helps teachers identify these problems before they reach the classroom.

The skill is an evaluator, not a generator. The teacher is the expert on their students, their curriculum, and their sources. They draft the question; the skill evaluates it and, where necessary, suggests modifications. This preserves the teacher's ownership of the inquiry while providing analytical feedback they might not generate on their own.

## Evidence Foundation

Reisman (2012) structured the Reading Like a Historian curriculum around central historical questions, describing the lesson format as a four-part "activity structure": background knowledge, a central historical question, historical documents with guiding questions and strategy instruction, and whole-class discussion. The central question was the organising element — it determined which documents were selected, what strategies were foregrounded, and what counted as a successful student response. Reisman's intervention produced significant gains in historical thinking, factual knowledge, and reading comprehension, suggesting that the question-document-discussion structure is pedagogically effective.

Wineburg, Martin, and Monte-Sano (2011) provided eight fully developed examples of central historical questions in their curriculum text. Analysis of these questions reveals consistent design features: they are framed as genuine problems ("Did Pocahontas rescue John Smith?" not "Describe the Jamestown colony"), they use language that signals contestation ("Did...?", "Was...?", "Who really benefited?"), they are scoped narrowly enough that students can investigate them with a small document set (2–5 sources), and they are anchored to specific evidence rather than requiring general knowledge.

Wineburg and Martin (2004) demonstrated the pedagogical power of a well-designed historical question through the Pocahontas unit. The question "Did Pocahontas rescue John Smith?" is effective precisely because it looks simple but is genuinely complex — the answer depends on how you weigh Smith's contradictory accounts, how you interpret the historians' competing analyses, and what you decide counts as sufficient evidence. The question invites students into a real historiographical debate rather than asking them to recite a settled narrative.

Wineburg (2007) argued that productive historical inquiry begins with genuine puzzlement. The "specification of ignorance" — the expert practice of using documents to articulate what one does not know — requires a question that genuinely admits of uncertainty. If the answer is predetermined or easily retrievable, there is nothing to specify as unknown. The quality of the central question determines whether students engage in genuine inquiry or perform a research simulation where the answer was decided before they began.

## Input Schema

The teacher must provide:
- **Draft question:** The central question as currently written. *e.g. "Did Pocahontas rescue John Smith?" / "Was the dropping of the atomic bomb on Hiroshima justified?" / "What were the causes of World War I?" / "Why did people support the Nazi Party?"*
- **Available sources:** What documents students will work with. *e.g. "Smith's 1608 and 1624 accounts, plus interpretations by Adams, Lemay, Lewis, and Barbour" / "Three propaganda posters from different countries, 1914–1916" / "Two eyewitness accounts of the bombing and a excerpt from Truman's diary"*
- **Student level:** *e.g. "Year 8, new to document-based inquiry" / "Year 11 IB History, experienced with source analysis"*

Optional:
- **Historical topic:** The broader unit context
- **Learning objectives:** What students should learn
- **Previous questions:** Earlier central questions in the unit — for variety
- **Curriculum framework:** DIG, Seixas, national curriculum, etc.

## Prompt

```
You are an expert in historical thinking pedagogy and document-based lesson design, with deep knowledge of the Reading Like a Historian curriculum structure (Reisman, 2012; Wineburg, Martin & Monte-Sano, 2011) and the role of central historical questions in driving genuine inquiry. You understand that a well-designed central question is the engine of a document-based lesson — it determines whether students engage in genuine historical thinking or merely retrieve answers, recite opinions, or perform research simulations.

Your task is to evaluate a teacher-drafted central historical question:

**Draft question:** {{draft_question}}
**Available sources:** {{available_sources}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available.

**Historical topic:** {{historical_topic}}
**Learning objectives:** {{learning_objectives}}
**Previous questions:** {{previous_questions}} — if provided, check that the draft question offers variety in question type.
**Curriculum framework:** {{curriculum_framework}}

Evaluate the draft question against these criteria:

1. **Evidence-dependent:** Does answering this question REQUIRE engagement with the available sources? Or could a student answer it from general knowledge or personal opinion without reading any documents?

2. **Genuinely contested:** Does the question permit multiple defensible answers? Could two students examine the same evidence and reach different but equally well-supported conclusions? If the question has a single correct answer, it is a retrieval task, not an inquiry.

3. **Historically specific:** Is the question anchored to specific evidence, events, and actors? Or is it so broad that it becomes an essay prompt rather than an investigation? A question that can only be answered with a book is too broad for a document-based lesson.

4. **Skill-demanding:** Does answering the question require students to use historical thinking skills — sourcing, close reading, contextualisation, corroboration — or could it be answered without any of these? The best questions make one or more skills essential to reaching a defensible answer.

5. **Appropriately scoped:** Is the question answerable with the available document set? Too few sources and the question can't be investigated; too many or too complex and the question overwhelms the students.

6. **Engaging and accessible:** Will this question interest students at this level? Does its language make the task clear? Questions that use jargon, assume prior knowledge students don't have, or sound like essay prompts rather than genuine puzzles will fail to motivate inquiry.

Classify the question type:
- **Factual-investigative:** "Did X happen?" — requires weighing evidence for and against a factual claim
- **Causal-analytical:** "What caused X?" or "Why did X happen?" — requires identifying and weighing causal factors
- **Evaluative-interpretive:** "Was X justified?" or "Was X a turning point?" — requires evaluating significance or making a judgement grounded in evidence
- **Perspective-analytical:** "How did different groups see X?" — requires reconstructing multiple viewpoints
- **Comparative:** "How was X different from Y?" — requires structured comparison

Return your output in this exact format:

## Question Evaluation

**Draft question:** [The question as submitted]
**Question type:** [Classification]
**Overall verdict:** [Strong / Needs modification / Needs substantial revision]

### Strengths

[What the question does well — be specific about which criteria it meets and why]

### Threats

[Specific problems, each with an explanation of why it threatens the quality of inquiry. Number each threat.]

### Source-Question Fit

[Does the available document set support investigation of this question? Are there gaps — sources that would strengthen the investigation — or mismatches — sources that don't connect to the question?]

### Revised Question

[If the question needs modification: the revised version with a brief explanation of what changed and why. If the question is strong: "No revision needed" with a brief explanation of why the question works as drafted.]

### Teaching Notes

[1–2 practical notes for the teacher: what historical thinking skills this question will foreground, what student responses to anticipate, and any potential pitfalls to watch for during the lesson.]

**Self-check before returning output:** Verify that (a) the evaluation addresses all six criteria, (b) the strengths and threats are specific to this question, not generic, (c) the source-question fit analysis considers the actual available sources, (d) any revised question preserves the teacher's intent while addressing the identified threats, and (e) the teaching notes are practical and actionable.
```

## Example Output

**Scenario:** *Draft question: "What were the causes of World War I?" / Available sources: "An excerpt from the Treaty of Versailles (Article 231 — the 'war guilt' clause), a political cartoon from 1914 showing European alliances as a chain of dominoes, and a letter from a British soldier written in August 1914 expressing enthusiasm for the war" / Student level: "Year 9, have done two previous document-based lessons with simpler questions" / Previous questions: "Did Pocahontas rescue John Smith? (factual-investigative); Was the execution of Charles I justified? (evaluative-interpretive)"*

---

## Question Evaluation

**Draft question:** "What were the causes of World War I?"
**Question type:** Causal-analytical
**Overall verdict:** Needs modification

### Strengths

The question addresses a substantive historical topic and is framed as a causal inquiry, which is appropriate for Year 9 students building on earlier document-based work. Causal questions are good for this stage because they push students beyond factual retrieval toward analytical reasoning. The question type also provides variety from the previous two lessons (factual-investigative and evaluative-interpretive), which is a positive progression.

### Threats

1. **Too broad for the document set.** The causes of World War I is a topic that fills entire books. Three documents cannot support a genuine investigation of this question — students will either fall back on textbook knowledge they already possess or produce superficial answers that gesture at the documents without using them as evidence. The question's scope exceeds what the available sources can support.

2. **Not genuinely contested as framed.** "What were the causes?" invites a list rather than an argument. Students are likely to produce a catalogue of causes (alliances, militarism, imperialism, nationalism, assassination) rather than a thesis that must be defended with evidence. A list is not an argument; a well-designed question should require students to take a position.

3. **Not evidence-dependent.** A Year 9 student who has studied World War I could answer this question without reading any of the three documents. The question does not require the sources — it can be answered from general knowledge. This means the documents become illustrations of a pre-existing answer rather than evidence for constructing one.

4. **The sources don't align well with the question as framed.** The Treaty of Versailles (1919) is a post-war document that assigns blame — it is about how the war's causes were INTERPRETED, not about the causes themselves. The political cartoon shows alliances, which is ONE cause. The soldier's letter shows enthusiasm, which relates to public sentiment — arguably a cause, but not one the question naturally directs attention toward. The sources are individually interesting but don't cohere around "causes" as a general question.

### Source-Question Fit

The three sources are individually rich but don't form a coherent document set for the question as drafted. They are better suited to a narrower question — specifically, one that asks about BLAME or RESPONSIBILITY rather than causes. The Treaty of Versailles blames Germany. The political cartoon implies that the alliance system made war inevitable (distributed blame). The soldier's letter suggests that enthusiasm for war was widespread (complicating the idea that any single country is to blame). This set is strong for a question about how blame for the war was assigned and whether that assignment was fair — but weak for a general "what caused the war?" question.

### Revised Question

**"Who was most to blame for World War I?"**

This revision narrows the scope, makes the question genuinely contested (reasonable people disagree about where blame lies), and aligns with the available sources. The Treaty of Versailles assigns blame to Germany — students must evaluate whether this is fair. The political cartoon suggests the alliance system made war inevitable — distributing blame across multiple countries. The soldier's letter complicates blame entirely — if soldiers were ENTHUSIASTIC, can we blame governments alone? The revised question turns the documents from illustrations into evidence and requires students to weigh them against each other (corroboration), consider when and why each was produced (sourcing, contextualisation), and attend to how each frames the question of responsibility (close reading).

**What changed:** The question narrowed from a broad causal survey to a specific evaluative-interpretive question that the three available sources can genuinely investigate. "Who was most to blame?" requires a position, not a list.

### Teaching Notes

This question will foreground **corroboration** — students must weigh the three sources against each other to construct an argument about blame. It also demands **sourcing** for the Treaty of Versailles: students need to recognise that the victorious powers wrote Article 231 and that this shapes its assignment of blame. Anticipate that some students will default to listing causes rather than making an argument about blame — redirect them with: "You've told me several causes. But which country or factor do you think was MOST responsible, and what evidence from the documents supports your position?" Watch for students who treat the Treaty of Versailles as a neutral historical fact rather than a politically motivated document — this is a sourcing opportunity.

---

## Known Limitations

1. **This skill evaluates the question-source combination, not the question in isolation.** A question that is excellent with one document set may be poor with another. The evaluation is always relative to the available sources. If the teacher changes the sources after the evaluation, the analysis may no longer apply.

2. **The skill cannot assess whether a question will engage a specific group of students.** Engagement depends on local context — students' prior knowledge, interests, cultural backgrounds, and the teacher's rapport with the class. The skill can assess whether a question is structurally engaging (genuinely puzzling, clearly framed, appropriately scoped) but not whether it will land with particular students.

3. **The skill is an evaluator, not a generator.** It assesses and, where necessary, modifies teacher-drafted questions. It does not generate questions from scratch. This is deliberate: the teacher knows their students, curriculum, and sources better than any skill can. The skill provides analytical feedback on a question the teacher has already crafted.

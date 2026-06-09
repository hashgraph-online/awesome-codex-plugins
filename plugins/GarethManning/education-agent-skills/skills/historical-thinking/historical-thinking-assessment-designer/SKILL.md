---
# AGENT SKILLS STANDARD FIELDS (v2)
name: historical-thinking-assessment-designer
description: "Design formative assessments that make students' historical thinking visible — revealing whether they source, close-read, contextualise, and corroborate. Use when assessing historical thinking skills or planning a diagnostic."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS
skill_id: "historical-thinking/historical-thinking-assessment-designer"
skill_name: "Historical Thinking Assessment Designer"
domain: "historical-thinking"
version: "1.0"
contributor: "Sean Hu"
evidence_strength: "strong"
evidence_sources:
  - "Wineburg, Smith & Breakstone (2018) — What is learned in college history classes?"
  - "Reisman (2012) — Reading like a historian: a document-based history curriculum intervention in urban high schools"
  - "Wineburg (2007) — Unnatural and essential: the nature of historical thinking"
  - "Wineburg (1991) — Historical problem solving: cognitive processes in the evaluation of documentary and pictorial evidence"
  - "Wiliam (2011) — Embedded Formative Assessment"
  - "Gottlieb & Wineburg (2012) — Between Veritas and Communitas: epistemic switching in the reading of academic and sacred history"
input_schema:
  required:
    - field: "target_skills"
      type: "string"
      description: "Which historical thinking skills the assessment should target — one or more of: sourcing, close reading, contextualisation, corroboration, or 'all four'"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current level of historical thinking development"
    - field: "assessment_purpose"
      type: "string"
      description: "What the teacher wants to learn from the assessment — e.g. 'whether students source before reading without prompting', 'whether students can contextualise a document they haven't seen before', 'baseline diagnostic at the start of a unit', 'end-of-unit check on all four skills'"
  optional:
    - field: "historical_topic"
      type: "string"
      description: "The topic or period the assessment should draw from — if not provided, the skill will use a topic that is accessible without specialised prior knowledge"
    - field: "assessment_format"
      type: "string"
      description: "Preferred format — e.g. 'constructed response (short written answers)', 'multiple choice', 'mixed', 'discussion-based', 'document analysis task'"
    - field: "time_available"
      type: "string"
      description: "How much time is available for the assessment — affects the number and complexity of tasks"
    - field: "prior_instruction"
      type: "string"
      description: "What historical thinking instruction students have received — so the assessment targets what has been taught"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: relevant curriculum standards or historical thinking framework in use"
output_schema:
  type: "object"
  fields:
    - field: "assessment_tasks"
      type: "array"
      description: "The assessment tasks — each with a document or stimulus, the question or prompt, what the task is designed to reveal, and a scoring guide"
    - field: "scoring_guide"
      type: "object"
      description: "A rubric or scoring guide for each task — with descriptors for what novice, developing, and proficient responses look like, tied to the specific historical thinking skill being assessed"
    - field: "diagnostic_value"
      type: "object"
      description: "What the assessment results tell the teacher — how to interpret different response patterns and what instructional adjustments they suggest"
    - field: "validity_notes"
      type: "object"
      description: "What the assessment does and does not measure — including construct-irrelevant variance and any threats to valid interpretation of the results"
chains_well_with:
  - "document-based-lesson-designer"
  - "sourcing-skill-builder"
  - "close-reading-skill-builder"
  - "contextualisation-skill-builder"
  - "corroboration-skill-builder"
  - "assessment-validity-checker"
  - "formative-assessment-technique-selector"
  - "criterion-referenced-rubric-generator"
  - "gap-analysis-from-student-work"
  - "historical-source-adapter"
teacher_time: "4 minutes"
tags: ["assessment", "historical-thinking", "formative-assessment", "HATs", "diagnostic", "sourcing", "close-reading", "contextualisation", "corroboration", "DIG"]
---

# Historical Thinking Assessment Designer

## What This Skill Does

Designs formative assessment tasks that make students' historical thinking visible — revealing whether students are sourcing, close reading, contextualising, and corroborating, and at what level of sophistication. The output includes assessment tasks with documents and prompts, a scoring guide distinguishing novice/developing/proficient responses, diagnostic guidance on how to interpret results, and validity notes identifying what the assessment does and does not measure.

The fundamental problem this skill addresses is that most history assessments test factual recall rather than historical thinking. A test that asks "When was the Battle of Gettysburg?" measures whether students memorised a date. A test that asks "Does this painting help us understand what happened at the first Thanksgiving in 1621? Explain your reasoning" — and provides a painting created in 1932 — measures whether students consider the temporal relationship between a source and the event it depicts. The first tells you what students remember; the second tells you how students think.

Wineburg, Smith, and Breakstone (2018) demonstrated this gap devastatingly. Using History Assessments of Thinking (HATs) — brief constructed-response tasks targeting sourcing, contextualisation, and claim-evidence reasoning — they found that 94% of introductory college students ignored the 300-year gap between a 1621 event and a 1932 painting. Upper-level history majors performed only slightly better: 78% earned zero on a task requiring them to use a Senate hearing's existence (not its content) as evidence of public opposition to war. Students consistently read for content rather than context — engaging with what documents said but not with the circumstances of their creation.

These findings confirm that historical thinking skills must be explicitly assessed, not assumed. And the HATs model shows how: brief tasks centred on a document, with questions that can only be answered well by deploying specific historical thinking skills. This skill generates assessments following that model.

## Evidence Foundation

Wineburg, Smith, and Breakstone (2018) developed History Assessments of Thinking (HATs) with Library of Congress support. Three HATs were administered to 78 introductory and 49 upper-level college students. Each HAT presented a document (a painting, testimony transcripts, a playbill) with full bibliographic information and asked questions that required sourcing, contextualisation, or claim-evidence reasoning to answer well. The scoring rubric used three levels: Basic (0) — no evidence of the target skill; Emergent (1) — some evidence but incomplete or superficial; Proficient (2) — clear demonstration of the skill. The results were stark: introductory students averaged less than 0.5 out of 12, and the highest score was 3 out of 12. The HATs model demonstrates that historical thinking can be assessed briefly, authentically, and diagnostically — each task reveals a specific skill presence or absence.

Reisman (2012) used a 30-item Historical Thinking Test (22 multiple choice + 8 constructed response, α = .79) and a 20-item Transfer test as outcome measures. The Historical Thinking Test assessed application of sourcing, close reading, contextualisation, and corroboration strategies. Treatment students showed significant gains on this measure, demonstrating that historical thinking skills are both teachable and assessable. Reisman's finding that effects were concentrated in sourcing and close reading (not contextualisation or corroboration) provides diagnostic guidance: if an assessment shows students performing well on sourcing but poorly on contextualisation, this is consistent with the research — the skills develop at different rates and require different instructional approaches.

Wiliam (2011) established that formative assessment's value lies in making student thinking visible so that teachers can adjust instruction. The most useful formative assessment tasks are those that distinguish between students who have developed a skill and students who have not — tasks where the wrong answer is as informative as the right answer because it reveals a specific misconception or skill gap. For historical thinking, this means assessment tasks where a student who sources will answer differently from a student who doesn't, and where the specific way a student fails to source reveals what they need to learn next.

Wineburg (2007) argued that the distinction between "being critical" and "thinking critically" is invisible without appropriate assessment. His student Jacob was passionately critical of Columbus — but his criticism was driven by spread of activation (everything he already believed about Columbus), not by disciplinary analysis of the document. A multiple-choice test on Columbus facts would not have revealed this. Only a task requiring Jacob to engage with the document as a document — attending to its source, context, and language — could make the distinction visible.

Gottlieb and Wineburg (2012) demonstrated that the quantity of sourcing references was similar between experts and novices — the difference was qualitative. Assessment tasks must therefore distinguish between mentioning a source and interrogating it. A student who writes "This was written by John Smith in 1624" has mentioned the source. A student who writes "Smith wrote this 17 years after the event, at a time when Pocahontas had become famous, which may explain why he added the rescue story" has interrogated it. The scoring guide must capture this distinction.

## Input Schema

The teacher must provide:
- **Target skills:** *e.g. "Sourcing only" / "Sourcing and contextualisation" / "All four skills" / "Corroboration — I want to know if students can compare two accounts"*
- **Student level:** *e.g. "Year 8, midway through first term of document-based lessons" / "Year 11 IB History, experienced with source analysis" / "Year 7, baseline diagnostic before any instruction"*
- **Assessment purpose:** *e.g. "Baseline diagnostic — I want to know where students are before I start teaching sourcing" / "Mid-unit check — are students sourcing without prompting?" / "End-of-unit — can students deploy all four skills on unfamiliar documents?"*

Optional:
- **Historical topic:** Topic to draw from — if omitted, a generally accessible topic is used
- **Assessment format:** Preferred format
- **Time available:** Constrains task number and complexity
- **Prior instruction:** What has been taught
- **Curriculum framework:** For alignment

## Prompt

```
You are an expert in assessing historical thinking skills, with deep knowledge of the History Assessments of Thinking (HATs) model developed by Wineburg, Smith, and Breakstone (2018), Reisman's (2012) assessment of sourcing, close reading, contextualisation, and corroboration, and Wiliam's (2011) principles of formative assessment. You understand that the purpose of formative assessment is to make student thinking visible so that teachers can adjust instruction — and that most history assessments fail at this because they test factual recall rather than historical thinking.

Your task is to design a formative assessment:

**Target skills:** {{target_skills}}
**Student level:** {{student_level}}
**Assessment purpose:** {{assessment_purpose}}

The following optional context may or may not be provided. Use whatever is available.

**Historical topic:** {{historical_topic}} — if not provided, select a topic and document that are accessible without specialised prior knowledge (the assessment should test historical thinking, not content knowledge).
**Assessment format:** {{assessment_format}} — if not provided, default to constructed response (short written answers), as these reveal more about student thinking than multiple choice.
**Time available:** {{time_available}} — if not provided, design for 15–20 minutes (a single task or brief set of tasks, not a full exam).
**Prior instruction:** {{prior_instruction}} — if provided, align the assessment to what has been taught. If not, design tasks that can function as baseline diagnostics.
**Curriculum framework:** {{curriculum_framework}}

Design the following:

1. **Assessment tasks:** For each task:
   - **Document/stimulus:** A brief historical document or source (with full attribution) that students will work with. The document should be short enough to read in 2–3 minutes and should contain features that reward the target skills — e.g., source information that is analytically productive for sourcing tasks, language choices that reward close reading, a date that matters for contextualisation.
   - **Question/prompt:** The question students must answer. Design the question so that a student who deploys the target skill will answer DIFFERENTLY from a student who does not. The question should not cue the skill by name (don't say "Source this document") — it should require the skill without naming it.
   - **What this task reveals:** Which specific skill the task targets and what a successful vs. unsuccessful response looks like.

2. **Scoring guide:** For each task, a three-level rubric:
   - **Basic (0):** The student does not demonstrate the target skill. Describe what a Basic response looks like — what the student does instead of the target skill (e.g., evaluates the painting by whether it matches their beliefs about Thanksgiving rather than noting the 300-year temporal gap).
   - **Emergent (1):** The student demonstrates the skill partially or superficially. Describe what partial demonstration looks like (e.g., notes the date of the painting but doesn't reason about what the temporal gap means for its reliability as evidence).
   - **Proficient (2):** The student demonstrates the skill fully. Describe what a proficient response includes (e.g., identifies the temporal gap, reasons that a 1932 painter could not have witnessed 1621 events, and concludes that the painting reflects 1930s ideas about Thanksgiving rather than historical reality).

   The scoring guide must distinguish between mentioning a skill and deploying it (Gottlieb & Wineburg, 2012). "This was written by Smith in 1624" is mentioning. "Smith wrote this 17 years after the event, which raises questions about..." is deploying.

3. **Diagnostic value:** What the results tell the teacher:
   - **If most students score Basic:** What this suggests about the class's skill development and what instruction to prioritise
   - **If most students score Emergent:** What the gap between Emergent and Proficient typically looks like and how to close it
   - **If scores vary across skills:** What it means if students source well but don't contextualise (consistent with Reisman, 2012) and what instructional adjustment to make
   - **Specific response patterns to watch for:** Common wrong answers that reveal specific misconceptions (not just "the student didn't get it" but "the student evaluated the source by its content rather than its provenance, which suggests...")

4. **Validity notes:** What the assessment does and does not measure:
   - What construct the assessment targets
   - Potential construct-irrelevant variance (e.g., does the assessment inadvertently test reading comprehension, content knowledge, or writing ability rather than historical thinking?)
   - Whether the assessment can distinguish between students who lack the skill and students who possess the skill but lack the content knowledge needed to deploy it in this specific context

Return your output in this exact format:

## Historical Thinking Assessment

**Target skills:** [Skills]
**Students:** [Level]
**Purpose:** [What the teacher wants to learn]
**Time:** [Duration]

### Task 1: [Brief title]

**Document:**
[Brief source with full attribution]

**Question:**
[The prompt — designed to require the target skill without naming it]

**What this reveals:** [Target skill and what success vs. failure looks like]

**Scoring guide:**
- **Basic (0):** [Description of a response that does not demonstrate the skill]
- **Emergent (1):** [Description of a partial or superficial demonstration]
- **Proficient (2):** [Description of a full demonstration]

[Repeat for additional tasks]

### Diagnostic Value

**If most students score Basic:** [What it means and what to do]
**If most students score Emergent:** [The gap and how to close it]
**If scores vary across skills:** [What the pattern reveals]
**Response patterns to watch for:** [Specific wrong answers and what they diagnose]

### Validity Notes

**What this assesses:** [The construct]
**Potential threats:** [Construct-irrelevant variance]
**Important caveat:** [Skill vs. knowledge distinction]

**Self-check before returning output:** Verify that (a) the questions require the target skill without naming it, (b) the scoring guide distinguishes between mentioning and deploying the skill, (c) a student who sources/close-reads/contextualises/corroborates will answer DIFFERENTLY from one who doesn't — the task discriminates, (d) the diagnostic value provides specific instructional guidance, not just "teach more sourcing," and (e) the validity notes honestly identify what the assessment does not measure.
```

## Example Output

**Scenario:** *Target skills: "Sourcing and contextualisation" / Student level: "Year 9, have received six weeks of sourcing instruction, contextualisation introduced but not yet practised independently" / Assessment purpose: "Mid-unit check — can students source without prompting, and are they beginning to contextualise?" / Time available: "15 minutes" / Historical topic: "not specified — use an accessible topic"*

---

## Historical Thinking Assessment

**Target skills:** Sourcing and contextualisation
**Students:** Year 9, six weeks of sourcing instruction, early contextualisation
**Purpose:** Mid-unit diagnostic — sourcing habit and emerging contextualisation
**Time:** 15 minutes (two tasks, approximately 7 minutes each)

### Task 1: The Thanksgiving Painting (Sourcing)

**Document:**
*A colour reproduction of J.L.G. Ferris's "The First Thanksgiving 1621"*
Source note: "J.L.G. Ferris, *The First Thanksgiving 1621*, oil on canvas, painted c. 1912–1915, published 1932."

**Question:**
"Does this painting help historians understand the relationship between the Pilgrims and the Wampanoag people in 1621? Explain your reasoning."

**What this reveals:** Whether students attend to the source information (date of painting vs. date of event) when evaluating a document's usefulness as historical evidence. A student who sources will note the 300-year gap. A student who does not will evaluate the painting based on whether its content matches their beliefs about Thanksgiving.

**Scoring guide:**
- **Basic (0):** The student evaluates the painting by its content alone. "Yes, it shows them eating together peacefully, so they had a good relationship" or "No, it makes it look too friendly when actually the Pilgrims were mean to the Native Americans." In both cases, the student is judging the painting by whether it matches their prior beliefs. The date of the painting is ignored.
- **Emergent (1):** The student notes the date but does not fully reason about its implications. "This was painted in 1912, which is a long time after 1621" or "The painter wasn't there, so it might not be accurate." The temporal gap is identified but the reasoning stops at "might not be accurate" without explaining WHY the gap matters or what the painting might reflect instead.
- **Proficient (2):** The student identifies the temporal gap and reasons about its consequences. "This was painted nearly 300 years after 1621, so Ferris couldn't have seen this event. The painting probably shows what people in the early 1900s imagined Thanksgiving looked like, not what actually happened. It might be more useful as evidence of how Americans in 1912 wanted to remember Thanksgiving than as evidence of the actual event."

### Task 2: The Recruitment Poster (Contextualisation)

**Document:**
*A World War I British recruitment poster showing a man sitting in an armchair while his children ask "Daddy, what did YOU do in the Great War?"*
Source note: "Parliamentary Recruiting Committee, printed by Johnson, Riddle & Co., London, 1915."

**Question:**
"Why was this poster created in 1915? What was happening at that time that made it necessary?"

**What this reveals:** Whether students can connect a document to its historical context. A student who contextualises will link the poster to 1915 circumstances (Britain relied on voluntary enlistment before conscription in 1916; the initial enthusiasm was fading; casualties were mounting). A student who does not will describe what the poster shows without connecting it to why it existed.

**Scoring guide:**
- **Basic (0):** The student describes the poster's content or states its obvious purpose without connecting it to 1915 specifically. "It was created to make men feel guilty so they would join the army" or "It's showing a dad who didn't fight in the war." These responses identify the poster's persuasive intent but don't explain why this kind of persuasion was needed in 1915 — the response would be the same if the poster were from 1914 or 1917.
- **Emergent (1):** The student makes a general connection to the war but doesn't specify what about 1915 made this poster necessary. "It was created because World War I was happening and they needed soldiers" or "Britain needed more men to fight." The context is present but vague — the student hasn't identified what was specific about 1915 that prompted this kind of recruitment.
- **Proficient (2):** The student connects the poster to specific 1915 circumstances. "By 1915, the war had been going on for over a year and the initial rush of volunteers was slowing down. Britain hadn't introduced conscription yet, so they relied on posters like this to pressure men into enlisting. The emotional manipulation — using children to guilt fathers — suggests that straightforward patriotic appeals weren't working anymore." The student uses contextual knowledge to explain not just THAT the poster was created but WHY it took this particular form at this particular moment.

### Diagnostic Value

**If most students score Basic on Task 1 (sourcing):** After six weeks of sourcing instruction, students should be attending to the source note. If most are scoring Basic, sourcing has not become habitual — students are still reading for content without checking the source. Return to the foundational sourcing routine: cover the document text and require 60 seconds on the source note before reading. The skill has been introduced but not internalised.

**If most students score Emergent on Task 1:** The habit is forming — students notice the date — but the analytical depth is missing. They identify the gap without reasoning about its implications. This is the distinction Gottlieb and Wineburg (2012) identified: mentioning vs. interrogating. Instruction should focus on the "So what?" move: after students note the date, push them to explain what it means for the document's reliability.

**If most students score Basic on Task 2 (contextualisation) but Emergent/Proficient on Task 1 (sourcing):** This is entirely consistent with the research. Reisman (2012) found treatment effects for sourcing but not for contextualisation. Sourcing is more concrete and develops faster. Contextualisation requires both knowledge AND the disposition to deploy it. Check whether the gap is knowledge (students don't know about 1915 recruitment conditions) or deployment (they know but don't connect it to the document). If knowledge, provide more background. If deployment, use the two-step bridge scaffold from contextualisation-skill-builder.

**Response patterns to watch for:**
- *Evaluating by content agreement:* "Yes, the painting is helpful because it shows a peaceful meal" — the student treats the painting's content as transparent truth. They need to learn that all sources have authors with perspectives.
- *Binary reliability judgement:* "We can't trust this because it was painted 300 years later" — correct observation, wrong conclusion. The painting IS useful — as evidence of how later generations imagined the event. The student needs to learn that "unreliable as an account of 1621" is not the same as "useless."
- *Describing without connecting:* "The poster shows a father with his children" — pure description. The student has not engaged with WHY the poster exists, only with WHAT it shows. This is reading for content, not context.

### Validity Notes

**What this assesses:** Whether students spontaneously deploy sourcing (Task 1) and contextualisation (Task 2) when interpreting historical documents. The tasks are designed so that the target skill produces a qualitatively different response from its absence — not a better version of the same response, but a fundamentally different one.

**Potential threats:** Task 2 (contextualisation) may measure content knowledge about World War I recruitment rather than the contextualisation skill itself. A student who lacks knowledge of 1915 Britain cannot contextualise the poster regardless of their skill level. If this assessment is used with students who have not studied WWI, Task 2 assesses knowledge rather than skill — and low scores should not be interpreted as evidence that students cannot contextualise. Consider replacing the poster with a document from a period students have studied if content knowledge is uncertain.

**Important caveat:** A student who scores Proficient on these tasks with familiar topics may not transfer the skills to unfamiliar topics. Sourcing and contextualisation were practised with specific document types during instruction; whether students generalise these skills to new types of sources is an open question. An end-of-unit assessment should include at least one document from outside the topics covered in class to test for transfer (cf. Reisman, 2012, who found significant transfer effects using unfamiliar contemporary topics).

---

## Known Limitations

1. **Constructed-response tasks reveal more about student thinking than multiple choice, but they also measure writing ability.** A student who thinks historically but writes poorly may score lower than their historical thinking warrants. Teachers should supplement written assessments with observation during discussion (see the assessment indicators in each skill builder) to triangulate. Where possible, allow students to explain their reasoning verbally as well as in writing.

2. **The HATs model (Wineburg, Smith & Breakstone, 2018) was developed and tested with US college students reading US history documents.** The task structure (document + question requiring a specific skill) transfers to other contexts, but the specific documents and scoring descriptors must be adapted for different age groups, national curricula, and historical topics.

3. **Formative assessment is only useful if it changes instruction.** The diagnostic value section provides specific instructional guidance for each score pattern, but the teacher must act on it. An assessment that reveals students are not contextualising but leads to no change in instruction is a wasted opportunity. The assessment's value lies entirely in what happens next.

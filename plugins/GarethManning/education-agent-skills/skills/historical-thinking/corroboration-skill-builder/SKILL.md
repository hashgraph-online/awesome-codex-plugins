---
# AGENT SKILLS STANDARD FIELDS (v2)
name: corroboration-skill-builder
description: "Build students' capacity to compare accounts across multiple historical sources — identifying agreements, contradictions, and gaps. Use when students treat individual documents as complete answers rather than partial perspectives."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS
skill_id: "historical-thinking/corroboration-skill-builder"
skill_name: "Corroboration Skill Builder"
domain: "historical-thinking"
version: "1.0"
contributor: "Sean Hu"
evidence_strength: "moderate"
evidence_sources:
  - "Wineburg (1991) — Historical problem solving: cognitive processes in the evaluation of documentary and pictorial evidence"
  - "Reisman (2012) — Reading like a historian: a document-based history curriculum intervention in urban high schools"
  - "Wineburg & Reisman (2015) — Disciplinary literacy in history: a toolkit for digital citizenship"
  - "Wineburg & Martin (2004) — Reading and rewriting history"
  - "Wineburg, Martin & Monte-Sano (2011) — Reading like a historian: teaching literacy in middle and high school history classrooms"
  - "Wineburg, Smith & Breakstone (2018) — What is learned in college history classes?"
input_schema:
  required:
    - field: "historical_topic"
      type: "string"
      description: "The historical topic, period, or question students are investigating"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current level of experience with multi-document analysis"
    - field: "current_challenge"
      type: "string"
      description: "What students currently do or fail to do when working with multiple sources — the observable behaviour that signals corroboration is not yet developed"
  optional:
    - field: "available_documents"
      type: "string"
      description: "Description of the specific document set students will work with — number of documents, types, and the tensions or contradictions built into the set"
    - field: "source_types"
      type: "string"
      description: "The mix of source types in the document set — e.g. two eyewitness accounts, an eyewitness plus a historian, primary and secondary sources, text and image"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: relevant curriculum standards or historical thinking framework in use"
    - field: "prior_instruction"
      type: "string"
      description: "What corroboration instruction students have already received, and whether they have developed sourcing, close reading, and contextualisation skills that corroboration builds on"
output_schema:
  type: "object"
  fields:
    - field: "corroboration_progression"
      type: "object"
      description: "What corroboration looks like at novice, developing, and proficient levels — with observable indicators distinguishing between reading multiple sources sequentially and genuinely comparing them to establish what is probable"
    - field: "explicit_instruction_sequence"
      type: "object"
      description: "A three-part sequence for teaching corroboration, designed for the complexity of multi-document reasoning — includes strategies for making the comparison move explicit rather than assuming students will naturally connect accounts"
    - field: "corroboration_prompts"
      type: "array"
      description: "Prompts that guide students to compare across documents — calibrated to the specific document set where possible"
    - field: "common_failure_patterns"
      type: "array"
      description: "Specific ways students fail to corroborate, including treating each document as an isolated reading task and defaulting to 'picking a side' rather than weighing evidence"
    - field: "assessment_indicators"
      type: "object"
      description: "Observable signs that students are corroborating — what to listen for in discussion, what to look for in written work"
chains_well_with:
  - "sourcing-skill-builder"
  - "close-reading-skill-builder"
  - "contextualisation-skill-builder"
  - "historical-thinking-strategy-modelling-guide"
  - "document-based-lesson-designer"
  - "historical-document-set-curator"
  - "historical-thinking-assessment-designer"
  - "argument-structure-scaffold-generator"
teacher_time: "4 minutes"
tags: ["corroboration", "historical-thinking", "disciplinary-literacy", "multi-document-reasoning", "evidence-weighing", "document-analysis", "DIG"]
---

# Corroboration Skill Builder

## What This Skill Does

Designs targeted instruction to develop students' corroboration practice — comparing accounts across multiple sources to identify agreements, contradictions, silences, and gaps, and using these comparisons to establish what is probable rather than accepting any single account as definitive. The output includes a developmental progression, an explicit instruction sequence designed for multi-document reasoning, corroboration prompts, common failure patterns, and assessment indicators.

Corroboration is the most complex of the four historical thinking skills because it is inherently intertextual. Sourcing, close reading, and contextualisation can each be practised on a single document. Corroboration cannot — it requires holding multiple accounts in mind simultaneously and reasoning about the relationships between them. This makes it the hardest to teach and the last to develop. Reisman (2012) found no significant treatment effects for corroboration in her six-month intervention, alongside contextualisation. She attributed this partly to the near-absence of whole-class discussion in treatment classrooms — corroboration may require dialogic instruction (discussion, debate, collaborative comparison) more than the other skills because the reasoning is inherently comparative.

Corroboration also depends on the other three skills as prerequisites. To compare sources productively, students must first be able to source each document (who wrote it and why), close-read each document (what exactly does it claim and how), and contextualise each document (what circumstances shaped it). Without these foundations, corroboration degrades into surface-level observation ("these two accounts say different things") rather than analytical reasoning about WHY they differ and what the differences reveal.

## Evidence Foundation

Wineburg (1991) identified corroboration as one of three core heuristics (alongside sourcing and contextualisation) that distinguished expert historians from novice readers. Historians systematically compared accounts, noting where they agreed and diverged, and used discrepancies as diagnostic tools — a contradiction between two sources was not a problem to resolve by picking the "right" one but a clue that demanded explanation. Why would two observers describe the same event differently? The answer always pointed back to the authors' perspectives, circumstances, and purposes.

Wineburg and Martin (2004) demonstrated corroboration in curricular practice through the Pocahontas unit. Students compared John Smith's 1608 and 1624 accounts — the same author contradicting himself — and then examined four historians who used the same evidence to reach different conclusions. The pedagogical power of this design lies in the layered contradiction: first, the same person disagrees with his earlier self; then, professional historians disagree with each other using the same documents. Students learn that historical knowledge is not found in any single source but constructed through the comparison and weighing of multiple accounts.

The Pocahontas chapter in Wineburg, Martin, and Monte-Sano (2011) operationalised corroboration through structured comparison tools. Students used worksheets that required them to identify what each source says, where sources agree and disagree, and what might explain the differences. The lesson architecture — reading sources in successive rounds, with whole-class discussion after each round — was designed to scaffold the comparative reasoning that corroboration demands.

Reisman (2012) found no significant treatment effects for corroboration. Her explanation was twofold: corroboration requires connections between documents (harder to model with discrete actions than sourcing), and the instructional conditions in her study may not have supported it — whole-class discussion, where comparative reasoning becomes visible and practicable, was extremely rare in treatment classrooms. This suggests that corroboration may require more dialogic, discussion-based instruction than a document-based lesson structure typically provides.

Wineburg, Smith, and Breakstone (2018) demonstrated the absence of corroboration in college students. When given two documents about the Philippine-American War — Senate testimony describing atrocities and a colonel's letter defending the war — over 80% of students analysed each document in isolation. They did not ask what the existence of BOTH documents (an investigation AND a defence) revealed about the broader public debate. Each document was treated as a self-contained reading task rather than as one piece of a larger evidentiary picture.

## Input Schema

The teacher must provide:
- **Historical topic:** *e.g. "Did Pocahontas rescue John Smith?" / "What caused the fall of the Roman Republic?" / "Was the dropping of the atomic bomb justified?"*
- **Student level:** *e.g. "Year 8, can analyse individual documents but don't compare them" / "Year 10, compare documents superficially (this one says X, that one says Y) but don't reason about why they differ" / "Year 12, can compare two sources but struggle to synthesise across three or more"*
- **Current challenge:** *e.g. "They read each document separately and don't connect them" / "They pick the source they find most convincing and ignore the others" / "They note that sources disagree but treat this as a dead end rather than a starting point for analysis"*

Optional:
- **Available documents:** Description of the document set — particularly important for corroboration because the analytical possibilities depend on what tensions exist between the sources
- **Source types:** The mix of source types matters — comparing two eyewitness accounts is different from comparing an eyewitness to a historian
- **Curriculum framework, prior instruction** — as per other skill builders

## Prompt

```
You are an expert in historical thinking pedagogy, with deep knowledge of Wineburg's (1991) identification of corroboration as a core historical thinking heuristic, Reisman's (2012) finding that corroboration did NOT show significant treatment effects in a six-month intervention (suggesting it requires different or more sustained instructional strategies than sourcing and close reading), and the Document-Based Lesson structure from Wineburg, Martin, and Monte-Sano (2011) that scaffolds multi-document comparison through successive rounds of reading and discussion.

You understand that corroboration is the most complex of the four historical thinking skills because it is inherently intertextual — it requires holding multiple accounts in mind and reasoning about relationships between them. You also understand that corroboration depends on sourcing, close reading, and contextualisation as prerequisites: students must be able to analyse individual documents before they can compare them productively.

Your task is to design targeted corroboration instruction for:

**Historical topic:** {{historical_topic}}
**Student level:** {{student_level}}
**Current challenge:** {{current_challenge}}

The following optional context may or may not be provided. Use whatever is available.

**Available documents:** {{available_documents}} — if provided, design the corroboration instruction around the specific tensions and contradictions in this document set. If not, design generalisable instruction with guidance on what kinds of document pairings create productive comparison opportunities.
**Source types:** {{source_types}}
**Curriculum framework:** {{curriculum_framework}}
**Prior instruction:** {{prior_instruction}} — particularly important to know whether students have developed sourcing, close reading, and contextualisation skills. If they have not, note that corroboration instruction should be preceded by work on those foundational skills.

Design the following:

1. **Corroboration progression:** What corroboration looks like at three levels:
   - **Novice:** The student reads each document as an isolated task. Even when given multiple sources, they analyse them one at a time without connecting them. If asked what the documents tell us together, they summarise each one separately. Describe what this looks like with observable indicators.
   - **Developing:** The student notices that sources agree or disagree but treats this as an observation rather than an analytical tool. They may say "Source A says X and Source B says Y" but do not reason about WHY they differ or what the differences reveal. They may default to picking the source they find most convincing rather than weighing the accounts against each other. Describe what this surface-level comparison looks like.
   - **Proficient:** The student uses agreements and contradictions between sources as diagnostic tools. When sources agree, they consider whether this confirms an account or whether both sources might share the same bias. When sources disagree, they reason about WHY — considering each author's perspective, circumstances, and purpose — and use the disagreement to build a more nuanced understanding than any single source provides. Describe what this analytical corroboration looks like.

2. **Explicit instruction sequence:**
   - **I DO:** A think-aloud script (150–200 words) showing the teacher modelling corroboration — reading a passage from one document, then turning to another and explicitly comparing them. The think-aloud should model the reasoning: "Document A says ___, but Document B says ___. Why might they differ? If I think about who wrote each one and when..."
   - **WE DO:** A guided practice activity that structures the comparison. Consider using a comparison matrix (what does Source A say about X? What does Source B say about X? Do they agree? If not, what might explain the difference?) or a structured discussion protocol where pairs argue for different sources before the class synthesises. The key is making the comparison step DELIBERATE rather than hoping students will do it naturally.
   - **YOU DO:** Independent corroboration with monitoring criteria.

3. **Corroboration prompts:** Prompts that guide multi-document comparison. For each prompt, include the prompt, why it matters, and a sentence starter. Prompts should push students beyond noting disagreement toward reasoning about what disagreement reveals.

4. **Common failure patterns:** 3–4 patterns including the "isolated reading" pattern (treating each document as a separate task) and the "picking a winner" pattern (choosing the most convincing source rather than weighing all accounts).

5. **Assessment indicators:** What to listen for, what to look for, and the key test.

Return your output in this exact format:

## Corroboration Instruction Plan

**Topic:** [Historical topic]
**Students:** [Level and current challenge]
**Document set:** [Description of available documents or "general"]

### Corroboration Progression

**Novice — reading documents in isolation:**
[Observable indicators]

**Developing — noting agreement/disagreement without reasoning about it:**
[Observable indicators]

**Proficient — using comparison as a diagnostic tool:**
[Observable indicators]

### Explicit Instruction Sequence

**I DO — Teacher Think-Aloud**
[Script, 150–200 words]

**WE DO — Guided Practice**
[Structured comparison activity]

**YOU DO — Independent Practice**
[What to monitor for]

### Corroboration Prompts

[Prompts with rationale and sentence starters]

### Common Failure Patterns

[3–4 patterns]

### Assessment Indicators

**In discussion:** [What to listen for]
**In written work:** [What to look for]
**The key test:** [Single most reliable indicator]

**Self-check before returning output:** Verify that (a) the progression distinguishes between noting that sources disagree and reasoning about WHY they disagree, (b) the think-aloud models cross-document reasoning, not sequential single-document analysis, (c) the guided practice includes a structure that makes comparison deliberate, (d) the failure patterns address both "isolated reading" and "picking a winner," and (e) the instruction design accounts for the finding that corroboration requires dialogic instruction and builds on the other three skills.
```

## Example Output

**Scenario:** *Historical topic: "Did Pocahontas rescue John Smith?" / Student level: "Year 8, can source and close-read individual documents but don't compare across documents" / Current challenge: "They analyse Smith's 1608 account, then analyse his 1624 account, but don't connect them — they don't reason about why the same person told different stories" / Available documents: "Smith's 1608 True Relation, Smith's 1624 General History, Adams's 1867 critique, Lemay's 1991 defence" / Source types: "Two primary accounts by the same author, two secondary interpretations by different historians"*

---

## Corroboration Instruction Plan

**Topic:** Did Pocahontas rescue John Smith?
**Students:** Year 8, can analyse individual documents but don't compare across them
**Document set:** Smith 1608, Smith 1624, Adams 1867, Lemay 1991

### Corroboration Progression

**Novice — reading documents in isolation:**
The student produces separate analyses of each document. Asked about the 1608 account, they summarise what Smith says. Asked about the 1624 account, they summarise that one separately. They may not even notice the contradiction without explicit prompting. If they do notice, they treat it as confusing rather than analytically productive: "I don't know which one is true." The documents live in separate mental compartments. The student has not yet understood that the relationship BETWEEN sources is itself evidence.

**Developing — noting disagreement without reasoning about it:**
The student observes that the accounts differ: "In the 1608 version, Smith doesn't mention the rescue, but in the 1624 version he does." They may also note that Adams and Lemay disagree. But the observation is the endpoint, not the beginning of analysis. They may say "So we don't know what really happened" and stop. Or they pick the account they find most convincing — often the more dramatic 1624 version — without explaining why that source should be privileged over the others.

**Proficient — using comparison as a diagnostic tool:**
The student uses the contradiction between Smith's two accounts as a research question: "Why would Smith add the rescue story 16 years later?" They bring sourcing and contextualisation to bear on this question: the 1624 account was written after Pocahontas had become famous in England. They use Adams's critique to challenge Smith's credibility and Lemay's defence to consider alternative explanations. Their conclusion is not "the rescue did/didn't happen" but a weighing of the evidence: "The fact that Smith didn't mention the rescue in 1608 when it supposedly happened, but added it in 1624 when Pocahontas was famous, suggests he may have been enhancing his own reputation — but Lemay argues he had different purposes for each account, which could also explain the differences."

### Explicit Instruction Sequence

**I DO — Teacher Think-Aloud**

*Teacher has both Smith accounts displayed side by side:*

"I've read both of these documents individually. Now I need to put them next to each other and ask: what happens when I compare them? In 1608, Smith writes 'He kindly welcomed me with good words and great platters of sundry victuals, assuring me his friendship.' In 1624, for the same meeting, he writes 'having feasted him after their best barbarous manner they could... being ready with their clubs to beat out his brains.'

Same person. Same event. Completely different language. The 1608 version: friendly, generous, safe. The 1624 version: barbarous, violent, near-death. I can't explain this by saying Smith just forgot the details — you don't forget someone trying to beat your brains out. So something ELSE is going on.

What changed between 1608 and 1624? Smith's circumstances changed. Pocahontas became famous. The relationship between colonists and Powhatan deteriorated. Smith was writing for a different audience with different purposes. The contradiction doesn't mean one account is true and the other false — it means both accounts are shaped by the moment they were written. And THAT is more historically interesting than either account alone."

**WE DO — Guided Practice**

Students receive a comparison matrix with four columns: What does this source say about the rescue? | When was it written? | Why might the author present it this way? | Does it agree or disagree with the other sources, and why?

In pairs, students complete one row for Smith 1608 and one row for Smith 1624. Then they write one sentence answering: "What does the DIFFERENCE between these two accounts tell us that neither account tells us on its own?"

Teacher circulates. Key redirections:
- If students complete the rows but skip the comparison sentence: "You've analysed each source. Now — what do they tell us TOGETHER that neither tells us alone? The contradiction IS the evidence."
- If students write "One of them must be lying": "Maybe. But what if neither is lying and both are just telling the story that suited their purpose at the time? What would that mean for how we use these sources?"

Class discussion: two or three pairs share their comparison sentences. Teacher models how to extend the comparison to the historians: "Now let's see what Adams and Lemay do with this same contradiction. Do they agree about what the contradiction means?"

**YOU DO — Independent Practice**

Students receive Adams's and Lemay's interpretations. Working independently, they write a paragraph that addresses: "Adams and Lemay both examine the same evidence — Smith's two accounts. They reach different conclusions. What does each one argue, and which do you find more persuasive based on the evidence?" The task requires students to compare the historians' arguments, not just summarise them.

Teacher monitors for whether students compare the two interpretations or analyse them in isolation.

### Corroboration Prompts

1. **Where do these sources agree, and does the agreement prove anything?**
   *Why it matters:* Students often assume that if two sources agree, the claim must be true. But two sources might agree because they share the same perspective or draw on the same information. Agreement is evidence, not proof.
   *Sentence starter:* "Sources A and B both say ___, but this might be because they both..."

2. **Where do these sources disagree, and what might explain the disagreement?**
   *Why it matters:* This is the core corroboration move. Disagreement is not a dead end but a diagnostic tool — the explanation for WHY sources disagree often reveals more about the past than either source alone.
   *Sentence starter:* "Source A says ___ while Source B says ___. This might be because..."

3. **What does each source leave out that the other includes?**
   *Why it matters:* Silences are as important as statements. What an author omits — and what another author includes — reveals what each considered important, irrelevant, or inconvenient.
   *Sentence starter:* "Source A doesn't mention ___, even though Source B says it was significant. This might be because..."

4. **Based on ALL the sources together, what do we think probably happened — and how certain can we be?**
   *Why it matters:* This pushes students toward the historian's goal: establishing what is probable by weighing multiple accounts, not picking one and calling it truth. The qualifier "probably" is important — it signals that historical knowledge is provisional.
   *Sentence starter:* "Based on the evidence from all the sources, it seems most likely that ___, although we can't be certain because..."

### Common Failure Patterns

**1. "Isolated reading" — analysing documents one at a time without connecting them**
*What it looks like:* The student produces a paragraph about Source A, then a paragraph about Source B, with no connection between them. Each document is a self-contained reading task.
*Why:* Classroom routines often reinforce sequential processing — "read Document 1 and answer the questions, then read Document 2 and answer the questions." The comparison step is assumed but not structured.
*Response:* Use a comparison matrix or side-by-side display that makes the documents physically adjacent. Require a written comparison sentence ("These sources agree/disagree about ___ because ___") before allowing students to write anything else. Structure forces comparison.

**2. "Picking a winner" — choosing the most convincing source and dismissing the rest**
*What it looks like:* "I believe Source B because it has more detail" or "Source A is more reliable because it's a primary source." The student treats corroboration as a competition between sources rather than a process of weighing them.
*Why:* Students are accustomed to finding "the right answer." When sources disagree, they look for the correct one rather than reasoning about what the disagreement reveals.
*Response:* Explicitly forbid the phrase "I believe Source ___" in the first draft. Instead require: "Source A is more convincing on the question of ___ because ___, but Source B is more convincing on ___ because ___." This forces recognition that different sources have different strengths for different questions.

**3. "Contradiction as dead end" — treating disagreement as proof that we can't know anything**
*What it looks like:* "The sources disagree, so we can't really know what happened." The student treats contradiction as a reason to give up rather than a reason to dig deeper.
*Why:* This reflects an epistemological stage: the student has moved past naive realism (one source = truth) but hasn't yet reached the understanding that historical knowledge is constructed by weighing evidence. They're stuck in relativism.
*Response:* "You're right that we can't know for certain. But historians don't give up when sources disagree — that's where the interesting work begins. The question isn't 'which one is true?' It's 'what does the disagreement TELL us?' WHY do these sources disagree? What does that reveal about the people who wrote them and the times they lived in?"

### Assessment Indicators

**In discussion:** Listen for students who spontaneously reference one source while discussing another: "But in the other document, Smith said..." or "Adams disagrees with Lemay about this because..." The hallmark of corroboration is cross-referencing — talking about documents in relation to each other rather than in isolation. Also listen for students who ask "What do the other sources say about this?" when encountering a claim.

**In written work:** Look for paragraphs that hold multiple sources in tension rather than treating them sequentially. A developing student writes: "Source A says X. Source B says Y." A proficient student writes: "While Source A claims X, Source B's account suggests Y. The disagreement may be explained by the fact that A was writing for ___ while B was writing for ___." The structural marker is the connective tissue — words like "while," "however," "this contradicts," "which is consistent with" — that links sources to each other.

**The key test:** After completing a multi-document activity, ask students: "What do these sources tell us TOGETHER that no single source could tell us on its own?" A student who can answer this question — articulating how comparison generates knowledge that individual analysis cannot — has understood the purpose of corroboration. A student who restates what each source says individually has not.

---

## Known Limitations

1. **Corroboration did not show significant treatment effects in Reisman (2012).** Like contextualisation, the instructional strategies here draw on expert reading behaviours and curricular design principles rather than tested interventions. Evidence strength is rated "moderate" accordingly. The suggestion that corroboration requires more dialogic instruction (whole-class discussion, structured debate) than the standard document-based lesson provides is a plausible but untested hypothesis.

2. **Corroboration depends on the other three skills as prerequisites.** Students who cannot source, close-read, or contextualise individual documents will not corroborate them productively — they will compare surface content rather than reasoning about why accounts differ. Teachers should ensure students have at least developing-level competence in the other three skills before emphasising corroboration.

3. **The quality of corroboration depends heavily on the document set.** Two sources that say essentially the same thing provide no analytical leverage for comparison. Productive corroboration requires sources that create genuine tension — different perspectives on the same event, contradictions in emphasis or detail, or visible silences where one account omits what another includes. See historical-document-set-curator for guidance on designing document sets with built-in analytical tension.

---
# AGENT SKILLS STANDARD FIELDS (v2)
name: sourcing-skill-builder
description: "Build students' capacity to interrogate a historical source before reading — asking who authored it, when, why, and what this means for reliability. Use when students read documents without attending to authorship."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS
skill_id: "historical-thinking/sourcing-skill-builder"
skill_name: "Sourcing Skill Builder"
domain: "historical-thinking"
version: "1.0"
contributor: "Sean Hu"
evidence_strength: "strong"
evidence_sources:
  - "Wineburg (1991) — Historical problem solving: cognitive processes in the evaluation of documentary and pictorial evidence"
  - "Wineburg (1998) — Reading Abraham Lincoln: an expert/expert study in historical cognition"
  - "Wineburg (2007) — Unnatural and essential: the nature of historical thinking"
  - "Gottlieb & Wineburg (2012) — Between Veritas and Communitas: epistemic switching in the reading of academic and sacred history"
  - "Reisman (2012) — Reading like a historian: a document-based history curriculum intervention in urban high schools"
  - "Wineburg & Reisman (2015) — Disciplinary literacy in history: a toolkit for digital citizenship"
input_schema:
  required:
    - field: "historical_topic"
      type: "string"
      description: "The historical topic, period, or question students are investigating"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current level of experience with primary source analysis"
    - field: "current_challenge"
      type: "string"
      description: "What students currently do or fail to do when encountering a historical source — the observable behaviour that signals sourcing is not yet habitual"
  optional:
    - field: "source_type"
      type: "string"
      description: "The type of historical source students are working with — e.g. written testimony, government document, photograph, political cartoon, newspaper article, map, personal letter"
    - field: "available_documents"
      type: "string"
      description: "Description of the specific documents students will encounter in the lesson or unit"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: relevant curriculum standards or historical thinking framework in use — e.g. DIG, Seixas Big Six, national curriculum requirements"
    - field: "prior_instruction"
      type: "string"
      description: "What sourcing instruction students have already received — so recommendations build on rather than repeat previous work"
output_schema:
  type: "object"
  fields:
    - field: "sourcing_progression"
      type: "object"
      description: "What sourcing looks like at novice, developing, and proficient levels for this student age group — with observable indicators at each level, distinguishing between mentioning a source and interrogating it"
    - field: "explicit_instruction_sequence"
      type: "object"
      description: "A three-part sequence (model → guided practice → independent practice) for teaching sourcing with the specified source type, including a teacher think-aloud script demonstrating what an expert reader does with bibliographic information before reading the text"
    - field: "guiding_questions"
      type: "array"
      description: "Source-type-specific questions students should ask before and during reading — adapted from the DIG sourcing protocol but calibrated to the developmental level and source type"
    - field: "common_failure_patterns"
      type: "array"
      description: "Specific ways students at this level typically fail to source — with targeted instructional responses for each"
    - field: "assessment_indicators"
      type: "object"
      description: "Observable signs that students are developing sourcing as a habitual practice rather than a prompted behaviour — what to listen for in discussion, what to look for in written work"
chains_well_with:
  - "close-reading-skill-builder"
  - "contextualisation-skill-builder"
  - "corroboration-skill-builder"
  - "historical-thinking-strategy-modelling-guide"
  - "document-based-lesson-designer"
  - "historical-source-adapter"
  - "historical-thinking-assessment-designer"
  - "source-credibility-evaluation-protocol"
teacher_time: "3 minutes"
tags: ["sourcing", "historical-thinking", "primary-sources", "disciplinary-literacy", "document-analysis", "Wineburg", "DIG"]
---

# Sourcing Skill Builder

## What This Skill Does

Designs targeted instruction to develop students' sourcing practice — the habit of interrogating who authored a historical document, when, why, for what audience, and what this means for the document's reliability — before and during reading. The output includes a developmental progression (what sourcing looks like from novice to proficient at the specified level), an explicit instruction sequence with a teacher think-aloud script, source-type-specific guiding questions, common failure patterns with instructional responses, and assessment indicators that distinguish between students who mention sources and students who interrogate them.

Sourcing is the foundational move in historical thinking. Wineburg and Reisman (2015) described it as the touchstone distinguishing expert from novice practice in every study of historical reading. But there is a critical distinction between routinised sourcing (students habitually glance at the source note because they have been trained to) and analytical sourcing (students use source information to generate hypotheses about the document's reliability, purpose, and relationship to other accounts before reading a word of the text). Gottlieb and Wineburg (2012) demonstrated that historians and non-historians referenced sourcing at similar frequencies — the difference was not how often they mentioned the source but what they did with the information. A scientist noted the authors' names and moved on. A historian mined the title, publisher, and date to generate hypotheses about the text's political stance, all from bibliographic information alone. This skill targets both levels — building the habit first, then deepening the analytical quality — because the first without the second produces students who perform sourcing as a classroom ritual rather than an intellectual practice.

AI is specifically valuable here because diagnosing why students fail to source requires distinguishing between several different failure modes that require different instructional responses. A student who skips the source note entirely needs different intervention than a student who reads the source note but doesn't use the information, who in turn needs different intervention than a student who uses source information but applies it superficially.

## Evidence Foundation

Wineburg (1991) established sourcing as an expert-novice discriminator through a landmark study comparing how historians and high school students read historical documents. Historians consistently examined the source of a document before reading its content — checking who wrote it, when, and under what circumstances. Students dove straight into the text. This finding has been replicated and extended across multiple studies (Wineburg, 1998; Rouet et al., 1997; Leinhardt & Young, 1996; Nokes, Dole & Hacker, 2007), making sourcing the most robustly documented feature of expert historical reading.

Wineburg (2007) explained why sourcing is cognitively "unnatural" through the mechanisms of spread of activation and the availability heuristic. When a document mentions a familiar topic, the reader's existing knowledge and opinions flood into the reading, overwhelming attention to the document's provenance. Disciplinary sourcing counteracts this default by training readers to pause — to resist engaging with the content until they have considered who produced it and why. Wineburg called the expert disposition that follows from this pause the "specification of ignorance": using a document not to confirm what one already believes but to articulate what one does not yet know.

Gottlieb and Wineburg (2012) refined the picture by showing that the quantity of sourcing references was similar between historians and PhD scientists/engineers — both groups noticed and mentioned source information. The difference was qualitative. A historian confronted with a book by unknown authors published by Free Press mined every word of the bibliographic information to generate hypotheses about the text's topic, political orientation, and relationship to contemporary debates. Scientists noted the same information and moved on. This finding means that teaching students to mention sources is necessary but insufficient — instruction must also develop the analytical depth of what students do with source information.

Reisman (2012) demonstrated that sourcing is teachable through explicit instruction in urban high school classrooms. In a six-month quasi-experimental intervention, treatment students showed significant gains in sourcing (F(1,181) = 15.89, p < .001, ηp² = .08). Sourcing was one of only two historical thinking skills (alongside close reading) that showed significant treatment effects — contextualisation and corroboration did not respond to the same instructional approach. Reisman attributed this to sourcing's concreteness: it involves a discrete, observable action (looking at the source note before reading) that can be modelled, practised on a single document, and reinforced until it becomes habitual.

Wineburg and Reisman (2015) characterised sourcing as not merely a strategy but a weltanschauung — a worldview that reconfigures the relationship between reader and text. When sourcing becomes habitual, the textbook's implicit claim to unassailable factual authority is disrupted. Reading becomes a dialectic between an active agent and a human author whose motives, limitations, and circumstances must be considered.

## Input Schema

The teacher must provide:
- **Historical topic:** The topic, period, or question students are investigating. *e.g. "The causes of the American Revolution" / "Life in the trenches during World War I" / "The impact of the transatlantic slave trade on West African societies" / "Did Pocahontas rescue John Smith?"*
- **Student level:** Age/year group and current experience with primary sources. *e.g. "Year 7, first time working with primary sources" / "Year 10, have done some document analysis but don't source consistently" / "Year 12 IB History, can source when prompted but don't do it independently"*
- **Current challenge:** What students currently do or fail to do. *e.g. "They dive straight into reading the text without looking at the source information" / "They note the author but don't think about what the author's position means for the document's reliability" / "They dismiss sources as 'biased' without explaining how the bias shapes the content" / "They treat all primary sources as equally trustworthy because they're 'from the time'"*

Optional (injected by context engine if available):
- **Source type:** The type of historical source — affects what sourcing questions are most productive
- **Available documents:** The specific documents students will work with
- **Curriculum framework:** DIG, Seixas Big Six, national curriculum, IB, etc.
- **Prior instruction:** What sourcing instruction students have already received

## Prompt

```
You are an expert in historical thinking pedagogy, with deep knowledge of Wineburg's (1991, 1998, 2007) research on sourcing as a disciplinary reading practice, Gottlieb and Wineburg's (2012) finding that the quality of sourcing — not the quantity — distinguishes expert from novice readers, and Reisman's (2012) evidence that sourcing is teachable through explicit instruction. You understand that sourcing is the foundational move in historical thinking: interrogating who authored a document, when, why, for what audience, and what this means for its reliability — before engaging with the document's content.

Your task is to design targeted sourcing instruction for:

**Historical topic:** {{historical_topic}}
**Student level:** {{student_level}}
**Current challenge:** {{current_challenge}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Source type:** {{source_type}} — if not provided, design for written primary sources as the default, noting how the approach would differ for visual or non-textual sources.
**Available documents:** {{available_documents}} — if provided, tailor the instruction to these specific documents. If not, design generalisable instruction with placeholder examples.
**Curriculum framework:** {{curriculum_framework}} — if provided, align the sourcing questions and progression descriptors to this framework. If not, use the DIG framework (who wrote this, what is their perspective, why was it written, when, where, is it reliable) as the default.
**Prior instruction:** {{prior_instruction}} — if provided, build on what students have already learned rather than repeating it. If not, assume this is early-stage sourcing instruction.

Design the following:

1. **Sourcing progression:** What sourcing looks like at three levels for this age group:
   - **Novice:** The student engages with the document's content without attending to its source. Describe what this typically looks like with this age group and topic — the specific things students say, write, or do that reveal they are not sourcing.
   - **Developing:** The student notes source information but uses it superficially. Describe what "superficial sourcing" looks like — e.g. mentioning the author but not considering their position, noting the date but not reasoning about what was happening at that time, labelling a source as "biased" without explaining how the bias shapes the content.
   - **Proficient:** The student uses source information to generate hypotheses about the document's reliability, purpose, and perspective before and during reading. Describe what this looks like with this topic — the specific questions a proficient student would ask, the inferences they would draw from the bibliographic information, the way source awareness shapes their reading of the content.

   IMPORTANT: The distinction between developing and proficient is the distinction Gottlieb and Wineburg (2012) identified — the difference between mentioning a source and interrogating it. Make this distinction concrete and observable for this specific context.

2. **Explicit instruction sequence:** A three-part sequence for moving students from their current challenge toward proficient sourcing:
   - **I DO (teacher models):** A think-aloud script (approximately 150–200 words) showing the teacher encountering the document's source information and modelling what an expert reader does with it. The think-aloud should make visible the internal reasoning that is normally invisible — pausing at the source note, generating questions from the author's name and position, forming hypotheses from the date and publication context, noting what is NOT in the source information and why that matters. The think-aloud must be specific to the source type and topic, not generic.
   - **WE DO (guided practice):** A structured activity where students practise sourcing a second document with teacher support. Specify what the teacher does (circulates, prompts, redirects), what questions the teacher asks when students skip the source or use it superficially, and how the teacher gradually withdraws support.
   - **YOU DO (independent practice):** What independent sourcing looks like — students source a third document without prompting. Specify what the teacher monitors for and how to assess whether students are sourcing habitually or only when reminded.

3. **Guiding questions:** Source-type-specific questions for students, calibrated to the developmental level. These should be adapted from the DIG sourcing protocol but made specific to the source type. For each question, include:
   - The question itself
   - Why this question matters for this source type (brief, one sentence)
   - A sentence starter students can use when responding

   Do NOT simply list the generic DIG questions (who, what, when, where, why, reliable?). Adapt them to the source type so they guide students toward the specific analytical moves that source type demands.

4. **Common failure patterns:** The 3–4 most common ways students at this level fail to source effectively, based on the current challenge described. For each pattern:
   - Name the pattern
   - Describe what it looks like (what the student says or writes)
   - Explain why the student does this (the cognitive habit or misconception driving it)
   - Provide a specific instructional response (what the teacher says or does to redirect)

5. **Assessment indicators:** Observable signs that sourcing is developing as a habitual practice:
   - **In discussion:** What to listen for — specific things students say spontaneously (not when prompted) that indicate sourcing is becoming automatic
   - **In written work:** What to look for — specific features of student writing that indicate source awareness is shaping their analysis, not just appearing as a formulaic opening sentence
   - **The key test:** One specific observable behaviour that most reliably distinguishes a student who sources habitually from one who sources only when reminded

Return your output in this exact format:

## Sourcing Instruction Plan

**Topic:** [Historical topic]
**Students:** [Level and current challenge]
**Source type:** [Type of source or "written primary sources (default)"]

### Sourcing Progression

**Novice — not yet sourcing:**
[Description with observable indicators specific to this context]

**Developing — sourcing superficially:**
[Description with observable indicators — what "mentioning but not interrogating" looks like here]

**Proficient — sourcing analytically:**
[Description with observable indicators — what genuine interrogation looks like here]

### Explicit Instruction Sequence

**I DO — Teacher Think-Aloud**
[Full think-aloud script, 150–200 words, modelling expert sourcing with a specific document]

**WE DO — Guided Practice**
[Structured activity with teacher prompts and gradual release]

**YOU DO — Independent Practice**
[What independent sourcing looks like and how to monitor it]

### Guiding Questions

[Source-type-specific questions with rationale and sentence starters]

### Common Failure Patterns

[3–4 patterns with descriptions, explanations, and instructional responses]

### Assessment Indicators

**In discussion:** [What to listen for]
**In written work:** [What to look for]
**The key test:** [The single most reliable indicator]

**Self-check before returning output:** Verify that (a) the progression clearly distinguishes between mentioning a source and interrogating it, (b) the think-aloud script models the INTERNAL reasoning of an expert reader, not just the external behaviour, (c) the guiding questions are adapted to the source type, not generic, (d) each failure pattern includes a specific instructional response, and (e) the assessment indicators describe what students do SPONTANEOUSLY, not what they do when prompted.
```

## Example Output

**Scenario:** *Historical topic: "Did Pocahontas rescue John Smith?" / Student level: "Year 8, second term of working with primary sources, have been introduced to sourcing but don't do it consistently" / Current challenge: "They note the author's name but don't think about what the author's position or circumstances mean for the document's reliability — they treat all eyewitness accounts as equally trustworthy because they're 'from the time'" / Source type: "Written first-person accounts" / Available documents: "John Smith's 1608 True Relation and his 1624 General History"*

---

## Sourcing Instruction Plan

**Topic:** Did Pocahontas rescue John Smith?
**Students:** Year 8, familiar with basic sourcing but treat all eyewitness accounts as equally trustworthy
**Source type:** Written first-person accounts

### Sourcing Progression

**Novice — not yet sourcing:**
The student reads Smith's account and evaluates it based on whether the content seems plausible or matches what they already know about Pocahontas (often from Disney). They may say things like "This proves the rescue happened because Smith was there" or "I don't believe it because it seems too dramatic." In both cases, the student is evaluating the CONTENT against their prior beliefs without considering who Smith was, why he wrote this, when he wrote it, or what circumstances might have shaped his account. The source note at the top of the document is ignored entirely — if asked, the student may not be able to name the author, the date, or the publication.

**Developing — sourcing superficially:**
The student notes that John Smith wrote the document and that it was written in 1608 or 1624. They may say "This was written by John Smith, who was a colonist" or "This is a primary source from 1624." But they do not use this information to reason about the document's reliability. They note the source as a factual label — like a heading — rather than using it as analytical leverage. If prompted ("Does it matter that Smith wrote this?"), they may say "He might be biased" but cannot explain HOW his position as a colonist, adventurer, or self-promoter might shape the specific claims he makes. The word "biased" functions as a generic dismissal rather than an analytical tool.

**Proficient — sourcing analytically:**
Before reading, the student examines the source note and reasons about what it means. For the 1608 account, they might ask: "This was written in the same year — who was Smith writing for? Was he reporting to his sponsors? Would he want to make things sound dangerous or peaceful?" For the 1624 account, they might note: "This was written 16 years later. Pocahontas had already gone to England and died. Was Smith trying to connect himself to her fame?" The student uses the date and authorship to generate hypotheses BEFORE reading the content, then reads the content with those hypotheses in mind. Crucially, they recognise that the SAME author writing at DIFFERENT times might produce different accounts — and they ask why rather than simply noting the discrepancy.

### Explicit Instruction Sequence

**I DO — Teacher Think-Aloud**

*The teacher projects Smith's 1624 General History with the source note visible and reads it aloud before touching the text:*

"OK, before I read a single word of this account, I'm going to look at who wrote it and when. It says 'John Smith, 1624, General History of Virginia.' So this is John Smith himself — he's the person at the centre of the story. That immediately makes me cautious, because he has a stake in how this story is told. It's HIS reputation on the line.

Now, 1624. When was the event supposed to have happened? 1607. So he's writing about something that happened 17 years ago. That's a long time — I'd struggle to remember details from 17 years ago. But there's something else. I happen to know that Pocahontas went to England in 1616 and became very famous there before she died in 1617. So by 1624, she was a well-known figure. Is Smith connecting himself to a celebrity? I don't know yet, but I'm going to read this with that question in mind.

One more thing — it says 'General History.' That means this was published as a book. He's writing for a public audience, not a private diary. He wants people to read this. WHY? What's he promoting?"

**WE DO — Guided Practice**

Students receive Smith's 1608 True Relation with the source note visible. In pairs, they have three minutes to examine ONLY the source information (not the text) and write down what they notice and what questions it raises.

The teacher circulates and listens. Common redirections:
- If a pair jumps straight to reading the text: "Wait — what's the first thing we do? What can you learn from the source note BEFORE you read?"
- If a pair notes the author and date but stops: "You said it's from 1608. The event happened in 1607. What does that timing tell you? Is that a long gap or a short gap? How does that compare to the 1624 account?"
- If a pair says "He's biased": "Biased HOW? What specific thing might Smith want to emphasise or hide in 1608 that's different from what he might want to emphasise in 1624?"

After three minutes, the teacher takes two or three pairs' observations and models how to turn observations into hypotheses: "So you noticed it was written in 1608, just a year after the event, and it was sent back to England as a report. What hypothesis does that give us about WHY Smith wrote it?"

**YOU DO — Independent Practice**

Students receive a third document — one of the historians' interpretations (e.g., Henry Adams's 1867 critique of Smith). Without prompting, they write a sourcing paragraph: what they notice about the source, what questions it raises, and what hypotheses they have about the document BEFORE reading it.

The teacher monitors for:
- Does the student begin with the source note or dive into the content?
- Does the student generate questions or only state facts about the source?
- Does the student connect the source information to possible implications for the document's reliability?

Students who source analytically without prompting are ready to move on. Students who need a reminder ("What's the first thing we do?") are still developing the habit and need more guided practice.

### Guiding Questions

1. **Who wrote this, and what was their relationship to the events?**
   *Why it matters for first-person accounts:* An eyewitness who is also a participant has a stake in how events are portrayed — their account is never neutral observation.
   *Sentence starter:* "The author was... which means they might want to..."

2. **When was this written, and how long after the events?**
   *Why it matters for first-person accounts:* Accounts written immediately serve different purposes (reporting, justifying) than accounts written years later (memorialising, reputation-building). Memory changes over time, and so do the writer's motivations.
   *Sentence starter:* "This was written [X years] after the event, which means..."

3. **Who was the intended audience, and what did the author want them to think or do?**
   *Why it matters for first-person accounts:* A report to sponsors, a published book, and a private letter serve different purposes and shape what the author includes, omits, or embellishes.
   *Sentence starter:* "The author was writing for... so they probably wanted to..."

4. **What might the author have a reason to exaggerate, omit, or present in a particular way?**
   *Why it matters for first-person accounts:* Every author has interests. Identifying those interests doesn't mean the account is false — it means reading with awareness of what the author stands to gain or lose.
   *Sentence starter:* "The author might have a reason to... because..."

5. **What CAN'T this source tell us, and what other sources would we need?**
   *Why it matters for first-person accounts:* A single eyewitness gives one perspective. Recognising the limits of any single source is the bridge to corroboration.
   *Sentence starter:* "This source can tell us about... but it can't tell us about... because..."

### Common Failure Patterns

**1. "Content first" — diving into the text without checking the source**
*What it looks like:* The student begins reading the document from the first line of text, skipping the source note entirely. Their response engages only with WHAT the document says, not WHO said it or WHY.
*Why they do this:* Reading habits from other contexts (novels, textbooks, websites) train students to start at the beginning of the text. The source note looks like a header — metadata to skip, not information to analyse.
*Instructional response:* Physically cover the document text, leaving only the source note visible. Ask students to spend 60 seconds generating questions from the source note alone before uncovering the text. Repeat this routine until looking at the source note first becomes automatic.

**2. "Source as label" — noting the source without using it**
*What it looks like:* The student writes "This was written by John Smith in 1624" and then proceeds to analyse the content as if the source information doesn't matter. The source appears as a factual opening sentence that is disconnected from the analysis that follows.
*Why they do this:* They have learned that sourcing is something you DO (mention the author and date) but not something that CHANGES how you read. Sourcing is a ritual, not a reasoning tool.
*Instructional response:* After the student notes the source, ask: "So what? How does knowing Smith wrote this in 1624 change how you read what he says?" Push them to complete the sentence: "Because Smith wrote this in 1624, I expect to find... / I'm suspicious that... / I want to check whether..."

**3. "Bias as dismissal" — using "biased" as a reason to reject a source**
*What it looks like:* The student says "This source is biased because Smith was involved, so we can't trust it." The word "biased" functions as a verdict that ends analysis rather than beginning it.
*Why they do this:* They have learned that primary sources can be unreliable, but they interpret this as a binary (trustworthy vs. biased) rather than a spectrum. They don't yet understand that ALL sources have perspectives and that the analytical task is to identify HOW the perspective shapes the account, not WHETHER it exists.
*Instructional response:* Ban the word "biased" temporarily. Replace it with: "This author's perspective might lead them to emphasise... and downplay..." This forces students to specify the DIRECTION of the bias rather than using it as a blanket dismissal. Point out that even a "biased" source tells us something — it reveals what the author WANTED people to believe, which is itself historically significant.

**4. "Eyewitness = truth" — treating primary sources as inherently reliable**
*What it looks like:* The student says "This is a primary source, so it's more reliable" or "Smith was there, so he would know." They privilege firsthand accounts over later interpretations simply because they are temporally closer to the event.
*Why they do this:* The primary/secondary distinction, often taught as a foundational concept, can inadvertently create a reliability hierarchy where primary = better. Students haven't yet encountered the idea that an eyewitness might have reasons to distort, exaggerate, or omit.
*Instructional response:* Use the Smith case directly: both the 1608 and 1624 accounts are primary sources by the same eyewitness, and they contradict each other. Ask: "If primary sources are always reliable, how do we explain this?" This disrupts the assumption and opens the door to genuine sourcing.

### Assessment Indicators

**In discussion:** Listen for students who spontaneously ask about the source before discussing the content — especially when a new document is introduced. The key phrase is unprompted questioning: "Wait, who wrote this?" or "When was this written? Was that before or after...?" If students only source when the teacher asks "What do we do first?", the habit is still teacher-dependent.

**In written work:** Look for source information that is INTEGRATED into the analysis rather than stated as a separate opening sentence. A developing student writes: "This was written by Smith in 1624. The passage describes..." (source and content are disconnected). A proficient student writes: "Smith wrote this account 17 years after the event, at a time when Pocahontas had become famous in England, which may explain why he now included the dramatic rescue story he had not mentioned in his earlier report." Here the source information shapes the interpretation — it's not a label but a lens.

**The key test:** Give students a new document they haven't seen before, with no instruction to source it. Watch what they do in the first 30 seconds. A student who has internalised sourcing will look at the source note before reading the text. A student who has only learned sourcing as a classroom procedure will begin reading the content. This 30-second window is the most reliable indicator of whether sourcing has become a disposition or remains a prompted behaviour.

---

## Known Limitations

1. **Sourcing is the most concrete and teachable of the four historical thinking skills (Reisman, 2012), but there is an important distinction between routinised sourcing behaviour and deep analytical sourcing.** This skill addresses both levels, but the transition from habit (looking at the source note) to disposition (using source information to reshape one's reading) requires sustained practice over months, not a single lesson. The skill provides the instructional design; the teacher provides the sustained reinforcement.

2. **The evidence base for sourcing as an expert-novice discriminator is drawn primarily from US studies with English-language historical documents.** How sourcing practices translate to non-Western historiographic traditions, oral history contexts, or multilingual source environments is not well studied. Teachers working in these contexts should adapt the guiding questions to honour the evidentiary traditions of the histories they teach.

3. **Gottlieb and Wineburg (2012) demonstrated that identity and community membership can shape how readers apply sourcing criteria — people may source rigorously when reading about topics that don't engage their identity but lower their critical guard when reading about a past that matters to them personally.** This skill does not address this "horizontal axis" of historical thinking. Teachers should be aware that students may source less carefully when the topic connects to their own community, heritage, or beliefs — not because they lack the skill but because identity engagement changes the epistemological criteria they apply.

4. **This skill focuses on sourcing in isolation for instructional clarity, but in authentic historical inquiry sourcing operates in concert with contextualisation, corroboration, and close reading.** Once students can source consistently, instruction should integrate sourcing with the other three skills through document-based lessons (see document-based-lesson-designer).

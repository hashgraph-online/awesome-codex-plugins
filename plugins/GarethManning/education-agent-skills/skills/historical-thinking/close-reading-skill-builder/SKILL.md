---
# AGENT SKILLS STANDARD FIELDS (v2)
name: close-reading-skill-builder
description: "Build students' capacity to read historical documents closely — attending to word choice, tone, and rhetoric as evidence of perspective. Use when students summarise sources without analysing language."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS
skill_id: "historical-thinking/close-reading-skill-builder"
skill_name: "Close Reading Skill Builder"
domain: "historical-thinking"
version: "1.0"
contributor: "Sean Hu"
evidence_strength: "strong"
evidence_sources:
  - "Wineburg (1991) — Historical problem solving: cognitive processes in the evaluation of documentary and pictorial evidence"
  - "Wineburg (1998) — Reading Abraham Lincoln: an expert/expert study in historical cognition"
  - "Reisman (2012) — Reading like a historian: a document-based history curriculum intervention in urban high schools"
  - "Wineburg & Reisman (2015) — Disciplinary literacy in history: a toolkit for digital citizenship"
  - "Wineburg, Martin & Monte-Sano (2011) — Reading like a historian: teaching literacy in middle and high school history classrooms"
  - "Leinhardt & Young (1996) — Two texts, three readers: distance and expertise in reading history"
input_schema:
  required:
    - field: "historical_topic"
      type: "string"
      description: "The historical topic, period, or question students are investigating"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current level of experience with close reading of historical texts"
    - field: "current_challenge"
      type: "string"
      description: "What students currently do or fail to do when reading a historical document closely — the observable behaviour that signals close reading is not yet developed"
  optional:
    - field: "source_type"
      type: "string"
      description: "The type of historical source — e.g. speech, letter, testimony, proclamation, diary entry, newspaper editorial, treaty, political cartoon"
    - field: "available_documents"
      type: "string"
      description: "Description of the specific documents students will work with"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: relevant curriculum standards or historical thinking framework in use"
    - field: "prior_instruction"
      type: "string"
      description: "What close reading instruction students have already received — including any literary close reading from English/Language Arts"
output_schema:
  type: "object"
  fields:
    - field: "close_reading_progression"
      type: "object"
      description: "What close reading looks like at novice, developing, and proficient levels for this student age group — with observable indicators distinguishing between summarising content and analysing language as evidence of perspective"
    - field: "explicit_instruction_sequence"
      type: "object"
      description: "A three-part sequence (model → guided practice → independent practice) for teaching close reading with the specified source type, including a teacher think-aloud script demonstrating how an expert reader attends to word choice, tone, and rhetorical strategy as evidence"
    - field: "language_analysis_prompts"
      type: "array"
      description: "Source-type-specific prompts that direct students' attention to how language reveals the author's perspective, purpose, and reliability — calibrated to developmental level"
    - field: "common_failure_patterns"
      type: "array"
      description: "Specific ways students at this level typically fail to read closely — with targeted instructional responses for each"
    - field: "assessment_indicators"
      type: "object"
      description: "Observable signs that students are developing close reading as an analytical practice — what to listen for in discussion, what to look for in written work"
chains_well_with:
  - "sourcing-skill-builder"
  - "contextualisation-skill-builder"
  - "corroboration-skill-builder"
  - "historical-thinking-strategy-modelling-guide"
  - "document-based-lesson-designer"
  - "historical-source-adapter"
  - "historical-thinking-assessment-designer"
  - "disciplinary-writing-scaffold"
  - "text-complexity-analyser"
teacher_time: "3 minutes"
tags: ["close-reading", "historical-thinking", "disciplinary-literacy", "language-analysis", "document-analysis", "rhetoric", "DIG"]
---

# Close Reading Skill Builder

## What This Skill Does

Designs targeted instruction to develop students' close reading of historical documents — the practice of attending to an author's word choice, claims, evidence, tone, and rhetorical strategies to assess argument, perspective, and probity. The output includes a developmental progression, an explicit instruction sequence with a teacher think-aloud script, language analysis prompts specific to the source type, common failure patterns with instructional responses, and assessment indicators.

Close reading in history is distinct from close reading in English or Language Arts. Literary close reading attends to aesthetic features — imagery, symbolism, narrative voice. Historical close reading attends to language as evidence of the author's perspective, purpose, and relationship to the events described. When a historian reads a document closely, they ask: what claims is the author making? What evidence do they offer? What words reveal their stance? What is the gap between what the author says and what they might mean? Wineburg (1998) demonstrated this in a study where historians reading Lincoln's documents attended to the strategic deployment of language — not its beauty — to assess Lincoln's political positioning. The question driving historical close reading is not "What does this text mean?" but "What does this author's language reveal about their perspective, and what does that tell us about the reliability of their account?"

Reisman (2012) found that close reading, alongside sourcing, was one of only two historical thinking skills that showed significant treatment effects in her intervention study (F(1,181) = 9.62, p = .002, ηp² = .05). Like sourcing, close reading involves concrete, demonstrable actions — underlining loaded language, identifying claims and evidence, noting shifts in tone — that can be modelled on a single document. This concreteness makes it more immediately teachable than contextualisation or corroboration, which require intertextual reasoning.

## Evidence Foundation

Wineburg (1991) identified close reading as a core component of expert historical reasoning. Historians in his study attended to the language of documents as evidence of perspective — noticing word choices that revealed an author's stance, identifying claims that went beyond what the evidence supported, and detecting rhetorical strategies designed to persuade. Students, by contrast, read for content: they extracted information from documents without attending to how the information was presented or what the presentation revealed about the author.

Leinhardt and Young (1996) deepened this finding by showing that expert historians constructed what they called an "Event Model" — an integrated representation built from close attention to how multiple documents used language differently to describe the same events. The linguistic differences between accounts were not noise to be filtered out but signal to be analysed: why does one author use "rebellion" where another uses "revolution"? The answer reveals not a vocabulary preference but a political commitment.

Wineburg (1998) demonstrated historical close reading in action through a study of historians reading Lincoln's documents. Experts attended to Lincoln's strategic deployment of language — how he positioned himself differently for different audiences, how his word choices shifted over time, and what the gaps between his public statements and private letters revealed about his actual views. This is close reading not as literary appreciation but as evidentiary analysis: the author's language is data about the author's perspective.

Reisman (2012) operationalised close reading in the Reading Like a Historian curriculum through guiding questions: What claims does the author make? What evidence does the author use? What language does the author use to persuade? How does the document's language indicate the author's perspective? Treatment effects for close reading were significant, suggesting that these concrete analytical moves are teachable through explicit instruction and practice.

Wineburg and Reisman (2015) situated close reading within disciplinary literacy, distinguishing it from generic reading comprehension. Generic reading strategies (summarising, predicting, backtracking) are necessary but not sufficient for historical reading. Close reading in history requires discipline-specific attention to language as evidence — a practice that generic reading instruction does not develop.

## Input Schema

The teacher must provide:
- **Historical topic:** *e.g. "Causes of the French Revolution" / "The debate over Japanese American internment" / "Perspectives on British imperialism in India"*
- **Student level:** *e.g. "Year 9, can summarise documents but don't analyse language choices" / "Year 11 IB History, familiar with close reading from English class but apply literary rather than historical analysis"*
- **Current challenge:** *e.g. "They summarise what the document says but don't notice HOW it says it" / "They can identify 'persuasive language' but can't connect it to the author's historical position" / "They treat all documents as neutral information sources — they don't notice that language reveals perspective"*

Optional:
- **Source type:** Affects which language features are most analytically productive
- **Available documents:** Allows tailoring to specific texts
- **Curriculum framework:** Aligns prompts to the framework in use
- **Prior instruction:** Especially important to know if students have literary close reading experience that can be built on (or that might create confusion about what historical close reading requires)

## Prompt

```
You are an expert in historical thinking pedagogy, with deep knowledge of Wineburg's (1991, 1998) research on how expert historians read documents closely for evidence of perspective, Leinhardt and Young's (1996) work on how language differences between accounts function as historical evidence, and Reisman's (2012) evidence that close reading is teachable through explicit instruction. You understand that close reading in history is distinct from literary close reading: the goal is not to appreciate aesthetic features but to analyse language as evidence of the author's perspective, purpose, and reliability.

Your task is to design targeted close reading instruction for:

**Historical topic:** {{historical_topic}}
**Student level:** {{student_level}}
**Current challenge:** {{current_challenge}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Source type:** {{source_type}} — if not provided, design for written primary sources as the default.
**Available documents:** {{available_documents}} — if provided, tailor the instruction to these specific documents.
**Curriculum framework:** {{curriculum_framework}} — if not provided, use the DIG framework as the default.
**Prior instruction:** {{prior_instruction}} — if provided, build on existing skills. If students have literary close reading experience, explicitly address how historical close reading differs.

Design the following:

1. **Close reading progression:** What close reading looks like at three levels for this age group:
   - **Novice:** The student extracts content from the document — they can tell you WHAT it says but not HOW it says it or WHY the author chose those words. Describe what this looks like with specific observable indicators.
   - **Developing:** The student notices some language features (e.g., identifies "persuasive language" or "emotive words") but treats them as generic categories rather than connecting them to the author's specific historical position and purpose. Describe what superficial close reading looks like.
   - **Proficient:** The student analyses specific word choices, claims, and rhetorical strategies as evidence of the author's perspective, connecting language to the author's historical circumstances. Describe what this looks like — the specific analytical moves a proficient student makes.

2. **Explicit instruction sequence:**
   - **I DO:** A think-aloud script (150–200 words) showing the teacher modelling close reading of a specific passage — pausing at key word choices, asking what they reveal about the author's stance, identifying claims and evaluating the evidence offered for them, noticing what the author does NOT say.
   - **WE DO:** A guided practice activity where students close-read a passage together with teacher support.
   - **YOU DO:** Independent close reading with monitoring criteria.

3. **Language analysis prompts:** Source-type-specific prompts that direct students' attention to historically significant language features. For each prompt, include the prompt itself, why it matters for this source type, and a sentence starter. Adapt prompts to the source type — a speech demands attention to rhetorical strategy and audience; a private letter demands attention to what the author says differently in private than in public; testimony demands attention to what is claimed vs. what is evidenced.

4. **Common failure patterns:** 3–4 patterns with descriptions, explanations, and instructional responses.

5. **Assessment indicators:** What to listen for in discussion, what to look for in written work, and the key test that distinguishes a student who close-reads analytically from one who only summarises content.

Return your output in this exact format:

## Close Reading Instruction Plan

**Topic:** [Historical topic]
**Students:** [Level and current challenge]
**Source type:** [Type of source]

### Close Reading Progression

**Novice — reading for content only:**
[Observable indicators]

**Developing — noticing language without connecting it to perspective:**
[Observable indicators]

**Proficient — analysing language as evidence of perspective:**
[Observable indicators]

### Explicit Instruction Sequence

**I DO — Teacher Think-Aloud**
[Script, 150–200 words]

**WE DO — Guided Practice**
[Activity with teacher prompts]

**YOU DO — Independent Practice**
[What to monitor for]

### Language Analysis Prompts

[Source-type-specific prompts with rationale and sentence starters]

### Common Failure Patterns

[3–4 patterns]

### Assessment Indicators

**In discussion:** [What to listen for]
**In written work:** [What to look for]
**The key test:** [Single most reliable indicator]

**Self-check before returning output:** Verify that (a) the progression distinguishes between summarising content and analysing language as evidence, (b) the think-aloud models attention to SPECIFIC word choices, not generic "language features," (c) the prompts are adapted to the source type, (d) the failure patterns distinguish between literary and historical close reading where relevant, and (e) the assessment indicators describe analytical close reading, not comprehension.
```

## Example Output

**Scenario:** *Historical topic: "Did Pocahontas rescue John Smith?" / Student level: "Year 8, can summarise documents but don't analyse language choices" / Current challenge: "They tell me what Smith says happened but don't notice the difference in tone and word choice between his two accounts" / Source type: "Written first-person accounts" / Available documents: "Smith's 1608 True Relation and 1624 General History"*

---

## Close Reading Instruction Plan

**Topic:** Did Pocahontas rescue John Smith?
**Students:** Year 8, can summarise but don't analyse language choices
**Source type:** Written first-person accounts

### Close Reading Progression

**Novice — reading for content only:**
The student can tell you what happens in each account — "In the first one, Smith meets Powhatan and they're friendly. In the second one, they try to kill him and Pocahontas saves him." They treat the documents as containers of information and extract the story. They do not notice that the 1608 account uses words like "kindly," "friendship," and "kindness" while the 1624 account uses "barbarous," "fearful," and "beat out his brains." If asked why the accounts differ, they speculate about the events ("maybe he forgot") rather than about the language ("maybe he chose different words for a reason").

**Developing — noticing language without connecting it to perspective:**
The student can identify that the two accounts use different language: "The first one sounds friendlier and the second one sounds scarier." They may label the language as "positive" or "negative." But they treat this as a description of the text rather than as evidence about the author. They don't ask WHY Smith would choose friendly language in 1608 and threatening language in 1624, or what the shift in tone reveals about his changing purposes.

**Proficient — analysing language as evidence of perspective:**
The student connects specific word choices to the author's circumstances. They might say: "In 1608, Smith describes Powhatan with words like 'kindly' and 'friendship' — he's writing a report for his sponsors and wants to show he has good relations with the natives. By 1624, he uses 'barbarous' and describes a dramatic rescue — he's writing a book for a public audience and wants an exciting story. The language shift tells us more about Smith's changing purposes than about what actually happened."

### Explicit Instruction Sequence

**I DO — Teacher Think-Aloud**

*Teacher projects a passage from Smith's 1608 True Relation and reads slowly:*

"Let me read this carefully. 'He kindly welcomed me with good words and great platters of sundry victuals, assuring me his friendship.' I'm going to pause on the word 'kindly.' Smith chose that word. He could have said 'he received me' or 'he allowed me to enter' — neutral descriptions. But 'kindly' tells me Smith wants the reader to see Powhatan as welcoming. And 'assuring me his friendship' — that's not just describing what happened, that's interpreting Powhatan's intentions. Smith is telling us what Powhatan MEANT, not just what Powhatan did.

Now I'm going to hold that in mind while I look at the 1624 version of the same meeting. 'Having feasted him after their best barbarous manner they could.' There's 'barbarous.' Same meeting, same author — but now the Powhatan are barbarous, not kind. That single word change tells me something shifted in how Smith wanted readers to see this encounter. The question isn't which version is true — it's why the same person described the same event so differently."

**WE DO — Guided Practice**

Students receive both passages side by side. In pairs, they underline three words or phrases in each account that reveal Smith's attitude toward Powhatan. For each underlined word, they complete: "Smith chose the word ___ instead of ___, which suggests he wanted the reader to think ___."

Teacher circulates. Key redirections:
- If students underline content words ("victuals," "clubs"): "Those tell us what happened. I want words that tell us what Smith THOUGHT about what happened."
- If students identify tone but stop at labelling: "You said the 1608 version sounds 'friendly.' Which SPECIFIC word makes it sound friendly? What word could he have used instead?"

**YOU DO — Independent Practice**

Students receive a new passage — one of the historians' interpretations. They identify two specific language choices the historian makes and explain what each reveals about the historian's stance on the rescue question. No prompting from the teacher.

### Language Analysis Prompts

1. **What words does the author use to describe people or groups, and what attitude do those words convey?**
   *Why it matters:* Descriptive word choices ("kindly" vs. "barbarous," "rescued" vs. "claimed to have been rescued") are the most direct evidence of an author's perspective.
   *Sentence starter:* "The author describes [person/group] as ___, which suggests they see them as..."

2. **What does the author claim happened, and what evidence do they offer for the claim?**
   *Why it matters:* First-person accounts often present interpretations as facts. Distinguishing between "this happened" and "I believe this happened" is a core close reading move.
   *Sentence starter:* "The author claims that ___, but the evidence they give is only..."

3. **What does the author NOT say that you would expect them to say?**
   *Why it matters:* Omissions are as revealing as inclusions. Smith's 1608 silence about the rescue is as significant as his 1624 inclusion of it.
   *Sentence starter:* "It's significant that the author doesn't mention ___, because..."

4. **How would this passage read differently if someone with a different perspective had written it?**
   *Why it matters:* This forces students to recognise that the document is ONE possible account, shaped by this particular author's position — not a transparent window onto the past.
   *Sentence starter:* "If this had been written by [different person], they might have described ___ as ___ instead of ___."

### Common Failure Patterns

**1. "Summary as analysis" — retelling what the document says**
*What it looks like:* "Smith says Powhatan welcomed him and gave him food." The student accurately reports content but performs no analysis of language.
*Why:* Students have been trained in reading comprehension (what does the text say?) but not close reading (how does the text say it and what does that reveal?).
*Response:* Ask: "You've told me WHAT Smith says. Now tell me HOW he says it. Pick one word and explain why he chose THAT word instead of a different one."

**2. "Generic labelling" — identifying tone without specificity**
*What it looks like:* "The author uses emotive language to persuade the reader." The student has a literary close reading vocabulary but applies it as a formula.
*Why:* Often imported from English/Language Arts, where identifying "persuasive techniques" is a common task. The student has learned to label but not to connect labels to historical context.
*Response:* "WHICH emotive language? Point to the specific word. Now — why would THIS author, writing at THIS time, choose THAT word? What was happening in their world that makes that word choice significant?"

**3. "Both accounts are true" — failing to recognise that language shapes meaning**
*What it looks like:* "The 1608 version describes a friendly meeting and the 1624 version describes a rescue. Both things could have happened."
*Why:* The student treats both accounts as transparent reports of different events rather than as differently constructed accounts of the same event. They don't yet see language as a lens that shapes what is reported.
*Response:* "These describe the SAME meeting. Smith can't have been both kindly welcomed AND dragged to the stones to have his brains beaten out. The language isn't just describing — it's constructing a version of events. Which version, and why?"

### Assessment Indicators

**In discussion:** Listen for students who reference specific words or phrases when making claims about a document — "Smith says 'barbarous,' which shows..." rather than "Smith describes the meeting." The shift from summarising content to citing language as evidence is the marker.

**In written work:** Look for quotation marks around specific words, followed by analysis of why those words matter. A developing student writes: "Smith describes the meeting in a negative way." A proficient student writes: "Smith's use of 'barbarous' to describe the same people he called 'kind' sixteen years earlier suggests his purpose for writing had changed."

**The key test:** Give students two accounts of the same event that use noticeably different language. Ask not "what happened?" but "how does each author want you to see this event, and how can you tell from their word choices?" A student who can answer the second question with specific textual evidence is close reading historically.

---

## Known Limitations

1. **Close reading in history overlaps with but is distinct from close reading in English/Language Arts.** Students who have strong literary close reading skills may need explicit guidance on how to redirect those skills toward historical analysis — attending to language as evidence of perspective rather than as aesthetic craft. This skill flags the distinction but teachers in cross-curricular contexts should coordinate with English colleagues to reinforce rather than confuse the two applications.

2. **Close reading was one of two skills that showed treatment effects in Reisman (2012), but the study's measures assessed strategy application, not depth of analysis.** Whether students who learn to identify word choices and rhetorical strategies also develop the deeper disposition to read all texts as constructed rather than transparent is an open question the evidence does not resolve.

3. **Close reading of historical documents requires language proficiency that may create barriers for EAL students or students with reading difficulties.** The skill's emphasis on word choice analysis assumes students can perceive the connotative differences between words like "kindly" and "barbarous." Teachers should ensure that vocabulary support (see text-complexity-analyser and vocabulary-tiering-tool) is in place before asking students to analyse language as evidence.

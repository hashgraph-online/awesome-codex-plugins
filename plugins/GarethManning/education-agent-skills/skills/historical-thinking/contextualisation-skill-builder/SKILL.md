---
# AGENT SKILLS STANDARD FIELDS (v2)
name: contextualisation-skill-builder
description: "Build students' capacity to place historical documents in their temporal and social context. Use when students read sources without considering what was happening at the time, or know the context but don't deploy it."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS
skill_id: "historical-thinking/contextualisation-skill-builder"
skill_name: "Contextualisation Skill Builder"
domain: "historical-thinking"
version: "1.0"
contributor: "Sean Hu"
evidence_strength: "moderate"
evidence_sources:
  - "Wineburg (2007) — Unnatural and essential: the nature of historical thinking"
  - "Wineburg (1998) — Reading Abraham Lincoln: an expert/expert study in historical cognition"
  - "Gottlieb & Wineburg (2012) — Between Veritas and Communitas: epistemic switching in the reading of academic and sacred history"
  - "Reisman (2012) — Reading like a historian: a document-based history curriculum intervention in urban high schools"
  - "Wineburg & Reisman (2015) — Disciplinary literacy in history: a toolkit for digital citizenship"
  - "Wineburg, Smith & Breakstone (2018) — What is learned in college history classes?"
input_schema:
  required:
    - field: "historical_topic"
      type: "string"
      description: "The historical topic, period, or question students are investigating"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current level of experience with contextualisation"
    - field: "current_challenge"
      type: "string"
      description: "What students currently do or fail to do when contextualising — the observable behaviour that signals contextualisation is not yet developed"
  optional:
    - field: "source_type"
      type: "string"
      description: "The type of historical source students are working with"
    - field: "available_documents"
      type: "string"
      description: "Description of the specific documents students will work with"
    - field: "background_knowledge"
      type: "string"
      description: "What background knowledge students already possess about the period — critical because contextualisation requires knowledge to deploy, and the gap may be knowledge rather than skill"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: relevant curriculum standards or historical thinking framework in use"
    - field: "prior_instruction"
      type: "string"
      description: "What contextualisation instruction students have already received"
output_schema:
  type: "object"
  fields:
    - field: "contextualisation_progression"
      type: "object"
      description: "What contextualisation looks like at novice, developing, and proficient levels — with observable indicators distinguishing between knowing background information and deploying it to transform interpretation of a document"
    - field: "explicit_instruction_sequence"
      type: "object"
      description: "A three-part sequence for teaching contextualisation, designed for the greater complexity of this skill compared to sourcing and close reading — includes strategies for making the invisible mental move of connecting a document to its historical moment visible and practicable"
    - field: "contextualisation_prompts"
      type: "array"
      description: "Prompts that guide students to connect a document to its historical moment — calibrated to developmental level and source type"
    - field: "common_failure_patterns"
      type: "array"
      description: "Specific ways students fail to contextualise, including the critical distinction between possessing background knowledge and activating it during document reading"
    - field: "assessment_indicators"
      type: "object"
      description: "Observable signs that students are contextualising — what to listen for in discussion, what to look for in written work"
chains_well_with:
  - "sourcing-skill-builder"
  - "close-reading-skill-builder"
  - "corroboration-skill-builder"
  - "historical-thinking-strategy-modelling-guide"
  - "document-based-lesson-designer"
  - "historical-thinking-assessment-designer"
  - "lesson-opening-designer"
teacher_time: "4 minutes"
tags: ["contextualisation", "historical-thinking", "disciplinary-literacy", "document-analysis", "chronological-reasoning", "DIG"]
---

# Contextualisation Skill Builder

## What This Skill Does

Designs targeted instruction to develop students' contextualisation practice — reasoning about how the temporal, spatial, and social circumstances of a document's creation shape its content, meaning, and reliability. The output includes a developmental progression, an explicit instruction sequence adapted for contextualisation's greater complexity, prompts that guide students to connect documents to their historical moment, common failure patterns, and assessment indicators.

Contextualisation is qualitatively different from sourcing and close reading, and harder to teach. Reisman (2012) found significant treatment effects for sourcing and close reading but not for contextualisation (or corroboration) in her six-month intervention. She attributed this to contextualisation's abstractness: while sourcing involves a discrete action (look at the source note) and close reading involves attention to concrete textual features (word choice), contextualisation requires an inferential leap — connecting a document to circumstances that are NOT in the document itself. The reader must bring external knowledge to the text and use it to transform the text's meaning. This means contextualisation depends on two things that the other skills do not: possession of relevant background knowledge AND the disposition to activate it during reading.

Wineburg (2007) demonstrated this double requirement through the Harrison Proclamation example. A student and primary school teachers all possessed knowledge about 1890s immigration trends — immigration is taught repeatedly in the US curriculum. But when they read Harrison's 1892 Columbus Day proclamation, that knowledge was not activated. The Columbus node overwhelmed it. Doctoral students in history, by contrast, connected the document to its 1892 context within seconds — not because they knew more about Columbus but because they had the disciplinary disposition to ask "what was happening in 1892 that would make this document necessary?" This is what Wineburg called the difference between knowledge possessed and knowledge deployed.

This skill is rated "moderate" rather than "strong" for evidence strength because, while the research clearly demonstrates that contextualisation is a core component of expert historical reading, the evidence for how to teach it effectively is thinner than for sourcing. Reisman (2012) suggested that contextualisation may require more whole-class discussion and more explicit modelling of the inferential connection between context and document — but this was a post-hoc explanation for null findings, not a tested instructional design.

## Evidence Foundation

Wineburg (2007) provided the clearest demonstration of what contextualisation looks like in practice. Confronted with Harrison's 1892 proclamation about Columbus, doctoral student Matt's response was: "Okay it's 1892... Benjamin Harrison. The 1890s, the beginning of the Progressive Era, end of the century, closing of the frontier, Frederick Jackson Turner, you've got the Columbian Exposition coming up the following year. Biggest wave of immigration in US history. That's it." In under a minute, Matt had connected the document to five distinct contextual reference points and arrived at a hypothesis: the proclamation was about immigration politics, not about Columbus. A 17-year-old student reading the same document spent his time evaluating Columbus's character. Both readers engaged seriously with the document; only one contextualised it.

Gottlieb and Wineburg (2012) found that historians used contextualisation significantly more than non-historians (Z = 2.84, p = .005), and that the qualitative character of their contextualisation was different. Non-historians could sense something was wrong with a document (Reverend I noticed everyone in a Thanksgiving picture "looks clean and well fed") but lacked the specific knowledge to articulate why. Historians deployed factual corrections and disciplinary concepts like anachronism. Six of eight historians read Washington's Thanksgiving Proclamation as evidence of Enlightenment deism, while all eight clergy and scientists read the same language as proof of religious piety. This demonstrates that contextualisation does not merely add background information — it transforms meaning.

Wineburg and Reisman (2015) argued that contextualisation is constitutive of comprehension, not supplementary to it: "For the novice reader, the available information begins and ends with the text. For historical readers, the text becomes a portal to another time." They criticised Common Core implementations that reduced historical documents to "informational texts" and instructed teachers to avoid contextual questions as "non text-dependent." Separating Lincoln's Gettysburg Address from the Civil War, they argued, renders the words meaningless.

Wineburg, Smith, and Breakstone (2018) provided negative evidence: 94% of introductory college students ignored the 300-year gap between a 1621 event and a 1932 painting depicting it. 84% of upper-level students failed to recognise that an 1859 fact cannot explain why someone wrote a play in 1936. Students consistently read for content rather than context — engaging with what documents said but not with the circumstances of their creation. Even history majors showed this pattern, suggesting that exposure to history courses does not automatically develop contextualisation.

Reisman (2012) found no significant treatment effects for contextualisation despite significant effects for sourcing and close reading. Her explanation: sourcing and close reading are "discrete, concrete actions" practicable on a single document, while contextualisation requires making connections between the document and knowledge not present in the document itself. The near-absence of whole-class discussion in treatment classrooms may have limited opportunities to practise this more complex, dialogic skill.

## Input Schema

The teacher must provide:
- **Historical topic:** *e.g. "The Gettysburg Address" / "Columbus Day proclamation of 1892" / "Propaganda posters from World War I" / "The Declaration of the Rights of Man (1789)"*
- **Student level:** *e.g. "Year 8, have studied the period but don't connect background knowledge to document analysis" / "Year 11, can source and close-read but don't spontaneously ask what was happening at the time a document was created"*
- **Current challenge:** *e.g. "They know the background but don't use it when reading documents" / "They treat documents as timeless — they don't consider that the same words meant different things in different periods" / "They can answer 'when was this written?' but can't answer 'why does it matter that it was written THEN?'"*

Optional:
- **Background knowledge:** What students already know about the period — critical for diagnosing whether the gap is knowledge or deployment
- **Source type, available documents, curriculum framework, prior instruction** — as per sourcing skill builder

## Prompt

```
You are an expert in historical thinking pedagogy, with deep knowledge of Wineburg's (2007) demonstration that contextualisation requires both possession of background knowledge AND the disposition to activate it during reading, Gottlieb and Wineburg's (2012) finding that contextualisation transforms meaning rather than merely adding background information, and Reisman's (2012) finding that contextualisation did NOT show significant treatment effects in a six-month intervention — suggesting it requires different instructional strategies than sourcing or close reading.

Your task is to design targeted contextualisation instruction for:

**Historical topic:** {{historical_topic}}
**Student level:** {{student_level}}
**Current challenge:** {{current_challenge}}

The following optional context may or may not be provided. Use whatever is available.

**Source type:** {{source_type}}
**Available documents:** {{available_documents}}
**Background knowledge:** {{background_knowledge}} — if provided, this is critical. If students already know the relevant context, the problem is DEPLOYMENT, not knowledge — and instruction should focus on activating existing knowledge during reading. If students lack the background, the problem is partly a knowledge gap and instruction must address both knowledge and deployment.
**Curriculum framework:** {{curriculum_framework}}
**Prior instruction:** {{prior_instruction}}

Design the following:

1. **Contextualisation progression:** What contextualisation looks like at three levels:
   - **Novice:** The student reads the document as if it could have been written at any time. They engage with the content in isolation from historical circumstances. Describe what this looks like with observable indicators.
   - **Developing:** The student can state relevant background information when prompted ("What was happening in 1892?") but does not spontaneously connect it to the document. Context and document remain in separate compartments. Describe what this disconnection looks like.
   - **Proficient:** The student spontaneously connects the document to its historical moment, using context to transform their interpretation of the document's meaning, purpose, or reliability. Describe what this integration looks like — the specific reasoning moves a proficient student makes.

   IMPORTANT: The critical distinction here is between POSSESSING context and DEPLOYING it (Wineburg, 2007). A student who can recite facts about the 1890s but reads Harrison's proclamation as a statement about Columbus possesses knowledge but does not deploy it. Make this distinction concrete and observable.

2. **Explicit instruction sequence:** This must differ from the sourcing and close reading sequences because contextualisation involves an inferential leap that is harder to model with concrete actions. Design a sequence that makes the invisible mental move of "connecting document to context" visible:
   - **I DO:** A think-aloud script (150–200 words) showing the teacher modelling the contextualisation move — reading the document's date and immediately reaching for what they know about that moment, connecting specific features of the document to specific historical circumstances, and showing how context changes the interpretation. The think-aloud should make the INFERENCE explicit: "Because I know X was happening in [year], this document probably means Y rather than Z."
   - **WE DO:** A guided practice activity that scaffolds the inferential leap. Consider using a structured bridge — e.g., students first list what they know about the period (activating knowledge), then read the document, then explicitly connect items from their list to specific features of the document. The bridge makes the connection step deliberate rather than implicit.
   - **YOU DO:** Independent practice with monitoring criteria.

3. **Contextualisation prompts:** Prompts that guide students toward the contextualisation move, calibrated to the source type. For each prompt, include the prompt itself, why it matters, and a sentence starter. Prompts should push students beyond "when was this written?" toward "why does it matter that it was written THEN?"

4. **Common failure patterns:** 3–4 patterns, including the knowledge-possession-without-deployment pattern that is distinctive to contextualisation.

5. **Assessment indicators:** What to listen for, what to look for, and the key test.

Return your output in this exact format:

## Contextualisation Instruction Plan

**Topic:** [Historical topic]
**Students:** [Level and current challenge]
**Source type:** [Type of source]

### Contextualisation Progression

**Novice — reading without context:**
[Observable indicators]

**Developing — knowing context but not deploying it:**
[Observable indicators]

**Proficient — deploying context to transform interpretation:**
[Observable indicators]

### Explicit Instruction Sequence

**I DO — Teacher Think-Aloud**
[Script, 150–200 words]

**WE DO — Guided Practice**
[Activity with scaffolded bridge between context knowledge and document interpretation]

**YOU DO — Independent Practice**
[What to monitor for]

### Contextualisation Prompts

[Prompts with rationale and sentence starters]

### Common Failure Patterns

[3–4 patterns]

### Assessment Indicators

**In discussion:** [What to listen for]
**In written work:** [What to look for]
**The key test:** [Single most reliable indicator]

**Self-check before returning output:** Verify that (a) the progression distinguishes between possessing background knowledge and deploying it during reading, (b) the think-aloud makes the inferential leap from context to interpretation EXPLICIT, (c) the guided practice includes a structured bridge that scaffolds the connection step, (d) the failure patterns address the knowledge-vs-deployment distinction, and (e) the instruction design accounts for the finding that contextualisation requires different strategies than sourcing and close reading.
```

## Example Output

**Scenario:** *Historical topic: "Columbus Day proclamation of 1892" / Student level: "Year 10, have studied 1890s immigration and the Progressive Era but don't connect this knowledge to document analysis" / Current challenge: "When they read Harrison's proclamation, they focus entirely on Columbus — whether he was a hero or a villain — and don't consider why a president in 1892 would create this holiday" / Background knowledge: "Students have studied the closing of the frontier, mass immigration from Southern and Eastern Europe, nativism, and the Columbian Exposition"*

---

## Contextualisation Instruction Plan

**Topic:** Columbus Day proclamation of 1892
**Students:** Year 10, know the 1890s context but deploy it as Columbus commentary rather than contextual analysis
**Source type:** Government proclamation

### Contextualisation Progression

**Novice — reading without context:**
The student reads Harrison's proclamation and responds to Columbus: "He says Columbus was noble but Columbus actually killed people" or "I agree that Columbus was brave." The document triggers opinions about Columbus, and the student evaluates those opinions against their existing knowledge. The year 1892 is irrelevant to their reading — the document could have been written in 1792 or 1992 and their response would be the same. If asked "Why was this written in 1892?", they are puzzled — the question doesn't make sense to them because they haven't considered that the document is a product of a specific moment.

**Developing — knowing context but not deploying it:**
The student can, when prompted, recall what was happening in the 1890s: immigration, nativism, the frontier closing, the Columbian Exposition. But this knowledge sits in a separate mental compartment from the document. When they read the proclamation, they engage with Columbus. When asked about the 1890s, they recite facts about immigration. The two are not connected. If directly asked "Could the 1890s immigration wave have anything to do with this proclamation?", they may begin to see a connection — but they would not have made it on their own.

**Proficient — deploying context to transform interpretation:**
The student reads "1892" and immediately connects it to what they know: the biggest wave of immigration in US history, predominantly from Southern and Eastern Europe — Catholic and Jewish immigrants seen as threatening by the Protestant establishment. They hypothesise that declaring Columbus (an Italian Catholic) a national hero might be a strategic move to expand the definition of "American" to include these new immigrants. The document stops being a statement about 1492 and becomes a political act in 1892. Context has transformed the interpretation.

### Explicit Instruction Sequence

**I DO — Teacher Think-Aloud**

*Teacher projects the proclamation with the date visible:*

"Before I engage with what this says about Columbus, I'm going to look at the date. 1892. What do I know about 1892? Immediately I'm thinking: this is the height of mass immigration. Millions of people arriving from Italy, Poland, Russia — Catholic and Jewish immigrants that many Americans saw as a threat. There's a huge nativist backlash.

Now — Columbus was Italian. And Catholic. So a president declaring Columbus a national hero in 1892 is not just making a statement about the past. He's making a statement about the present. He's saying: Italians — Catholics — are part of the American story. They've been part of it from the very beginning.

That changes EVERYTHING about how I read this document. When Harrison calls Columbus's journey 'one of the most notable achievements of human will and effort,' I'm not hearing a history lesson about 1492. I'm hearing a political argument about 1892: these new immigrants are heirs to a noble tradition, not foreign invaders. The document is about NOW, not then."

**WE DO — Guided Practice**

Two-step bridge activity:

*Step 1 — Activate knowledge:* Before seeing the document, students spend three minutes in pairs listing everything they know about the 1890s on a graphic organiser (immigration, nativism, frontier closing, Columbian Exposition, Progressive Era). This activates the knowledge.

*Step 2 — Connect:* Students receive the proclamation. Their task is NOT to analyse it in full but to complete one specific sentence: "This document was written in 1892, and knowing what I know about the 1890s, I think the real purpose of this proclamation was ___ because ___." They must draw an explicit arrow between at least one item on their 1890s list and a specific feature of the document.

Teacher circulates. Key redirections:
- If students write about Columbus's character: "Your sentence should start with 1892, not with Columbus. What was happening in 1892 that makes this document make sense?"
- If students make a vague connection ("It was written during a time of change"): "WHICH change? Be specific. Pick one thing from your 1890s list and connect it to one specific thing in the document."

**YOU DO — Independent Practice**

Students receive a new document from a different period (e.g., a World War I recruitment poster). Without the two-step bridge scaffold, they write a contextualisation paragraph: "This document was created in [year]. At this time, [relevant context]. This context helps explain why the document [specific feature], because [connection]."

Teacher monitors for whether students spontaneously reach for context or need prompting.

### Contextualisation Prompts

1. **What was happening at the time this document was created, and how might that shape what the author wrote?**
   *Why it matters:* This is the core contextualisation move — connecting the document to its moment.
   *Sentence starter:* "At the time this was written, ___ was happening, which helps explain why the author..."

2. **Would this document have been different if it had been written 20 years earlier or 20 years later? How and why?**
   *Why it matters:* Forces students to see the document as time-bound rather than timeless. If the answer is "no, it would be the same," the student isn't contextualising.
   *Sentence starter:* "If this had been written in [different year], it would probably be different because..."

3. **What problem or situation was the author responding to?**
   *Why it matters:* Documents are not produced in a vacuum. They are responses to circumstances. This prompt pushes students to identify the circumstance that made the document necessary.
   *Sentence starter:* "The author was probably responding to ___, which is why they..."

4. **What did the words in this document mean at the time — and is that different from what they mean now?**
   *Why it matters:* Gottlieb and Wineburg (2012) showed that historians recognised historical language (Washington's deist phrasing) where non-historians imposed contemporary meanings. Words change meaning over time, and contextualisation includes linguistic awareness.
   *Sentence starter:* "When the author wrote '___,' they probably meant ___, which is different from how we'd understand it today because..."

### Common Failure Patterns

**1. "Knowledge possessed but not deployed" — knowing the context but not connecting it**
*What it looks like:* The student can answer "What was happening in the 1890s?" correctly on a test but reads an 1892 document without any reference to the 1890s. Context knowledge and document analysis are stored in separate compartments.
*Why:* Reading habits treat documents as self-contained. Students have not been taught to ask "what was happening at the time?" as a reflex action before reading, the way they (may) have been taught to check the source note. Contextualisation requires an inferential leap that sourcing does not.
*Response:* Use the two-step bridge: activate context knowledge BEFORE giving students the document, then require an explicit written connection between a context item and a document feature. Over time, students internalise the bridge and no longer need the scaffold.

**2. "Presentism" — reading historical documents through contemporary values**
*What it looks like:* The student evaluates Harrison's praise of Columbus by contemporary standards: "He shouldn't have celebrated Columbus because Columbus committed genocide." The student is applying 2024 moral standards to an 1892 document without considering what those words meant to their original audience.
*Why:* This is the spread of activation effect (Wineburg, 2007). The Columbus node triggers everything the student knows about Columbus revisionism, overwhelming attention to 1892 circumstances.
*Response:* Validate the student's moral position but redirect: "You're right that we see Columbus differently today. But the question isn't whether WE think Columbus was a hero — it's why HARRISON, in 1892, thought celebrating Columbus was politically useful. What was happening in 1892 that made this make sense to people at the time?"

**3. "Context as decoration" — adding background information without using it**
*What it looks like:* The student writes a paragraph of background information about the period, then a separate paragraph analysing the document. The two paragraphs don't connect. Context appears as scene-setting rather than as an analytical tool.
*Why:* Students have learned that "context" means "write about the historical background." They haven't learned that context should CHANGE how they interpret the document.
*Response:* Require the word "because" or "which explains why" at the connection point. The student must write a sentence that explicitly links a contextual fact to a specific feature of the document: "Because mass immigration was creating anti-Catholic sentiment in the 1890s, Harrison's celebration of Columbus — an Italian Catholic — was a political act, not just a historical commemoration."

### Assessment Indicators

**In discussion:** Listen for students who spontaneously ask about the time period before or during discussion of a document: "When was this written? What was going on then?" More advanced: listen for students who connect the document to contemporary events without prompting — "This reminds me of what was happening with immigration at the time."

**In written work:** Look for sentences that use context to CHANGE the interpretation, not just set the scene. The test: can you remove the context paragraph without changing the analysis paragraph? If yes, the student is decorating, not contextualising. If removing the context would make the analysis collapse, the student is genuinely deploying context.

**The key test:** Give students a document from a period they have studied, with the date visible but no instruction to contextualise. Do they spontaneously connect the document to what they know about the period, or do they engage with the content in isolation? The gap between what students do when prompted ("What was happening in 1892?") and what they do unprompted is the measure of how far contextualisation has developed from a school exercise into a thinking disposition.

---

## Known Limitations

1. **Contextualisation did not show significant treatment effects in Reisman (2012), the foundational effectiveness study for the Reading Like a Historian curriculum.** The instructional strategies in this skill draw on Reisman's post-hoc explanations and on the expert reading behaviours documented in Wineburg (2007) and Gottlieb and Wineburg (2012), but they have not been tested as an intervention in their own right. Evidence strength is rated "moderate" accordingly.

2. **Contextualisation depends on background knowledge in a way that sourcing and close reading do not.** A student cannot contextualise a document about the 1890s if they know nothing about the 1890s. This means contextualisation instruction must be preceded by or paired with content instruction. The skill addresses the deployment problem (students who know the context but don't use it) more effectively than the knowledge gap problem (students who lack the context entirely). Teachers should diagnose which problem their students have before selecting instructional strategies.

3. **The distinction between contextualisation and presentism is pedagogically sensitive.** Teaching students to understand a document "in its time" can be misread as asking them to suspend moral judgement — to accept that slavery was acceptable because "people thought differently then." This is not what contextualisation means. Contextualisation means understanding WHY people in the past acted and thought as they did, not approving of it. Teachers should make this distinction explicit to avoid the impression that historical understanding requires moral relativism.

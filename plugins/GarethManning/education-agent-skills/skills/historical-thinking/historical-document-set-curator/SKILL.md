---
# AGENT SKILLS STANDARD FIELDS (v2)
name: historical-document-set-curator
description: "Design a document set for a document-based lesson — selecting and sequencing sources for analytical tension around a central question. Use when assembling sources for a new lesson or when an existing set produces flat responses."
disable-model-invocation: false
user-invocable: true
effort: high

# EXISTING FIELDS
skill_id: "historical-thinking/historical-document-set-curator"
skill_name: "Historical Document Set Curator"
domain: "historical-thinking"
version: "1.0"
contributor: "Sean Hu"
evidence_strength: "moderate"
evidence_sources:
  - "Reisman (2012) — Reading like a historian: a document-based history curriculum intervention in urban high schools"
  - "Wineburg, Martin & Monte-Sano (2011) — Reading like a historian: teaching literacy in middle and high school history classrooms"
  - "Wineburg & Martin (2004) — Reading and rewriting history"
  - "Wineburg (2007) — Unnatural and essential: the nature of historical thinking"
  - "Caswell (2014) — Seeing yourself in history: community archives and the fight against symbolic annihilation"
  - "Theimer (2012) — Archives in context and as context"
input_schema:
  required:
    - field: "central_question"
      type: "string"
      description: "The central historical question the document set must support — the inquiry that students will investigate using these sources"
    - field: "student_level"
      type: "string"
      description: "Age/year group, reading level, and experience with document-based inquiry"
    - field: "target_skills"
      type: "string"
      description: "Which historical thinking skills the document set should foreground — e.g. sourcing and corroboration, close reading, all four"
  optional:
    - field: "existing_sources"
      type: "string"
      description: "Sources the teacher already has or plans to use — the skill will evaluate these and suggest additions, removals, or resequencing"
    - field: "set_size"
      type: "string"
      description: "Target number of documents — typically 2–5 for a single lesson, more for a multi-day unit"
    - field: "source_constraints"
      type: "string"
      description: "Practical constraints — e.g. sources must be freely available online, must be in English, must be shorter than 200 words each, must include visual sources"
    - field: "representation_priorities"
      type: "string"
      description: "Whose perspectives should be represented in the set — e.g. ensure Indigenous voices are included, include perspectives from multiple social classes, include women's perspectives"
    - field: "historical_topic"
      type: "string"
      description: "The broader topic or unit the lesson sits within"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: relevant curriculum standards or historical thinking framework in use"
output_schema:
  type: "object"
  fields:
    - field: "document_set_design"
      type: "object"
      description: "The recommended document set with rationale — which sources, in what sequence, and why each earns its place"
    - field: "analytical_tensions"
      type: "array"
      description: "The specific tensions, contradictions, or complementarities built into the set — what students will discover when they compare sources"
    - field: "skill_affordances"
      type: "object"
      description: "For each target skill, which documents in the set provide the best opportunity to practise it and why"
    - field: "sequencing_rationale"
      type: "string"
      description: "Why the documents are ordered as they are — what each round of reading adds to the investigation"
    - field: "representation_audit"
      type: "object"
      description: "Whose perspectives are present and absent in the set, with honest acknowledgement of gaps and suggestions for addressing them"
chains_well_with:
  - "central-historical-question-evaluator"
  - "historical-source-adapter"
  - "document-based-lesson-designer"
  - "historical-thinking-strategy-modelling-guide"
  - "sourcing-skill-builder"
  - "corroboration-skill-builder"
  - "historical-thinking-assessment-designer"
teacher_time: "5 minutes"
tags: ["document-sets", "historical-thinking", "primary-sources", "source-selection", "lesson-design", "corroboration", "representation", "DIG"]
---

# Historical Document Set Curator

## What This Skill Does

Designs a document set for a document-based history lesson — recommending which sources to include, how to sequence them, and why each document earns its place in the set. The output includes the set design with rationale, the analytical tensions built into the set, a mapping of which documents support which historical thinking skills, a sequencing rationale, and a representation audit identifying whose perspectives are present and absent.

A document set is not a collection of sources on a topic. It is a carefully designed evidentiary environment that creates productive analytical tension around a central question. The difference matters: a collection of five documents about World War I gives students information to read; a curated set of five documents that contradict, complement, and complicate each other gives students a problem to solve. The quality of the document set determines whether students engage in genuine corroboration (weighing accounts against each other) or sequential summarisation (reading one source, then the next, without connecting them).

The Reading Like a Historian curriculum (Reisman, 2012; Wineburg, Martin & Monte-Sano, 2011) used 2–5 documents per lesson, selected for specific analytical properties: contradictions between accounts, differences in perspective or purpose, tensions between primary evidence and received narratives. The Pocahontas lesson paired Smith's two contradictory self-accounts with four historians who reached different conclusions from the same evidence — creating layered analytical tension that makes corroboration not just possible but necessary.

This skill also addresses the representation question that Caswell (2014) raised: whose history is documented, whose is absent, and what the implications of those absences are for what students can learn. A document set on early American colonisation that includes only English-authored sources doesn't just limit perspectives — it structurally prevents students from practising certain analytical moves (they cannot corroborate across genuinely different viewpoints if all viewpoints share the same cultural assumptions). The skill includes a representation audit that names these gaps honestly.

## Evidence Foundation

Reisman (2012) used document sets of 2–5 primary sources per lesson in the Reading Like a Historian curriculum. Each lesson's documents were selected to create a central tension requiring investigation. The significant treatment effects for sourcing and close reading (but not corroboration) suggest that document set design matters: the sources must create opportunities for the target skills. Reisman attributed the null corroboration finding partly to the near-absence of whole-class discussion, but the document set design also plays a role — corroboration requires sources that genuinely tension with each other, not just sources that say different things.

Wineburg, Martin, and Monte-Sano (2011) provided detailed rationales for their document set designs. The Pocahontas chapter uses six sources in three rounds: Round 1 (Smith's two accounts) creates the foundational contradiction; Round 2 (Adams and Lemay) shows historians disagreeing about what the contradiction means; Round 3 (Lewis and Barbour) adds further interpretive complexity. Each round deepens the investigation without overwhelming students with too many documents at once. This progressive architecture — contradiction first, then competing interpretations, then further complication — is a design principle, not an accident.

Wineburg and Martin (2004) demonstrated that document selection shapes what students can discover. The Pocahontas unit begins with Disney's version to activate prior knowledge, then dismantles it through primary source comparison. The documents are sequenced to create cognitive dissonance: what students think they know (from Disney) is destabilised by what the sources reveal. This sequencing principle — start with the familiar, then complicate — is central to effective document set design.

Caswell (2014) argued that archival absence constitutes symbolic annihilation — when a community's history is not preserved, that community is rendered invisible in the historical record. For document set design, this means that the available pool of sources is not neutral. A document set on South Asian American history requires the kind of community-archiving work that SAADA does; without it, the curriculum has nothing to work with. Teachers should be aware that some topics will have richer source pools than others, and that absence from the archive is itself historically significant.

Theimer (2012) emphasised that how sources are collected, arranged, and presented shapes what historical thinking is possible. A source removed from its archival context — stripped of information about who collected it, how it was preserved, and what other materials surrounded it — loses the contextual information that sourcing and contextualisation depend on. Document sets should preserve provenance information wherever possible.

## Input Schema

The teacher must provide:
- **Central question:** The inquiry question. *e.g. "Did Pocahontas rescue John Smith?" / "Who was most to blame for World War I?" / "Was the dropping of the atomic bomb justified?" / "How did enslaved people resist the institution of slavery?"*
- **Student level:** *e.g. "Year 8, second term of document-based work" / "Year 11 IB History, experienced with multi-document analysis" / "Year 7, first document-based lesson — need simple, short sources"*
- **Target skills:** *e.g. "Sourcing and corroboration — students need to compare conflicting accounts" / "Close reading — students need to analyse language in speeches" / "All four skills — this is a culminating lesson"*

Optional:
- **Existing sources:** Sources the teacher already has — for evaluation and supplementation
- **Set size:** Target number of documents
- **Source constraints:** Practical limitations on what sources can be used
- **Representation priorities:** Whose perspectives to include
- **Historical topic, curriculum framework** — for contextual alignment

## Prompt

```
You are an expert in designing document sets for document-based history lessons, with deep knowledge of the Reading Like a Historian curriculum's approach to source selection (Reisman, 2012; Wineburg, Martin & Monte-Sano, 2011), the role of analytical tension in driving genuine historical inquiry, and the representation concerns raised by Caswell (2014) about whose histories are documented and whose are absent.

You understand that a document set is not a collection of sources on a topic but a designed evidentiary environment that creates productive analytical tension around a central question. Each document must earn its place by contributing something that the other documents do not — a contradicting perspective, a different type of evidence, a complicating detail, or a voice that would otherwise be absent.

Your task is to design a document set for:

**Central question:** {{central_question}}
**Student level:** {{student_level}}
**Target skills:** {{target_skills}}

The following optional context may or may not be provided. Use whatever is available.

**Existing sources:** {{existing_sources}} — if provided, evaluate these sources first. Do they create analytical tension? Do they support the target skills? Should any be removed, replaced, or supplemented?
**Set size:** {{set_size}} — if not provided, recommend 3–4 documents for a single lesson, noting that 2 is the minimum for corroboration and 5+ risks overwhelming students.
**Source constraints:** {{source_constraints}}
**Representation priorities:** {{representation_priorities}} — if provided, design the set to include these perspectives. If not, audit the set for representation and flag gaps.
**Historical topic:** {{historical_topic}}
**Curriculum framework:** {{curriculum_framework}}

Design the following:

1. **Document set design:** For each recommended document, provide:
   - A description (author, date, type, key content)
   - Why it earns its place in the set — what it contributes that no other document in the set provides
   - Which historical thinking skills it most directly supports
   - Its role in the sequence (what it adds to the investigation at this point)

   If existing sources were provided, evaluate them first and indicate which to keep, modify, or replace before recommending additions.

2. **Analytical tensions:** The specific contradictions, complementarities, or complications built into the set. For each tension, identify:
   - Which documents create the tension
   - What students should discover when they compare them
   - What historical thinking skill the tension demands

   A set with no analytical tension is a reading list, not an investigation. Every set must have at least one clear tension.

3. **Skill affordances:** For each target skill, identify which documents in the set provide the best opportunity to practise it:
   - **Sourcing:** Which document has source information that is most analytically productive?
   - **Close reading:** Which document has language most worth attending to closely?
   - **Contextualisation:** Which document is most illuminated by knowledge of its historical context?
   - **Corroboration:** Which document pairing creates the most productive comparison?

4. **Sequencing rationale:** Why the documents are ordered as they are. The default structure from the RLH curriculum is:
   - Round 1: The foundational source(s) that establish the problem
   - Round 2: Source(s) that complicate, contradict, or reinterpret
   - Round 3 (if applicable): Source(s) that add further complexity or introduce new perspectives

   Explain what each round adds to the investigation and why the order matters.

5. **Representation audit:** Whose perspectives are present in the set and whose are absent. Be honest about gaps. If the central question concerns an event involving multiple groups (colonisers and Indigenous peoples, employers and workers, men and women), note which groups have voice in the set and which do not. Where possible, suggest sources that would address gaps. Where sources from absent perspectives do not exist (because those voices were not documented), name this as a historically significant silence — itself a teaching opportunity.

Return your output in this exact format:

## Document Set Design

**Central question:** [Question]
**Students:** [Level]
**Set size:** [Number of documents]

### Document 1: [Brief title]
**Source:** [Author, date, type]
**Why it's here:** [What it contributes]
**Supports:** [Which skills]
**Role in sequence:** [What it adds at this point]

### Document 2: [Brief title]
[Same format]

[Continue for each document]

### Analytical Tensions

[Numbered list of tensions with documents involved, what students should discover, and skill demanded]

### Skill Affordances

**Sourcing:** [Best document and why]
**Close reading:** [Best document and why]
**Contextualisation:** [Best document and why]
**Corroboration:** [Best pairing and why]

### Sequencing Rationale

[Why this order, what each round adds]

### Representation Audit

**Perspectives present:** [Who has voice]
**Perspectives absent:** [Who doesn't, and why]
**Suggestions:** [How to address gaps, or acknowledgement that the gap is itself historically significant]

**Self-check before returning output:** Verify that (a) every document earns its place — remove any source that doesn't contribute something unique, (b) at least one clear analytical tension exists in the set, (c) the skill affordances are specific to the documents, not generic, (d) the sequencing has a rationale beyond chronological order, and (e) the representation audit is honest about whose voices are missing.
```

## Example Output

**Scenario:** *Central question: "Did Pocahontas rescue John Smith?" / Student level: "Year 8, second term of document-based lessons" / Target skills: "All four — sourcing, close reading, contextualisation, corroboration" / Set size: "4 documents for a 2-hour lesson"*

---

## Document Set Design

**Central question:** Did Pocahontas rescue John Smith?
**Students:** Year 8, familiar with document-based inquiry
**Set size:** 4 documents across 2 rounds

### Document 1: Smith's 1608 True Relation (adapted excerpt)
**Source:** John Smith, 1608, *A True Relation*, report sent to England
**Why it's here:** Establishes the baseline account — written closest to the event, with NO mention of threat or rescue. Uses language of friendship and generosity. Its significance is in what it does NOT say.
**Supports:** Sourcing (date, purpose, audience); close reading (tone: "kindly," "friendship," "kindness")
**Role in sequence:** Round 1 — the first source students encounter, establishing expectations that the second source will disrupt.

### Document 2: Smith's 1624 General History (adapted excerpt)
**Source:** John Smith, 1624, *General History of Virginia*, published book
**Why it's here:** Creates the foundational contradiction. Same author, same event, completely different account — now with dramatic rescue, threatening language, and Pocahontas as heroine. The contrast with Document 1 IS the historical problem.
**Supports:** Sourcing (17-year gap, different publication context); close reading (tone shift: "barbarous," "beat out his brains," "dearest daughter"); corroboration (direct contradiction with Document 1)
**Role in sequence:** Round 1 — paired with Document 1 to create the central puzzle. Students should encounter both before any interpretive framework is offered.

### Document 3: Adams's 1867 critique (adapted summary)
**Source:** Henry Adams, 1867, *The North American Review*, scholarly critique
**Why it's here:** Introduces historical interpretation — a trained historian who argues Smith's rescue story is fabricated, citing the contradictions between the two accounts. Shows students that historians use the SAME evidence they just examined to build arguments.
**Supports:** Sourcing (Adams's identity as a great-grandson of John Adams, his political context — writing during Reconstruction); corroboration (his argument depends on comparing the two Smith accounts, modelling the skill students just practised)
**Role in sequence:** Round 2 — after students have formed their own hypotheses from the primary sources, they encounter a historian who has done the same analysis. This validates and extends their thinking.

### Document 4: Lemay's 1991 defence (adapted summary)
**Source:** J. A. Leo Lemay, 1991, *The American Dream of Captain John Smith*, scholarly interpretation
**Why it's here:** Creates tension with Adams. Lemay argues Smith WAS truthful, that the two accounts differ because they had different purposes, and that the event was probably a ritual adoption ceremony rather than a genuine rescue. This prevents students from settling on Adams's scepticism as the final answer.
**Supports:** Corroboration (direct disagreement with Adams using the same evidence); contextualisation (Lemay's interpretation draws on knowledge of Powhatan adoption rituals — context students may not have)
**Role in sequence:** Round 2 — paired with Adams. Students must now weigh two historians who reach opposite conclusions from the same primary sources. The question cannot be resolved by choosing one source — it requires genuine weighing of evidence and argument.

### Analytical Tensions

1. **Smith vs. Smith (Documents 1 and 2).** The same author contradicts himself across a 16-year gap. Students should discover that eyewitness testimony is not inherently reliable and that the same person can tell the same story differently depending on when and why they write. *Skill demanded:* sourcing (why the accounts differ) and close reading (how the language differs).

2. **Adams vs. Lemay (Documents 3 and 4).** Two historians examine the same primary evidence and reach opposite conclusions. Students should discover that historical knowledge is constructed through interpretation, not simply found in documents. *Skill demanded:* corroboration (comparing the historians' arguments) and contextualisation (understanding what each historian brings to their reading).

3. **Primary vs. secondary sources (Documents 1–2 vs. 3–4).** Students encounter raw evidence first, then professional interpretations of that evidence. They should discover that their own analysis of the primary sources is a valid entry point into a genuine historiographical debate. *Skill demanded:* all four — this tension structures the entire lesson.

### Skill Affordances

**Sourcing:** Document 2 (the 1624 General History) — the 17-year gap, the shift from report to published book, and Smith's self-interest make this the richest sourcing opportunity. But Document 3 (Adams) is also productive for sourcing: his 1867 date, during Reconstruction, adds a political dimension to his critique of a Virginian hero.

**Close reading:** Documents 1 and 2 together — the shift from "kindly welcomed me" to "their best barbarous manner" is the most analytically productive language comparison in the set. Individual words carry enormous weight.

**Contextualisation:** Document 2 — understanding why Smith wrote differently in 1624 requires knowing that Pocahontas had visited England and become famous by then. Document 3 also rewards contextualisation: Adams writing during Reconstruction had political reasons to undermine Virginia's founding mythology.

**Corroboration:** Documents 3 and 4 together — Adams and Lemay create the cleanest comparison because they examine the same evidence and reach opposite conclusions. This pairing teaches students that corroboration is not about finding agreement but about reasoning through disagreement.

### Sequencing Rationale

**Round 1 (Documents 1 and 2 — Smith's two accounts):** Students encounter the primary evidence before any interpretation. This ensures they form their own hypotheses about why the accounts differ before being told what historians think. The 1608 account comes first because its ABSENCE of the rescue is only significant in comparison — students need to read the friendly account, then be surprised by the dramatic account.

**Round 2 (Documents 3 and 4 — Adams and Lemay):** After students have grappled with the primary evidence, they encounter two historians who have done the same work. This validates students' analytical efforts (historians asked the same questions they did) while extending the inquiry (historians brought more knowledge and reached more developed arguments). Adams comes before Lemay so students experience scepticism about Smith first, then have that scepticism complicated by Lemay's defence.

### Representation Audit

**Perspectives present:** English colonist (Smith), 19th-century American historian (Adams), 20th-century American literary scholar (Lemay). All are male, white, and writing from positions of institutional authority.

**Perspectives absent:** Pocahontas herself left no written record. No Powhatan perspective is directly represented. No woman's voice appears. No Indigenous scholarly interpretation is included.

**Suggestions:** This absence is historically significant and should be named in the lesson: the fact that we have no Powhatan account of this event is not a gap to paper over but a consequence of power — who gets to write history and whose words survive. If extending the set, consider adding Helen Rountree's ethnohistorical work, which reconstructs Powhatan perspectives from archaeological and anthropological evidence, or Camilla Townsend's *Pocahontas and the Powhatan Dilemma*, which foregrounds Indigenous context. A teacher might also use the absence as a teaching moment for sourcing: "Why do we only have Smith's account? What does that tell us about whose stories get preserved?"

---

## Known Limitations

1. **This skill designs document sets but cannot supply the documents themselves.** It recommends specific sources by author, date, and type, but the teacher must locate, obtain, and (where necessary) adapt them. For freely available sources, the SHEG/DIG curriculum at sheg.stanford.edu provides adapted primary sources for many US history topics. For other topics, teachers will need to source documents from archives, textbooks, or digital collections.

2. **The representation audit identifies gaps but cannot always fill them.** For some historical topics, the voices of marginalised groups were not documented — not because they didn't exist but because the power structures that determine what gets preserved excluded them (Caswell, 2014; Theimer, 2012). The skill names these silences honestly rather than pretending they can be easily resolved. In some cases, the absence itself becomes the most important thing to teach.

3. **Document set design is inseparable from the central question.** A set designed for "Did Pocahontas rescue John Smith?" will not work for "What was the nature of Powhatan-English relations?" The skill evaluates the set against the specific question provided. If the question changes, the set should be re-evaluated.

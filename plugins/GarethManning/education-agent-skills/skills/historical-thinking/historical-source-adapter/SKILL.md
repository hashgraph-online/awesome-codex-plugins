---
# AGENT SKILLS STANDARD FIELDS (v2)
name: historical-source-adapter
description: "Adapt a historical primary source for classroom use — modifying complexity and length while preserving features for sourcing, close reading, and corroboration. Use when a primary source is too complex for the target age group."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS
skill_id: "historical-thinking/historical-source-adapter"
skill_name: "Historical Source Adapter"
domain: "historical-thinking"
version: "1.0"
contributor: "Sean Hu"
evidence_strength: "moderate"
evidence_sources:
  - "Reisman (2012) — Reading like a historian: a document-based history curriculum intervention in urban high schools"
  - "Wineburg, Martin & Monte-Sano (2011) — Reading like a historian: teaching literacy in middle and high school history classrooms"
  - "Wineburg & Reisman (2015) — Disciplinary literacy in history: a toolkit for digital citizenship"
  - "Wineburg (2007) — Unnatural and essential: the nature of historical thinking"
  - "Faggella-Luby, Graner, Deshler & Drew (2012) — Building a house on sand: why disciplinary literacy is not sufficient to replace general strategies for adolescent learners who struggle"
input_schema:
  required:
    - field: "original_source"
      type: "string"
      description: "The full text of the original primary source, or the passage to be adapted, with complete source attribution (author, date, publication, context of production)"
    - field: "student_level"
      type: "string"
      description: "Age/year group and reading level of the target students"
    - field: "target_skills"
      type: "string"
      description: "Which historical thinking skills the adapted source must support — e.g. sourcing, close reading, contextualisation, corroboration — so the adaptation preserves the features necessary for those analytical moves"
  optional:
    - field: "target_length"
      type: "string"
      description: "Desired approximate length of the adapted source — e.g. '150 words', '1 paragraph', 'half the original length'"
    - field: "central_question"
      type: "string"
      description: "The central historical question the source will be used to investigate — ensures the adaptation preserves the features most relevant to the inquiry"
    - field: "key_passages"
      type: "string"
      description: "Specific passages or phrases that MUST be preserved in the adapted version because they are analytically important — e.g. loaded language for close reading, contradictions for corroboration"
    - field: "eal_considerations"
      type: "string"
      description: "Whether the class includes English as an Additional Language learners, and at what proficiency level — affects the degree of vocabulary support needed"
    - field: "paired_documents"
      type: "string"
      description: "Other documents in the lesson's document set — ensures the adaptation preserves features needed for corroboration across the set"
output_schema:
  type: "object"
  fields:
    - field: "adapted_source"
      type: "string"
      description: "The adapted version of the source, with source attribution preserved in full and clear indication of what has been modified"
    - field: "adaptation_notes"
      type: "object"
      description: "Transparent documentation of every change made — what was cut, what was simplified, what was glossed — so the teacher can verify that the adaptation preserves analytical value"
    - field: "preserved_features"
      type: "array"
      description: "Explicit list of features preserved for each target skill — e.g. which word choices were kept for close reading, which bibliographic details were kept for sourcing"
    - field: "word_bank"
      type: "array"
      description: "Vocabulary support for difficult words retained in the adapted version — definitions that don't interpret the document's meaning for the student"
    - field: "analytical_value_check"
      type: "object"
      description: "A brief check confirming that each target skill can still be practised with the adapted version — flagging any analytical moves that the adaptation may have compromised"
chains_well_with:
  - "document-based-lesson-designer"
  - "historical-document-set-curator"
  - "central-historical-question-evaluator"
  - "sourcing-skill-builder"
  - "close-reading-skill-builder"
  - "text-complexity-analyser"
  - "vocabulary-tiering-tool"
  - "language-demand-analyser"
  - "scaffolded-task-modifier"
teacher_time: "3 minutes"
tags: ["source-adaptation", "historical-thinking", "primary-sources", "accessibility", "disciplinary-literacy", "differentiation", "DIG"]
---

# Historical Source Adapter

## What This Skill Does

Adapts a historical primary source for classroom use — modifying language complexity, length, and presentation while preserving the features that make the document analytically valuable for historical thinking. The output includes the adapted source with full attribution, transparent documentation of every change, a list of features preserved for each target skill, a word bank for difficult retained vocabulary, and an analytical value check confirming the adapted version still supports the intended historical thinking skills.

The central tension in source adaptation is between accessibility and authenticity. A source simplified into modern paraphrase is easy to read but analytically dead — if the author's word choices have been replaced, there is nothing left to close-read; if archaic phrasing has been modernised, the document no longer feels like a product of its time. Conversely, an unmodified 17th-century document may be so linguistically impenetrable that students spend all their cognitive resources on decoding and have nothing left for analysis. The goal is the middle ground: a document that students can read with effort but that retains the features — loaded language, source attribution, temporal markers, rhetorical strategies — that make historical thinking possible.

Reisman (2012) addressed this directly in the Reading Like a Historian curriculum. The 83 Document-Based Lessons used primary sources that had been "modified for accessibility" — adapted for the reading level of urban 11th-grade students, many of whom read below the 25th percentile. Crucially, these adaptations preserved the documents' analytical features: source notes remained intact, key language choices were retained, and the modifications were transparent (original and adapted versions were often provided side by side, as in the Pocahontas chapter of Wineburg, Martin & Monte-Sano, 2011). The significant treatment effects for sourcing and close reading suggest that well-adapted sources can support disciplinary reading even with struggling readers.

## Evidence Foundation

Reisman (2012) demonstrated that primary sources modified for accessibility can produce significant gains in historical thinking. Treatment students, including those reading below the 25th percentile, showed significant improvements in sourcing and close reading when working with adapted documents. The adaptations in the RLH curriculum involved shortening documents, glossing archaic vocabulary, and providing both original and adapted versions — but did not paraphrase the author's voice or remove source attribution. The finding that struggling readers in the treatment condition outperformed their counterparts on historical thinking (ηp² = .17) and factual knowledge (ηp² = .22) suggests that accessibility modifications do not compromise analytical value when done carefully.

Wineburg, Martin, and Monte-Sano (2011) provided concrete examples of source adaptation in the Pocahontas chapter. Smith's 1608 and 1624 accounts appear in both original and adapted forms, with a word bank for archaic terms. The adapted versions preserve the key analytical features: the source attribution (author, date, publication), the contrasting language ("kindly" vs. "barbarous"), and the narrative structure. What is modified is sentence complexity and archaic spelling — changes that reduce the decoding burden without altering the analytical opportunity.

Wineburg and Reisman (2015) argued that disciplinary literacy in history requires engagement with the author's actual language — sourcing depends on the source note, close reading depends on word choice, contextualisation depends on temporal markers. Generic reading strategies (summarising, predicting) can be applied to paraphrased documents, but disciplinary strategies cannot. This means that source adaptation must preserve the features that disciplinary reading targets, even as it modifies the features that obstruct access.

Faggella-Luby et al. (2012) argued that general reading strategies "may even form the bedrock of fluent reading" — students who cannot decode the text cannot analyse it. This supports the case for adaptation: if a document is so linguistically complex that students cannot read it fluently, the historical thinking skills that depend on fluent reading are inaccessible. Adaptation is not a concession to lower standards but a prerequisite for disciplinary engagement.

## Input Schema

The teacher must provide:
- **Original source:** The full text with complete attribution. *e.g. The full text of Smith's 1624 General History passage, with: "John Smith (1624), General History of Virginia, New England and the Summer Isles, Vol. 2, Chapel Hill: University of North Carolina Press, p. 151."*
- **Student level:** *e.g. "Year 7, average reading age 10–11" / "Year 10, includes several EAL students at intermediate proficiency" / "Year 8, mixed ability with some students reading significantly below age"*
- **Target skills:** Which historical thinking skills the source must support. *e.g. "Sourcing and close reading" / "All four — this is the main document in a document-based lesson" / "Corroboration — this source will be compared with two others"*

Optional:
- **Target length:** Desired length of the adapted version
- **Central question:** The inquiry question — guides what to preserve
- **Key passages:** Specific language that must be retained
- **EAL considerations:** Affects vocabulary support level
- **Paired documents:** Other sources in the set — ensures corroboration features are preserved

## Prompt

```
You are an expert in adapting historical primary sources for classroom use, with deep knowledge of how the Reading Like a Historian curriculum (Reisman, 2012; Wineburg, Martin & Monte-Sano, 2011) modified sources for accessibility while preserving their analytical value for historical thinking. You understand the central tension in source adaptation: accessibility vs. authenticity. Your goal is the middle ground — a document students can read with effort that retains the features necessary for sourcing, close reading, contextualisation, and corroboration.

Your task is to adapt the following source:

**Original source:** {{original_source}}
**Student level:** {{student_level}}
**Target skills:** {{target_skills}}

The following optional context may or may not be provided. Use whatever is available.

**Target length:** {{target_length}} — if not provided, use your judgement to reduce the source to a length manageable for the student level while preserving analytical value.
**Central question:** {{central_question}} — if provided, prioritise preserving features that are most relevant to investigating this question.
**Key passages:** {{key_passages}} — if provided, these passages MUST appear in the adapted version with minimal modification.
**EAL considerations:** {{eal_considerations}} — if provided, adjust the word bank and glossing accordingly.
**Paired documents:** {{paired_documents}} — if provided, ensure the adaptation preserves features needed for comparison with these other sources.

Apply these adaptation principles:

1. **Preserve the source note in full.** Author, date, publication context — never simplify, abbreviate, or remove source attribution. This is what students need for sourcing.

2. **Preserve the author's voice.** The adapted version should still sound like the original author, not like a modern textbook. If Smith wrote "barbarous," keep "barbarous" and gloss it in the word bank — do not replace it with "uncivilised." The author's word choices are what students need for close reading.

3. **Preserve analytically significant language.** Identify the words, phrases, and rhetorical features that carry analytical weight for the target skills. These must survive the adaptation. Flag them in the preserved features list.

4. **Simplify sentence structure, not vocabulary.** Long, complex sentences with multiple embedded clauses can be broken into shorter sentences. Archaic syntax can be modernised. But content-bearing vocabulary — especially loaded or evaluative words — should be retained and glossed rather than replaced.

5. **Provide both versions where possible.** For key passages, include the original text alongside the adapted version so students can see what was changed. This models transparency about textual modification — itself a historical thinking principle.

6. **Use a word bank, not inline definitions.** Difficult words should be defined in a separate word bank at the bottom of the source, not replaced or defined inline. Inline definitions interrupt the reading flow and remove the opportunity for students to encounter and wrestle with unfamiliar language.

7. **Mark all cuts and modifications.** Use [...] for omitted passages and (adapted) in the source note to signal that the text has been modified. Transparency about modification is non-negotiable.

8. **Do not interpret the source.** The word bank should define words, not explain what the author meant. "Barbarous: savage, uncivilised" is a definition. "Barbarous: Smith is showing his negative attitude toward the Powhatan" is an interpretation that pre-empts the student's close reading.

Produce the following:

1. **Adapted source:** The modified document with full source attribution, [...] for cuts, and (Adapted) in the source note. Include original and adapted versions of key passages side by side where this is instructive.

2. **Adaptation notes:** A transparent list of every modification, grouped by type:
   - **Cut:** What was removed and why (e.g., "Removed three sentences describing the geography of Werowocomoco — not relevant to the central question and adds length without analytical value")
   - **Simplified:** What was syntactically modified and how (e.g., "Split one 47-word sentence into two shorter sentences — original embedded clause structure exceeded target reading level")
   - **Retained:** What was deliberately kept despite being difficult, and why (e.g., "Retained 'barbarous' — essential for close reading comparison with 'kindly' in the 1608 account")

3. **Preserved features:** For each target skill, list the specific features preserved:
   - **For sourcing:** What source information is retained
   - **For close reading:** Which word choices, rhetorical features, or tone markers are preserved
   - **For contextualisation:** Which temporal or situational markers remain
   - **For corroboration:** Which features enable comparison with paired documents

4. **Word bank:** Definitions for difficult retained vocabulary. Definitions only — no interpretations.

5. **Analytical value check:** For each target skill, confirm that the adapted version still supports it. If any adaptation has compromised a skill, flag it explicitly and explain the trade-off.

Return your output in this exact format:

## Adapted Source

**Source:** [Full attribution with (Adapted) marker]

[Adapted text with [...] for cuts]

**Original version of key passage(s):**
[Side-by-side where instructive]

### Word Bank
[Vocabulary with definitions only]

## Adaptation Notes

**Cut:** [What was removed and why]
**Simplified:** [What was modified and how]
**Retained:** [What was kept despite difficulty, and why]

## Preserved Features

**For sourcing:** [What's preserved]
**For close reading:** [What's preserved]
**For contextualisation:** [What's preserved]
**For corroboration:** [What's preserved]

## Analytical Value Check

[Confirmation for each target skill, with any trade-offs flagged]

**Self-check before returning output:** Verify that (a) the source attribution is complete and unmodified, (b) the author's voice is preserved — the adapted version sounds like the original author, not a textbook, (c) analytically significant language is retained and glossed, not replaced, (d) all modifications are transparently documented, (e) the word bank defines without interpreting, and (f) the analytical value check honestly assesses whether each target skill can still be practised.
```

## Example Output

**Scenario:** *Original source: Smith's 1624 General History passage (full archaic text) / Student level: "Year 7, first time working with primary sources, average reading age 10–11" / Target skills: "Sourcing and close reading" / Central question: "Did Pocahontas rescue John Smith?" / Key passages: "'barbarous' and 'Pocahontas the King's dearest daughter, when no entreaty could prevail, got his head in her arms, and laid her own upon his to save him from death'"*

---

## Adapted Source

**Source:** John Smith (1624), *General History of Virginia, New England and the Summer Isles*, Vol. 2. (Adapted)

At last they brought Smith to Meronocomoco, where Powhatan, their Emperor, was waiting. At his entrance, all the people gave a great shout. [...] Having feasted him after their best barbarous manner they could, a long consultation was held. But the conclusion was, two great stones were brought before Powhatan. Then, as many as could laid hands on him, dragged him to them, and laid his head on the stones. Being ready with their clubs to beat out his brains, Pocahontas, the King's dearest daughter, when no entreaty could prevail, got his head in her arms, and laid her own upon his to save him from death. The Emperor was contented that Smith should live.

Two days after, Powhatan [...] came to Smith and told him they were now friends. Soon Smith should go to Jamestown, and send Powhatan two great guns and a grindstone. For this, Powhatan would forever esteem Smith as his son.

**Original version of key passage:**

| Original (1624) | Adapted |
|---|---|
| "having feasted him after their best barbarous manner they could, a long consultation was held, but the conclusion was, two great stones were brought before Powhatan: then, as many as could layd hands on him, dragged him to them, and thereon laid his head, and being ready with their clubs, to beate out his braines, Pocahontas the Kings dearest daughter, when no intreaty could prevaile, got his head in her armes, and laid her owne upon his to save him from death" | "Having feasted him after their best barbarous manner they could, a long consultation was held. But the conclusion was, two great stones were brought before Powhatan. Then, as many as could laid hands on him, dragged him to them, and laid his head on the stones. Being ready with their clubs to beat out his brains, Pocahontas, the King's dearest daughter, when no entreaty could prevail, got his head in her arms, and laid her own upon his to save him from death." |

### Word Bank

- **barbarous:** savage, uncivilised
- **consultation:** discussion, meeting to decide something
- **entreaty:** a serious request or plea
- **prevail:** succeed, work
- **esteem:** value, respect
- **contented:** satisfied, willing to agree

## Adaptation Notes

**Cut:** Removed the opening description of Powhatan's court ("proudly lying upon a bedstead a foot high upon ten or twelve mats") — adds atmospheric detail but is not relevant to the central question. Removed Smith's description of Powhatan "disguised in the most fearful manner he could" — secondary detail that adds length without analytical value for sourcing or close reading of the rescue passage.

**Simplified:** Modernised archaic spelling throughout (layd → laid, braines → brains, intreaty → entreaty, armes → arms, owne → own, prevaile → prevail). Broke the 73-word rescue sentence into four shorter sentences while preserving all content words. Changed "thereon laid his head" to "laid his head on the stones" for clarity.

**Retained:** "Barbarous" — essential for close reading comparison with "kindly" in the 1608 account. "The King's dearest daughter" — key phrase for close reading (why "dearest"? why "King" rather than "chief"?). "When no entreaty could prevail" — dramatic phrasing that reveals Smith's narrative construction. "Esteem him as his son" — important for the question of what the encounter meant (adoption ritual vs. genuine threat). Full source attribution including author, date, and publication title.

## Preserved Features

**For sourcing:** Full source note (John Smith, 1624, General History of Virginia). The 17-year gap between event (1607) and publication (1624) is visible from the source note and timeline context. Students can identify Smith as both author and subject of the story.

**For close reading:** "Barbarous" (loaded language revealing Smith's attitude); "the King's dearest daughter" (elevating language); "when no entreaty could prevail" (dramatic narrative construction); "beat out his brains" (violent imagery for dramatic effect); "esteem him as his son" (the adoption language that historians interpret differently).

**For contextualisation:** The date (1624) is preserved in the source note. The passage retains enough period detail (clubs, stones, emperor, grindstone) to locate it in early colonial Virginia.

**For corroboration:** The adapted version preserves the features that differ most from Smith's 1608 account — the threatening tone, the rescue, and the "barbarous" language — enabling direct comparison.

## Analytical Value Check

**Sourcing:** ✓ Fully supported. Source note is complete. Students can identify author, date, and the author's relationship to events.

**Close reading:** ✓ Fully supported. All analytically significant word choices are preserved. The sentence-breaking does not alter the vocabulary or tone — students can still analyse "barbarous," "dearest daughter," and the dramatic rescue language.

**Contextualisation:** ✓ Supported with caveat. The adapted version preserves the date and period markers, but the cuts reduce the atmospheric detail that might help students imagine the setting. Teachers may want to supplement with brief background information about Werowocomoco.

**Corroboration:** ✓ Fully supported. The key features for comparison with the 1608 account — contrasting language ("barbarous" vs. "kindly"), presence vs. absence of the rescue, tone shift — are all preserved.

---

## Known Limitations

1. **Every adaptation involves trade-offs.** Simplifying sentence structure may reduce the rhetorical force of the original. Cutting passages removes context that might be relevant to questions the teacher hasn't anticipated. The adaptation notes exist so teachers can assess these trade-offs — and reverse specific changes if they judge the original feature is worth the additional difficulty.

2. **The skill adapts text, not images or material objects.** Historical sources include photographs, maps, political cartoons, artefacts, and other non-textual materials that require different adaptation strategies (e.g., annotation, guided looking protocols, contextual captions). This skill is designed for textual primary sources.

3. **Adaptation is not a substitute for reading instruction.** Students who cannot decode at all need reading support before they can engage with even adapted primary sources. The skill assumes students can read at or near their age level and targets the gap between general reading ability and the specific demands of historical texts. For students reading significantly below age level, see text-complexity-analyser and scaffolded-task-modifier for additional support strategies.

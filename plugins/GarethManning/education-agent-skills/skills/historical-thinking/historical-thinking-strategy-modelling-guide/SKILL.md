---
# AGENT SKILLS STANDARD FIELDS (v2)
name: historical-thinking-strategy-modelling-guide
description: "Design a teacher think-aloud that models historical thinking strategies with a specific document. Use when planning explicit strategy instruction or when students follow a protocol without understanding the underlying reasoning."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS
skill_id: "historical-thinking/historical-thinking-strategy-modelling-guide"
skill_name: "Historical Thinking Strategy Modelling Guide"
domain: "historical-thinking"
version: "1.0"
contributor: "Sean Hu"
evidence_strength: "strong"
evidence_sources:
  - "Wineburg (2007) — Unnatural and essential: the nature of historical thinking"
  - "Wineburg (1991) — Historical problem solving: cognitive processes in the evaluation of documentary and pictorial evidence"
  - "Wineburg (1998) — Reading Abraham Lincoln: an expert/expert study in historical cognition"
  - "Reisman (2012) — Reading like a historian: a document-based history curriculum intervention in urban high schools"
  - "Gottlieb & Wineburg (2012) — Between Veritas and Communitas: epistemic switching in the reading of academic and sacred history"
  - "Rosenshine (2012) — Principles of instruction: research-based strategies that all teachers should know"
input_schema:
  required:
    - field: "document_description"
      type: "string"
      description: "The specific historical document the teacher will model with — including its source information (author, date, publication context) and a summary or key passage of its content"
    - field: "target_strategies"
      type: "string"
      description: "Which historical thinking strategies to model — one or more of: sourcing, close reading, contextualisation, corroboration. If corroboration, a second document must be described."
    - field: "student_level"
      type: "string"
      description: "Age/year group and current level of experience with historical thinking"
  optional:
    - field: "current_challenge"
      type: "string"
      description: "What students currently struggle with — allows the think-aloud to specifically target the gap between what students do and what expert readers do"
    - field: "second_document"
      type: "string"
      description: "A second document to compare with the first. REQUIRED if corroboration is listed in target_strategies — the modelling cannot proceed without it."
    - field: "lesson_context"
      type: "string"
      description: "Where in the lesson this modelling will occur — e.g. opening a new document set, transitioning from guided to independent practice, demonstrating a strategy students have not yet encountered"
    - field: "prior_instruction"
      type: "string"
      description: "What strategy instruction students have already received"
output_schema:
  type: "object"
  fields:
    - field: "think_aloud_script"
      type: "string"
      description: "A complete teacher think-aloud script that models the target strategies with the specified document — including pauses, self-questions, hypotheses, and the specification of ignorance"
    - field: "cognitive_moves_annotated"
      type: "array"
      description: "The think-aloud script annotated with labels identifying each cognitive move — so the teacher understands what they are modelling and can name it for students"
    - field: "common_pitfalls"
      type: "array"
      description: "Common mistakes teachers make when modelling historical thinking — e.g. narrating the answer rather than the thinking process, modelling too quickly, not pausing to show uncertainty"
    - field: "transition_to_practice"
      type: "object"
      description: "How to move from the modelled think-aloud to guided student practice — what to hand over, what to scaffold, what to watch for"
chains_well_with:
  - "sourcing-skill-builder"
  - "close-reading-skill-builder"
  - "contextualisation-skill-builder"
  - "corroboration-skill-builder"
  - "document-based-lesson-designer"
  - "historical-source-adapter"
  - "think-aloud-script-generator"
  - "explicit-instruction-sequence-builder"
teacher_time: "3 minutes"
tags: ["modelling", "think-aloud", "historical-thinking", "explicit-instruction", "worked-example", "strategy-instruction", "DIG"]
---

# Historical Thinking Strategy Modelling Guide

## What This Skill Does

Generates a teacher think-aloud script that models one or more historical thinking strategies (sourcing, close reading, contextualisation, corroboration) with a specific document. The output includes the complete script with pauses and self-talk, annotations identifying each cognitive move, common pitfalls to avoid, and guidance on transitioning from the modelled example to student practice.

The central insight from Wineburg's research is that expert historical reading is invisible. When a historian reads a document, the cognitive work — pausing at the source note, generating hypotheses from bibliographic information, noticing loaded language, connecting the document to its historical moment — happens internally. Students see the historian read and then produce an interpretation, but the process between reading and interpretation is a black box. The purpose of a think-aloud is to open that box: to externalise the internal reasoning so students can see, hear, and eventually replicate it.

This skill is distinct from the four individual skill builders (sourcing, close reading, contextualisation, corroboration), which design a complete instructional sequence. This skill generates only the modelling component — the "I DO" phase — but does so in greater depth and with greater specificity than any single skill builder can. It produces a document-specific script that a teacher can rehearse and deliver, with annotations explaining what each move demonstrates and why it matters.

Reisman (2012) found that explicit strategy instruction — modelling, guided practice, independent practice — was the pedagogical structure through which historical thinking skills were taught in the Reading Like a Historian curriculum. However, Reisman also found that teacher fidelity to modelling was low: most teachers scored below baseline on the fidelity rubric, and whole-class discussion (where modelling is most visible) was extremely rare. This skill exists to make modelling more accessible by providing a concrete, rehearsable script rather than leaving teachers to improvise expert-level historical reasoning on the spot.

## Evidence Foundation

Wineburg (2007) demonstrated what expert modelling reveals through the Harrison Proclamation example. A doctoral student's think-aloud showed a cascade of cognitive moves: reading the date, immediately activating contextual knowledge about the 1890s, connecting that context to the document's language, and arriving at a hypothesis about its political purpose — all in under a minute. This think-aloud made visible what Wineburg called the "specification of ignorance": the expert practice of using a document to articulate what one does not know and needs to find out, rather than rushing to judgement.

Wineburg (1991, 1998) established through think-aloud studies that historians engage in qualitatively different cognitive processes when reading documents. These processes — sourcing before reading, attending to language as evidence of perspective, connecting documents to their historical moment, comparing accounts across sources — are the target behaviours for modelling. The think-aloud methodology used to study experts became, in the Reading Like a Historian curriculum, the pedagogical method used to teach novices.

Gottlieb and Wineburg (2012) showed that the quality of expert reading is in the depth of reasoning, not the frequency of strategy use. A scientist and a historian might both note an author's name, but the historian mines that information for inferences about the text's likely stance. Modelling must therefore demonstrate not just the action (look at the source note) but the reasoning (what the source information tells you before you read a word).

Reisman (2012) operationalised explicit strategy instruction through a three-part structure: teacher models the strategy, students practise with guidance, students apply independently. The modelling phase is the foundation — without it, students learn what to do (check the source) but not how to think (use the source to generate hypotheses). Reisman's finding that teacher fidelity to the full lesson structure was low suggests that modelling is the component teachers find hardest to deliver, likely because it requires performing expert-level historical reasoning in real time.

Rosenshine (2012) identified modelling and think-alouds as one of ten research-based principles of effective instruction across domains. He argued that making cognitive processes visible is especially important for complex skills where the expert's thinking is not apparent from observing their behaviour. Historical thinking is precisely such a skill — the difference between a novice and expert reading the same document is entirely internal.

## Input Schema

The teacher must provide:
- **Document description:** The specific document to model with, including source information and key content. *e.g. "President Benjamin Harrison's 1892 proclamation declaring a national holiday for the 400th anniversary of Columbus's arrival. Source note: 'Benjamin Harrison, Presidential Proclamation, July 21, 1892, published in the New York Times.' Key passage: 'On the 12th day of October, 1892, let the people, so far as possible, cease from toil, and devote themselves to... the world-changing event which shall have been thus commemorated.'"*
- **Target strategies:** Which strategies to model. *e.g. "Sourcing and contextualisation" / "Close reading only" / "All four — sourcing, close reading, contextualisation, then corroboration with a second document"*
- **Student level:** *e.g. "Year 8, first encounter with think-aloud modelling of historical reading" / "Year 11, familiar with sourcing but need to see contextualisation modelled"*

Optional:
- **Current challenge:** What students struggle with — targets the think-aloud
- **Second document:** Required for corroboration modelling
- **Lesson context:** Where the modelling fits in the lesson
- **Prior instruction:** What students have already learned

## Prompt

```
You are an expert in historical thinking pedagogy and explicit strategy instruction, with deep knowledge of Wineburg's (1991, 1998, 2007) research on expert historical reading, Reisman's (2012) three-part explicit instruction model (I DO → WE DO → YOU DO), and Rosenshine's (2012) principles of instruction. You understand that the purpose of a think-aloud is to make visible the invisible cognitive processes of expert historical reading — showing students not just WHAT to do (check the source, read closely, contextualise, compare) but HOW to think while doing it.

Your task is to generate a teacher think-aloud script that models historical thinking with a specific document:

**Document description:** {{document_description}}
**Target strategies:** {{target_strategies}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available.

**Current challenge:** {{current_challenge}} — if provided, design the think-aloud to specifically target the gap between what students currently do and what the think-aloud demonstrates.
**Second document:** {{second_document}} — required if corroboration is a target strategy.
**Lesson context:** {{lesson_context}}
**Prior instruction:** {{prior_instruction}}

Generate the following:

1. **Think-aloud script:** A complete, rehearsable teacher script (300–500 words depending on how many strategies are targeted) that models the target strategies with the specified document. The script must:
   - Be written in first person as the teacher speaking aloud to the class
   - Include explicit pauses marked with [PAUSE] where the teacher stops to think visibly
   - Show uncertainty and hypothesis-generation, not just confident interpretation — expert readers don't know the answer immediately; they generate questions and possibilities
   - Demonstrate the "specification of ignorance" (Wineburg, 2007): using the document to articulate what the reader does NOT know and needs to find out
   - Be specific to this document — not a generic demonstration of "how historians read" but a concrete example of what THIS document reveals when read with disciplinary skill
   - If multiple strategies are targeted, show them in the natural order an expert would use them (typically: sourcing → contextualisation → close reading → corroboration), making the transitions between strategies visible

2. **Cognitive moves annotated:** The same script presented a second time with annotations in [brackets] labelling each cognitive move. For example: "Let me look at who wrote this [SOURCING: checking author before reading]. 1892 — what do I know about 1892? [CONTEXTUALISATION: activating period knowledge]." These annotations serve two purposes: they help the teacher understand what they are modelling, and they can be shared with students after the think-aloud to name the strategies explicitly.

3. **Common pitfalls:** 3–4 mistakes teachers commonly make when modelling historical thinking, with guidance on how to avoid them. Include:
   - Narrating the answer rather than the thinking process
   - Modelling too quickly without showing the pauses and uncertainty that characterise genuine expert reasoning
   - Performing confidence rather than demonstrating the productive discomfort of not knowing
   - Modelling strategies generically rather than showing what they reveal with this specific document

4. **Transition to practice:** How to move from the teacher's think-aloud to guided student practice. Specify:
   - What to hand over (which strategy, which document)
   - How to scaffold the transition (e.g., students try the same strategy on a new document with sentence starters; pairs practise while teacher circulates)
   - What to watch for (signs students are replicating the cognitive moves vs. just copying the surface behaviours)

Return your output in this exact format:

## Think-Aloud Modelling Plan

**Document:** [Brief description]
**Target strategies:** [List]
**Students:** [Level]

### Think-Aloud Script

[Complete script with [PAUSE] markers, written in first person as the teacher speaking aloud]

### Cognitive Moves Annotated

[Same script with [STRATEGY: description] annotations after each move]

### Common Pitfalls

[3–4 pitfalls with guidance]

### Transition to Practice

**Hand over:** [What students will now try]
**Scaffold:** [How to support the transition]
**Watch for:** [Signs of genuine vs. surface-level replication]

**Self-check before returning output:** Verify that (a) the script is specific to this document, not generic, (b) the script shows uncertainty and hypothesis-generation, not just confident analysis, (c) the annotations correctly label each cognitive move, (d) the pitfalls address the difference between narrating answers and modelling thinking, and (e) the transition to practice specifies what genuine replication of the modelled thinking looks like.
```

## Example Output

**Scenario:** *Document: "John Smith's 1624 General History passage describing his capture and rescue by Pocahontas. Source note: 'John Smith (1624), General History of Virginia, New England and the Summer Isles, Vol. 2, Chapel Hill: University of North Carolina Press, p. 151.' Key passage: 'having feasted him after their best barbarous manner they could, a long consultation was held, but the conclusion was, two great stones were brought before Powhatan: then, as many as could laid hands on him, dragged him to them, and thereon laid his head, and being ready with their clubs, to beat out his brains, Pocahontas the King's dearest daughter, when no entreaty could prevail, got his head in her arms, and laid her own upon his to save him from death.'" / Target strategies: "Sourcing and close reading" / Student level: "Year 8, first encounter with think-aloud modelling of historical reading"*

---

## Think-Aloud Modelling Plan

**Document:** Smith's 1624 General History — Pocahontas rescue passage
**Target strategies:** Sourcing and close reading
**Students:** Year 8, first encounter with modelled historical reading

### Think-Aloud Script

"Before I read this, I'm going to do what historians do — look at who wrote it and when. It says John Smith, 1624. [PAUSE] OK. John Smith is the person this story is about. He's writing about himself. That immediately makes me pay attention, because when someone tells a story where THEY are the hero, I want to think about why they're telling it that way.

1624. The event was supposed to have happened in 1607. That's a 17-year gap. [PAUSE] I'm trying to think — do I remember what happened 17 years ago? Not very well. So either Smith has an extraordinary memory, or he's reconstructing. And here's something else I know: Pocahontas went to England in 1616 and became very famous before she died in 1617. By 1624, she's a well-known figure. Is Smith attaching his name to her fame? I don't know yet. But I'm going to read with that question in mind.

Now let me read the passage. 'Having feasted him after their best barbarous manner they could.' [PAUSE] I'm stopping at 'barbarous.' That's a strong word. Smith could have said 'their traditional manner' or 'their customary manner.' He chose 'barbarous.' That tells me something about how he wants his readers to see the Powhatan people — as savage, uncivilised. Why? [PAUSE] Maybe because it makes the rescue more dramatic. You need danger to have a rescue.

'Pocahontas the King's dearest daughter, when no entreaty could prevail, got his head in her arms and laid her own upon his to save him from death.' [PAUSE] 'The King's dearest daughter.' That's significant. Not just 'a girl' or 'Powhatan's daughter' — 'the King's DEAREST daughter.' Smith is elevating Pocahontas. And by making her the one who saved him, he's also elevating himself — he's important enough that a princess risked her life for him.

So here's what I'm thinking after reading this: I don't know whether this happened. But I do know that Smith had reasons to tell this story in 1624 — reasons that have nothing to do with what actually happened in 1607. The question I want to investigate next is: did Smith mention this rescue in his FIRST account, written in 1608? If he didn't, that would be very interesting."

### Cognitive Moves Annotated

"Before I read this, I'm going to do what historians do — look at who wrote it and when. [SOURCING: examining author and date before reading content] It says John Smith, 1624. [PAUSE] OK. John Smith is the person this story is about. He's writing about himself. [SOURCING: identifying author's relationship to the events] That immediately makes me pay attention, because when someone tells a story where THEY are the hero, I want to think about why they're telling it that way. [SOURCING: reasoning about how author's position shapes the account]

1624. The event was supposed to have happened in 1607. That's a 17-year gap. [SOURCING: reasoning about temporal distance between event and account] [PAUSE] I'm trying to think — do I remember what happened 17 years ago? Not very well. [SOURCING: using personal experience to evaluate plausibility of detailed recall] So either Smith has an extraordinary memory, or he's reconstructing. And here's something else I know: Pocahontas went to England in 1616 and became very famous before she died in 1617. [CONTEXTUALISATION: activating period knowledge] By 1624, she's a well-known figure. Is Smith attaching his name to her fame? [SOURCING + CONTEXTUALISATION: generating hypothesis about motive from context] I don't know yet. But I'm going to read with that question in mind. [SPECIFICATION OF IGNORANCE: holding the hypothesis as a question, not a conclusion]

Now let me read the passage. 'Having feasted him after their best barbarous manner they could.' [PAUSE] I'm stopping at 'barbarous.' [CLOSE READING: attending to specific word choice] That's a strong word. Smith could have said 'their traditional manner' or 'their customary manner.' He chose 'barbarous.' [CLOSE READING: considering alternative word choices to reveal the significance of the one used] That tells me something about how he wants his readers to see the Powhatan people — as savage, uncivilised. Why? [CLOSE READING: connecting word choice to author's purpose] [PAUSE] Maybe because it makes the rescue more dramatic. You need danger to have a rescue. [CLOSE READING: reasoning about rhetorical strategy]

'Pocahontas the King's dearest daughter, when no entreaty could prevail, got his head in her arms and laid her own upon his to save him from death.' [PAUSE] 'The King's dearest daughter.' [CLOSE READING: attending to specific phrase] That's significant. Not just 'a girl' or 'Powhatan's daughter' — 'the King's DEAREST daughter.' Smith is elevating Pocahontas. [CLOSE READING: analysing how language choices construct the narrative] And by making her the one who saved him, he's also elevating himself. [CLOSE READING + SOURCING: connecting language to author's self-interest]

So here's what I'm thinking after reading this: I don't know whether this happened. [SPECIFICATION OF IGNORANCE: maintaining uncertainty rather than rushing to a verdict] But I do know that Smith had reasons to tell this story in 1624 — reasons that have nothing to do with what actually happened in 1607. The question I want to investigate next is: did Smith mention this rescue in his FIRST account, written in 1608? If he didn't, that would be very interesting. [SPECIFICATION OF IGNORANCE + BRIDGE TO CORROBORATION: generating the next question]"

### Common Pitfalls

**1. Narrating the answer instead of modelling the thinking**
*The mistake:* The teacher says "Smith wrote this in 1624, which was 17 years after the event, and by that time Pocahontas was famous, so he was probably trying to capitalise on her fame." This delivers the interpretation without showing how the teacher arrived at it.
*The fix:* Slow down. Show the thinking that generates the interpretation. Pause at "1624," visibly calculate the gap, wonder aloud whether anyone remembers things from 17 years ago, recall the Pocahontas-in-England detail, and THEN arrive at the hypothesis. The process is the lesson, not the conclusion.

**2. Modelling confidence rather than productive uncertainty**
*The mistake:* The teacher presents each move as if the answer is obvious: "Of course Smith chose 'barbarous' to make the rescue seem more dramatic." This models certainty, which is the opposite of expert historical reasoning.
*The fix:* Use hedging language deliberately: "Maybe... I wonder... That could mean... I'm not sure yet, but..." Expert readers generate hypotheses, not conclusions. Students need to see that not knowing is a productive state, not a failure.

**3. Rushing through the source note**
*The mistake:* The teacher glances at the source note and says "OK, it's by John Smith in 1624" and immediately begins reading the content. The sourcing move is performed but not demonstrated — students see that you checked the source but not what checking the source DOES for your reading.
*The fix:* Spend at least 60 seconds on the source note alone. Generate multiple observations and questions from it before touching the text. The disproportionate time spent on the source note, relative to its small amount of text, is itself the lesson: this tiny piece of information changes everything about how you read what follows.

**4. Modelling all strategies at the same level of detail**
*The mistake:* Trying to demonstrate sourcing, close reading, contextualisation, and corroboration in a single think-aloud, resulting in a 15-minute performance where each strategy gets superficial treatment.
*The fix:* Focus deeply on one or two strategies per modelling session. It is better for students to see sourcing demonstrated thoroughly with one document than to see all four strategies demonstrated superficially.

### Transition to Practice

**Hand over:** Students receive Smith's 1608 True Relation — the earlier account of the same event. Their task is to do with this document what the teacher just demonstrated: examine the source note FIRST, generate questions from it, and THEN read the text paying attention to specific word choices.

**Scaffold:** Provide sentence starters that mirror the teacher's think-aloud: "This was written by ___ in ___. That makes me wonder..." / "I notice the word ___. The author could have said ___ instead, which suggests..." Students work in pairs, talking through their reading aloud to each other. The teacher circulates and listens for the cognitive moves, not just the correct answers.

**Watch for:** The difference between students who replicate the moves and students who replicate the words. A student who says "I notice the word 'kindly' — the author could have said something else" is copying the surface structure. A student who says "Smith says 'kindly' here, but in the 1624 version he says 'barbarous' for the same meeting — so one of these descriptions is being shaped by something other than what actually happened" is replicating the cognitive move. The second student has understood that language is evidence of perspective; the first is performing a strategy without understanding its purpose.

---

## Known Limitations

1. **A think-aloud script is a starting point, not a finished performance.** Teachers must rehearse the script, internalise its reasoning, and adapt it to their own voice. Reading a script aloud to students is not modelling — it is reading. The cognitive moves must appear genuine, which requires the teacher to understand WHY they are pausing, questioning, and hypothesising, not just THAT they should.

2. **This skill generates the modelling component only.** It does not design the complete lesson structure (see document-based-lesson-designer) or the progression of skill development over time (see the individual skill builders). Modelling is the "I DO" phase; the guided and independent practice that follow require separate design, though the transition-to-practice section provides initial guidance.

3. **Modelling historical thinking requires the teacher to possess the historical knowledge that expert reading draws on.** The contextualisation demonstrated in the example (connecting the 1624 date to Pocahontas's 1616 England visit) requires the teacher to know that fact. If the teacher lacks the relevant background knowledge, the think-aloud will be thin. Teachers should prepare by reading the historiographical context for their documents before modelling — this preparation is part of the work, not a limitation of the skill.

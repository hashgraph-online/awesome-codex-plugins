---
# AGENT SKILLS STANDARD FIELDS (v2)
name: document-based-lesson-designer
description: "Design a complete document-based history lesson using the Reading Like a Historian four-part structure. Use when planning a primary source inquiry lesson or converting a textbook lesson into document-based investigation."
disable-model-invocation: false
user-invocable: true
effort: high

# EXISTING FIELDS
skill_id: "historical-thinking/document-based-lesson-designer"
skill_name: "Document-Based Lesson Designer"
domain: "historical-thinking"
version: "1.0"
contributor: "Sean Hu"
evidence_strength: "strong"
evidence_sources:
  - "Reisman (2012) — Reading like a historian: a document-based history curriculum intervention in urban high schools"
  - "Wineburg, Martin & Monte-Sano (2011) — Reading like a historian: teaching literacy in middle and high school history classrooms"
  - "Wineburg & Martin (2004) — Reading and rewriting history"
  - "Wineburg (2007) — Unnatural and essential: the nature of historical thinking"
  - "Wineburg & Reisman (2015) — Disciplinary literacy in history: a toolkit for digital citizenship"
  - "Wineburg (2016) — Why historical thinking is not about history"
input_schema:
  required:
    - field: "central_question"
      type: "string"
      description: "The central historical question driving the lesson — the inquiry students will investigate using primary sources"
    - field: "document_set"
      type: "string"
      description: "The sources students will work with — number, types, key content, and the tensions built into the set"
    - field: "student_level"
      type: "string"
      description: "Age/year group, reading level, and experience with document-based inquiry"
    - field: "lesson_duration"
      type: "string"
      description: "Available time — e.g. '1 hour', '2 × 50-minute periods', '3 hours across a week'"
  optional:
    - field: "target_skills"
      type: "string"
      description: "Which historical thinking skills to foreground — if not specified, the lesson will integrate all four where the document set supports them"
    - field: "background_knowledge"
      type: "string"
      description: "What background knowledge students already have and what they will need — determines how much time the lesson devotes to the background phase"
    - field: "learning_objectives"
      type: "string"
      description: "What students should know, understand, or be able to do by the end of the lesson"
    - field: "writing_task"
      type: "string"
      description: "Whether the lesson should culminate in a written argument — e.g. an evidence-based essay, a short paragraph, or no formal writing"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: relevant curriculum standards or historical thinking framework in use"
    - field: "prior_instruction"
      type: "string"
      description: "What historical thinking instruction students have received — determines whether strategy instruction is introductory or reinforcing"
output_schema:
  type: "object"
  fields:
    - field: "lesson_plan"
      type: "object"
      description: "A complete lesson plan following the four-part RLH activity structure — background knowledge, central question introduction, document investigation rounds with strategy instruction, and whole-class discussion — with timing, teacher actions, and student actions for each phase"
    - field: "strategy_instruction_plan"
      type: "object"
      description: "Which historical thinking strategies will be explicitly taught or reinforced in this lesson, at which points, and with which documents"
    - field: "discussion_plan"
      type: "object"
      description: "How the whole-class discussion will be structured — the questions that drive it, how student responses are connected to evidence, and how the discussion builds toward the lesson's argumentative endpoint"
    - field: "differentiation_notes"
      type: "object"
      description: "How the lesson accommodates different reading levels and prior knowledge — including which documents to adapt, which scaffolds to provide, and how to support struggling readers without reducing the analytical demand"
    - field: "assessment_opportunities"
      type: "array"
      description: "Points in the lesson where student understanding of historical thinking skills can be observed or assessed — formatively, not summatively"
chains_well_with:
  - "central-historical-question-evaluator"
  - "historical-document-set-curator"
  - "historical-source-adapter"
  - "historical-thinking-strategy-modelling-guide"
  - "sourcing-skill-builder"
  - "close-reading-skill-builder"
  - "contextualisation-skill-builder"
  - "corroboration-skill-builder"
  - "historical-thinking-assessment-designer"
  - "backwards-design-unit-planner"
  - "discussion-protocol-selector"
teacher_time: "5 minutes"
tags: ["lesson-design", "document-based-lessons", "historical-thinking", "primary-sources", "disciplinary-literacy", "activity-structure", "RLH", "DIG"]
---

# Document-Based Lesson Designer

## What This Skill Does

Designs a complete document-based history lesson following the four-part activity structure from the Reading Like a Historian curriculum: (1) background knowledge, (2) central historical question, (3) primary source investigation with explicit strategy instruction, and (4) whole-class discussion. The output is a lesson plan with timing, teacher actions, student actions, strategy instruction points, a discussion plan, differentiation notes, and formative assessment opportunities.

This skill is the integrator of the historical thinking domain. It takes the outputs of the other skills — a central question (evaluated by central-historical-question-evaluator), a document set (curated by historical-document-set-curator), adapted sources (from historical-source-adapter), and strategy instruction plans (from the four skill builders and strategy-modelling-guide) — and assembles them into a coherent lesson architecture. It can also work from scratch when a teacher provides the central question and documents directly.

The four-part activity structure is not arbitrary. Reisman (2012) demonstrated its effectiveness in a six-month intervention with 236 students across five urban high schools. Treatment students who experienced this lesson format outperformed controls on historical thinking, factual knowledge, reading comprehension, and transfer of historical thinking to contemporary topics. The structure works because each phase serves a specific cognitive function: background knowledge activates the context students need for contextualisation; the central question provides the analytical focus; the document rounds scaffold progressive complexity; and whole-class discussion makes reasoning visible and social.

However, Reisman also found that teacher fidelity to the full structure was low — most teachers scored below baseline on the fidelity rubric, and whole-class discussion was extremely rare. The most common failure was omitting discussion, which may explain the null results for contextualisation and corroboration (both of which benefit from dialogic instruction). This skill designs the discussion phase explicitly and provides the questions and protocols teachers need to facilitate it, because discussion is both the most important and the most frequently skipped component of the lesson.

## Evidence Foundation

Reisman (2012) developed the Document-Based Lesson as a new "activity structure" consisting of four phases. Treatment teachers used this structure for 42–72% of instructional time (M = 58.3%), implementing 36–50 document-based lessons over six months. The intervention produced significant effects across all four outcome measures: historical thinking (ηp² = .09), transfer (ηp² = .08), factual knowledge (ηp² = .03), and reading comprehension (ηp² = .05). No school × treatment interaction was found, suggesting the structure worked across widely varying school contexts.

The four-part structure was designed to address specific pedagogical problems. The background knowledge phase ensures students have the contextual knowledge needed for contextualisation — without it, students cannot connect documents to their historical moment (Wineburg, 2007). The central question phase provides analytical focus — without a driving question, source analysis becomes a skills exercise rather than an investigation (Wineburg, Martin & Monte-Sano, 2011). The document investigation phase with explicit strategy instruction makes historical thinking skills visible and practicable — without modelling, students do not develop sourcing, close reading, contextualisation, or corroboration (Wineburg, 1991). The whole-class discussion phase makes reasoning social and accountable — without discussion, the comparative and inferential reasoning that corroboration and contextualisation require remains internal and undeveloped (Reisman, 2012).

Wineburg, Martin, and Monte-Sano (2011) provided eight complete lesson exemplars following this structure. Analysis reveals consistent design principles: lessons begin by activating what students already know (often starting with the familiar — Disney's Pocahontas, for example — then complicating it); documents are introduced in rounds of increasing complexity (primary sources first, then historians' interpretations); and each round is followed by discussion that connects back to the central question.

Wineburg and Martin (2004) demonstrated that the capstone of a document-based lesson is argumentative writing: students must construct an evidence-based response to the central question, using specific evidence from the documents. Reading and writing are paired activities — reading sources without writing arguments is incomplete because writing forces students to commit to a position and marshal evidence for it.

Reisman's (2012) finding that treatment students outperformed controls on factual knowledge despite spending LESS time on conventional content instruction is important for the lesson design. Document-based lessons provide "meaningful activities and schematic frameworks for students to organize and retain otherwise disparate facts" — students remember facts better when they encounter them in the context of an investigation than when they memorise them from a textbook.

## Input Schema

The teacher must provide:
- **Central question:** *e.g. "Did Pocahontas rescue John Smith?" / "Who was most to blame for World War I?" / "Was Rosa Parks's arrest spontaneous or planned?"*
- **Document set:** *e.g. "4 documents: Smith's 1608 and 1624 accounts (adapted), Adams's critique, Lemay's defence" / "3 documents: Treaty of Versailles excerpt, political cartoon, soldier's letter" / "5 documents: Parks's autobiography excerpt, newspaper account from 1955, NAACP internal memo, bus boycott flyer, interview with Jo Ann Robinson"*
- **Student level:** *e.g. "Year 8, third document-based lesson this term" / "Year 11 IB History, experienced" / "Year 7, first-ever document-based lesson"*
- **Lesson duration:** *e.g. "1 hour" / "2 × 50 minutes" / "3 hours across the week"*

Optional:
- **Target skills:** Which skills to foreground
- **Background knowledge:** What students already know and need to know
- **Learning objectives:** What students should achieve
- **Writing task:** Whether the lesson culminates in writing
- **Curriculum framework, prior instruction** — for alignment and progression

## Prompt

```
You are an expert in designing document-based history lessons, with deep knowledge of the Reading Like a Historian four-part activity structure (Reisman, 2012; Wineburg, Martin & Monte-Sano, 2011), the role of explicit strategy instruction in developing historical thinking skills (Wineburg, 1991, 2007), and the finding that whole-class discussion is both the most important and the most frequently omitted component of the lesson structure (Reisman, 2012).

Your task is to design a complete document-based lesson:

**Central question:** {{central_question}}
**Document set:** {{document_set}}
**Student level:** {{student_level}}
**Lesson duration:** {{lesson_duration}}

The following optional context may or may not be provided. Use whatever is available.

**Target skills:** {{target_skills}} — if not provided, integrate all four skills where the document set supports them, but foreground the 1–2 skills most naturally demanded by the document set.
**Background knowledge:** {{background_knowledge}} — if provided, design the background phase accordingly. If students already have the knowledge, the phase can be brief (5 minutes). If they lack critical context, the phase must be more substantial.
**Learning objectives:** {{learning_objectives}} — if provided, align the lesson to these objectives and ensure assessment opportunities target them.
**Writing task:** {{writing_task}} — if not provided, include a short written response (1 paragraph minimum) as the default culminating activity, following Wineburg and Martin's (2004) argument that reading and writing are paired activities.
**Curriculum framework:** {{curriculum_framework}}
**Prior instruction:** {{prior_instruction}} — if students are new to document-based inquiry, include more explicit strategy instruction. If experienced, reduce scaffolding and increase independence.

Design the following:

1. **Lesson plan:** A complete plan following the four-part structure, with timing, teacher actions, and student actions for each phase:

   **Phase 1 — Background knowledge** (typically 5–15 minutes):
   How the teacher activates or provides the contextual knowledge students need. This might include a brief lecture, a timeline, a short video clip, or a review of prior learning. The background phase should be efficient — its purpose is to equip students for the investigation, not to deliver all the content.

   **Phase 2 — Central question introduction** (typically 3–5 minutes):
   How the teacher introduces the question, why it matters, and what students will do to investigate it. The question should be posted visibly and returned to throughout the lesson.

   **Phase 3 — Document investigation rounds** (the bulk of the lesson):
   The document rounds with explicit strategy instruction. For each round:
   - Which documents students read
   - Which historical thinking strategy is modelled or practised
   - What guiding questions or tools students use
   - How long each round takes
   - What whole-class check-in happens between rounds (brief discussion connecting findings back to the central question)

   Design the rounds to build progressively: Round 1 introduces the core evidence and models the primary strategy; Round 2 introduces complication or contradiction; Round 3 (if time allows) adds further complexity. Each round should include a brief whole-class discussion connecting findings to the central question.

   **Phase 4 — Whole-class discussion and/or writing** (typically 10–20 minutes):
   How the teacher structures the culminating discussion. Include:
   - 2–3 discussion questions that build from factual to interpretive
   - How the teacher connects student responses to evidence from the documents
   - How the discussion addresses the central question without imposing a single correct answer
   - If a writing task is included: the prompt, the evidence requirement, and how long students have

2. **Strategy instruction plan:** Which historical thinking strategies are explicitly taught or reinforced at which points in the lesson:
   - Which strategy is foregrounded in each round
   - Whether the instruction is introductory (modelling from scratch) or reinforcing (prompting students to apply a strategy they've practised before)
   - Where the teacher think-aloud occurs (if applicable)

3. **Discussion plan:** The specific questions and protocols for the whole-class discussion phase. Reisman (2012) found that discussion was extremely rare in treatment classrooms — this section exists to make discussion concrete and facilitatable rather than abstract and skippable. Include:
   - Opening question (connected to the central question)
   - Follow-up question (pushing toward evidence and reasoning)
   - Closing question (synthesising — what do the documents tell us together?)
   - Teacher moves for common situations: what to do when students give opinions without evidence, what to do when the discussion stalls, what to do when students want "the right answer"

4. **Differentiation notes:** How the lesson accommodates different levels:
   - Which documents might need adaptation for struggling readers (see historical-source-adapter)
   - Which scaffolds to provide (sentence starters, graphic organisers, paired reading)
   - How to extend the lesson for advanced students (additional documents, more complex writing task)
   - Important: differentiation should adjust the SUPPORT, not the DEMAND. All students should engage with the same central question and the same analytical challenge.

5. **Assessment opportunities:** 2–3 specific points in the lesson where the teacher can observe whether students are developing historical thinking skills. For each opportunity:
   - When it occurs
   - What to look for (specific observable student behaviour)
   - What it tells you (which skill is being demonstrated or not)
   - How to respond (if the skill is absent, what to do)

Return your output in this exact format:

## Document-Based Lesson Plan

**Central question:** [Question]
**Students:** [Level]
**Duration:** [Time]
**Documents:** [Brief summary of the set]

### Phase 1: Background Knowledge ([time])

**Teacher does:** [Actions]
**Students do:** [Actions]
**Purpose:** [What this phase equips students with]

### Phase 2: Central Question ([time])

**Teacher does:** [Actions]
**Students do:** [Actions]

### Phase 3: Document Investigation

**Round 1 ([time]):**
**Documents:** [Which ones]
**Strategy focus:** [Which skill]
**Teacher does:** [Actions, including any think-aloud]
**Students do:** [Actions]
**Check-in:** [Brief whole-class connection to central question]

**Round 2 ([time]):**
[Same format]

**Round 3 ([time], if applicable):**
[Same format]

### Phase 4: Discussion and Writing ([time])

**Discussion questions:**
[2–3 questions building from factual to interpretive]

**Teacher moves:**
[Guidance for common situations]

**Writing task (if applicable):**
[Prompt, evidence requirement, time]

### Strategy Instruction Plan

[Which strategies, when, introductory or reinforcing]

### Discussion Plan

[Specific questions and protocols]

### Differentiation Notes

[Support adjustments — not demand reductions]

### Assessment Opportunities

[2–3 specific observation points with indicators and responses]

**Self-check before returning output:** Verify that (a) all four phases are present and timed to fit the lesson duration, (b) the document rounds build progressively in complexity, (c) the discussion phase has specific questions, not just "discuss the central question," (d) strategy instruction is embedded in the document rounds rather than delivered as a standalone mini-lesson disconnected from the sources, (e) differentiation adjusts support without reducing demand, and (f) the lesson returns to the central question repeatedly — it is the thread connecting all phases.
```

## Example Output

**Scenario:** *Central question: "Did Pocahontas rescue John Smith?" / Document set: "4 documents: Smith 1608, Smith 1624, Adams 1867, Lemay 1991 (all adapted)" / Student level: "Year 8, third document-based lesson — familiar with sourcing, still developing close reading" / Lesson duration: "2 × 50-minute periods" / Target skills: "Sourcing and close reading (primary), corroboration (secondary)" / Background knowledge: "Students have studied early English colonisation; they know who Pocahontas and John Smith are, mostly from popular culture" / Writing task: "Short evidence-based paragraph answering the central question"*

---

## Document-Based Lesson Plan

**Central question:** Did Pocahontas rescue John Smith?
**Students:** Year 8, third document-based lesson
**Duration:** 2 × 50-minute periods (100 minutes total)
**Documents:** Smith 1608 (adapted), Smith 1624 (adapted), Adams 1867 (adapted summary), Lemay 1991 (adapted summary)

### Phase 1: Background Knowledge (10 minutes — Period 1)

**Teacher does:** Shows a 2-minute clip from Disney's Pocahontas (the rescue scene). Asks: "What do you already know about Pocahontas and John Smith? Where did you learn it?" Records responses on the board. Provides a brief timeline (Tool 1.1 from RLH curriculum) covering 1607–1624.
**Students do:** Share prior knowledge. Note the timeline dates. Several will cite Disney; this is the intended starting point.
**Purpose:** Activates prior knowledge (mostly from popular culture) that the lesson will then complicate. The Disney version is not dismissed but positioned as one account among several — a narrative to test against evidence.

### Phase 2: Central Question (3 minutes — Period 1)

**Teacher does:** Posts the question visibly: "Did Pocahontas rescue John Smith?" Says: "Historians have been arguing about this for 150 years. Today you're going to examine the same evidence they used and make your own argument. By the end of tomorrow's lesson, you'll write a paragraph answering this question using evidence from the documents."
**Students do:** Copy the question. Note that their job is to investigate, not to guess.

### Phase 3: Document Investigation

**Round 1 (20 minutes — Period 1):**
**Documents:** Smith 1608 (True Relation) and Smith 1624 (General History)
**Strategy focus:** Sourcing (primary) and close reading (secondary)
**Teacher does:** Models sourcing with the 1624 document using a think-aloud (see strategy-modelling-guide): examines author, date, publication context, and generates hypotheses before reading. Then distributes both documents. Pairs complete Tool 1.2 (Comparing Smith's Accounts).
**Students do:** In pairs, read both accounts. Identify differences in facts and tone. Complete the comparison worksheet. Underline three words in each account that reveal Smith's attitude.
**Check-in (5 minutes):** Teacher asks: "What did you notice? Do these two accounts agree?" Collects 2–3 observations. Asks: "Why would the same person tell the same story differently?" Does NOT resolve the question — leaves it open.

**Round 2 (25 minutes — Period 2):**
**Documents:** Adams 1867 and Lemay 1991
**Strategy focus:** Corroboration — comparing how two historians use the same primary evidence
**Teacher does:** Briefly introduces the historians: "Adams wrote in 1867 that Smith made the story up. Lemay wrote in 1991 that Smith was telling the truth but misunderstood what happened. They examined the SAME evidence you just looked at. Let's see what they argue." Distributes both summaries with Tool 1.3 (Comparing Historians and Smith).
**Students do:** In pairs, read both historians. Complete the comparison tool: what does each historian believe happened, and what evidence do they use? Identify one point where Adams and Lemay directly disagree.
**Check-in (5 minutes):** Teacher asks: "Adams and Lemay read the same documents you did. How did they reach different conclusions?" Pushes toward the idea that evidence must be interpreted, and interpretation depends on the questions you ask.

### Phase 4: Discussion and Writing (15 minutes — Period 2)

**Discussion questions:**
1. "Based on ALL the sources, what do you think probably happened? Did Pocahontas rescue John Smith?" (Opening — invites positions)
2. "What is your strongest piece of evidence? How does it support your position?" (Follow-up — demands evidence)
3. "Can we know FOR CERTAIN what happened? Why or why not? What does that tell us about how history works?" (Closing — synthesises the epistemological lesson)

**Teacher moves:**
- If a student says "I think..." without evidence: "What document supports that? Can you point to a specific part?"
- If the discussion stalls: "Let's go back to Round 1. Smith described the same meeting as 'kindly' in 1608 and 'barbarous' in 1624. What does that tell us?"
- If students want the right answer: "Historians have been debating this for 150 years and they still disagree. Your job isn't to find the right answer — it's to make the best argument you can with the evidence."

**Writing task (10 minutes):**
"Did Pocahontas rescue John Smith? Write one paragraph answering this question. You must include evidence from at least two documents. You must explain WHY your evidence supports your answer."

### Strategy Instruction Plan

**Sourcing:** Reinforced (students' third lesson). Teacher models with one document (think-aloud on Smith 1624), then students source Smith 1608 independently. By Round 2, students should be sourcing the historians' interpretations without prompting.

**Close reading:** Developing. Embedded in Round 1 through the word-underlining task — students identify words that reveal Smith's attitude in each account. Not formally modelled in this lesson; teacher draws attention to key language choices during the Round 1 check-in.

**Corroboration:** Introduced. Round 2 is the first structured comparison of historians' interpretations. The comparison tool scaffolds the move. The Phase 4 discussion makes corroboration social — students hear different positions supported by different evidence, which IS corroboration in practice.

**Contextualisation:** Not foregrounded but present. Background knowledge phase provides the timeline context. Sourcing the 1624 document naturally raises contextualisation ("Pocahontas had become famous by then"). Not explicitly taught as a separate strategy in this lesson.

### Discussion Plan

The Phase 4 discussion is the most important and most easily skipped part of the lesson. It must happen.

**Opening:** "So — did she rescue him? Hands up: who thinks yes? Who thinks no? Who's not sure?" (Quick poll to surface the range of positions. The "not sure" option is important — it validates uncertainty.)

**Follow-up:** Call on 2–3 students from different positions. For each: "What's your strongest piece of evidence?" Then: "Does anyone have evidence that contradicts what [student] just said?" This models corroboration as a social practice — students are comparing evidence in real time.

**Closing:** "We've heard different arguments supported by different evidence. Can we ever know FOR CERTAIN whether the rescue happened?" Expect some students to say no. Follow up: "If we can't know for certain, does that mean studying it is pointless? What did we LEARN by investigating this question, even without a definitive answer?" Guide toward: we learned to read sources critically, to ask who wrote something and why, to compare accounts — skills that matter beyond this one historical question.

### Differentiation Notes

**For struggling readers:** Use adapted versions of Smith's accounts (see historical-source-adapter). Pair struggling readers with stronger readers for the document analysis. Provide sentence starters for the writing task: "Based on the evidence from [document], I believe that... because..."

**For EAL students:** Provide the word bank from the adapted sources. Allow use of first language for paired discussion before writing in English. The comparison tools (worksheets) provide visual structure that supports comprehension.

**For advanced students:** After completing the main writing task, provide Lewis's and Barbour's interpretations (Sources 1.5 and 1.6 from the RLH curriculum) as extension documents. Challenge: "Does this new evidence change your argument? How?"

**Important:** All students investigate the same question with the same core documents. Differentiation adjusts the support (adapted sources, sentence starters, paired reading), not the analytical demand. A struggling reader is still asked "Did Pocahontas rescue John Smith?" — they are not given a simpler question.

### Assessment Opportunities

**1. Round 1 check-in — sourcing habit**
*When:* After pairs complete the comparison of Smith's two accounts.
*What to look for:* Did pairs examine the source notes before reading? Can they identify the 16-year gap and explain why it matters?
*What it tells you:* Whether sourcing is becoming habitual (this is their third document-based lesson).
*If absent:* Prompt: "What's the first thing we do before reading a document? What does the source note tell you?"

**2. Round 2 — corroboration**
*When:* During paired work on Adams and Lemay.
*What to look for:* Do students identify a specific point of disagreement between the two historians? Do they reason about WHY they disagree, or just note that they do?
*What it tells you:* Whether students are moving from "noting disagreement" to "reasoning about disagreement."
*If absent:* Ask: "Adams says Smith made it up. Lemay says it happened. They read the SAME evidence. How is that possible?"

**3. Writing task — evidence use**
*When:* During the paragraph writing.
*What to look for:* Does the student cite specific evidence from at least two documents? Does the evidence actually support their claim, or is it tangentially related?
*What it tells you:* Whether students can construct an evidence-based argument — the culminating skill that integrates sourcing, close reading, and corroboration.
*If absent:* Before students write, model one sentence: "For example, I might write: 'Smith's 1608 account describes Powhatan as kind and welcoming, but his 1624 account describes the same meeting as barbarous and violent. This contradiction suggests that Smith's later account may have been influenced by Pocahontas's fame in England.' Notice how I used evidence from two documents and explained what it means."

---

## Known Limitations

1. **This skill designs the lesson but cannot ensure implementation fidelity.** Reisman (2012) found that even with training and observation, teachers frequently omitted or abbreviated the discussion phase. The skill provides detailed discussion questions and protocols, but whether the teacher delivers them depends on classroom conditions, time pressure, and the teacher's comfort with open-ended discussion. The discussion plan is deliberately specific to make it as facilitatable as possible.

2. **The lesson assumes a document set has already been curated and sources have been adapted.** If the teacher provides raw, unadapted sources, the lesson plan may overestimate what students can accomplish. Teachers should use historical-source-adapter to prepare documents for their specific student level before designing the lesson.

3. **The four-part structure is a design framework, not a rigid template.** Some lessons may require a longer background phase (if students lack critical context), a shorter discussion phase (if time is limited), or additional document rounds (if the document set is rich). The skill designs within the framework but the teacher should adjust based on their professional judgement and knowledge of their students.

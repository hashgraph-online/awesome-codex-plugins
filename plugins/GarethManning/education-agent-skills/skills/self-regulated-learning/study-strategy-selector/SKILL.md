---
# AGENT SKILLS STANDARD FIELDS (v2)
name: study-strategy-selector
description: "Select evidence-based study strategies matched to material type, learning goal, and student habits. Use when advising students on revision techniques, homework, or independent study approaches."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "self-regulated-learning/study-strategy-selector"
skill_name: "Study Strategy Selector & Guide"
domain: "self-regulated-learning"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Dunlosky et al. (2013) — Improving students' learning with effective learning techniques: promising directions from cognitive and educational psychology"
  - "Roediger & Pyc (2012) — Inexpensive techniques to improve education: applying cognitive psychology to enhance educational practice"
  - "Kornell & Bjork (2007) — The promise and perils of self-regulated study"
  - "Hartwig & Dunlosky (2012) — Study strategies of college students: are self-testing and scheduling related to achievement?"
  - "Miyatsu et al. (2018) — Five popular study strategies: their pitfalls and optimal implementations"
input_schema:
  required:
    - field: "learning_task"
      type: "string"
      description: "The specific study task or learning goal"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current study habits"
    - field: "material_type"
      type: "string"
      description: "Type of material: factual/conceptual/procedural/mixed"
  optional:
    - field: "time_available"
      type: "string"
      description: "How much study time the student has"
    - field: "assessment_type"
      type: "string"
      description: "What they're studying for: exam, essay, presentation, practical"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: current study habits, academic performance data"
    - field: "subject_area"
      type: "string"
      description: "Subject context for domain-specific strategy adaptations"
output_schema:
  type: "object"
  fields:
    - field: "recommended_strategies"
      type: "array"
      description: "Ranked list of strategies with evidence rating, implementation guide, and time allocation"
    - field: "strategies_to_avoid"
      type: "array"
      description: "Common but ineffective strategies students should replace"
    - field: "study_plan"
      type: "string"
      description: "A concrete study plan applying the recommended strategies to this specific task"
    - field: "student_guide"
      type: "string"
      description: "Copy-pasteable student-facing strategy guide"
chains_well_with:
  - "retrieval-practice-generator"
  - "spaced-practice-scheduler"
  - "metacognitive-prompt-library"
  - "goal-setting-protocol-designer"
teacher_time: "3 minutes"
tags: ["study-skills", "learning-strategies", "revision", "self-regulation", "metacognition"]
---

# Study Strategy Selector & Guide

## What This Skill Does

Analyses a specific learning task and recommends the most evidence-supported study strategies, with an explicit implementation guide for each. Crucially, the skill also identifies ineffective strategies the student is likely using (highlighting, re-reading, copying notes) and provides specific replacement strategies with the evidence rationale. AI is specifically valuable here because students overwhelmingly default to the least effective study strategies — Kornell & Bjork (2007) found that the most popular strategies (re-reading, highlighting) are rated "low utility" by research, while the most effective strategies (retrieval practice, distributed practice) are the least used. This skill encodes Dunlosky et al.'s (2013) landmark review into actionable, task-specific guidance.

## Evidence Foundation

Dunlosky et al. (2013) conducted the most comprehensive review of study strategies ever published, systematically evaluating ten techniques against four criteria (generalisability across learning conditions, student characteristics, materials, and criterion tasks). Only two strategies received a "high utility" rating: practice testing (retrieval practice) and distributed practice (spacing). Three received "moderate utility": interleaved practice, elaborative interrogation, and self-explanation. Five were rated "low utility" despite being the most popular among students: highlighting, re-reading, summarisation, keyword mnemonic, and imagery for text. Kornell & Bjork (2007) demonstrated that students are poor judges of their own learning — they choose strategies that feel effective (re-reading produces fluency, which feels like learning) over strategies that are effective (retrieval practice feels harder but produces better retention). Hartwig & Dunlosky (2012) found that students who self-tested and used spacing achieved significantly higher grades. Miyatsu et al. (2018) identified that even "good" strategies have pitfalls — retrieval practice fails if students don't check their answers, and spacing fails if the gaps are too large.

## Input Schema

The teacher must provide:
- **Learning task:** What the student needs to study. *e.g. "Prepare for a Year 10 Biology exam on cells and transport (70% factual recall, 30% application questions)" / "Revise for GCSE History Paper 2: causes and events of the Cold War"*
- **Student level:** Year group and current habits. *e.g. "Year 10, currently re-reads notes and highlights" / "Year 12, uses flashcards but no spacing"*
- **Material type:** Factual, conceptual, procedural, or mixed. *e.g. "Mixed — key terms to memorise plus processes to understand and apply"*

Optional (injected by context engine if available):
- **Time available:** Study time available before the assessment
- **Assessment type:** What they're preparing for (exam, essay, presentation, practical)
- **Student profiles:** Current study habits, academic performance data
- **Subject area:** Subject context

## Prompt

```
You are an expert in the cognitive psychology of learning, specialising in evidence-based study strategies. You have deep knowledge of Dunlosky et al.'s (2013) comprehensive review of learning techniques, Kornell & Bjork's (2007) research on self-regulated study, and the implementation pitfalls identified by Miyatsu et al. (2018).

Your task is to recommend study strategies for the following:

**Learning task:** {{learning_task}}
**Student level:** {{student_level}}
**Material type:** {{material_type}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Time available:** {{time_available}} — if not provided, design a general study plan and note how to adjust for more or less time.
**Assessment type:** {{assessment_type}} — if not provided, infer from the learning task description and recommend strategies that transfer across assessment types.
**Student profiles:** {{student_profiles}} — if not provided, assume the student uses common but ineffective strategies (re-reading, highlighting) and needs to be guided toward evidence-based alternatives.
**Subject area:** {{subject_area}} — if not provided, infer from the task and adapt strategies to the domain.

Apply these evidence-based principles:

1. **Rank strategies by Dunlosky et al.'s (2013) utility ratings:**
   - **High utility (recommend first):** Practice testing (retrieval practice), distributed practice (spacing). These should form the backbone of any study plan.
   - **Moderate utility (recommend second):** Interleaved practice, elaborative interrogation, self-explanation. Use as complements to the high-utility strategies.
   - **Low utility (identify and replace):** Highlighting, re-reading, summarisation, keyword mnemonic, imagery for text. If the student is currently using these, explicitly explain why they don't work and what to do instead.

2. **Explain *why* ineffective strategies feel effective (Kornell & Bjork, 2007):** Re-reading produces fluency — the text feels familiar, which the brain misinterprets as understanding. Highlighting feels productive — the coloured marks feel like engagement. But familiarity is not learning, and marking text is not encoding it. Students need to understand this illusion to break the habit.

3. **Provide implementation detail, not just strategy names (Miyatsu et al., 2018):** "Use retrieval practice" is not a recommendation. "Close your notes. Write down everything you remember about cell transport. Then open your notes and check — focus your next study session on what you couldn't recall" is a recommendation. Every strategy must include exactly how to do it.

4. **Flag pitfalls for each strategy (Miyatsu et al., 2018):**
   - Retrieval practice pitfall: not checking answers — students must verify and correct, or retrieval practice can reinforce errors.
   - Spacing pitfall: gaps too large — forgetting too much between sessions reduces the benefit. Start with short gaps and expand.
   - Self-testing pitfall: only testing what you already know — students must test weak areas, not just practise easy recall.

5. **Match strategies to material type:**
   - Factual recall (terms, dates, names) → flashcard retrieval practice, spaced repetition
   - Conceptual understanding (processes, relationships) → elaborative interrogation, self-explanation, concept mapping from memory
   - Procedural skills (calculations, methods) → interleaved practice problems, worked example study
   - Application/transfer → practice with varied problem types, self-explanation of why each approach works

6. **Create a concrete, schedulable plan:** Don't just list strategies — show the student exactly what to do, when, and for how long.

Return your output in this exact format:

## Study Strategy Guide: [Task]

**For:** [Student level]
**Material type:** [Type]

### Strategies to STOP Using (and Why)
[2–3 ineffective strategies the student is likely using, with honest explanation of why they don't work despite feeling productive]

### Recommended Strategies (Ranked by Evidence)
For each strategy:
- **Strategy name** — [Dunlosky rating]
- **What to do:** [Specific, step-by-step implementation]
- **Why it works:** [1–2 sentence evidence-based explanation]
- **Pitfall to avoid:** [The common implementation error]
- **Time needed:** [How long per session]

### Study Plan
[A concrete, schedulable plan applying these strategies to this specific task — laid out by session or by day]

### Student Guide
[Copy-pasteable, student-friendly version with practical instructions]

**Self-check before returning output:** Verify that (a) every recommended strategy has specific implementation instructions, not just a name, (b) ineffective strategies are identified with honest explanations, (c) pitfalls are flagged for each recommended strategy, (d) the study plan is concrete and schedulable, and (e) strategies are matched to the material type.
```

## Example Output

**Scenario:** *Learning task: "Prepare for Year 10 combined science exam — Biology topics: cell structure, transport across membranes, cell division. 40 marks: 20 recall, 10 application, 10 extended writing." / Student level: "Year 10, currently re-reads textbook and makes colourful notes" / Material type: "Mixed — terminology to recall, processes to understand, 6-mark questions requiring structured explanation"*

---

## Study Strategy Guide: Year 10 Biology Exam — Cells

**For:** Year 10, currently using re-reading and decorative note-making
**Material type:** Mixed (factual recall + conceptual understanding + extended writing)

### Strategies to STOP Using (and Why)

**1. Re-reading the textbook**
You feel like you're learning because the text becomes familiar — you recognise the words, and your brain interprets that familiarity as understanding. But Kornell & Bjork (2007) showed this is an illusion. Try this test: close your textbook right now and explain the stages of mitosis from memory. If you can't, the re-reading didn't teach you — it just made the text feel familiar. Dunlosky et al. (2013) rated re-reading as "low utility."

**2. Making colourful, detailed notes**
Copying information from the textbook into neat notes feels productive — you've spent time, you've produced something, and it looks good. But you've done the intellectual equivalent of photocopying. The information went from the book to the page without passing through your brain in a meaningful way. Dunlosky et al. (2013) rated summarisation as "low utility" because passive note-making doesn't require you to process or retrieve information.

**3. Highlighting**
Highlighting marks text but doesn't process it. You're deciding what's important (sometimes useful) but not doing anything to learn it. A highlighted textbook feels like a studied textbook — it's not. Dunlosky et al. (2013): "low utility."

### Recommended Strategies (Ranked by Evidence)

**1. Retrieval Practice (Practice Testing)** — High Utility (Dunlosky et al., 2013)

**What to do:**
1. Study a topic for 10–15 minutes (cell structure, for example).
2. Close all notes and textbooks completely.
3. On a blank piece of paper, write down EVERYTHING you can remember about that topic. Draw diagrams from memory. Define terms from memory.
4. Open your notes. Check what you got right (tick), what you missed (add in a different colour), and what you got wrong (correct in red).
5. The items you missed or got wrong are now your priority for the next study session.

**Why it works:** Retrieving information from memory strengthens the memory trace far more than re-reading it. Roediger & Pyc (2012) call this "the testing effect." The effort of reconstruction is what produces learning.

**Pitfall to avoid:** You MUST check your answers after retrieval. If you retrieve incorrect information and don't correct it, you'll learn the error. Always verify against your notes or textbook.

**Time needed:** 20 minutes per topic (10 min study + 5 min retrieval + 5 min checking and correction).

---

**2. Distributed Practice (Spacing)** — High Utility (Dunlosky et al., 2013)

**What to do:**
1. Do NOT study all three topics in one long session the night before. Instead, spread study across multiple short sessions over 2+ weeks.
2. Schedule: Study each topic 3 times, with gaps between sessions.
   - Session 1: 2 weeks before the exam
   - Session 2: 1 week before
   - Session 3: 2–3 days before
3. In each session, use retrieval practice (Strategy 1 above), not re-reading.

**Why it works:** Ebbinghaus's forgetting curve shows that without review, you lose ~70% of new learning within 24 hours. Spacing reviews at expanding intervals catches the forgetting before it becomes permanent. Cepeda et al. (2006): optimal spacing depends on retention interval.

**Pitfall to avoid:** Don't space sessions too far apart. If you've forgotten everything by the next session, the gap was too large — shorten it. Some forgetting is productive (it makes retrieval harder, which strengthens the memory), but complete forgetting means starting over.

**Time needed:** 3 sessions of 20 minutes per topic = 3 hours total across 2 weeks (vs. 3 hours in one session, which is less effective).

---

**3. Elaborative Interrogation** — Moderate Utility (Dunlosky et al., 2013)

**What to do:** For every fact you study, ask yourself "WHY is this true?" and generate an explanation.
- Cell membrane is selectively permeable → WHY? Because it needs to let some substances in (nutrients, oxygen) while keeping others out (waste, toxins) to maintain the cell's internal environment.
- Mitosis produces two identical cells → WHY identical? Because every chromosome is copied first, so each new cell gets a complete set. Why does the body need identical copies? For growth and repair — a skin cell needs to produce more skin cells, not different cells.

**Why it works:** Generating explanations creates additional retrieval pathways to the information (Pressley et al., 1992). You're connecting new knowledge to things you already understand.

**Pitfall to avoid:** This only works if you have enough background knowledge to generate plausible explanations. If you genuinely don't know why something is true, look it up and then practise explaining it — don't just skip the question.

**Time needed:** Add 5 minutes of "why?" questioning to each retrieval practice session.

---

**4. Interleaved Practice** — Moderate Utility (Dunlosky et al., 2013)

**What to do:** When practising exam questions, mix topics. Don't do 10 cell structure questions, then 10 transport questions. Instead, shuffle them: cell structure, transport, division, structure, transport, division. This forces you to identify which topic each question is about before you can answer it.

**Why it works:** In the exam, questions come from all topics mixed together. If you only practise in blocks, you never develop the skill of recognising which topic is being tested. Rohrer et al. (2015) found interleaved practice improved maths scores by 25%.

**Pitfall to avoid:** Don't interleave before you've studied each topic individually. You need to understand the basics first, then mix for practice.

**Time needed:** When doing practice questions (the last week of revision), interleave all topics. No extra time needed — just change the order.

### Study Plan

**Assuming 2 weeks before the exam, 30 minutes per day:**

| Day | What to do |
|-----|-----------|
| Day 1 (Mon) | Cell structure: read notes for 10 min, then close and retrieve everything on blank paper (15 min), check and correct (5 min) |
| Day 2 (Tue) | Transport across membranes: same pattern — read, close, retrieve, check |
| Day 3 (Wed) | Cell division: same pattern — read, close, retrieve, check |
| Day 4 (Thu) | Cell structure AGAIN: don't re-read. Go straight to retrieval. Blank paper, write everything. Compare to Day 1 — what did you remember this time that you forgot before? |
| Day 5 (Fri) | Transport AGAIN: straight to retrieval. Focus on what you missed on Day 2 |
| Day 6–7 (weekend) | Rest one day. On the other: retrieve ALL three topics on one sheet. Time yourself — 20 minutes for all three |
| Day 8 (Mon) | Cell division retrieval + elaborative interrogation: for each stage of mitosis, explain WHY it happens |
| Day 9 (Tue) | Practice exam questions — INTERLEAVED. Mix all three topics. Focus on identifying question type |
| Day 10 (Wed) | Practice 6-mark questions: write one full extended answer under timed conditions. Check against mark scheme |
| Day 11 (Thu) | Final retrieval: everything on blank paper. Identify the 3 weakest areas. Study ONLY those |
| Day 12 (Fri) | Final retrieval of the 3 weakest areas. Then stop — you're as prepared as spacing allows |

### Student Guide

---

**HOW TO ACTUALLY STUDY (based on what the research says works)**

**STOP doing these** (they feel productive but aren't):
- Re-reading your notes — familiarity is not understanding
- Making beautiful notes — copying is not learning
- Highlighting — marking is not remembering

**START doing these:**

**Step 1: Retrieve, don't re-read.** Close your notes. Write everything you remember on blank paper. Then check. The stuff you forgot? That's what you study next.

**Step 2: Space it out.** Study each topic 3 times over 2 weeks, not once the night before. Short sessions with gaps between them beat long sessions every time.

**Step 3: Ask "why?"** For every fact, explain why it's true. If you can explain it, you understand it. If you can't, you've found a gap.

**Step 4: Mix it up.** When doing practice questions, shuffle the topics. Don't do all cell questions then all transport questions — mix them.

**The golden rule:** If it feels easy, you're probably not learning. Retrieval practice feels harder than re-reading — that's the point. The harder the retrieval, the stronger the memory.

---

## Known Limitations

1. **Students may resist replacing comfortable, familiar strategies with effortful ones.** Re-reading feels productive. Retrieval practice feels frustrating. Kornell & Bjork (2007) showed that students rate the less effective strategy as more effective because of the fluency illusion. Teachers should expect resistance and provide the evidence rationale — students are more likely to persist with effortful strategies if they understand *why* they work.

2. **The strategy recommendations assume students have access to accurate study materials.** If a student's notes contain errors, retrieval practice may reinforce those errors. The "check and correct" step is essential but relies on having a reliable source to check against.

3. **Dunlosky et al.'s (2013) utility ratings are based primarily on studies of verbal learning (text comprehension, factual recall).** Transfer to highly practical subjects (PE, music performance, art, design technology) is less well-established. For procedural skills, interleaved practice is well-evidenced, but the "close your notes and retrieve" approach needs adaptation — physical rehearsal and deliberate practice may be more appropriate.

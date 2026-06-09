---
# AGENT SKILLS STANDARD FIELDS (v2)
name: retrieval-practice-generator
description: "Generate retrieval practice questions at varied difficulty levels for a topic or concept. Use when creating quiz starters, revision activities, or low-stakes testing materials."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "memory-learning-science/retrieval-practice-generator"
skill_name: "Retrieval Practice Question Generator"
domain: "memory-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Roediger & Butler (2011) — The critical role of retrieval practice in long-term retention"
  - "Karpicke & Roediger (2008) — The critical importance of retrieval for learning"
  - "Rowland (2014) — Meta-analysis: the effect of testing versus restudy on retention (effect size 0.50)"
  - "Agarwal et al. (2012) — Classroom-based retrieval practice studies with middle school students"
  - "Dunlosky et al. (2013) — Practice testing rated as high-utility learning strategy"
input_schema:
  required:
    - field: "topic"
      type: "string"
      description: "The specific concept or skill students need to retrieve"
    - field: "student_level"
      type: "string"
      description: "Age/year group and approximate prior knowledge level"
    - field: "question_count"
      type: "integer"
      description: "Number of questions to generate (recommended 6–10)"
  optional:
    - field: "student_profiles"
      type: "array"
      description: "From context engine: individual language levels, prior knowledge gaps"
    - field: "competency_framework"
      type: "string"
      description: "From context engine: school's assessment framework or curriculum standard"
    - field: "time_since_learning"
      type: "string"
      description: "How long ago students first encountered this material"
    - field: "known_misconceptions"
      type: "array"
      description: "Specific misconceptions already observed in this cohort"
output_schema:
  type: "object"
  fields:
    - field: "questions"
      type: "array"
      description: "List of retrieval questions, each with question text, retrieval type label (free recall / cued recall / recognition), and difficulty estimate"
    - field: "spacing_recommendation"
      type: "string"
      description: "When to use these questions relative to original learning"
    - field: "answer_notes"
      type: "string"
      description: "Key points for correct answers and common errors to watch for"
    - field: "teacher_script"
      type: "string"
      description: "Brief suggested implementation script (how to run the retrieval activity)"
chains_well_with:
  - "spaced-practice-scheduler"
  - "formative-assessment-technique-selector"
  - "gap-analysis-from-student-work"
  - "cognitive-load-analyser"
teacher_time: "3 minutes"
tags: ["retrieval", "memory", "assessment", "spaced-practice", "testing-effect"]
---

# Retrieval Practice Question Generator

## What This Skill Does

Generates a set of retrieval practice questions that force genuine reconstruction of knowledge from memory — not recognition, not re-reading, not familiarity-based guessing. The skill distinguishes between free recall (no cues), cued recall (partial cues), and recognition (select from options) question types, and calibrates the mix based on student level and time since learning. AI is specifically valuable here because designing questions that target reconstruction rather than recognition requires deep understanding of the testing effect literature — most teacher-made quiz questions inadvertently test recognition.

## Evidence Foundation

The testing effect is one of the most robust findings in cognitive psychology. Karpicke & Roediger (2008) demonstrated that retrieval practice produces substantially better long-term retention than re-studying, even when re-study involves more total exposure time. Roediger & Butler (2011) established that retrieval practice strengthens memory traces through a distinct mechanism from encoding — the act of reconstruction itself modifies the memory. Rowland's (2014) meta-analysis of 159 studies found a mean effect size of 0.50 for testing versus restudy, with effects robust across age groups, materials, and delay intervals. Critically, Agarwal et al. (2012) replicated these effects in real classroom settings with middle school students, confirming the lab-to-classroom transfer. Dunlosky et al. (2013) rated practice testing as one of only two "high utility" learning strategies in their landmark review of ten techniques.

## Input Schema

The teacher must provide:
- **Topic:** The specific concept or skill students need to retrieve. *e.g. "causes of World War I" / "photosynthesis light reactions" / "solving linear equations with one variable"*
- **Student level:** Year group and approximate prior knowledge. *e.g. "Year 9, mid-ability, covered this topic 2 weeks ago" / "Year 12 Biology, high prior knowledge"*
- **Question count:** Number of questions to generate. *e.g. 8*

Optional (injected by context engine if available):
- **Student profiles:** Individual language proficiency levels, identified knowledge gaps from prior assessments
- **Competency framework:** The specific curriculum standard or assessment framework being targeted
- **Time since learning:** Duration since the material was first taught (affects difficulty calibration)
- **Known misconceptions:** Specific misconceptions already observed in student responses

## Prompt

```
You are an expert in cognitive psychology specialising in the testing effect and retrieval-based learning. You have deep knowledge of Roediger & Butler's (2011) work on retrieval practice, Karpicke & Roediger's (2008) research on the critical importance of retrieval for learning, and Rowland's (2014) meta-analysis demonstrating robust effect sizes for testing versus restudy.

Your task is to generate {{question_count}} retrieval practice questions on the topic "{{topic}}" for {{student_level}}.

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Time since learning:** {{time_since_learning}} — if not provided, assume the material was taught within the last 1–2 weeks and calibrate difficulty accordingly.
**Known misconceptions:** {{known_misconceptions}} — if not provided, include questions targeting the most common misconceptions for this topic based on your subject knowledge.
**Competency framework:** {{competency_framework}} — if not provided, generate questions aligned to general curriculum expectations for the stated year group.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical mixed-ability class with no specific language or learning needs.

Apply these evidence-based criteria when generating questions:

1. **Retrieval type distribution:** Include a mix of:
   - Free recall questions (no cues — e.g. "Explain the process of..." / "List the factors that...") — these produce the strongest learning effect but are hardest
   - Cued recall questions (partial cues — e.g. "The three main causes were _____, _____, and _____" / "Complete this diagram...") — moderate difficulty, good scaffolding
   - Recognition questions (select from options — e.g. multiple choice) — weakest retrieval effect but useful for building confidence in novice learners
   Weight toward free and cued recall. Only include recognition questions for novice learners or as warm-up.

2. **Genuine reconstruction, not recognition:** Every question must require the student to reconstruct knowledge from memory, not simply recognise familiar-looking information. Avoid questions answerable by surface-level pattern matching.

3. **Target the right knowledge:** Questions should target the core concepts, relationships, and procedures — not trivial details, dates, or definitions unless those are genuinely important to understanding.

4. **Difficulty calibration:** If time since learning is recent (< 1 week), include more cued recall. If time since learning is longer (> 2 weeks), free recall becomes more valuable as it provides stronger retrieval practice during the forgetting phase.

5. **Misconception targeting:** If known misconceptions are provided, include at least 2 questions specifically designed to surface those misconceptions.

Return your output in this exact format:

## Retrieval Practice Questions: [Topic]

**For:** [Student level]
**Spacing recommendation:** [When to use these questions — e.g. "Use 3–7 days after initial teaching for optimal spacing effect. Re-use a subset at 2–4 weeks for a second retrieval opportunity."]

### Questions

For each question, provide:
- The question text
- **Type:** [Free Recall / Cued Recall / Recognition]
- **Targets:** [What specific knowledge this retrieves]

### Answer Notes

For each question, provide:
- Key points for a correct answer
- Common errors or misconceptions to watch for

### Implementation Script

A brief (3–4 sentence) script for how the teacher should run this retrieval activity in class, including:
- Whether to allow notes (no — that defeats the purpose)
- How long to give students (typically 8–12 minutes for 6–10 questions)
- What to do after (discuss answers, identify gaps, do NOT grade — low-stakes is essential)

**Self-check before returning output:** Verify that (a) each question requires genuine reconstruction, not just recognition, (b) the mix of retrieval types is appropriate for the student level, (c) no question is answerable from the question text alone without prior knowledge, and (d) the questions target meaningful knowledge, not trivia.
```

## Example Output

**Scenario:** *Topic: "The causes and process of erosion" / Student level: "Year 7 Geography, mixed ability, covered this 10 days ago" / Question count: 8*

---

## Retrieval Practice Questions: The Causes and Process of Erosion

**For:** Year 7 Geography, mixed ability
**Spacing recommendation:** Use now (10 days post-learning is within the optimal spacing window). Re-use questions 1, 3, 5, and 7 in 2–3 weeks for a second retrieval opportunity. After that, integrate erosion retrieval into mixed-topic quizzes once per half-term.

### Questions

**Q1.** Without looking at any notes, explain the difference between erosion and weathering. Why are they not the same thing?
- **Type:** Free Recall
- **Targets:** Distinction between two commonly conflated processes; understanding that erosion involves transport

**Q2.** Name the four main types of erosion that rivers cause. For each one, describe what physically happens to the rock or riverbed.
- **Type:** Free Recall
- **Targets:** Hydraulic action, abrasion, attrition, solution — and the mechanism of each, not just the label

**Q3.** A farmer notices that the soil on a hillside field is thinner every year. The field has no trees or hedgerows. Explain why the soil is disappearing, using the correct geographical terms.
- **Type:** Cued Recall (scenario provides contextual cue)
- **Targets:** Soil erosion process, role of vegetation in preventing erosion, surface runoff

**Q4.** Complete this sequence: Rock is broken down by weathering → loose material is __________ by erosion → material is carried by a river, which is called __________ → material is dropped when the river slows, which is called __________.
- **Type:** Cued Recall
- **Targets:** Transport/erosion, transportation, deposition — the full cycle

**Q5.** Draw a simple diagram showing how a waterfall is formed by erosion. Label at least four features and explain what type of erosion is happening at each point.
- **Type:** Free Recall (diagram from memory)
- **Targets:** Undercutting, hard/soft rock, plunge pool, retreat — spatial understanding of the process

**Q6.** A student writes: "Erosion is when rocks get broken into smaller pieces by the weather." What is wrong with this statement? Write a more accurate version.
- **Type:** Cued Recall (error correction)
- **Targets:** Distinguishing weathering from erosion; understanding that erosion is about movement, not just breakdown

**Q7.** Why does erosion happen faster in some places than others? Give three specific factors and explain how each one affects the rate of erosion.
- **Type:** Free Recall
- **Targets:** Rock type/hardness, climate/rainfall, vegetation cover, human activity — causal reasoning

**Q8.** Which of the following is an example of abrasion?
(a) Salt crystals expanding in cracks in a cliff face
(b) Pebbles carried by a river grinding against the riverbed
(c) Carbon dioxide in rainwater dissolving limestone
(d) Waves compressing air into cracks in rock
- **Type:** Recognition
- **Targets:** Distinguishing abrasion from salt weathering (a), chemical weathering/solution (c), and hydraulic action (d)

### Answer Notes

- **Q1:** Key distinction — weathering breaks down rock *in situ*, erosion involves the *transport* of material. Common error: students say "erosion is when rock breaks down" (conflating with weathering).
- **Q2:** Hydraulic action (force of water), abrasion (sediment scraping), attrition (particles grinding each other), solution (chemical dissolving). Common error: confusing abrasion with attrition.
- **Q3:** Without vegetation roots to bind soil, rainfall creates surface runoff that carries topsoil downhill. Key terms: surface runoff, soil erosion, lack of interception. Common error: saying "the wind blows it away" without explaining the water-based mechanism.
- **Q4:** Transported (or picked up/moved), transportation, deposition. Common error: using "erosion" for all three blanks.
- **Q5:** Must show hard rock over soft rock, undercutting of soft rock, overhang, collapse, plunge pool, and gorge formation through retreat. Common error: drawing it as a single event rather than a process over time.
- **Q6:** The statement describes weathering, not erosion. Erosion specifically involves the *movement* of material. Better: "Erosion is the process by which weathered material is picked up and transported by agents such as rivers, waves, wind, or ice."
- **Q7:** Accept: rock hardness/type, rainfall amount and intensity, vegetation cover, slope angle, human activity (deforestation, construction). Must explain the mechanism, not just list factors.
- **Q8:** Correct answer: (b). Distractor analysis: (a) = salt weathering, (c) = chemical weathering/solution, (d) = hydraulic action.

### Implementation Script

Run this as a low-stakes retrieval starter — no notes, no textbooks, no devices. Tell students: "This is not a test for marks. It's a memory exercise. Getting stuck is normal and actually helps you learn — that's what the research shows." Give 10 minutes for all 8 questions. Students who finish early should go back and add more detail. After time is up, discuss answers as a class, focusing on Q1 and Q6 (the most common misconceptions). Do not collect or grade — the learning happens in the retrieval attempt itself, not in the score.

---

## Known Limitations

1. **Cannot verify factual accuracy against a specific textbook or syllabus.** The questions are generated from general subject knowledge. Teachers should check that terminology and expected answers match what was actually taught — especially for Q2 and Q4 where specific terms may vary between curricula.

2. **Free recall questions may overwhelm students with very low prior knowledge or limited English proficiency.** For EAL students or those with significant gaps, increase the proportion of cued recall and recognition questions. Chain with the Scaffolded Task Modifier for language-adapted versions.

3. **The spacing recommendation is calibrated to lab research on optimal intervals.** Real classroom scheduling constraints (timetable gaps, holidays, assessment windows) may make the recommended spacing impractical. Teacher judgment on timing is always necessary.

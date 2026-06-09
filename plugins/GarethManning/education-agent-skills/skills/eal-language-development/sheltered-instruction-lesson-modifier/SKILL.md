---
# AGENT SKILLS STANDARD FIELDS (v2)
name: sheltered-instruction-lesson-modifier
description: "Modify a lesson plan using SIOP sheltered instruction principles to support language learners across all four skills. Use when planning lessons for classes that include EAL students."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "eal-language-development/sheltered-instruction-lesson-modifier"
skill_name: "Sheltered Instruction Lesson Modifier"
domain: "eal-language-development"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Echevarría, Vogt & Short (2008, 2017) — Making Content Comprehensible for English Learners: the SIOP Model"
  - "Short, Fidelman & Louguit (2012) — Developing academic language in English language learners through sheltered instruction"
  - "Cummins (2000) — Language, Power and Pedagogy"
  - "Gibbons (2015) — Scaffolding Language, Scaffolding Learning"
  - "Lyster (2007) — Learning and Teaching Languages Through Content: a counterbalanced approach"
input_schema:
  required:
    - field: "lesson_plan"
      type: "string"
      description: "A description of the planned lesson — topic, activities, resources, and learning objective"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "eal_students"
      type: "string"
      description: "Number of EAL students and their approximate proficiency levels"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: first languages, time in English-medium schooling, specific needs"
    - field: "lesson_duration"
      type: "string"
      description: "Length of the lesson"
    - field: "resources_available"
      type: "string"
      description: "Technology, bilingual resources, teaching assistants, or other supports available"
output_schema:
  type: "object"
  fields:
    - field: "modified_lesson"
      type: "object"
      description: "The lesson plan modified with SIOP components — content objectives, language objectives, scaffolds for each phase"
    - field: "language_objectives"
      type: "array"
      description: "Explicit language objectives aligned to the content being taught"
    - field: "siop_component_checklist"
      type: "object"
      description: "How each SIOP component is addressed in the modified lesson"
    - field: "teacher_adaptations"
      type: "array"
      description: "Specific changes to teacher talk, pacing, and interaction patterns"
chains_well_with:
  - "language-demand-analyser"
  - "vocabulary-tiering-tool"
  - "scaffolded-task-modifier"
  - "academic-language-sentence-frame-generator"
teacher_time: "5 minutes"
tags: ["SIOP", "sheltered-instruction", "EAL", "lesson-planning", "content-language-integration"]
---

# Sheltered Instruction Lesson Modifier

## What This Skill Does

Takes a content lesson plan and modifies it using the SIOP (Sheltered Instruction Observation Protocol) model principles, adding explicit language objectives, building background knowledge, making input comprehensible, structuring meaningful interaction, and providing opportunities for practice and application — all while maintaining the content learning objective. The output is a modified lesson plan that serves all students (not just EAL students), because the SIOP principles — clear objectives, comprehensible input, structured interaction, meaningful practice — are good teaching for everyone. AI is specifically valuable here because effective sheltered instruction requires analysing a lesson through two simultaneous lenses (content AND language) and making modifications across multiple SIOP components in a way that is coherent and practical — not a checklist of disconnected additions but an integrated redesign.

## Evidence Foundation

Echevarría, Vogt & Short (2008, 2017) developed the SIOP Model — the most rigorously researched approach to teaching content to English language learners. The model identifies 30 features across 8 components: Lesson Preparation (content and language objectives), Building Background (connecting to prior knowledge), Comprehensible Input (clear, adapted teacher talk), Strategies (scaffolding, metacognitive prompts), Interaction (structured talk opportunities), Practice/Application (meaningful tasks), Lesson Delivery (pacing, engagement), and Review/Assessment (checking understanding). Short, Fidelman & Louguit (2012) demonstrated that systematic SIOP implementation produced significant gains in both content learning and academic language development, with effect sizes of 0.40–0.60 across subjects. Critically, SIOP-taught classes showed gains for ALL students, not just EAL students — the principles are universally effective. Cummins (2000) established that academic language develops through meaningful engagement with challenging content, not through simplified content or isolated language exercises. Gibbons (2015) emphasised that the most powerful language learning happens when students are engaged in cognitively demanding content tasks with appropriate support. Lyster (2007) demonstrated that content-based language instruction is more effective than isolated language teaching, but only when language is explicitly noticed and practised alongside content — implicit "immersion" is insufficient.

## Input Schema

The teacher must provide:
- **Lesson plan:** Description of the planned lesson. *e.g. "Year 8 Geography: Introduction to tectonic plates. Activities: teacher explanation with diagrams (15 min), students label a cross-section diagram (10 min), students answer textbook questions about plate boundaries (20 min). Objective: understand the three types of plate boundary and their effects."*
- **Subject area:** The subject. *e.g. "Geography"*
- **Student level:** Year group. *e.g. "Year 8"*

Optional (injected by context engine if available):
- **EAL students:** Number and proficiency levels
- **Student profiles:** First languages, time in English-medium schooling, specific needs
- **Lesson duration:** Length of the lesson
- **Resources available:** Technology, bilingual resources, TA support

## Prompt

```
You are an expert in sheltered instruction and content-language integrated teaching, with deep knowledge of the SIOP Model (Echevarría, Vogt & Short, 2008, 2017), Cummins' (2000) framework for academic language development, and Gibbons' (2015) approach to scaffolding in content classrooms. You understand that effective instruction for EAL students does not mean simplifying content — it means making challenging content accessible through clear language objectives, comprehensible input, structured interaction, and meaningful practice.

Your task is to modify this lesson plan using SIOP principles:

**Lesson plan:** {{lesson_plan}}
**Subject area:** {{subject_area}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**EAL students:** {{eal_students}} — if not provided, assume 4–6 EAL students at mixed proficiency levels (Early Acquisition to Consolidating) in a class of 25–30.
**Student profiles:** {{student_profiles}} — if not provided, assume mixed first languages with conversational fluency but varying academic language proficiency.
**Lesson duration:** {{lesson_duration}} — if not provided, assume a 60-minute lesson.
**Resources available:** {{resources_available}} — if not provided, assume standard classroom resources (whiteboard, projector, textbooks) but no bilingual TA or specialist technology.

Apply the SIOP Model's eight components:

1. **Lesson Preparation:**
   - Identify the content objective (what students will LEARN about the subject).
   - Add a language objective (what academic language students will USE to demonstrate their content learning). Language objectives should be specific: "Students will use causal connectives (because, therefore, as a result) to explain how plate boundaries cause earthquakes" — NOT vague: "Students will practise speaking."
   - Both objectives should be displayed and referred to throughout the lesson.

2. **Building Background:**
   - Identify the background knowledge the lesson assumes. What must students already know?
   - Design a brief activity (3–5 minutes) that activates or builds this background — especially for EAL students who may lack the cultural or contextual knowledge assumed by the content.
   - Explicitly link new content to what students already know.

3. **Comprehensible Input:**
   - Modify teacher talk: slow down (not simplify), use shorter sentences, repeat key terms, write key words on the board as you say them.
   - Add visual support: diagrams, images, gestures, demonstrations, graphic organisers.
   - Pre-teach key vocabulary (Tier 2 and 3 words essential for comprehension).

4. **Strategies:**
   - Add metacognitive scaffolds: What do students do when they don't understand? Teach them to ask: "What word don't I understand?" "Can I work out the meaning from context?" "Should I ask?"
   - Provide graphic organisers, sentence frames, or thinking scaffolds appropriate to the tasks.

5. **Interaction:**
   - Build in structured talk opportunities. EAL students need to USE language, not just hear it.
   - Replace individual silent tasks with partner or group tasks where possible.
   - Provide talk frames for discussion: "I think ___ because ___" / "I agree with ___ because ___" / "Can you explain what you mean by ___?"
   - Ensure sufficient wait time for EAL students to process and formulate responses.

6. **Practice/Application:**
   - Ensure the practice task requires students to USE the content knowledge AND the academic language.
   - Hands-on, visual, or collaborative tasks are more accessible than text-heavy tasks — but must still be cognitively demanding.
   - Provide language support (sentence frames, word banks) during practice tasks.

7. **Lesson Delivery:**
   - Check pacing: are transitions clear? Are instructions given step-by-step rather than all at once?
   - Vary activity types to maintain engagement and provide multiple access points.
   - Monitor comprehension continuously, not just at the end.

8. **Review/Assessment:**
   - Check comprehension of BOTH content and language objectives at the end of the lesson.
   - Use methods that don't depend solely on English proficiency: diagrams, matching tasks, mini-whiteboards, partner explanations.
   - Provide opportunity for self-assessment: "Can I explain [content] using [academic language]?"

Return your output in this exact format:

## Modified Lesson: [Topic]

**For:** [Student level] [Subject area]
**Duration:** [Minutes]

### Objectives (displayed on board)

**Content objective:** [What students will learn about the subject]
**Language objective:** [What academic language students will use — specific and observable]

### Modified Lesson Plan

[Complete lesson plan with SIOP modifications integrated — not as an appendix but built INTO the lesson flow. Each phase should show what the teacher does, what students do, and what SIOP modification has been applied.]

### SIOP Component Checklist

[How each of the 8 SIOP components is addressed in the modified lesson]

### Teacher Adaptations

[Specific changes to teacher talk, pacing, questioning, and interaction patterns — practical, concrete advice]

### What Changed and Why

[Summary of the key modifications, linked to the SIOP principles that justify them]

**Self-check before returning output:** Verify that (a) both content AND language objectives are explicit and specific, (b) the modifications are integrated into the lesson flow, not added as separate EAL activities, (c) comprehensible input strategies are applied to teacher talk, (d) structured interaction opportunities are built in, (e) practice tasks require use of academic language, (f) the content objective has NOT been reduced — cognitive demand is maintained, and (g) the modifications benefit all students, not just EAL students.
```

## Example Output

**Scenario:** *Lesson plan: "Year 8 Science: Introduction to the digestive system. Activities: (1) Teacher explanation with PowerPoint slides showing the organs of the digestive system (15 min), (2) Students label a diagram of the digestive system from memory (10 min), (3) Students read a textbook page about the function of each organ and answer questions (20 min), (4) Plenary quiz — teacher asks questions, students raise hands to answer (5 min). Objective: Students should be able to name the organs of the digestive system and describe their functions." / Subject area: "Science (Biology)" / Student level: "Year 8" / EAL students: "5 EAL students — 1 New to English (Somali), 2 Early Acquisition (Polish, Arabic), 2 Developing (Spanish, Mandarin)" / Lesson duration: "50 minutes"*

---

## Modified Lesson: The Digestive System

**For:** Year 8 Science (Biology)
**Duration:** 50 minutes

### Objectives (displayed on board)

**Content objective:** Name the main organs of the digestive system and describe the function of each organ.

**Language objective:** Use the sentence structure "The [organ] [verb]s the food by [process]" to describe what each organ does. (Example: "The stomach digests the food by mixing it with acid and enzymes.")

*Display both objectives on the board at the start. Return to them at the end: "Can you do this now?"*

### Modified Lesson Plan

**Phase 1: Building Background + Comprehensible Input (12 minutes)**

*SIOP modification: Replace the 15-minute teacher explanation with a shorter, more interactive input phase that builds background and makes input comprehensible.*

**0:00–3:00 — Building Background (SIOP Component 2)**
"Before we start — everyone knows what happens when you eat food. Think about the last thing you ate. What happened to it? Where did it go? Talk to your partner for 30 seconds."

Take 2–3 responses. Write key words on the board as students say them: *mouth, chew, swallow, stomach, toilet.*

"So you already know that food goes on a journey through your body. Today we're going to learn the scientific names for each stop on that journey, and — more importantly — what happens at each stop."

*Why this works:* Connects to universal experience (everyone eats). Activates existing knowledge in accessible language. The word "journey" provides a metaphor scaffold that makes the sequential process intuitive.

**3:00–12:00 — Comprehensible Input: Teacher Explanation (SIOP Component 3)**

Show the PowerPoint slides BUT with these modifications:
- Each slide shows ONE organ, not a full diagram. Introduce organs one at a time.
- For each organ: show the image, say the name, write it on the board, have students repeat the name aloud (choral repetition — normalises pronunciation for everyone).
- For each organ: describe function in ONE simple sentence, then write the sentence on the board using the frame from the language objective.

**Board builds progressively:**

| Organ | What it does | Key sentence |
|-------|-------------|--------------|
| Mouth | Breaks food into smaller pieces | The mouth breaks down the food by chewing and mixing with saliva. |
| Oesophagus | Moves food to the stomach | The oesophagus moves the food by squeezing it downwards (peristalsis). |
| Stomach | Digests food chemically | The stomach digests the food by mixing it with acid and enzymes. |
| Small intestine | Absorbs nutrients into the blood | The small intestine absorbs the nutrients by passing them through its walls into the blood. |
| Large intestine | Absorbs water | The large intestine absorbs water from the remaining food. |

*Why this works:* Visual + verbal + written. Students see, hear, AND read each term. The progressive table stays visible throughout the lesson. The sentence frame is modelled consistently, building the language objective into the content explanation.

**Adaptation for the New to English student (Somali):** Provide a bilingual glossary (English–Somali) with key organ names and simple definitions. If a bilingual peer or TA is available, allow brief first-language explanation of the concept. The student should still attempt the English sentence frame.

**Phase 2: Structured Interaction + Practice (15 minutes)**

*SIOP modification: Replace the silent individual labelling task with a collaborative, interactive task that requires students to USE the academic language.*

**12:00–17:00 — Partner Labelling (SIOP Components 5 & 6)**
Give each pair a blank body outline diagram and cut-out organ name labels.
"With your partner, place the organ labels in the correct position. As you place each one, say the key sentence: 'The [organ] [verb]s the food by [process].' You must say it out loud — not just place the label silently."

*Why this works:* Collaborative (students help each other). Kinaesthetic (physical manipulation of labels). Oral practice (the sentence frame is used for speaking, not just writing). The board table remains visible as a reference — this is supported recall, not unsupported memory.

**17:00–27:00 — Describing the Journey (SIOP Components 4, 5, 6)**

*Replace the textbook reading and comprehension questions with a more interactive and linguistically supported task.*

Give each student a "Food's Journey" worksheet with the organs listed in order and a sentence frame for each:

"Imagine you are a piece of food. Describe your journey through the digestive system. For each organ, complete the sentence:"

1. First, I enter the **mouth**. The mouth ___ me by ___.
2. Next, I travel down the **oesophagus**. The oesophagus ___ me by ___.
3. Then, I arrive in the **stomach**. The stomach ___ me by ___.
4. After that, I move into the **small intestine**. The small intestine ___ from me by ___.
5. Finally, I pass through the **large intestine**. The large intestine ___ from me by ___.

**Early Acquisition students:** Use a cloze version with word bank: *breaks down, moves, digests, absorbs nutrients, absorbs water, chewing, squeezing, mixing with acid, passing through walls, removing water.*

**Developing students:** Use the open sentence frame above.

**Consolidating students and native speakers:** Write the journey WITHOUT the frame — produce a paragraph using their own language, incorporating the key terms.

**Extension for fast finishers:** "What happens if one organ stops working? Choose one organ and explain what would go wrong."

*Why this works:* Same content (organs and functions), same cognitive demand (describing processes), differentiated by language scaffold level. Every student practises the language objective. The first-person perspective ("I enter the mouth") is engaging and makes the abstract process concrete.

**Phase 3: Review and Assessment (8 minutes)**

*SIOP modification: Replace the hands-up plenary quiz (which only assesses the fastest/most confident students) with a whole-class assessment method.*

**27:00–32:00 — Mini-whiteboard Quiz (SIOP Component 8)**

"Show me on your whiteboards..."
1. "Which organ absorbs nutrients?" [Students write: small intestine]
2. "What does the stomach do to food?" [Students write a phrase or sentence]
3. "Put these organs in order: stomach, mouth, large intestine, small intestine, oesophagus" [Students write 1–5]

*Why this works:* EVERY student responds (not just hand-raisers). The teacher can scan all boards simultaneously. Question 2 checks whether students can use the language objective (describing function), not just recall the name. Lower-proficiency students can still show understanding through single words or labelled diagrams.

**32:00–35:00 — Return to Objectives (SIOP Component 8)**

"Look at our two objectives. Content: can you name the organs and describe their functions? Let's check — everyone point to the organ I name on your diagram..."

"Language: can you use the sentence 'The [organ] [verb]s the food by [process]'? Turn to your partner and say one sentence about one organ. Go."

Listen for correct use of the frame. Identify students who still need support — they'll need additional practice next lesson.

### SIOP Component Checklist

| SIOP Component | How it's addressed |
|---|---|
| **1. Lesson Preparation** | Content AND language objectives are explicit, written on the board, and revisited at the end |
| **2. Building Background** | 3-minute warm-up connects to universal experience (eating) before introducing scientific vocabulary |
| **3. Comprehensible Input** | One organ at a time, visual + verbal + written, progressive board table, choral repetition, bilingual glossary for New to English student |
| **4. Strategies** | Sentence frames scaffold language production; progressive table serves as a reference tool; first-person perspective makes abstract process concrete |
| **5. Interaction** | Partner labelling with oral requirement; pair discussion at plenary; no silent individual tasks without a talk component |
| **6. Practice/Application** | "Food's Journey" task requires USE of language objective with content; differentiated by scaffold level, not by content |
| **7. Lesson Delivery** | Pacing shortened from 15-min lecture to 9-min interactive input; varied activities; continuous monitoring via circulation |
| **8. Review/Assessment** | Mini-whiteboards (whole class, not hand-raisers); explicit return to both objectives; partner check of language objective |

### Teacher Adaptations

1. **Slow down teacher talk, don't simplify it.** Say "The oesophagus moves the food by squeezing it downwards — this squeezing is called peristalsis" — speak slowly and repeat "squeezing" and "peristalsis." Do NOT say "The food goes down a tube." The scientific language IS the content.

2. **Write as you speak.** Every key term goes on the board as you say it. EAL students can read and re-read what they cannot re-hear. The progressive table becomes the most important resource in the lesson.

3. **Choral repetition for pronunciation.** "Say it with me: oesophagus. O-soph-a-gus." This is not babyish — it normalises scientific pronunciation for everyone and gives EAL students a chance to practise saying unfamiliar words.

4. **Instructions one step at a time.** Instead of: "Get your worksheet, work with your partner, complete the sentences, and put your hand up when you're done" — say: "Step 1: Pick up the worksheet from the front table." [Pause.] "Step 2: Work with your partner." [Pause.] "Step 3: Complete the sentences using the table on the board to help you."

5. **Wait time.** After asking a question, wait 5–7 seconds (not the typical 1–2). EAL students need processing time to formulate a response in English. Saying "Take your time" explicitly signals that speed is not the goal.

6. **Check task comprehension separately from content comprehension.** Before students start any activity, ask: "What are you going to do?" (checking they understand the TASK). Don't ask "Do you understand?" (always gets "yes"). Ask: "Tell me step one" — this reveals whether they understood the instruction.

### What Changed and Why

| Original | Modified | Why |
|----------|----------|-----|
| 15-min teacher explanation (all slides at once) | 9-min interactive input (one organ at a time, visual + verbal + written, choral repetition) | SIOP Comprehensible Input: multi-modal, paced, progressive. Reduces cognitive load while maintaining content. |
| Silent individual diagram labelling | Partner labelling with oral sentence requirement | SIOP Interaction: EAL students need to USE language, not just receive it. Partner work provides low-stakes oral practice. |
| Read textbook + answer questions | "Food's Journey" sentence frame task, differentiated by scaffold level | SIOP Practice/Application: reading-heavy tasks are a language barrier disguised as content assessment. The modified task assesses the SAME content knowledge through a more accessible format. |
| Hands-up plenary quiz | Mini-whiteboard whole-class assessment + partner check | SIOP Review: hands-up only assesses the fastest/most confident. Whiteboards assess everyone simultaneously. |
| No language objective | Explicit language objective: "The [organ] [verb]s by [process]" | SIOP Lesson Preparation: without a language objective, language development is incidental. With one, it's intentional. |

---

## Known Limitations

1. **SIOP modifications take time to plan.** The modified lesson is better for all students but requires more preparation than the original. As teachers become familiar with SIOP principles, the modifications become more automatic, but the initial investment is significant. This skill accelerates the planning process but cannot eliminate it.

2. **The modifications assume a typical classroom setup.** Schools with specialist EAL teachers, bilingual TAs, or access to first-language resources can implement additional supports that this modification doesn't include. The output provides a baseline modification that works with standard resources; additional specialist support should be layered on where available.

3. **Sheltered instruction is one lesson at a time, but language development is longitudinal.** This skill modifies a single lesson, but EAL students need consistent, sustained support across all lessons. The language objective in one lesson should connect to language objectives in subsequent lessons, building a coherent programme of academic language development. Individual lesson modification is necessary but not sufficient — it must be part of a whole-school approach.

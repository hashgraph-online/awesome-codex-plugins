---
# AGENT SKILLS STANDARD FIELDS (v2)
name: lesson-opening-designer
description: "Design a lesson opening that activates prior knowledge and connects previous learning to today's content. Use when planning lesson starters, retrieval openers, or advance organisers."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "explicit-instruction/lesson-opening-designer"
skill_name: "Lesson Opening Designer"
domain: "explicit-instruction"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Rosenshine (2012) — Principles of Instruction, Principle 1: begin a lesson with a short review of previous learning"
  - "Ausubel (1960) — The use of advance organizers in the learning and retention of meaningful verbal material"
  - "Marzano (2007) — The Art and Science of Teaching: activating prior knowledge and setting purpose"
  - "Agarwal et al. (2012) — Classroom-based retrieval practice improves learning with minimal lesson time"
  - "Hattie (2009) — Visible Learning: prior knowledge activation as foundational to new learning"
input_schema:
  required:
    - field: "todays_topic"
      type: "string"
      description: "What will be taught in this lesson"
    - field: "previous_learning"
      type: "string"
      description: "What was taught in the last lesson or recent lessons that connects"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "opening_time"
      type: "string"
      description: "Minutes available for the lesson opening (default: 10 minutes)"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: retention data, common gaps from last lesson"
    - field: "lesson_objectives"
      type: "string"
      description: "Specific learning objectives for today's lesson"
    - field: "assessment_data"
      type: "string"
      description: "From context engine: exit ticket data from last lesson"
output_schema:
  type: "object"
  fields:
    - field: "retrieval_starter"
      type: "object"
      description: "A retrieval practice activity reviewing previous learning"
    - field: "prior_knowledge_bridge"
      type: "string"
      description: "How to connect previous learning to today's new content"
    - field: "learning_intention"
      type: "string"
      description: "How to frame today's learning purpose"
    - field: "opening_script"
      type: "string"
      description: "A complete, timed script for the lesson opening"
chains_well_with:
  - "retrieval-practice-generator"
  - "explicit-instruction-sequence-builder"
  - "spaced-practice-scheduler"
  - "checking-for-understanding-protocol-designer"
teacher_time: "3 minutes"
tags: ["lesson-opening", "retrieval", "prior-knowledge", "advance-organiser", "lesson-planning"]
---

# Lesson Opening Designer

## What This Skill Does

Generates an evidence-based lesson opening comprising three components: a retrieval practice starter that reviews previous learning, a prior-knowledge bridge that connects what students already know to today's new content, and a learning intention framing that sets purpose without revealing all answers. The output is a complete timed script for the first 8–12 minutes of a lesson. AI is specifically valuable here because effective lesson openings must simultaneously serve three functions (retrieval, activation, framing) within a tight time constraint, and the retrieval questions must be carefully chosen to target the most important prior knowledge for today's lesson — not just "what we did last time" but specifically the knowledge that today's lesson will build on.

## Evidence Foundation

Rosenshine (2012) places daily review as Principle 1 of effective instruction: "The most effective teachers began their lessons with a five-to-eight-minute review of previously covered material." This serves two purposes — strengthening retention through retrieval practice and activating the prior knowledge schemas that new learning will attach to. Ausubel (1960) demonstrated that advance organisers — conceptual frameworks presented before new content — significantly improve learning by providing "ideational scaffolding" that helps learners organise incoming information. Marzano (2007) identified that connecting new content to prior knowledge is a foundational instructional strategy, but only when the connections are made explicit (not assumed). Agarwal et al. (2012) showed that brief retrieval practice at the start of lessons improves retention with minimal time cost — even 5 minutes of retrieval produces measurable benefits. Hattie (2009) identified prior knowledge as the single strongest predictor of new learning — what a student already knows determines what they can learn next.

## Input Schema

The teacher must provide:
- **Today's topic:** What will be taught today. *e.g. "Adding fractions with unlike denominators" / "The causes of World War I: the alliance system" / "Writing a balanced argument paragraph"*
- **Previous learning:** What was recently taught that connects. *e.g. "Last lesson: equivalent fractions. Last week: adding fractions with like denominators" / "Last lesson: the assassination of Archduke Franz Ferdinand"*
- **Student level:** Year group. *e.g. "Year 8"*

Optional (injected by context engine if available):
- **Opening time:** Minutes available (default 10)
- **Student profiles:** Retention data, gaps from prior lessons
- **Lesson objectives:** Specific learning objectives for today
- **Assessment data:** Exit ticket data from the last lesson

## Prompt

```
You are an expert in lesson design and the science of learning, with deep knowledge of Rosenshine's (2012) Principles of Instruction (Principle 1: daily review), Ausubel's (1960) advance organisers, and Agarwal et al.'s (2012) research on classroom retrieval practice. You understand that the lesson opening is the highest-leverage 10 minutes of any lesson — it determines whether students can access new content by activating the prior knowledge it depends on.

Your task is to design a lesson opening for:

**Today's topic:** {{todays_topic}}
**Previous learning:** {{previous_learning}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Opening time:** {{opening_time}} — if not provided, design for 10 minutes.
**Student profiles:** {{student_profiles}} — if not provided, assume a typical mixed-ability class where some students will have forgotten key content from the previous lesson.
**Lesson objectives:** {{lesson_objectives}} — if not provided, infer the learning objective from today's topic and frame it as a clear, student-facing intention.
**Assessment data:** {{assessment_data}} — if provided, use this to target retrieval questions toward the specific gaps identified. If not provided, target the prerequisite knowledge most critical for today's lesson.

Apply these evidence-based principles:

1. **Retrieval starter — not re-teaching (Rosenshine, 2012; Agarwal et al., 2012):**
   - The opening should require students to RETRIEVE previous learning from memory, not re-read or re-listen.
   - Questions should target the specific prior knowledge that today's lesson depends on — if today's lesson builds on equivalent fractions, retrieve equivalent fractions, not everything from last week.
   - Low stakes: no grades, no pressure. The purpose is strengthening memory and identifying gaps.
   - 5–6 minutes maximum for the retrieval activity.

2. **Prior knowledge bridge — make connections explicit (Ausubel, 1960; Marzano, 2007):**
   - After retrieval, explicitly connect previous learning to today's new content.
   - Do not assume students see the connection. State it: "You've just shown you can find equivalent fractions. Today we need that skill because..."
   - Use an advance organiser if appropriate: a brief conceptual framework that shows where today's content fits in the bigger picture.

3. **Learning intention — set purpose, not procedure (Hattie, 2009):**
   - Frame what students will learn, not what they will do. "By the end of this lesson, you will be able to add fractions with different denominators" (learning) is better than "Today we will complete a worksheet on adding fractions" (activity).
   - Keep it concise — one sentence.
   - Optionally include success criteria: "You'll know you've got it when you can..."

4. **Pace and energy:**
   - The opening sets the tone. Keep it brisk, purposeful, and interactive.
   - Students should be thinking within the first 60 seconds — no long teacher introductions.
   - Aim for the retrieval starter to begin as students enter the room (a "Do Now" displayed on the board).

Return your output in this exact format:

## Lesson Opening: [Today's Topic]

**For:** [Student level]
**Time:** [Opening duration]
**Builds on:** [Previous learning]

### On the Board as Students Enter (Do Now)
[The retrieval activity displayed on the board — students begin immediately on arrival]

### Retrieval Starter (X minutes)
[The retrieval questions, expected answers, and what to do if students struggle]

### Prior Knowledge Bridge (X minutes)
[Teacher script connecting retrieval to today's new content]

### Learning Intention (X minutes)
[How to frame today's learning — what students will be able to do, and how they'll know they've succeeded]

### Complete Timed Script
[The full opening as a single timed sequence the teacher can follow]

**Self-check before returning output:** Verify that (a) the retrieval starter requires genuine retrieval from memory, not re-reading, (b) retrieval questions target the specific prior knowledge today's lesson needs, (c) the bridge between prior and new learning is explicit, (d) the learning intention describes learning, not activity, and (e) the total timing fits within the stated opening time.
```

## Example Output

**Scenario:** *Today's topic: "Adding fractions with unlike denominators" / Previous learning: "Last lesson: finding equivalent fractions (multiplying numerator and denominator by the same number). Two lessons ago: adding fractions with like denominators." / Student level: "Year 7" / Opening time: "10 minutes"*

---

## Lesson Opening: Adding Fractions with Unlike Denominators

**For:** Year 7 Mathematics
**Time:** 10 minutes
**Builds on:** Equivalent fractions (last lesson), adding fractions with like denominators (2 lessons ago)

### On the Board as Students Enter (Do Now)

*Displayed on the board or projected before students arrive:*

**RETRIEVAL CHALLENGE — no notes, no looking back. Do what you can from memory.**

1. Find an equivalent fraction for 3/4 with a denominator of 12.
2. Find an equivalent fraction for 2/5 with a denominator of 15.
3. Calculate: 3/8 + 2/8 = ?
4. Calculate: 5/12 + 4/12 = ?
5. **Think question:** Why can you add the fractions in Q3 and Q4 easily? What makes them straightforward?

### Retrieval Starter (5 minutes)

**Questions 1–2** target equivalent fractions — the critical prerequisite for today's lesson. If students can't find equivalent fractions fluently, they can't add fractions with unlike denominators.

**Questions 3–4** target adding fractions with like denominators — the skill today's lesson extends. Students need to remember that when denominators are the same, you add numerators and keep the denominator.

**Question 5** is a metacognitive bridge question — it asks students to articulate *why* same-denominator addition is easy, which sets up the challenge for today: what do you do when the denominators are NOT the same?

**Expected answers:**
1. 9/12 (multiply both by 3)
2. 6/15 (multiply both by 3)
3. 5/8
4. 9/12 (which simplifies to 3/4, but accept 9/12)
5. "Because the denominators are the same, so you just add the top numbers."

**If students struggle with Q1–2 (equivalent fractions):**
Do not proceed to the new content. Spend 3 minutes reviewing: "What do we multiply the numerator AND denominator by to make an equivalent fraction?" Use mini-whiteboards for 2 more practice examples. Then bridge to the new lesson. Today's content will not make sense if equivalent fractions aren't secure.

**If students struggle with Q3–4 (like-denominator addition):**
Quick recap: "When the denominators are the same, we're adding pieces that are the same size. 3 eighths + 2 eighths = 5 eighths, just like 3 apples + 2 apples = 5 apples." Two more quick examples, then proceed.

### Prior Knowledge Bridge (2 minutes)

"Hands up if you got Q5 right — you said something like 'the denominators are the same.' Exactly. When the denominators match, addition is straightforward because the pieces are the same size. Three eighths plus two eighths — we're adding pieces of the same size.

But what if I asked you: what is 1/3 + 1/4? The pieces are DIFFERENT sizes — a third is not the same as a quarter. You can't just add 1 + 1 and get 2/7 — that doesn't work. [Write 1/3 + 1/4 ≠ 2/7 on the board.] So what do we need to do first?

[Pause. Let students think. Some will see it.]

We need to make the denominators the same — which means we need EQUIVALENT FRACTIONS. That skill you just practised in Q1 and Q2? That's exactly what we need now. Today, we're combining two skills you already have — finding equivalent fractions AND adding fractions — to solve a new type of problem."

### Learning Intention (1 minute)

"By the end of this lesson, you will be able to add two fractions that have different denominators by finding a common denominator first.

You'll know you've got it when you can solve a problem like 2/3 + 3/5 without help, and explain to someone else why you need a common denominator.

Let's go."

### Complete Timed Script

| Time | What happens |
|------|-------------|
| 0:00 | Students enter. Retrieval challenge is on the board. Students begin immediately — no waiting, no register pause. Teacher greets at the door and directs: "Starter is on the board. Begin." |
| 0:00–5:00 | Students work on Q1–5 in silence (retrieval conditions — no notes, no discussion). Teacher circulates, scanning for Q1–2 accuracy. Identifies 2–3 students who are struggling with equivalent fractions. |
| 5:00–5:30 | "Pens down. Let's check." Quick-fire answers: Q1: "9/12 — show me on whiteboards." Q2: "6/15." Q3: "5/8." Q4: "9/12." 30-second scan. |
| 5:30–6:00 | "Q5 — why were Q3 and Q4 easy?" Cold-call one student. Listen for "the denominators are the same." |
| 6:00–8:00 | Prior knowledge bridge (script above). Write 1/3 + 1/4 on the board. Let students see the problem. Connect equivalent fractions to the new challenge. |
| 8:00–8:30 | State learning intention. Write it on the board. |
| 8:30–10:00 | Transition to I Do phase: "Watch me solve 1/3 + 1/4. I'm going to think out loud so you can follow my reasoning." |

---

## Known Limitations

1. **The retrieval starter only works if students have been taught the prerequisite content.** If students were absent for the equivalent fractions lesson, or if the prerequisite wasn't taught effectively, the retrieval starter will surface gaps that need addressing before today's content. This is a feature (diagnostic information), not a bug — but it may require the teacher to spend more time on review than planned, compressing the main lesson.

2. **"Do Now" starters require consistent classroom routines.** If students are not trained to begin working immediately on entry, the first 2–3 minutes are lost to settling, instructions, and reminders. The lesson opening design assumes an established routine. Building that routine is a classroom management task, not a lesson design task.

3. **The prior knowledge bridge is scripted for this specific content connection.** If the teacher has not followed the assumed teaching sequence (equivalent fractions → like-denominator addition → unlike-denominator addition), the bridge won't land. Teachers must verify that the "previous learning" field accurately reflects what was taught, not what was planned.

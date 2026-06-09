---
# AGENT SKILLS STANDARD FIELDS (v2)
name: lesson-study-cycle-designer
description: "Design a complete lesson study cycle from research question through collaborative planning to research lesson. Use when planning jugyou kenkyuu or collaborative teacher inquiry into practice."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "professional-learning/lesson-study-cycle-designer"
skill_name: "Lesson Study Cycle Designer"
domain: "professional-learning"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Stigler & Hiebert (1999) — The Teaching Gap: best ideas from the world's teachers for improving education in the classroom"
  - "Lewis, Perry & Murata (2006) — How should research contribute to instructional improvement? The case of lesson study"
  - "Dudley (2014) — Lesson Study: a handbook"
  - "Takahashi & McDougal (2016) — Collaborative lesson research: maximizing the impact of lesson study"
  - "Fernandez & Yoshida (2004) — Lesson Study: a Japanese approach to improving mathematics teaching and learning"
input_schema:
  required:
    - field: "teaching_challenge"
      type: "string"
      description: "The specific teaching problem or student learning difficulty the lesson study will investigate"
    - field: "subject_and_topic"
      type: "string"
      description: "The subject, topic, and year group for the research lesson"
    - field: "team_composition"
      type: "string"
      description: "Who is in the lesson study group — number of teachers, experience levels, subjects"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group of the students"
    - field: "available_time"
      type: "string"
      description: "How much time the team has — number of meetings, release time available"
    - field: "previous_lesson_study"
      type: "string"
      description: "Whether the team has done lesson study before"
    - field: "school_context"
      type: "string"
      description: "Relevant features of the school — phase, demographics, improvement priorities"
    - field: "case_students"
      type: "string"
      description: "The 3 'case students' who will be the focus of observation — their profiles"
output_schema:
  type: "object"
  fields:
    - field: "research_theme"
      type: "string"
      description: "The overarching question the lesson study investigates"
    - field: "cycle_plan"
      type: "object"
      description: "The complete lesson study cycle — planning, teaching, observing, reflecting, revising"
    - field: "research_lesson_plan"
      type: "object"
      description: "A detailed lesson plan designed for collaborative observation"
    - field: "observation_protocol"
      type: "object"
      description: "What observers should watch for, how to record observations, and how to structure the post-lesson discussion"
chains_well_with:
  - "instructional-coaching-conversation-guide"
  - "lesson-observation-protocol-designer"
  - "reflective-practice-prompt-generator"
  - "teacher-inquiry-cycle-designer"
  - "pedagogical-content-knowledge-developer"
teacher_time: "5 minutes"
tags: ["lesson-study", "jugyou-kenkyuu", "collaborative-planning", "research-lesson", "professional-learning"]
---

# Lesson Study Cycle Designer

## What This Skill Does

Designs a complete lesson study cycle — the structured, collaborative process originated in Japan (jugyō kenkyū) where a team of teachers jointly plan a "research lesson," one teacher teaches it while others observe student learning (not teacher performance), and the team analyses what students actually learned and why. The critical principle is that lesson study is research INTO teaching, not evaluation OF teachers — the lesson belongs to the group, the focus is on student learning (not teacher behaviour), and the purpose is to develop shared professional knowledge about how students learn specific content. The output includes a research theme, a cycle plan with meeting agendas, a research lesson plan designed for collaborative observation, and an observation protocol focused on case students. AI is specifically valuable here because designing an effective lesson study cycle requires understanding both the Japanese model (with its emphasis on kyōzai kenkyū — deep study of the subject matter and curriculum) and the practical constraints of non-Japanese school contexts where release time, team stability, and lesson study experience may be limited.

## Evidence Foundation

Stigler & Hiebert (1999) introduced lesson study to Western audiences through "The Teaching Gap," showing that Japanese teachers continuously improve their practice through collaborative cycles of planning, observing, and analysing research lessons. They argued that the power of lesson study lies not in individual lessons but in the collaborative process: teachers develop shared professional knowledge about how students learn, which accumulates over years and is passed to new teachers. Lewis, Perry & Murata (2006) identified four pathways through which lesson study improves instruction: increased knowledge of subject matter, increased knowledge of instruction, increased ability to observe students, and stronger collegial networks. Dudley (2014) adapted lesson study for UK schools, introducing the concept of "case students" — three carefully chosen students (one high-attaining, one middle, one lower-attaining) who become the focus of observation, making student learning visible and manageable to track. Takahashi & McDougal (2016) emphasised that the most important (and most often skipped) phase of lesson study is kyōzai kenkyū — the deep study of the subject matter, curriculum, and existing research that precedes lesson planning. Without this, lesson study becomes collaborative planning without the research foundation. Fernandez & Yoshida (2004) documented the complete Japanese lesson study process, showing that a single cycle typically takes 3–5 meetings over several weeks, with the research lesson itself being just one component of a much deeper process.

## Input Schema

The teacher must provide:
- **Teaching challenge:** The problem to investigate. *e.g. "Students can calculate the area of simple shapes but can't apply this to compound shapes — they don't see how to decompose a compound shape into simpler ones" / "Students can identify language features in a text but can't explain their effect on the reader" / "Year 7 students struggle to write developed explanations in Science — they make a claim but don't support it with evidence or reasoning"*
- **Subject and topic:** What the research lesson will cover. *e.g. "Year 8 Mathematics — area of compound shapes" / "Year 9 English — analysing language in poetry" / "Year 7 Science — writing CER (Claim-Evidence-Reasoning) explanations"*
- **Team composition:** Who is involved. *e.g. "3 maths teachers, mixed experience — one NQT, one 5 years experience, one head of department" / "4 English teachers from the same department, all experienced"*

Optional (injected by context engine if available):
- **Student level:** Year group
- **Available time:** Meetings and release time
- **Previous lesson study:** Team's experience with the process
- **School context:** Phase, demographics, priorities
- **Case students:** The 3 focus students

## Prompt

```
You are an expert in lesson study (jugyō kenkyū), with deep knowledge of Stigler & Hiebert's (1999) analysis of Japanese lesson study, Dudley's (2014) UK adaptation, Lewis, Perry & Murata's (2006) pathways of improvement, and Takahashi & McDougal's (2016) emphasis on kyōzai kenkyū (deep study of subject matter and curriculum). You understand that lesson study is fundamentally different from lesson observation: it is collaborative research INTO teaching and learning, not evaluation OF a teacher.

CRITICAL PRINCIPLES:
- The lesson belongs to the GROUP, not the individual who teaches it. The research lesson is "our lesson," not "my lesson being watched."
- Observers watch STUDENTS, not the teacher. The question is "What did students learn and how?" not "How well did the teacher perform?"
- The most important phase is the pre-lesson study of subject matter and curriculum (kyōzai kenkyū), not the lesson itself.
- Case students (Dudley, 2014) make observation manageable: observers track 3 specific students to understand how different learners experience the lesson.

Your task is to design a lesson study cycle for:

**Teaching challenge:** {{teaching_challenge}}
**Subject and topic:** {{subject_and_topic}}
**Team composition:** {{team_composition}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, infer from the subject and topic.
**Available time:** {{available_time}} — if not provided, design for 4 meetings (realistic minimum) with one observation lesson.
**Previous lesson study:** {{previous_lesson_study}} — if not provided, assume the team is new to lesson study and include orientation.
**School context:** {{school_context}} — if not provided, design for general school application.
**Case students:** {{case_students}} — if not provided, guide the team in selecting their own case students.

Design the complete cycle:

1. **Meeting 1 — Research and goal-setting (kyōzai kenkyū):**
   - Define the research theme: what question about student learning are we investigating?
   - Study the subject matter: what does the curriculum say? What does the research say about how students learn this content? What are the known misconceptions?
   - Study existing approaches: how is this typically taught? What has worked and what hasn't?
   - Select case students: one high-attaining, one middle, one who typically struggles with this content. What do we predict each will find easy/difficult?

2. **Meeting 2 — Collaborative lesson planning:**
   - Design the research lesson collaboratively — every team member contributes.
   - The lesson plan must be unusually detailed: anticipated student responses at each stage, what the teacher will do if students respond in different ways, where the key learning moments are.
   - Design the observation schedule: who watches which case student? What are they looking for?

3. **Meeting 3 — The research lesson and post-lesson discussion:**
   - One team member teaches; others observe.
   - Observers sit near their assigned case student(s) and record: what the student does, says, writes, and appears to be thinking.
   - Post-lesson discussion (immediately after, 45–60 minutes): what did we learn about how students learn this content? Not "what could the teacher have done better" but "what did we observe about student learning?"

4. **Meeting 4 — Analysis and knowledge-building:**
   - What did we learn from this cycle?
   - What would we change if we taught this lesson again?
   - What implications does this have for our broader teaching of this topic/subject?
   - How do we share what we learned with colleagues who weren't in the team?

Return your output in this exact format:

## Lesson Study Cycle: [Research Theme]

**Teaching challenge:** [The problem being investigated]
**Subject and topic:** [What the research lesson covers]
**Team:** [Who is involved]

### Research Theme

[The overarching question the lesson study investigates — framed as a question about student learning]

### Cycle Plan

For each meeting:
**Meeting [N]: [Purpose] — [Suggested timing]**
- **Agenda:** [What the team does in this meeting]
- **Preparation needed:** [What team members should do before the meeting]
- **Key output:** [What the meeting produces]

### Research Lesson Plan

[A detailed lesson plan designed for collaborative observation — including anticipated student responses and observation focus points]

### Observation Protocol

**Case Student A (higher-attaining):** [What to watch for]
**Case Student B (middle-attaining):** [What to watch for]
**Case Student C (typically struggles):** [What to watch for]

**Recording format:** [How observers should record what they see]

### Post-Lesson Discussion Guide

[Structured questions for the post-lesson discussion — focused on student learning, not teacher evaluation]

**Self-check before returning output:** Verify that (a) the focus is on student learning, not teacher performance, (b) kyōzai kenkyū is included, (c) case students are specified, (d) the research lesson plan includes anticipated student responses, (e) the observation protocol is student-focused, and (f) the post-lesson discussion guide avoids evaluative language about the teacher.
```

## Example Output

**Scenario:** *Teaching challenge: "Year 8 students can calculate the area of simple shapes (rectangles, triangles) but struggle with compound shapes. They don't see how to decompose a compound shape into simpler shapes — they try to use a single formula or just guess." / Subject and topic: "Year 8 Mathematics — area of compound shapes" / Team composition: "3 maths teachers — one NQT (first year), one experienced teacher (8 years), one head of department (15 years). None have done lesson study before." / Available time: "4 one-hour meetings over 3 weeks, plus the research lesson itself"*

---

## Lesson Study Cycle: How Do Students Learn to Decompose Compound Shapes?

**Teaching challenge:** Students can find the area of simple shapes but don't decompose compound shapes into components
**Subject and topic:** Year 8 Mathematics — area of compound shapes
**Team:** 3 maths teachers (NQT, experienced, HoD), new to lesson study

### Research Theme

**How do Year 8 students develop the ability to decompose compound shapes into simpler shapes for area calculations — and what prevents them from doing this independently?**

Sub-questions:
- At what point in the lesson do students "see" the decomposition? What triggers this insight?
- What do students who CAN'T decompose the shape do instead? What alternative strategies do they attempt?
- Does showing the decomposition lines help students learn the skill, or does it bypass the learning?

### Cycle Plan

**Meeting 1: Research and Goal-Setting — Week 1, 1 hour**
- **Agenda:**
  1. Orientation to lesson study (15 min): The HoD explains the process. Key messages: the lesson belongs to us all; we observe students, not the teacher; this is research, not evaluation. Distribute Dudley's (2014) one-page summary.
  2. Kyōzai kenkyū — study the content (25 min): As a team, work through 5 compound shape problems at increasing difficulty. Notice: what mathematical knowledge is needed? Where do WE have to think carefully? The team should experience the mathematics as learners before designing the lesson. Review the Year 8 scheme of work: what have students been taught before this lesson? What comes after?
  3. Discuss known difficulties (10 min): What do we know about how students struggle with this? Pool experience: "What do students typically do when they see a compound shape?" Document the known misconceptions and difficulties.
  4. Select case students (10 min): From the class that will be taught, identify three students: Student A (confident with area, likely to find decomposition accessible), Student B (competent with simple shapes, represents the typical student), Student C (struggles with area of simple shapes — may find compound shapes overwhelming). Write a brief profile for each: what we predict they will find easy/difficult.
- **Preparation needed:** Each team member brings 2–3 compound shape problems from their teaching resources. The teacher who will teach the research lesson provides a class list with brief attainment data.
- **Key output:** Research theme agreed, case students selected, known difficulties documented.

**Meeting 2: Collaborative Lesson Planning — Week 1 or 2, 1 hour**
- **Agenda:**
  1. Review research theme and case students (5 min).
  2. Design the research lesson collaboratively (45 min): Structure the lesson phase by phase. For each phase, the team must specify: what the teacher does, what students do, what we anticipate each case student will do, and what the teacher does if the anticipated responses occur. The lesson plan should be more detailed than a normal lesson plan — because it's designed for observation, every moment matters.
  3. Design the observation schedule (10 min): Assign each observer to one case student. Create a simple recording sheet: a table with three columns — Time, What the student does/says, What this suggests about their understanding.
- **Preparation needed:** The teacher who will teach brings a draft lesson structure. Other team members bring ideas for tasks and resources.
- **Key output:** Complete research lesson plan with anticipated responses. Observation schedule assigned.

**Meeting 3: Research Lesson and Post-Lesson Discussion — Week 2 or 3, lesson time + 1 hour**
- **The research lesson (50 minutes):** One teacher teaches (decided during Meeting 2 — typically a volunteer, not the most/least experienced). The other two observe. Each observer sits near their assigned case student with the recording sheet. Observers do NOT help students, intervene, or interact with the class. They watch and record.
- **Post-lesson discussion (immediately after, 1 hour):**
  1. The teacher who taught speaks first (5 min): "How did I feel it went? What did I notice?" This honours the teacher and allows them to process before hearing feedback.
  2. Each observer reports on their case student (15 min total): "Here is what Student A/B/C did at each phase. Here is what I think this tells us about their learning." Evidence-based — what was observed, not what was inferred.
  3. Discussion of the research theme (25 min): "What did we learn about how students learn to decompose compound shapes? Did the lesson succeed in developing this skill? What surprised us? What would we change and why?"
  4. Implications (15 min): "What does this mean for how we teach this topic in future? What have we learned that applies beyond this one lesson?"
- **Key output:** Observation notes, post-lesson discussion notes, list of implications.

**Meeting 4: Analysis and Knowledge-Building — Week 3, 1 hour**
- **Agenda:**
  1. Review post-lesson discussion notes (10 min): What did we conclude?
  2. Revise the lesson (20 min): If we taught this lesson again, what would we change? Write a revised lesson plan — this is not about the original teacher "doing better," but about the team's collective understanding improving the lesson.
  3. Extract transferable knowledge (15 min): What did we learn about how students learn compound shape area that applies to other topics? (E.g., "Students need to be given compound shapes WITHOUT decomposition lines first — showing the lines too early bypasses the thinking. This principle probably applies to other multi-step problems.")
  4. Plan for sharing (15 min): How do we share what we learned with colleagues who weren't in the team? A brief presentation at a department meeting? A one-page summary? Teaching the revised lesson while other teachers observe?
- **Key output:** Revised lesson plan, transferable insights, sharing plan.

### Research Lesson Plan

**Lesson: Decomposing Compound Shapes for Area Calculation**
**Duration:** 50 minutes

**Phase 1 — Activating prior knowledge (8 minutes):**
Display three simple shapes (rectangle, triangle, parallelogram) with dimensions. Students calculate the area of each on mini-whiteboards. "3, 2, 1, show me."
- *Anticipated: Student A gets all three quickly. Student B gets rectangle and triangle, may hesitate on parallelogram. Student C may struggle with the triangle formula.*
- *Observation focus: Does Student C remember the area formulas? If not, the compound shape task will be inaccessible — the teacher may need to provide a formula reference sheet.*

**Phase 2 — The problem without instruction (12 minutes):**
Display a compound L-shape (dimensions labelled) with NO decomposition lines. "Find the area of this shape. You can use any method you like. Work on your own for 3 minutes, then compare with your partner."
- *Anticipated: Student A may see the decomposition immediately or after brief thought. Student B will likely try to find a single formula, realise it doesn't work, and either stall or try splitting the shape. Student C may be overwhelmed and not start.*
- *THIS IS THE KEY OBSERVATION MOMENT. What strategies do students attempt BEFORE being shown the decomposition? Document exactly what each case student does during these 3 minutes.*
- *Teacher move: Do NOT show the decomposition yet. Circulate silently. If Student C is completely stuck after 2 minutes, say: "Could you split this shape into shapes you already know?" — this is a nudge, not an answer.*

**Phase 3 — Sharing strategies (8 minutes):**
"Who found a way to work this out? Come and show us." Select students to share — prioritise students who decomposed the shape differently (horizontal split vs. vertical split vs. subtraction method). If no one decomposed it, the teacher demonstrates: "What if I draw a line here? What shapes do I get?"
- *Anticipated: Multiple decomposition strategies will emerge. Discuss: do they all give the same answer? Which is easiest? Why?*
- *Observation focus: Does Student B's understanding change when they see a peer's strategy? Does Student C understand the strategy when it's shown, or do they just copy the procedure?*

**Phase 4 — Guided practice with new shapes (12 minutes):**
Three compound shapes, increasing difficulty. Students work in pairs. For each shape: first, draw the decomposition lines (don't calculate yet). Teacher circulates to check decomposition before students calculate.
- *Anticipated: Student A will find decomposition straightforward. Student B will manage shape 1 and 2 but may struggle with shape 3 (which can be decomposed in multiple ways). Student C may be able to copy the decomposition approach for shape 1 but struggle to transfer to shape 2.*
- *Observation focus: Is Student C decomposing independently or copying their partner? This is the critical evidence for the research theme — can this student SEE the decomposition, or are they following a procedure they don't understand?*

**Phase 5 — Independent application (8 minutes):**
One final compound shape, done independently. No discussion, no partner help. This is the diagnostic: can each student independently decompose and calculate?
- *Observation focus: What does each case student produce independently? Compare this to what they produced in Phase 2 (before instruction) — what has changed?*

**Phase 6 — Reflection (2 minutes):**
"Write one sentence: what is the trick to finding the area of any shape, even a complicated one?"
- *Anticipated: Strong responses will say something like "Split it into shapes you already know." Weaker responses will say "Use the formula" (which suggests they haven't grasped decomposition as a strategy).*

### Observation Protocol

**Case Student A (higher-attaining):** Watch for: how quickly they see the decomposition in Phase 2. Do they use decomposition or a different strategy (e.g., enclosing the shape in a rectangle and subtracting)? During Phase 4, do they find MULTIPLE decompositions? In Phase 5, do they decompose fluently?

**Case Student B (middle-attaining):** Watch for: what they try FIRST in Phase 2 (the pre-instruction attempt). Do they stall? Try a single formula? Guess? During Phase 3, what causes the "aha" moment — seeing a peer's method or the teacher's demonstration? In Phase 4, can they transfer to new shapes, or do they only copy the method from Phase 3?

**Case Student C (typically struggles):** Watch for: can they access the task at all in Phase 2? If not, what do they do (wait, copy, guess, ask for help)? After instruction in Phase 3, do they understand the decomposition or just follow the procedure? In Phase 5, can they do it independently? This student's experience will tell us the most about whether the lesson succeeded.

**Recording format:**
| Time/Phase | What the student does/says/writes | What this suggests about their understanding |
|---|---|---|

### Post-Lesson Discussion Guide

**Round 1 — The teacher's voice (5 minutes):**
"Before we hear from the observers, [teacher's name]: how did you feel the lesson went? What did you notice?"

**Round 2 — Case student reports (15 minutes):**
"Observer 1: tell us about Student A — what did you observe at each phase?"
"Observer 2: tell us about Student B..."
"Observer 3: tell us about Student C..."
(Evidence only — what was seen and heard, not judgements about the teacher.)

**Round 3 — Research theme discussion (25 minutes):**
- "At what point in the lesson did students 'see' the decomposition? What triggered this?"
- "What did students who couldn't decompose the shape do instead? What alternative strategies did they try?"
- "Did the teacher's demonstration in Phase 3 help Student C understand the decomposition, or did they just copy the procedure?"
- "Was Phase 2 (the problem without instruction) valuable? Did struggling before being shown the method help or hinder learning?"
- "What surprised us?"

**Round 4 — Implications (15 minutes):**
- "If we taught this lesson again, what ONE thing would we change and why?"
- "What have we learned about how students learn to decompose shapes that applies to our broader teaching?"
- "What questions do we still have?"

**IMPORTANT: Discussion norms.** At no point should the discussion become "You should have..." or "It would have been better if you had..." directed at the teacher. All comments are about THE LESSON (which belongs to the group) and STUDENT LEARNING (which is the research focus). The sentence stems to use: "I noticed that Student B..." / "The lesson seemed to..." / "Next time, WE could try..."

---

## Known Limitations

1. **Lesson study requires protected time.** Four one-hour meetings plus observation time is a significant investment. In schools without dedicated professional learning time, lesson study is extremely difficult to sustain. The cycle above represents a minimum — Japanese lesson study cycles often span months. Schools must allocate time explicitly, not expect teachers to find it.

2. **Lesson study requires a culture of trust.** Being observed by colleagues is vulnerable. If the school culture is evaluative (observations are judgements, not learning), teachers will not feel safe enough for genuine lesson study. The facilitator (typically the most experienced team member) must actively protect the discussion norms: research, not evaluation.

3. **Lesson study builds knowledge slowly.** One cycle produces modest insights. The power of lesson study is cumulative — repeated cycles over years build deep professional knowledge about how students learn. Schools should commit to lesson study as an ongoing practice, not a one-off event.

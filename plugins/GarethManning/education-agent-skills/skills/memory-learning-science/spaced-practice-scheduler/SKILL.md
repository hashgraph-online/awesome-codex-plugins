---
# AGENT SKILLS STANDARD FIELDS (v2)
name: spaced-practice-scheduler
description: "Design a spaced retrieval schedule for any topic list and timeline. Use when planning units, term sequences, or revision programmes."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "memory-learning-science/spaced-practice-scheduler"
skill_name: "Spaced Practice Schedule Builder"
domain: "memory-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Ebbinghaus (1885/1913) — The forgetting curve: exponential decay of memory without review"
  - "Cepeda et al. (2006) — Meta-analysis of 254 studies on distributed practice: optimal spacing depends on retention interval"
  - "Kornell & Bjork (2008) — Spacing and interleaving effects on learning"
  - "Carpenter et al. (2012) — Using spacing to enhance diverse forms of learning"
  - "Dunlosky et al. (2013) — Distributed practice rated high-utility learning strategy"
input_schema:
  required:
    - field: "topics"
      type: "array"
      description: "List of topics or concepts to be spaced across the schedule"
    - field: "timeline"
      type: "string"
      description: "Available teaching period (e.g. '6-week half-term' or 'Term 2: Jan 15 – Mar 28')"
    - field: "lessons_per_week"
      type: "integer"
      description: "Number of lessons per week for this subject"
  optional:
    - field: "assessment_date"
      type: "string"
      description: "Date of summative assessment, if known — affects final spacing intervals"
    - field: "topic_difficulty"
      type: "array"
      description: "Teacher's estimate of relative difficulty for each topic (high/medium/low)"
    - field: "curriculum_sequence"
      type: "array"
      description: "From context engine: mandated teaching order or prerequisite dependencies"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: class-level retention data from prior assessments"
output_schema:
  type: "object"
  fields:
    - field: "schedule"
      type: "array"
      description: "Week-by-week schedule showing new teaching and spaced review slots"
    - field: "spacing_rationale"
      type: "string"
      description: "Explanation of why topics are spaced at these intervals"
    - field: "review_activity_suggestions"
      type: "array"
      description: "Brief retrieval activities for each review slot"
    - field: "teacher_guidance"
      type: "string"
      description: "How to implement the schedule and adjust based on student response"
chains_well_with:
  - "retrieval-practice-generator"
  - "interleaving-unit-planner"
  - "formative-assessment-technique-selector"
  - "lesson-opening-designer"
teacher_time: "5 minutes"
tags: ["spacing", "memory", "planning", "forgetting-curve", "distributed-practice"]
---

# Spaced Practice Schedule Builder

## What This Skill Does

Takes a list of topics and a teaching timeline and generates an optimised review schedule that spaces retrieval opportunities at expanding intervals to combat the forgetting curve. The output is a week-by-week plan showing when to introduce new content and when to revisit previous topics, with specific activity suggestions for each review slot. AI is specifically valuable here because calculating optimal spacing intervals across multiple topics while respecting prerequisite dependencies and timetable constraints is genuinely complex — most teachers default to blocked practice (finish topic A, move to topic B, never return) because the cognitive load of planning spaced schedules manually is too high.

## Evidence Foundation

Ebbinghaus (1885/1913) first demonstrated that memory follows an exponential decay curve — without review, approximately 70% of new learning is lost within 24 hours. Cepeda et al. (2006) conducted a meta-analysis of 254 studies and established that the optimal gap between study sessions depends on the desired retention interval: roughly 10–20% of the retention interval is optimal (e.g., if you need students to remember something for 30 days, space reviews approximately 3–6 days apart). Carpenter et al. (2012) extended these findings to diverse classroom learning contexts, showing that spaced practice benefits declarative knowledge, procedural skills, and problem-solving. Kornell & Bjork (2008) demonstrated that spacing feels less effective to learners — students rate massed practice as more effective even when spaced practice produces better retention. This means teachers should expect students to initially prefer (and request) the less effective approach. Dunlosky et al. (2013) rated distributed practice as one of only two "high utility" strategies in their comprehensive review.

## Input Schema

The teacher must provide:
- **Topics:** List of topics to space. *e.g. ["Cell structure", "Cell transport", "Cell division", "Enzymes", "Biological molecules"]*
- **Timeline:** The available teaching period. *e.g. "8-week term, starting 3 February"*
- **Lessons per week:** How many lessons per week. *e.g. 3*

Optional (injected by context engine if available):
- **Assessment date:** When the summative assessment falls — this anchors the final review cycle
- **Topic difficulty:** Teacher estimate of relative difficulty per topic, so harder topics get more review slots
- **Curriculum sequence:** Mandated order or prerequisite constraints
- **Student profiles:** Class-level data on retention from prior assessments

## Prompt

```
You are an expert in the cognitive psychology of memory, specialising in the spacing effect and distributed practice. You have deep knowledge of Cepeda et al.'s (2006) meta-analysis on optimal inter-study intervals, Ebbinghaus's forgetting curve, and Carpenter et al.'s (2012) work on spacing in educational contexts.

Your task is to generate a spaced practice schedule for the following:

**Topics:** {{topics}}
**Timeline:** {{timeline}}
**Lessons per week:** {{lessons_per_week}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Assessment date:** {{assessment_date}} — if provided, ensure all topics have at least one retrieval opportunity in the final week before the assessment. If not provided, design the schedule for long-term retention without a specific deadline.
**Topic difficulty ratings:** {{topic_difficulty}} — if provided, allocate more review slots to high-difficulty topics. If not provided, treat all topics as roughly equal difficulty unless your subject knowledge suggests otherwise.
**Required teaching order:** {{curriculum_sequence}} — if provided, respect prerequisite dependencies. If not provided, assume topics can be taught in the order listed.
**Class retention data:** {{student_profiles}} — if provided, weight additional review toward topics where prior data shows weak retention. If not provided, use standard expanding spacing intervals.

Apply these evidence-based principles:

1. **Expanding intervals:** Space review at increasing intervals — first review at 1–3 days after initial teaching, second review at 1–2 weeks, third review at 3–4 weeks. This follows Cepeda et al.'s (2006) finding that optimal spacing expands as retention strengthens.

2. **Review through retrieval, not re-teaching:** Each review slot should involve a retrieval activity (quiz, brain dump, diagram from memory), NOT re-teaching or re-reading. The learning happens through the retrieval attempt (Roediger & Butler, 2011).

3. **New teaching to review ratio:** In any given lesson, approximately 10–15 minutes should be available for retrieval of previously taught material (typically the lesson opening). New content occupies the main teaching portion.

4. **Interleaving where appropriate:** When topics share a domain, mix review questions from different topics in the same retrieval session. This produces an interleaving effect (Rohrer et al., 2015) that improves discrimination between similar concepts.

5. **Difficulty-weighted spacing:** Topics rated as more difficult should receive more frequent review slots. Topics with strong initial encoding may need fewer.

6. **Pre-assessment consolidation:** If an assessment date is provided, ensure every topic has at least one retrieval opportunity in the 5 days before the assessment — but do NOT cram all review into the final week. That defeats the purpose of spacing.

Return your output in this exact format:

## Spaced Practice Schedule: [Subject/Context]

**Timeline:** [Start to end]
**Topics:** [List]
**Total lessons:** [Number]

### Week-by-Week Schedule

For each week, provide:
| Lesson | New Content | Spaced Review (10–15 min starter) |
|--------|------------|-----------------------------------|
| [Day]  | [Topic]    | [Which previous topic(s) to retrieve + brief activity type] |

### Spacing Rationale

Explain in 3–4 sentences why the topics are spaced at these specific intervals, referencing the evidence base.

### Review Activity Suggestions

For each review slot, suggest a specific brief retrieval activity (not "review Topic X" but "5 free-recall questions on cell transport mechanisms" or "label a blank diagram of cell structure from memory").

### Teacher Guidance

- How long each review starter should take
- What to do when review reveals gaps (re-teach briefly vs. schedule additional retrieval)
- How to explain the purpose to students (they will feel like spaced practice is less effective — this is normal)

**Self-check before returning output:** Verify that (a) no topic goes more than 3 weeks without a retrieval opportunity, (b) expanding intervals are maintained, (c) harder topics get more review slots, (d) the schedule is realistic given the lessons-per-week constraint, and (e) review activities involve retrieval, not re-reading or re-teaching.
```

## Example Output

**Scenario:** *Topics: ["Tectonic plates", "Earthquakes", "Volcanoes", "Weathering & erosion", "River landscapes"] / Timeline: "6-week half-term, 5 lessons per week" / Lessons per week: 5 / Assessment date: "End of Week 6"*

---

## Spaced Practice Schedule: Year 8 Geography — Physical Landscapes

**Timeline:** Weeks 1–6 (30 lessons)
**Topics:** Tectonic plates, Earthquakes, Volcanoes, Weathering & erosion, River landscapes
**Total lessons:** 30

### Week-by-Week Schedule

| Week | Lesson | New Content | Spaced Review Starter (10–15 min) |
|------|--------|-------------|-----------------------------------|
| 1 | 1 | Tectonic plates — structure of the Earth | — (baseline assessment: what do students already know?) |
| 1 | 2 | Tectonic plates — plate boundaries | Retrieve: sketch Earth's layers from memory, label and annotate |
| 1 | 3 | Tectonic plates — convection currents | Retrieve: name 3 plate boundary types and one feature of each |
| 1 | 4 | Earthquakes — causes and focus/epicentre | Retrieve: explain in 3 sentences how convection currents drive plate movement |
| 1 | 5 | Earthquakes — measuring and effects | Retrieve: draw and label a diagram showing focus, epicentre, and seismic waves |
| 2 | 1 | Earthquakes — case studies | Retrieve: **Tectonic plates** — 5 free-recall questions on plate boundaries (first spaced review, ~7 days) |
| 2 | 2 | Volcanoes — formation and types | Retrieve: compare two earthquake case studies from memory — causes, effects, responses |
| 2 | 3 | Volcanoes — eruption processes | Mixed retrieve: 3 Qs on **tectonic plates** + 2 Qs on **earthquake measurement** |
| 2 | 4 | Volcanoes — case studies | Retrieve: draw a cross-section of a composite volcano from memory, label 5 features |
| 2 | 5 | Volcanoes — living with volcanic risk | Retrieve: **Earthquakes** full topic — "Write everything you know about earthquakes in 5 minutes" (brain dump) |
| 3 | 1 | Weathering & erosion — types of weathering | Mixed retrieve: 4 Qs interleaving **tectonic plates** and **volcanoes** (2 weeks since tectonics — expanding interval) |
| 3 | 2 | Weathering & erosion — erosion processes | Retrieve: name and explain 3 types of weathering from memory |
| 3 | 3 | Weathering & erosion — erosion vs weathering | Retrieve: **Volcanoes** — blank diagram: label volcanic features and explain formation |
| 3 | 4 | River landscapes — long profile and processes | Mixed retrieve: distinguish weathering from erosion + 2 Qs on **earthquake effects** |
| 3 | 5 | River landscapes — upper course features | Retrieve: **Weathering & erosion** — explain 4 types of river erosion from memory |
| 4 | 1 | River landscapes — middle course features | Mixed retrieve: 2 Qs **tectonic plates** + 2 Qs **volcanoes** + 1 Q **weathering** (interleaved, ~3 weeks since tectonics) |
| 4 | 2 | River landscapes — lower course features | Retrieve: draw and annotate the long profile of a river from memory |
| 4 | 3 | River landscapes — flooding | Retrieve: **Earthquakes** — compare two case studies + explain one measurement scale |
| 4 | 4 | River landscapes — flood management | Mixed retrieve: 3 Qs on **river processes** + 2 Qs on **erosion types** |
| 4 | 5 | Consolidation / depth lesson | Full interleaved quiz: 10 Qs across all 5 topics (2 per topic, mixed order) |
| 5 | 1 | Extended writing: comparing physical processes | Retrieve: **River landscapes** — sketch upper/middle/lower course features from memory |
| 5 | 2 | Case study depth: chosen topic | Mixed retrieve: 5 Qs interleaving **volcanoes**, **weathering**, **rivers** |
| 5 | 3 | Connections between topics | Retrieve: **Tectonic plates** — full free recall (4 weeks since initial teaching — critical spacing point) |
| 5 | 4 | Exam technique: using case studies | Mixed retrieve: 6 Qs across all 5 topics, focusing on commonly confused concepts |
| 5 | 5 | Practice assessment | Retrieve: quick-fire 1-minute-per-question across all 5 topics before practice assessment |
| 6 | 1 | Review based on practice assessment gaps | Targeted retrieval on weakest 2 topics from practice assessment data |
| 6 | 2 | Targeted depth: weakest topic | Retrieve: second-weakest topic from practice assessment |
| 6 | 3 | Targeted depth: second weakest | Mixed interleaved retrieval: all 5 topics, emphasis on gap areas |
| 6 | 4 | Final consolidation | Full brain dump: everything you know about all 5 topics in 12 minutes |
| 6 | 5 | **Assessment** | — |

### Spacing Rationale

Topics are spaced at expanding intervals following Cepeda et al.'s (2006) finding that optimal gaps increase as memory strengthens. Tectonic plates (taught first) receives retrieval at days 3, 7, 14, 21, and 28 — an expanding schedule. Each subsequent topic follows the same expanding pattern from its teaching date. Topics are interleaved in review sessions from Week 3 onwards, producing both a spacing and interleaving benefit. The final two weeks shift toward mixed retrieval across all topics, with targeted review driven by practice assessment data in Week 6.

### Review Activity Suggestions

- **Brain dump:** "Write everything you know about [topic] in 5 minutes. No notes." Most demanding — use for topics 2+ weeks after teaching.
- **Blank diagram:** "Draw and label [specific diagram] from memory." Excellent for spatial/process knowledge.
- **Free-recall questions:** 5 short questions requiring written answers from memory. 8–10 minutes.
- **Interleaved quiz:** Mix questions from 3+ topics in random order. Forces discrimination between similar concepts.
- **Error correction:** Give a paragraph with 3–4 deliberate errors. Students identify and correct from memory.

### Teacher Guidance

- Each review starter should take **10–15 minutes maximum**. It replaces a traditional lesson starter, not the main teaching.
- **When review reveals gaps:** If more than 40% of the class cannot recall a concept, schedule a brief re-teach (5 minutes) in the next lesson, then re-test 3 days later. Do not abandon the spacing schedule for a full re-teach.
- **Explain the purpose to students:** "This will feel harder than re-reading your notes, and you might feel like you're not learning as much. That feeling is actually a sign that your brain is working harder — and harder retrieval builds stronger memory. The research on this is very clear."
- **Do not grade review starters.** The moment these become high-stakes, students focus on performance rather than learning, and the beneficial difficulty effect is lost.

---

## Known Limitations

1. **The schedule assumes relatively even topic length.** If one topic requires 8 lessons of new teaching and another requires 2, the spacing intervals will be uneven. Teachers need to adjust the schedule based on actual topic weight — this tool provides a starting framework, not a rigid plan.

2. **Optimal spacing intervals from Cepeda et al. (2006) are derived primarily from laboratory studies of verbal learning.** Transfer to complex procedural skills (e.g., mathematical problem-solving, essay writing) is less well-established, though Carpenter et al. (2012) provide supportive classroom evidence.

3. **The schedule does not account for school disruptions** (assemblies, field trips, cancelled lessons, teacher absence). Teachers should treat the schedule as a target pattern and shift review slots when disruptions occur rather than skipping them entirely.

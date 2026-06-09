---
# AGENT SKILLS STANDARD FIELDS (v2)
name: professional-development-session-designer
description: "Design a professional development session using adult learning principles with active teacher engagement. Use when planning INSET days, CPD workshops, or staff training sessions."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "professional-learning/professional-development-session-designer"
skill_name: "Professional Development Session Designer"
domain: "professional-learning"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Timperley et al. (2007) — Teacher Professional Learning and Development: Best Evidence Synthesis (BES)"
  - "Darling-Hammond, Hyler & Gardner (2017) — Effective Teacher Professional Development"
  - "Desimone (2009) — Improving impact studies of teachers' professional development"
  - "Kennedy (2016) — How does professional development improve teaching?"
  - "Knowles (1984) — Andragogy: adult learning theory"
input_schema:
  required:
    - field: "pd_topic"
      type: "string"
      description: "The teaching practice or knowledge the session aims to develop"
    - field: "audience"
      type: "string"
      description: "Who will attend — number of teachers, experience range, subjects, roles"
    - field: "session_duration"
      type: "string"
      description: "How long the session lasts — 1 hour, 2 hours, half day, full day"
  optional:
    - field: "session_purpose"
      type: "string"
      description: "Why this session is happening — new initiative, improvement priority, teacher request"
    - field: "current_practice"
      type: "string"
      description: "What teachers currently do in this area — the starting point"
    - field: "school_context"
      type: "string"
      description: "Relevant school features — improvement priorities, Ofsted, staff morale"
    - field: "follow_up_plan"
      type: "string"
      description: "What happens after the session — coaching, peer observation, further sessions"
    - field: "facilitator_expertise"
      type: "string"
      description: "Who is leading the session and their level of expertise in the topic"
output_schema:
  type: "object"
  fields:
    - field: "session_plan"
      type: "object"
      description: "A time-structured session plan using adult learning principles"
    - field: "active_learning_tasks"
      type: "array"
      description: "Hands-on tasks that require teachers to DO, not just listen"
    - field: "practice_application"
      type: "object"
      description: "How teachers will apply the learning in their own classroom — specific commitments"
    - field: "follow_through"
      type: "object"
      description: "What happens after the session to sustain the learning — accountability, support, review"
chains_well_with:
  - "instructional-coaching-conversation-guide"
  - "lesson-study-cycle-designer"
  - "teacher-inquiry-cycle-designer"
  - "reflective-practice-prompt-generator"
  - "pedagogical-content-knowledge-developer"
  - "technological-pedagogical-content-knowledge-developer"
teacher_time: "4 minutes"
tags: ["CPD", "professional-development", "Timperley", "adult-learning", "INSET", "staff-training"]
---

# Professional Development Session Designer

## What This Skill Does

Designs a professional development session using evidence-based adult learning principles — ensuring the session is active (teachers DO, not just listen), connected to practice (teachers plan how to apply the learning in their own classrooms), and includes follow-through (what happens after the session to sustain the change). The critical insight from Timperley's research is that most professional development fails not because the content is wrong but because the design is wrong: a one-off presentation with no follow-up, no practice, and no accountability produces zero change in teaching. The output is a time-structured session plan with active learning tasks, practice application activities, and a follow-through plan. AI is specifically valuable here because designing effective PD requires balancing content delivery (teachers need to learn something new), active engagement (teachers need to process and apply it), and practical planning (teachers need to leave with a specific plan for their classroom) — all within a limited time frame.

## Evidence Foundation

Timperley et al. (2007) conducted the most comprehensive synthesis of effective professional learning, finding that impactful PD: (a) is sustained over time (not one-off), (b) focuses on the link between teaching practice and student outcomes, (c) involves teachers in active learning (not passive listening), (d) includes collaboration, (e) is supported by expert facilitation, and (f) integrates theory with practice. They found that the CONTENT of PD matters less than the PROCESS — a poorly designed session on an important topic produces less change than a well-designed session on a narrower topic. Darling-Hammond, Hyler & Gardner (2017) identified seven features of effective PD: content-focused, active learning, collaboration, models of effective practice, coaching and expert support, feedback and reflection, and sustained duration. Desimone (2009) proposed a core conceptual framework: effective PD changes teacher knowledge and beliefs → which changes teaching practice → which changes student outcomes. Kennedy (2016) argued that PD improves teaching not by adding new techniques but by helping teachers understand WHY certain approaches work — the mechanism, not just the method. Knowles (1984) established adult learning principles: adults learn best when the learning is problem-based (not abstract), connects to their experience, offers choice, and has immediate practical application.

## Input Schema

The teacher or PD leader must provide:
- **PD topic:** What the session is about. *e.g. "Implementing retrieval practice across the school" / "Using formative assessment to improve responsiveness" / "Supporting students with SEND in mainstream classrooms" / "Improving the quality of teacher feedback"*
- **Audience:** Who attends. *e.g. "30 teachers, mixed subjects, ECTs to experienced staff" / "8 members of the English department, all experienced" / "Full staff of 60, INSET day"*
- **Session duration:** How long. *e.g. "1 hour after school" / "2-hour INSET session" / "Full day — 6 hours"*

Optional (injected by context engine if available):
- **Session purpose:** Why this is happening
- **Current practice:** What teachers already do
- **School context:** Improvement priorities, staff morale
- **Follow-up plan:** What happens after
- **Facilitator expertise:** Who leads and their background

## Prompt

```
You are an expert in professional development design, with deep knowledge of Timperley et al.'s (2007) Best Evidence Synthesis on professional learning, Darling-Hammond et al.'s (2017) features of effective PD, Desimone's (2009) conceptual framework, Kennedy's (2016) research on how PD improves teaching, and Knowles' (1984) adult learning principles. You understand that most PD fails because it is designed as a presentation (passive, one-off, disconnected from practice) when it should be designed as a learning experience (active, sustained, connected to the teacher's own classroom).

CRITICAL DESIGN PRINCIPLES:
- **The 20/80 rule:** No more than 20% of session time should be the facilitator talking. At least 80% should be teachers DOING: discussing, planning, practising, analysing, creating. If you design a session that is mostly presentation, you have failed.
- **Start from teachers' experience (Knowles, 1984).** Adults learn by connecting new knowledge to existing practice. The session must begin with what teachers already know and do, not with what they should do.
- **End with a specific classroom commitment.** Every teacher should leave with a concrete plan: "In my Year 8 lesson on [topic] next [day], I will try [specific strategy]." Vague takeaways ("I'll try to use more formative assessment") produce no change.
- **Plan the follow-through.** A session without follow-up is professional entertainment, not professional development. What happens next week, next month?
- **Respect teachers' time and intelligence.** Teachers are professionals with deep expertise. Don't patronise. Don't over-simplify. Don't pretend the solution is easy when it's complex.

Your task is to design a PD session on:

**PD topic:** {{pd_topic}}
**Audience:** {{audience}}
**Session duration:** {{session_duration}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Session purpose:** {{session_purpose}} — if not provided, infer from the topic.
**Current practice:** {{current_practice}} — if not provided, build in an activity that surfaces current practice.
**School context:** {{school_context}} — if not provided, design for a general school context.
**Follow-up plan:** {{follow_up_plan}} — if not provided, recommend a follow-up structure.
**Facilitator expertise:** {{facilitator_expertise}} — if not provided, design for a facilitator with good knowledge of the topic.

Return your output in this exact format:

## PD Session: [Topic]

**Topic:** [What teachers will learn]
**Audience:** [Who attends]
**Duration:** [How long]

### Session Overview

[One paragraph: what teachers will learn, do, and leave with]

### Session Plan

For each phase:
**[Time block]: [Phase name]**
- **Facilitator does:** [What the facilitator says/does — kept brief]
- **Teachers do:** [What teachers actively do — the main activity]
- **Purpose:** [Why this phase matters for the learning]
- **Resources needed:** [Materials, handouts, technology]

### Active Learning Tasks

[Detailed description of the 2–3 key active tasks — what teachers do, how it's structured, what it produces]

### Practice Application

[How teachers plan to apply the learning in their own classroom — a specific planning activity]

### Follow-Through Plan

[What happens after the session — coaching, peer observation, check-in meeting, follow-up session]

### Facilitator Notes

[Tips for the facilitator — how to manage the session, common challenges, how to handle resistance]

**Self-check before returning output:** Verify that (a) at least 80% of session time is active (teachers doing, not listening), (b) the session starts from teachers' existing practice, (c) every teacher leaves with a specific classroom commitment, (d) follow-through is planned, and (e) the session respects teachers' professionalism.
```

## Example Output

**Scenario:** *PD topic: "Implementing retrieval practice across the school — helping teachers understand why retrieval practice works, how to use it efficiently, and how to embed it into their existing routines without adding workload" / Audience: "Full staff of 45 teachers, mixed subjects (primary and secondary in an all-through school), experience ranges from ECTs to 25 years. Staff are generally positive but time-poor and sceptical of 'another initiative.'" / Session duration: "90 minutes, after-school INSET" / School context: "The school's improvement plan prioritises 'improving long-term retention of knowledge.' Staff have heard of retrieval practice but few use it systematically."*

---

## PD Session: Retrieval Practice — From Research to Your Classroom

**Topic:** Understanding and implementing retrieval practice
**Audience:** 45 teachers, mixed subjects and experience, all-through school
**Duration:** 90 minutes

### Session Overview

Teachers will experience retrieval practice as learners (so they understand how it FEELS), examine the evidence for why it works (so they understand the MECHANISM, not just the method), and design a specific retrieval routine for one of their classes (so they leave with a PLAN, not just an intention). The session is designed around the principle that retrieval practice should ADD to learning without adding to workload — every routine designed should take less than 5 minutes of lesson time and require minimal preparation.

### Session Plan

**0:00–0:10 — Experience It (10 min)**
- **Facilitator does:** "Before I tell you anything about retrieval practice, I want you to experience it. Take a blank piece of paper. Write down everything you remember from the last whole-school CPD session — topic, key ideas, any details. You have 3 minutes. Go."
- **Teachers do:** Brain-dump for 3 minutes (most will remember very little, which IS the point). Then turn to a partner and compare: did you remember the same things? Different things? How much did you retain?
- **Purpose:** This IS retrieval practice — and it demonstrates the problem (we forget most of what we hear in CPD sessions). It also creates the motivation: "If we can barely remember last month's CPD, imagine what students retain from our lessons." The experience creates the need for the content that follows.
- **Resources needed:** Blank paper, nothing else.

**0:10–0:20 — Why It Works (10 min)**
- **Facilitator does:** Brief (10 minutes maximum) presentation of the evidence: Roediger & Butler (2011), the testing effect, Bjork's desirable difficulties. Key message: retrieving information from memory STRENGTHENS the memory trace — it is not just assessment, it is a learning strategy. Two key slides: (1) the forgetting curve — showing how rapidly we forget without retrieval; (2) a graph comparing re-reading vs. retrieval practice for long-term retention.
- **Teachers do:** Listen (this is the 20% facilitator-talking portion). But ACTIVELY: after each key point, the facilitator asks a retrieval question about what was just said. "Without looking at the slide — what is the testing effect?" This models the technique in real time.
- **Purpose:** Teachers need to understand the WHY before they'll invest in the HOW. But the presentation is SHORT — 10 minutes, not 40.
- **Resources needed:** Slides (maximum 6), handout with key references.

**0:20–0:40 — Explore the Techniques (20 min)**
- **Facilitator does:** Introduces 5 low-workload retrieval techniques, each on a card: (1) Brain dump, (2) Retrieval grid, (3) Last lesson/last week/last month, (4) Low-stakes quiz (no technology needed), (5) Elaborative interrogation ("Why is this true?").
- **Teachers do:** In subject-alike groups of 4–5, examine all 5 technique cards. For each: discuss how it could work in YOUR subject. Mark each technique: "Easy to implement immediately" / "Would need adaptation" / "Not suitable for my subject." Groups share their top 2 techniques with the room.
- **Purpose:** Teachers evaluate the techniques against their own practice — not "which is best?" but "which works for ME?" Choice creates ownership. Subject-alike grouping ensures the discussion is relevant (a retrieval grid works differently in Maths than in English).
- **Resources needed:** Technique cards (5 cards per table, with description and example), large paper for group notes.

**0:40–1:05 — Design Your Routine (25 min)**
- **Facilitator does:** "Now you're going to plan a specific retrieval routine for one of your classes. Not 'I'll try retrieval practice sometime' — a specific routine that answers: which class, which lesson, which technique, how often, and how long." Provide a planning template.
- **Teachers do:** Individually, complete the planning template:
  - **Class:** (e.g., Year 9 Geography, Tuesday Period 3)
  - **Technique:** (e.g., "Last lesson / last week / last month" — 3 questions at the start of every lesson)
  - **Frequency:** (e.g., every lesson for the next 3 weeks)
  - **Time required:** (e.g., 5 minutes at the start)
  - **First set of questions:** (write them now — leave with questions ready to use tomorrow)

  After 15 minutes individual planning, pair up with a colleague and share: "Here's my plan. Does it make sense? What might go wrong?"
- **Purpose:** This is the most important phase. Teachers leave with a PLAN, not a concept. They've already written their first set of questions — the barrier to starting tomorrow has been removed.
- **Resources needed:** Planning template (one per teacher), pens.

**1:05–1:15 — Commit and Follow Up (10 min)**
- **Facilitator does:** "On a Post-it note, write: your name, your class, your technique, and the date you'll start. Stick it on the board on your way out. In three weeks, I'll check in with everyone to see how it's going — not to judge, but to learn what's working and what needs adjusting."
- **Teachers do:** Write their commitment, share with the person next to them ("I'm going to do X — what about you?"), and post the Post-it publicly.
- **Purpose:** Public commitment increases follow-through (Cialdini, 2006). The three-week check-in provides accountability without surveillance. The "not to judge but to learn" framing reduces anxiety.
- **Resources needed:** Post-it notes, display board.

### Active Learning Tasks

**Task 1 — The Opening Brain Dump:** Teachers experience retrieval practice as learners. This takes 3 minutes but sets the entire tone: "We're doing this, not talking about it."

**Task 2 — Technique Evaluation:** Subject-alike groups evaluate 5 techniques against their own practice. This is 20 minutes of active discussion where teachers make professional judgements about what works for their subject and context.

**Task 3 — The Planning Template:** Every teacher designs a specific retrieval routine with questions already written. This is the difference between "interesting session" and "I'm starting this tomorrow."

### Practice Application

Every teacher leaves with:
1. A completed planning template specifying class, technique, frequency, and timing
2. Their first set of retrieval questions ready to use
3. A public commitment (Post-it) specifying when they'll start

### Follow-Through Plan

**Week 1:** Brief email from facilitator: "You started your retrieval routines this week — how's it going? Reply with one sentence: what's working and what's tricky."

**Week 3:** 15-minute slot in the next staff meeting. Three teachers share their experience (one from primary, one from secondary, one who found it challenging). Structured: "What I tried, what happened, what I learned." This is peer learning, not performance.

**Half-term:** Optional "retrieval practice drop-in" — 30 minutes for teachers who want to develop their practice further, try new techniques, or problem-solve difficulties. Facilitated, not mandatory.

**Next full INSET:** 20-minute revisit — retrieval practice on retrieval practice. "Without looking at your notes from last time, write down the three most important things you learned about retrieval practice." Meta-modelling: using the technique to sustain the learning about the technique.

### Facilitator Notes

1. **The biggest risk is talking too much.** If you find yourself presenting for more than 10 minutes continuously, stop. The teachers are disengaging — you're modelling the exact opposite of what you're teaching (passive reception vs. active retrieval). Trust the activities.

2. **Handle scepticism with evidence, not enthusiasm.** If a teacher says "This is just another fad," don't dismiss them: "That's a fair concern. Here's the evidence: the testing effect has been replicated in over 100 studies across 40 years. It's not new — it's one of the most robust findings in cognitive science. What would help you feel more confident about trying it?"

3. **Some teachers will already use retrieval practice.** Celebrate this. Ask them to share what they do — peer expertise is more credible than facilitator expertise. "Who already does something like this? Tell us about it."

4. **The Post-it wall is essential.** Don't skip it. Public commitment dramatically increases follow-through. And the wall itself becomes a visible artefact: "45 teachers committed to trying retrieval practice this week."

---

## Known Limitations

1. **A single session cannot sustain change.** Timperley et al. (2007) are unequivocal: one-off PD does not change practice. This session is designed to be the START of a sustained focus — not a standalone event. Without the follow-through plan, this session will produce the same outcome as every other INSET session: initial enthusiasm followed by gradual reversion to previous practice.

2. **The session assumes basic facilitator competence.** The plan provides structure, but the facilitation — managing group dynamics, handling resistance, calibrating pace, responding to questions — requires skill. A facilitator who reads the plan like a script will not produce the same outcomes as one who understands the principles and can adapt in the moment.

3. **School culture affects PD effectiveness.** In schools with low trust, high accountability pressure, or a history of initiative fatigue, even well-designed PD faces resistance. The session design addresses this (starting from experience, offering choice, respecting time), but it cannot fully compensate for a toxic professional culture. Leadership must create the conditions for professional learning to thrive.

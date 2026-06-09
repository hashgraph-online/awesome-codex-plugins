---
# AGENT SKILLS STANDARD FIELDS (v2)
name: teacher-inquiry-cycle-designer
description: "Design a practitioner inquiry cycle from research question through data collection to evidence-informed action. Use when starting action research, teacher-led investigation, or professional inquiry."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "professional-learning/teacher-inquiry-cycle-designer"
skill_name: "Teacher Inquiry Cycle Designer"
domain: "professional-learning"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Timperley (2011) — Realizing the Power of Professional Learning"
  - "Timperley et al. (2007) — Teacher Professional Learning and Development: Best Evidence Synthesis"
  - "Cochran-Smith & Lytle (2009) — Inquiry as Stance: practitioner research for the next generation"
  - "Dana & Yendol-Hoppey (2014) — The Reflective Educator's Guide to Classroom Research"
  - "Earl & Katz (2006) — Leading Schools in a Data-Rich World"
input_schema:
  required:
    - field: "inquiry_question"
      type: "string"
      description: "The question the teacher wants to investigate — about their practice and its impact on student learning"
    - field: "teacher_context"
      type: "string"
      description: "The teacher's situation — subject, year group, professional learning goal"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "available_time"
      type: "string"
      description: "How much time the teacher can dedicate to the inquiry — one term, one year"
    - field: "data_available"
      type: "string"
      description: "What data the teacher already has or can collect — test scores, student work, surveys, observations"
    - field: "collaboration"
      type: "string"
      description: "Whether the teacher is working alone or with a team"
    - field: "school_support"
      type: "string"
      description: "Whether the school has a structured inquiry programme or the teacher is working independently"
output_schema:
  type: "object"
  fields:
    - field: "inquiry_design"
      type: "object"
      description: "The complete inquiry cycle — question, baseline, intervention, evidence collection, analysis, conclusions"
    - field: "data_plan"
      type: "object"
      description: "What data to collect, when, and how — practical and manageable"
    - field: "analysis_framework"
      type: "object"
      description: "How to analyse the data — what patterns to look for, how to draw conclusions"
    - field: "sharing_plan"
      type: "string"
      description: "How to share findings with colleagues — spreading the learning beyond the individual teacher"
chains_well_with:
  - "reflective-practice-prompt-generator"
  - "lesson-study-cycle-designer"
  - "instructional-coaching-conversation-guide"
  - "professional-development-session-designer"
  - "pedagogical-content-knowledge-developer"
  - "technological-pedagogical-content-knowledge-developer"
teacher_time: "4 minutes"
tags: ["inquiry", "Timperley", "practitioner-research", "action-research", "data-informed", "professional-learning"]
---

# Teacher Inquiry Cycle Designer

## What This Skill Does

Designs a structured teacher inquiry cycle — a form of practitioner research where a teacher investigates a specific question about their practice and its impact on student learning, collects evidence, analyses what they find, and draws conclusions that inform their future teaching. The critical principle from Timperley's research is that the most powerful professional learning occurs when teachers inquire into the IMPACT of their practice on student outcomes, not just reflect on what they did. The output includes a complete inquiry design (question, baseline, intervention, evidence collection, analysis, conclusions), a practical data plan (what to collect and when — manageable within teaching workload), an analysis framework, and a plan for sharing findings. AI is specifically valuable here because designing a rigorous but manageable inquiry requires balancing research standards (valid question, appropriate evidence, fair analysis) with practical teaching constraints (limited time, limited research training, need for the inquiry to serve learning, not just investigation).

## Evidence Foundation

Timperley (2011) placed teacher inquiry at the centre of effective professional learning, arguing that the most powerful professional learning cycle is: identify a student learning need → identify what the teacher needs to learn → engage in professional learning → apply it in practice → assess the impact on students → refine. This is inquiry — a systematic investigation into the relationship between teaching and learning. Timperley et al. (2007) found that the most effective professional development programmes involved teachers actively investigating the impact of new practices on their students — not just implementing strategies but checking whether they worked. Cochran-Smith & Lytle (2009) developed "inquiry as stance" — the idea that inquiry is not a one-off project but a professional disposition: a habitual orientation toward questioning, investigating, and learning from practice. Dana & Yendol-Hoppey (2014) provided practical guidance for classroom research, emphasising that teacher inquiry need not meet the standards of academic research — it is practical, context-specific, and designed to improve teaching, not to produce generalisable knowledge. Earl & Katz (2006) distinguished between "data-driven" decision-making (letting data dictate) and "data-informed" decision-making (using data as one input alongside professional judgement). Teacher inquiry is data-informed — the data illuminates, but the teacher interprets.

## Input Schema

The teacher must provide:
- **Inquiry question:** What they want to investigate. *e.g. "Does using retrieval practice at the start of every lesson improve my Year 9 students' retention of key Science vocabulary?" / "What happens to student participation when I replace 'hands up' with cold-calling?" / "How does providing written success criteria affect the quality of my Year 7 students' creative writing?"*
- **Teacher context:** Their situation. *e.g. "Year 9 Science, 5 years' experience, interested in memory and retention" / "NQT, Year 7 English, struggling with uneven participation"*

Optional (injected by context engine if available):
- **Student level:** Year group
- **Available time:** Duration of inquiry
- **Data available:** What data is accessible
- **Collaboration:** Solo or team
- **School support:** Structured programme or independent

## Prompt

```
You are an expert in teacher inquiry and practitioner research, with deep knowledge of Timperley's (2011) inquiry cycle, Cochran-Smith & Lytle's (2009) inquiry as stance, Dana & Yendol-Hoppey's (2014) practical classroom research methods, and Earl & Katz's (2006) data-informed professional practice. You understand that teacher inquiry is PRACTICAL research — designed to improve teaching, not to produce academic publications. It must be rigorous enough to produce trustworthy findings but manageable enough to fit within a teaching workload.

CRITICAL PRINCIPLES:
- **The question must be about IMPACT, not just practice.** "Am I using retrieval practice?" is about practice. "Does my use of retrieval practice improve student retention?" is about impact. Impact questions are more useful because they focus on what matters: student learning.
- **The inquiry must be MANAGEABLE.** A teacher conducting inquiry alongside a full teaching load cannot collect data with the rigour of a university researcher. Design data collection that fits within existing routines — using student work, existing assessments, and brief observations rather than creating additional workload.
- **Baseline before intervention.** The teacher needs to know the starting point before they can measure change. What does student learning look like BEFORE the new practice is introduced?
- **Multiple sources of evidence.** No single data source is sufficient. Triangulate: student work + teacher observation + student voice. If all three point in the same direction, the finding is trustworthy.
- **Honest conclusions.** The inquiry should report what was FOUND, not what was hoped for. If the intervention didn't work, that's a valuable finding — it prevents the teacher from persisting with an ineffective practice.

Your task is to design a teacher inquiry for:

**Inquiry question:** {{inquiry_question}}
**Teacher context:** {{teacher_context}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, infer from the question.
**Available time:** {{available_time}} — if not provided, design for a one-term inquiry (10–12 weeks).
**Data available:** {{data_available}} — if not provided, identify manageable data sources.
**Collaboration:** {{collaboration}} — if not provided, design for a solo inquiry with optional peer review.
**School support:** {{school_support}} — if not provided, design as an independent inquiry.

Return your output in this exact format:

## Teacher Inquiry: [Question]

**Question:** [The inquiry question]
**Teacher:** [Context]
**Duration:** [How long]

### Inquiry Design

**Phase 1 — Baseline (Weeks 1–2):**
[What data to collect before the intervention starts]

**Phase 2 — Intervention (Weeks 3–8):**
[What the teacher will change in their practice and how]

**Phase 3 — Evidence Collection (Throughout):**
[What data to collect during the intervention — practical, manageable sources]

**Phase 4 — Analysis (Weeks 9–10):**
[How to analyse the evidence — what to look for, how to compare to baseline]

**Phase 5 — Conclusions (Weeks 11–12):**
[How to draw conclusions and decide what to do next]

### Data Plan

| Data Source | What It Shows | When to Collect | Time Required |
|---|---|---|---|
| [Source 1] | [What it reveals] | [Timing] | [Time cost] |
| [Source 2] | | | |
| [Source 3] | | | |

### Analysis Framework

[How to make sense of the data — what patterns to look for, how to compare baseline and post-intervention, how to handle mixed results]

### Sharing Plan

[How to share findings with colleagues — not as a formal presentation but as practical professional knowledge]

### Honest Caveats

[What the inquiry can and cannot prove — the limitations of a small-scale classroom inquiry]

**Self-check before returning output:** Verify that (a) the question is about impact on student learning, (b) baseline data is collected before the intervention, (c) multiple data sources are used, (d) the data plan is manageable within teaching workload, (e) the analysis framework is honest about limitations, and (f) the sharing plan spreads the learning beyond the individual teacher.
```

## Example Output

**Scenario:** *Inquiry question: "Does using retrieval practice at the start of every lesson improve my Year 9 students' retention of key Science vocabulary?" / Teacher context: "Year 9 Science, 5 years' experience, interested in cognitive science and memory research, noticed that students struggle with topic-specific vocabulary and forget key terms between lessons" / Available time: "One term — 10 weeks" / Data available: "End-of-topic test scores from the previous two topics (baseline comparison), student exercise books, and the teacher's own lesson records"*

---

## Teacher Inquiry: Retrieval Practice and Vocabulary Retention

**Question:** Does using retrieval practice at the start of every lesson improve Year 9 students' retention of key Science vocabulary?
**Teacher:** Year 9 Science, 5 years' experience
**Duration:** 10 weeks (one term)

### Inquiry Design

**Phase 1 — Baseline (Weeks 1–2):**
Before introducing retrieval practice, collect baseline data on current vocabulary retention:
- Administer a short vocabulary quiz (10 key terms from the previous topic) at the START of the new term, before any new teaching. This measures how much vocabulary students retained over the holiday/gap.
- Review end-of-topic test scores from the PREVIOUS two topics. How did students perform on vocabulary-dependent questions? This provides historical comparison data.
- Ask students (brief survey, 3 questions): "How do you revise for Science? When you forget a key word, what do you do? How confident are you with Science vocabulary?" This captures student perception before the intervention.

**Phase 2 — Intervention (Weeks 3–8):**
Introduce a 5-minute retrieval practice routine at the start of every Science lesson:
- "Last lesson / Last week / Last month" format: 3 questions displayed on the board. Students answer from memory on mini-whiteboards or in a dedicated section of their exercise book. Teacher reviews answers, addresses errors, and moves on. Total time: 5 minutes maximum.
- Questions focus specifically on vocabulary: "What does 'photosynthesis' mean?" / "Use the word 'enzyme' in a sentence that shows you understand it" / "What is the difference between 'respiration' and 'breathing'?"
- The teacher keeps a log: which questions were asked, what percentage of students answered correctly. This takes 30 seconds per lesson (a tally on a sticky note).

**Phase 3 — Evidence Collection (Throughout):**
1. **Weekly retrieval data:** The teacher's lesson log — percentage of students answering vocabulary questions correctly. Track this over the 6 intervention weeks to see if accuracy improves.
2. **Mid-point vocabulary quiz (Week 6):** A 10-term vocabulary quiz on the current topic, administered under the same conditions as the baseline quiz. This provides a direct comparison.
3. **End-of-topic test (Week 8):** Compare student performance on vocabulary-dependent questions to performance on the previous two end-of-topic tests (the baseline data).
4. **Student voice (Week 8):** Repeat the 3-question survey from Week 1. Has student confidence with vocabulary changed? Have students noticed the retrieval routine?

**Phase 4 — Analysis (Weeks 9–10):**
Compare:
- Baseline vocabulary quiz scores (Week 1) vs. mid-point quiz scores (Week 6): did retention improve?
- End-of-topic test vocabulary scores (current topic, with retrieval practice) vs. previous topic scores (without): did performance on vocabulary-dependent questions improve?
- Weekly retrieval data: is there a trend? Are students answering correctly more often in Week 8 than Week 3?
- Student survey: has self-reported confidence changed?

**Phase 5 — Conclusions (Weeks 10–11):**
Answer the inquiry question honestly:
- If the data shows improvement across multiple sources (quiz scores up, test performance up, retrieval accuracy trending up, students feeling more confident): conclude that retrieval practice appears to have improved vocabulary retention for this class.
- If the data is mixed (quiz scores improved but test performance didn't change): investigate why. Possible explanations: the test didn't isolate vocabulary (other factors affected the score), or retrieval practice improved short-term retention but not long-term (need to continue longer).
- If the data shows no improvement: report this honestly. Possible explanations: 5 minutes was not enough "dosage," the questions were not targeting the right vocabulary, or vocabulary retention depends on factors beyond retrieval practice.

### Data Plan

| Data Source | What It Shows | When to Collect | Time Required |
|---|---|---|---|
| Baseline vocabulary quiz (10 terms) | Pre-intervention retention level | Week 1 | 10 min lesson time, 15 min to mark |
| Weekly retrieval log (tally) | Trend in retrieval accuracy | Every lesson (Weeks 3–8) | 30 seconds per lesson |
| Mid-point vocabulary quiz | Mid-intervention retention | Week 6 | 10 min lesson time, 15 min to mark |
| End-of-topic test (vocabulary questions isolated) | Post-intervention performance | Week 8 | Already part of normal assessment |
| Student survey (3 questions) | Student perception of vocabulary confidence | Weeks 1 and 8 | 5 min lesson time |

**Total additional time:** Approximately 90 minutes over 10 weeks (beyond normal teaching). This is manageable.

### Analysis Framework

**Look for convergence.** If all four data sources (quizzes, test, weekly log, student voice) point in the same direction, the finding is robust. If they diverge, investigate why.

**Use simple comparison.** This is not a statistical study. Compare means: "Average vocabulary quiz score was 4.2/10 at baseline and 7.1/10 at mid-point." Compare proportions: "In Week 3, 45% of students answered retrieval questions correctly. By Week 8, this had risen to 78%." Visual representation (a simple line graph of weekly retrieval accuracy) makes trends visible.

**Be honest about attribution.** You cannot prove that retrieval practice CAUSED the improvement. Other factors changed simultaneously (students learned new content, became more familiar with the teacher, matured over the term). What you CAN say is: "Vocabulary retention improved during the period when retrieval practice was introduced, and students reported feeling more confident. This is consistent with the research on retrieval practice and suggests it is worth continuing."

### Sharing Plan

**Informal:** Share findings with the Science department at a department meeting (15 minutes). Show the data, describe the routine, invite questions. Offer to share the retrieval question bank.

**Structured:** Write a one-page summary: Question → What I did → What I found → What I'll do next. Pin it to the staffroom professional learning board (if one exists) or share via email.

**Practical:** Offer to model the retrieval routine for a colleague who is interested. Better yet, invite a colleague to observe one of your lessons specifically to see the retrieval routine in action.

### Honest Caveats

1. **This is a small-scale inquiry, not a controlled experiment.** There is no control group (a parallel class that didn't receive retrieval practice). You cannot definitively attribute the improvement to retrieval practice — other factors may have contributed. This is a common limitation of practitioner inquiry — but the findings are still valuable for informing YOUR practice.

2. **The teacher is both researcher and practitioner.** You want the intervention to work (you believe in retrieval practice), which creates a bias. Be honest with yourself: if the data doesn't show improvement, resist the temptation to explain it away. Negative findings are just as valuable as positive ones.

3. **One term may not be enough.** Retrieval practice effects are strongest over longer periods (Roediger & Butler, 2011). If the results are modest after one term, consider extending the inquiry for a second term before concluding that retrieval practice doesn't work for your students.

---

## Known Limitations

1. **Teacher inquiry is context-specific.** Findings from one teacher's inquiry with one class in one school cannot be generalised to all contexts. The value of teacher inquiry is that it produces LOCAL knowledge — knowledge that is directly applicable to the teacher's own practice, even if it cannot be claimed as universal truth.

2. **Inquiry requires a genuine question.** If the teacher has already decided that retrieval practice works and is using the inquiry to confirm this belief, the inquiry loses its value. Genuine inquiry requires genuine uncertainty: "I think this might work — let me find out." If the teacher is not genuinely open to the possibility that the intervention doesn't work, the inquiry becomes advocacy, not investigation.

3. **Data collection must not harm teaching.** If the inquiry's data demands become so burdensome that they reduce the quality of teaching, the inquiry is counterproductive. The data plan above is designed to be minimal — but teachers should abandon any data collection that feels unsustainable. A slightly less rigorous inquiry that is actually completed is more valuable than a perfectly designed inquiry that is abandoned in Week 4.

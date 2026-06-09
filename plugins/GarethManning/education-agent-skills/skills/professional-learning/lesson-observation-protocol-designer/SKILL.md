---
# AGENT SKILLS STANDARD FIELDS (v2)
name: lesson-observation-protocol-designer
description: "Design a focused lesson observation protocol with specific look-fors and evidence collection methods. Use when planning peer observations, coaching visits, or developmental classroom visits."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "professional-learning/lesson-observation-protocol-designer"
skill_name: "Lesson Observation Protocol Designer"
domain: "professional-learning"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Darling-Hammond (2010) — Evaluating Teacher Effectiveness: how teacher performance assessments can measure and improve teaching"
  - "Hill, Charalambous & Kraft (2012) — When rater reliability is not enough: teacher observation systems and a case for the generalizability study"
  - "Wragg (2012) — An Introduction to Classroom Observation"
  - "O'Leary (2014) — Classroom Observation: a guide to the effective observation of teaching and learning"
  - "Coe et al. (2014) — What Makes Great Teaching? Review of the underpinning research"
input_schema:
  required:
    - field: "observation_focus"
      type: "string"
      description: "The specific teaching practice or aspect of learning to observe — not 'everything' but a focused lens"
    - field: "observation_purpose"
      type: "string"
      description: "Why the observation is happening — developmental, coaching, peer learning, quality assurance, research"
  optional:
    - field: "teacher_context"
      type: "string"
      description: "Experience level, subject, any relevant background"
    - field: "student_level"
      type: "string"
      description: "Age/year group being taught"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "observation_duration"
      type: "string"
      description: "Full lesson, drop-in (15 minutes), or learning walk (5 minutes)"
    - field: "school_context"
      type: "string"
      description: "Observation culture in the school — supportive, high-stakes, new initiative"
output_schema:
  type: "object"
  fields:
    - field: "observation_protocol"
      type: "object"
      description: "The complete protocol — what to look for, how to record, what to ignore"
    - field: "look_fors"
      type: "array"
      description: "Specific, observable indicators linked to the focus — what 'good' looks like in practice"
    - field: "recording_format"
      type: "object"
      description: "How to capture evidence during the observation — structured notes, tally, time-sampling"
    - field: "feedback_framework"
      type: "object"
      description: "How to structure the post-observation conversation — evidence-based, specific, forward-looking"
chains_well_with:
  - "instructional-coaching-conversation-guide"
  - "lesson-study-cycle-designer"
  - "reflective-practice-prompt-generator"
  - "explicit-instruction-sequence-builder"
  - "pedagogical-content-knowledge-developer"
  - "technological-pedagogical-content-knowledge-developer"
teacher_time: "3 minutes"
tags: ["observation", "look-fors", "feedback", "professional-development", "evidence-based"]
---

# Lesson Observation Protocol Designer

## What This Skill Does

Designs a focused, evidence-based lesson observation protocol for a specific teaching practice — providing clear "look-fors" (observable indicators of the practice in action), a structured recording format, and a framework for the post-observation feedback conversation. The critical principle is that observations should be FOCUSED (looking for specific things, not "everything"), EVIDENCE-BASED (recording what is seen, not judgements), and DEVELOPMENTAL (generating learning for the teacher, not just a grade). The output is a ready-to-use protocol that an observer can take into a classroom, plus a feedback framework for the post-observation conversation. AI is specifically valuable here because designing effective look-fors requires translating abstract teaching practices ("effective questioning") into observable, specific indicators ("the teacher waits at least 3 seconds after asking a question before accepting a response") — a translation that requires both research knowledge and practical teaching experience.

## Evidence Foundation

Darling-Hammond (2010) argued that teacher observation is most effective when it is standards-based (linked to clear criteria), evidence-based (grounded in observable behaviour, not subjective impression), and developmental (designed to improve practice, not just rate it). She emphasised that the quality of the observation depends on the quality of the protocol — vague criteria produce vague feedback. Hill, Charalambous & Kraft (2012) demonstrated that observation reliability depends on focus: observers who are looking for specific, defined practices produce more consistent ratings than observers looking at "overall quality." Wragg (2012) provided foundational guidance on classroom observation methods, distinguishing between structured observation (systematic recording against predefined criteria) and unstructured observation (open-ended narrative). He argued for structured approaches because they produce more reliable, usable evidence. O'Leary (2014) challenged the use of observation as performance management, arguing that observation is most powerful when used for professional learning — when teachers observe each other, receive specific feedback, and use it to develop their practice. Coe et al. (2014) in "What Makes Great Teaching?" identified the practices with the strongest evidence base for student outcomes: content knowledge, quality of instruction (including questioning, feedback, and assessment), classroom climate, and classroom management. These provide the evidence base for what to look for during observations.

## Input Schema

The teacher must provide:
- **Observation focus:** What to look for. *e.g. "Checking for understanding — how does the teacher assess whether students have understood before moving on?" / "Think time and student participation — how many students are actively involved in responding to questions?" / "Feedback during independent practice — what does the teacher say to students as they circulate?"*
- **Observation purpose:** Why. *e.g. "Developmental — coaching cycle, looking at questioning as an agreed focus" / "Peer observation — two teachers observing each other to share practice" / "Quality assurance — SLT monitoring the implementation of the new feedback policy"*

Optional (injected by context engine if available):
- **Teacher context:** Experience, subject, background
- **Student level:** Year group
- **Subject area:** The subject
- **Observation duration:** Full lesson, drop-in, or learning walk
- **School context:** Observation culture

## Prompt

```
You are an expert in classroom observation and teacher development, with deep knowledge of Darling-Hammond's (2010) framework for teacher evaluation, Hill et al.'s (2012) research on observation reliability, Wragg's (2012) observation methods, O'Leary's (2014) developmental approach, and Coe et al.'s (2014) evidence on effective teaching practices. You understand that the value of an observation depends almost entirely on the quality of the protocol — what the observer looks for and how they record it determines what they learn and what feedback they can provide.

CRITICAL PRINCIPLES:
- **Focused, not comprehensive.** An observer cannot meaningfully assess "teaching quality" in one lesson. A focused lens on ONE aspect of practice produces much more useful evidence than a general sweep. The protocol must specify what to look for AND what to ignore.
- **Evidence, not judgement.** The protocol should guide the observer to record what they SEE and HEAR, not what they THINK about it. "The teacher asked 12 questions in 10 minutes, 9 of which were closed" is evidence. "The questioning was weak" is judgement. Evidence can be discussed; judgement provokes defensiveness.
- **Look-fors must be observable.** "The teacher has high expectations" is not observable. "The teacher sets a timer for the task and says 'I expect you to complete all 5 questions'" is observable. The protocol must translate research-based practices into things an observer can actually see and hear.
- **The feedback conversation matters as much as the observation.** The protocol must include guidance for the post-observation conversation — how to share evidence, how to prompt reflection, how to agree on next steps.

Your task is to design an observation protocol for:

**Observation focus:** {{observation_focus}}
**Observation purpose:** {{observation_purpose}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Teacher context:** {{teacher_context}} — if not provided, design a protocol that works for any teacher.
**Student level:** {{student_level}} — if not provided, design for general classroom observation.
**Subject area:** {{subject_area}} — if not provided, design for cross-subject use.
**Observation duration:** {{observation_duration}} — if not provided, design for a full-lesson observation (50–60 minutes).
**School context:** {{school_context}} — if not provided, design for a developmental purpose (not performance management).

Return your output in this exact format:

## Observation Protocol: [Focus Area]

**Focus:** [What the observer is looking for]
**Purpose:** [Why this observation is happening]
**Duration:** [How long]

### Before the Observation

[What the observer should know, do, or prepare before entering the classroom]

### Look-Fors

For each look-for (4–6):
**Look-for [N]: [Observable indicator]**
- **What to watch/listen for:** [Specific, observable behaviour]
- **Evidence of strong practice:** [What this looks like when done well]
- **Evidence of developing practice:** [What this looks like when it's not yet strong]
- **How to record:** [Tally, time-stamp, verbatim quote, or narrative note]

### Recording Template

[A structured format the observer can use during the observation]

### Post-Observation Feedback Framework

[How to structure the feedback conversation — evidence-based, specific, forward-looking]

### What NOT to Look For

[What to deliberately exclude from this observation — to maintain focus]

**Self-check before returning output:** Verify that (a) every look-for is observable (you can see or hear it), (b) the protocol distinguishes evidence from judgement, (c) the recording format is practical (can be used in real-time), (d) the feedback framework is evidence-based and developmental, and (e) the protocol is focused — it looks for specific things, not everything.
```

## Example Output

**Scenario:** *Observation focus: "Checking for understanding — specifically, how the teacher assesses whether students have grasped the content before moving to the next phase of the lesson. Are they checking ALL students or just volunteers?" / Observation purpose: "Developmental — part of a coaching cycle. The teacher has identified 'responsive teaching' as their development focus. This observation gathers evidence on their current checking-for-understanding practice." / Teacher context: "4th year teacher, Year 9 Geography" / Observation duration: "Full lesson (55 minutes)"*

---

## Observation Protocol: Checking for Understanding

**Focus:** How the teacher checks whether students understand before moving on — who is checked, how, and what happens with the information
**Purpose:** Developmental — coaching cycle, teacher's chosen focus area
**Duration:** Full lesson (55 minutes), Year 9 Geography

### Before the Observation

1. **Agree the focus with the teacher.** Before the lesson, confirm: "I'm looking specifically at how you check for understanding — when you check, how you check, and what you do with the information. I won't be looking at anything else." This reduces anxiety and ensures the teacher knows what to expect.

2. **Get the lesson plan.** Ask the teacher: "Where in the lesson do you expect to check understanding? What are you hoping to find out?" This gives the observer context and identifies planned checking points (the teacher may also check spontaneously, which is equally important to observe).

3. **Position yourself.** Sit at the back or side where you can see both the teacher and the students. You need to observe student responses (not just the teacher's questions), so a position where you can see students' faces, whiteboards, and written work is essential.

### Look-Fors

**Look-for 1: How Many Students Are Checked?**
- **What to watch/listen for:** When the teacher checks understanding, does the technique collect information from ALL students or just volunteers? Count how many students are involved in each check.
- **Evidence of strong practice:** Whole-class techniques: mini-whiteboards with "3-2-1-show me" (all students respond simultaneously), exit tickets (every student writes), cold-calling (random selection, not volunteers). The teacher gathers data from 80%+ of students.
- **Evidence of developing practice:** "Hands up who understands?" (self-report, not evidence). "Any questions?" (relies on students knowing what they don't know). Only 3–5 students respond while 20+ are unchecked.
- **How to record:** For each checking moment, note: the technique used, the approximate number of students who responded, and whether the response required DEMONSTRATING understanding or just CLAIMING it.

**Look-for 2: What Kind of Understanding Is Checked?**
- **What to watch/listen for:** Is the check testing recall (can students remember what was said?), procedural application (can they do it?), or conceptual understanding (can they explain why)?
- **Evidence of strong practice:** Questions and tasks that require students to explain, apply, or demonstrate — not just repeat. "Show me how you would calculate the population density of this region" (application) vs. "What is population density?" (recall).
- **Evidence of developing practice:** Checks that only test surface recall: "Can anyone tell me what we said about population density?" Students can repeat the definition without understanding it.
- **How to record:** For each check, classify it: Recall / Application / Explanation. Note the exact question or task.

**Look-for 3: Timing — When Does the Teacher Check?**
- **What to watch/listen for:** Does the teacher check BEFORE moving to the next phase (diagnostic — used to decide what to do next) or only at the END of the lesson (summative — too late to adjust)?
- **Evidence of strong practice:** Checking happens at transition points — after the teacher explains a concept and before students practise independently, after guided practice and before releasing to independent work. The check is a decision point: "Do I proceed, re-explain, or differentiate?"
- **Evidence of developing practice:** Checking happens only at the end (exit ticket as the bell rings) or not at all (the teacher assumes understanding from nodding heads).
- **How to record:** Time-stamp each checking moment. Note where it falls in the lesson sequence (during explanation / after guided practice / before independent work / end of lesson).

**Look-for 4: What Does the Teacher DO With the Information?**
- **What to watch/listen for:** After checking, does the teacher adapt? Or do they check and proceed regardless?
- **Evidence of strong practice:** The teacher checks (whiteboards show 60% correct), pauses, re-teaches: "I can see some of you aren't sure about this yet. Let me show it again a different way." OR the teacher checks, sees 90% correct, proceeds: "Great — you've got this. Let's move on." The check informs the NEXT teaching decision.
- **Evidence of developing practice:** The teacher checks, sees mixed results, and proceeds anyway: "OK, well done, let's move on." The data was gathered but not used. This is diagnostic without being formative.
- **How to record:** For each check, note: what the data showed AND what the teacher did next. Was the next action responsive to the data?

**Look-for 5: Student Engagement With the Check**
- **What to watch/listen for:** Do students take the check seriously? Do they attempt it genuinely or rush through / copy / put minimal effort in?
- **Evidence of strong practice:** Students engage fully with the checking task — they think, write, discuss. The check has become a routine that students value because they know the teacher will use it to help them.
- **Evidence of developing practice:** Students write minimal responses, copy from neighbours, or don't respond at all. The check has become a ritual with no perceived value.
- **How to record:** Note the level of student engagement during each checking moment. Count approximate participation rate.

### Recording Template

| Time | Checking Technique Used | # Students Checked | Type (Recall/Apply/Explain) | What Data Showed | Teacher's Next Action | Responsive? (Y/N) |
|---|---|---|---|---|---|---|
| | | | | | | |
| | | | | | | |

Also record: verbatim quotes of checking questions (write them down exactly).

### Post-Observation Feedback Framework

**Step 1 — Share evidence, not judgement (5 minutes):**
"Here's what I recorded. You checked for understanding [X] times during the lesson. The techniques you used were [list]. The number of students responding ranged from [Y to Z]. Here are the exact questions you asked: [verbatim]."

Present the recording template. Let the teacher read it.

**Step 2 — Invite reflection (10 minutes):**
"What do you notice when you look at this data?" (Let them analyse.)
"Which checking moment do you think was most useful for your teaching? Why?"
"Were there any moments where you checked and then used the information to change what you did next?"
"Were there moments where you wished you'd checked but didn't?"

**Step 3 — Identify one specific next step (10 minutes):**
"Based on what we've seen, what's the ONE thing you'd want to change or try next time?"
The next step should be specific and achievable: e.g., "Use mini-whiteboards at the transition between explanation and practice to check all students before releasing them to independent work."

**Step 4 — Plan the follow-up (5 minutes):**
"When will you try this? Shall I come and observe that specific moment? We can compare the data."

### What NOT to Look For

During this observation, deliberately IGNORE:
- The quality of the teacher's subject knowledge (not the focus)
- Behaviour management (unless it directly affects checking for understanding)
- The quality of resources or displays
- The teacher's presentation style, confidence, or personality
- Whether students are "engaged" in a general sense (focus only on engagement with the checking tasks)

Staying focused on ONE aspect produces deep, useful evidence. Spreading attention across everything produces shallow impressions.

---

## Known Limitations

1. **A single observation is a snapshot.** One lesson may not represent the teacher's typical practice. The teacher may perform differently because they're being observed (the observer effect). The protocol should be used across multiple observations to build a reliable picture.

2. **The quality of feedback depends on the observer's skill.** A well-designed protocol in the hands of an observer who delivers feedback judgementally will produce defensiveness, not growth. The feedback framework guides the conversation, but the observer must be trained to deliver feedback as evidence-based dialogue, not evaluation.

3. **Developmental observation and performance management observation require different approaches.** This protocol is designed for developmental purposes. If the same protocol is used for high-stakes performance management, teachers will perform for the observer rather than teach naturally, and the data will be unreliable. Schools should separate developmental observation from accountability observation.

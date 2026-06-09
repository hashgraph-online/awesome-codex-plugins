---
# AGENT SKILLS STANDARD FIELDS (v2)
name: instructional-coaching-conversation-guide
description: "Generate a coaching conversation guide with questions, protocols, and follow-up actions for a teaching focus. Use when preparing for coaching sessions, mentoring, or peer feedback conversations."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "professional-learning/instructional-coaching-conversation-guide"
skill_name: "Instructional Coaching Conversation Guide"
domain: "professional-learning"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Knight (2007) — Instructional Coaching: a partnership approach to improving instruction"
  - "Knight (2018) — The Impact Cycle: what instructional coaches should do to foster powerful improvements in teaching"
  - "Kraft, Blazar & Hogan (2018) — The effect of teacher coaching on instruction and achievement: a meta-analysis"
  - "Costa & Garmston (2016) — Cognitive Coaching: developing self-directed leaders and learners"
  - "Aguilar (2013) — The Art of Coaching: effective strategies for school transformation"
input_schema:
  required:
    - field: "coaching_focus"
      type: "string"
      description: "The specific teaching practice or challenge being worked on — what the teacher wants to improve"
    - field: "teacher_context"
      type: "string"
      description: "Brief context about the teacher — experience level, subject, current situation"
  optional:
    - field: "observation_data"
      type: "string"
      description: "Data from a lesson observation, student work, or video — evidence to ground the conversation"
    - field: "coaching_phase"
      type: "string"
      description: "Where in the coaching cycle — initial goal-setting, mid-cycle check-in, or reflection on impact"
    - field: "relationship_stage"
      type: "string"
      description: "New coaching relationship, established trust, or challenging dynamic"
    - field: "teacher_disposition"
      type: "string"
      description: "The teacher's current stance — eager, resistant, overwhelmed, confident, uncertain"
    - field: "school_context"
      type: "string"
      description: "Relevant school features — coaching programme structure, leadership expectations"
output_schema:
  type: "object"
  fields:
    - field: "conversation_plan"
      type: "object"
      description: "A structured coaching conversation with specific questions, anticipated responses, and facilitator moves"
    - field: "questioning_sequence"
      type: "array"
      description: "Questions sequenced from reflective to analytical to action-planning"
    - field: "dialogue_strategies"
      type: "object"
      description: "Specific strategies for the coach — pausing, paraphrasing, probing, providing data"
    - field: "next_steps"
      type: "string"
      description: "Clear, specific next steps with accountability — what the teacher will try and when the coach will follow up"
chains_well_with:
  - "lesson-study-cycle-designer"
  - "lesson-observation-protocol-designer"
  - "reflective-practice-prompt-generator"
  - "teacher-inquiry-cycle-designer"
  - "pedagogical-content-knowledge-developer"
teacher_time: "4 minutes"
tags: ["coaching", "instructional-coaching", "Knight", "professional-learning", "feedback", "dialogue"]
---

# Instructional Coaching Conversation Guide

## What This Skill Does

Designs a structured coaching conversation between an instructional coach and a teacher — using Knight's (2007, 2018) partnership approach and the Impact Cycle model — that helps the teacher identify a specific improvement focus, analyse evidence from their practice, and commit to a concrete next step. The critical principle is that effective coaching is a PARTNERSHIP: the coach does not tell the teacher what to do (that's directing) or simply affirm what the teacher already thinks (that's cheerleading). Instead, the coach uses questions, data, and dialogue to help the teacher think more clearly about their practice and make their own decisions about what to change. The output is a conversation plan with specific questions, anticipated responses, dialogue strategies for the coach (pausing, paraphrasing, probing), and clear next steps with accountability. AI is specifically valuable here because designing a coaching conversation requires anticipating the teacher's likely responses, selecting the right questions for the right moment, and balancing challenge with support — a real-time facilitation skill that benefits from advance planning.

## Evidence Foundation

Knight (2007) established the partnership principles of instructional coaching: equality (the coach and teacher are equal partners), choice (the teacher decides what to work on), voice (the teacher's perspective is central), dialogue (real conversation, not one-way telling), reflection (the teacher examines their own practice), and praxis (learning is applied in the classroom). Knight (2018) operationalised these principles into the Impact Cycle: Identify (what's the current reality and what's the goal?), Learn (what strategy could close the gap?), Improve (implement, monitor, adjust). Kraft, Blazar & Hogan (2018) conducted a meta-analysis of 60 teacher coaching studies and found a pooled effect size of 0.49 standard deviations on instruction quality and 0.18 on student achievement — making coaching one of the most effective forms of professional development. They found that coaching is most effective when it is sustained (not one-off), focused on specific practices (not general), and includes observation and feedback cycles. Costa & Garmston (2016) developed Cognitive Coaching, emphasising that the coach's primary tool is questioning — questions that help teachers become more self-directed, self-monitoring, and self-modifying. Aguilar (2013) added the emotional dimension: effective coaching requires attention to the teacher's emotions, beliefs, and identity — not just their techniques.

## Input Schema

The teacher must provide:
- **Coaching focus:** What they're working on. *e.g. "I want to improve my questioning — I ask too many closed questions and don't give students enough think time" / "My Year 10 class is disengaged and I can't work out why" / "I've been told I need to differentiate more but I don't know where to start"*
- **Teacher context:** Brief background. *e.g. "NQT, first year of teaching, Science, generally enthusiastic but overwhelmed" / "Experienced teacher (12 years), English, recently had a critical observation and is defensive" / "Middle leader, 6 years, Maths, keen to improve but time-poor"*

Optional (injected by context engine if available):
- **Observation data:** Evidence to ground the conversation
- **Coaching phase:** Where in the cycle
- **Relationship stage:** New, established, or challenging
- **Teacher disposition:** Eager, resistant, overwhelmed, etc.
- **School context:** Coaching programme structure

## Prompt

```
You are an expert in instructional coaching, with deep knowledge of Knight's (2007, 2018) partnership approach, the Impact Cycle, Kraft, Blazar & Hogan's (2018) meta-analysis of coaching effectiveness, Costa & Garmston's (2016) Cognitive Coaching, and Aguilar's (2013) attention to the emotional dimension of coaching. You understand that effective coaching is a partnership where the coach uses questions and data to help the teacher think more clearly, not a directive process where the coach tells the teacher what to do.

CRITICAL PRINCIPLES:
- **Partnership, not direction.** The coach does not have the answers — the coach has the questions that help the teacher find their own answers. If the coach does all the talking, it's not coaching.
- **Data, not opinion.** Ground conversations in observable evidence (lesson observation data, student work, video clips), not subjective impressions. "I noticed 4 out of 25 students responded to your questions" is data. "Your questioning needs work" is opinion.
- **Specific, not general.** "Improve your differentiation" is too vague to act on. "Next lesson, provide three versions of the practice task at different difficulty levels" is specific enough to try.
- **The teacher decides.** The coach may suggest, model, or provide options — but the teacher chooses what to work on and what to try. Choice creates ownership; direction creates compliance.

Your task is to design a coaching conversation for:

**Coaching focus:** {{coaching_focus}}
**Teacher context:** {{teacher_context}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Observation data:** {{observation_data}} — if not provided, design the conversation to elicit the teacher's own perception of the issue, and recommend that observation data be gathered before the next meeting.
**Coaching phase:** {{coaching_phase}} — if not provided, assume this is an initial coaching conversation (Identify phase).
**Relationship stage:** {{relationship_stage}} — if not provided, assume early-stage relationship where trust is being built.
**Teacher disposition:** {{teacher_disposition}} — if not provided, design for a willing but uncertain teacher.
**School context:** {{school_context}} — if not provided, design for a standard school coaching programme.

Apply Knight's Impact Cycle:

1. **Identify Phase:**
   - Help the teacher articulate the current reality: what's happening now?
   - Help the teacher define a clear goal: what would "better" look like?
   - Use data to bridge the gap between current reality and goal.

2. **Learn Phase:**
   - Explore strategies that could close the gap.
   - The coach may offer options, model a strategy, share research, or facilitate the teacher's own problem-solving.
   - The teacher selects the strategy to try.

3. **Improve Phase:**
   - The teacher implements the strategy.
   - The coach observes or the teacher self-monitors.
   - Review: did the strategy work? Adjust if needed.

For EACH question, provide:
- The question itself
- Why this question matters (what it's designed to surface)
- How to respond to likely answers (including if the teacher deflects, becomes defensive, or gives a surface-level answer)

Return your output in this exact format:

## Coaching Conversation: [Focus Area]

**Focus:** [What the teacher is working on]
**Teacher:** [Brief context]
**Phase:** [Identify / Learn / Improve]

### Conversation Plan

**Opening (5 minutes):**
[How to begin — building rapport, setting the agenda, establishing the partnership frame]

**Exploration (15 minutes):**
[Core questions to explore the focus area — with anticipated responses and follow-up moves]

**Action Planning (10 minutes):**
[Questions that move toward a specific next step]

**Closing (5 minutes):**
[Summarise, confirm next steps, schedule follow-up]

### Key Coaching Moves

[Specific dialogue strategies — pausing, paraphrasing, probing — with examples of each]

### If the Conversation Gets Stuck

[What to do when the teacher deflects, becomes defensive, gives surface answers, or the conversation loses focus]

### Next Steps Template

[A clear format for the agreed next step — what the teacher will try, when, and when the coach will follow up]

**Self-check before returning output:** Verify that (a) the conversation is a partnership, not a lecture, (b) questions are open and reflective, not leading, (c) the conversation is grounded in or moves toward evidence, (d) the next step is specific and achievable, and (e) the coach's role is to facilitate the teacher's thinking, not to provide all the answers.
```

## Example Output

**Scenario:** *Coaching focus: "I want to improve my questioning — I know I ask too many closed questions and don't give students enough think time, but when I try to change, I revert to my old habits within minutes" / Teacher context: "3rd year teacher, History, genuinely motivated to improve, self-aware about the problem but frustrated that they can't fix it" / Observation data: "In a recent observation, the coach recorded 23 questions in 15 minutes. 19 were closed (yes/no or one-word answer). Average wait time after a question was 1.8 seconds. The same 5 students answered 80% of the questions." / Coaching phase: "Identify — first coaching conversation on this focus"*

---

## Coaching Conversation: Questioning and Think Time

**Focus:** Improving questioning — more open questions, longer think time, wider participation
**Teacher:** 3rd year, History, self-aware and motivated, frustrated by reversion to old habits
**Phase:** Identify

### Conversation Plan

**Opening (5 minutes):**
"Thanks for making time for this. Before we start — how's things? How's the week going?" [Genuine check-in. Build rapport. Do not rush into the data.]

Then: "You mentioned you wanted to work on questioning. Before I share what I noticed in the observation, I'd love to hear your perspective. What's your sense of how questioning goes in your lessons?"

*Why this question:* Asking the teacher's perspective FIRST honours the partnership principle. It also reveals their self-awareness — if they already know the issue, the coach doesn't need to "reveal" it. If their perception differs from the data, that gap becomes a discussion point.

*Anticipated response:* "I know I ask too many closed questions. I've tried to change but I keep reverting. It's really frustrating." — The teacher is self-aware. Affirm this and build on it.

*Coach move:* "That self-awareness is really valuable — a lot of teachers don't notice their questioning patterns at all. You've identified the pattern. What I'd like to do is look at some data together and see if we can figure out WHY the reversion happens and what we can do about it."

**Exploration (15 minutes):**

Question 1: "Can I share what I saw in the observation? I recorded some data on your questions — would you like to look at it together?"
*Why:* Introduces the data with permission. Maintains partnership — the teacher agrees to look at data, rather than having it delivered.

[Share the data: 23 questions in 15 minutes, 19 closed, 1.8 second wait time, 5 students answering 80%.]

Question 2: "What do you notice when you look at this data?"
*Why:* Lets the teacher interpret the data themselves rather than the coach telling them what it means. This builds analytical capacity.

*Anticipated response:* "That's worse than I thought. 19 out of 23 closed — and 1.8 seconds wait time is nothing."

*Coach move:* Paraphrase: "So the pattern is even more pronounced than you expected. 19 out of 23 is about 83% closed questions. And the wait time — 1.8 seconds — what do you think that means for students?"

Question 3: "You said you try to change but revert within minutes. Can you walk me through what happens? What does the reversion feel like?"
*Why:* This is the crucial question. Most coaching focuses on WHAT to change. This question focuses on WHY the change doesn't stick — which is where the real leverage is.

*Anticipated response:* "I plan open questions before the lesson. I ask one or two at the start. But then students give a short answer, or there's silence, and I panic and fill the space. Before I know it, I'm doing 'Does everyone understand?' and 'What's the answer to number 3?'"

*Coach move:* "So the silence is the trigger. You ask an open question, students don't respond immediately, and the discomfort of the silence pushes you back to closed questions. Is that right?"

Question 4: "What do you think students are doing during that silence? Is silence necessarily a bad thing?"
*Why:* Challenges the assumption that silence = failure. Silence after an open question may mean students are THINKING — which is exactly what think time is for.

*Anticipated response:* "I know they're probably thinking. But it doesn't FEEL like that in the moment. It feels like they're confused or I've asked a bad question."

*Coach move:* "So there's a gap between what you KNOW (silence is thinking time) and what you FEEL (silence means something's gone wrong). That's really common. The feeling is the enemy here, not the students."

Question 5: "If you could change just ONE thing about your questioning — not everything, just one thing — what would have the biggest impact?"
*Why:* Moves from analysis to action. Forces prioritisation — the teacher can't change everything at once. The coach's job is to help the teacher choose one specific, achievable change.

*Anticipated response:* "Probably the think time. If I could just WAIT after an open question, everything else might follow — students would have time to think, more students would be ready to answer, and I wouldn't need to fill the silence with closed questions."

**Action Planning (10 minutes):**

Question 6: "OK — think time. Let's make that really specific. How many seconds of silence would feel like progress?"
*Why:* Turns a vague goal into a measurable one.

*Anticipated:* "Five seconds? That sounds doable but it would feel like an eternity."

Question 7: "What would help you hold the silence? Some teachers count silently. Some hold up a hand to signal 'I'm waiting on purpose.' Some use a visual timer. What would work for you?"
*Why:* Provides options without directing. The teacher chooses the strategy that fits their style.

Question 8: "Here's what I'd suggest. In your next lesson, pick 3 moments where you'll ask an open question and wait 5 full seconds before taking any response. Just 3 moments — not the whole lesson. Would you be willing to try that?"
*Why:* Small, specific, achievable. Three moments is not overwhelming. The teacher can plan the 3 questions in advance, which makes the silence feel more manageable.

**Closing (5 minutes):**

"Let me summarise what we've agreed. You're going to plan 3 open questions for your next Year 8 lesson and wait a full 5 seconds after each one before accepting any response. I'll come and observe that lesson — not the whole lesson, just those 3 moments — and I'll record the wait time and who responds. We'll meet again next week to look at what happened. Does that feel right?"

### Key Coaching Moves

**Pausing:** After asking a question, wait. Don't fill the silence. The same think-time principle that applies to students applies to coaching conversations — the teacher needs time to think. Count to 5 in your head before speaking again.

**Paraphrasing:** Reflect the teacher's words back in slightly different language: "So what you're saying is that the silence feels uncomfortable, and that discomfort is what triggers the reversion to closed questions." This confirms understanding and helps the teacher hear their own thinking.

**Probing:** When the teacher gives a surface answer, go deeper: "You said 'I try but I can't change it.' What specifically happens in the moment when you revert? What are you feeling?" Probing is not interrogation — it's gentle curiosity that helps the teacher examine their practice more closely.

**Providing data (not opinion):** "I counted 1.8 seconds average wait time" is data. "Your wait time is too short" is opinion. Data invites reflection; opinion invites defensiveness.

### If the Conversation Gets Stuck

**If the teacher deflects:** ("It's not just me — the students don't want to answer open questions.") Acknowledge the frustration, then redirect to what's within the teacher's control: "You're right — student participation is partly about them. But the thing you CAN control is the type of question and the time you give them. Let's focus there."

**If the teacher becomes defensive:** ("Are you saying I'm a bad teacher?") Reassure immediately: "Not at all. You identified this as something you want to work on — that shows real professional awareness. The data is just a starting point so we can measure progress. This is about growth, not judgement."

**If the teacher gives only surface answers:** ("I just need to ask better questions.") Probe: "What would a 'better' question sound like? Can you give me an example?" This moves from abstract ("better") to concrete (an actual question they could ask).

### Next Steps Template

**What:** Plan 3 open questions and hold 5 seconds of think time after each.
**When:** Next Year 8 History lesson (specify date).
**Support:** The coach will observe the 3 moments and record wait time + student response data.
**Follow-up:** Coaching meeting next week (specify date) to review what happened.

---

## Known Limitations

1. **Coaching conversations require trust.** The conversation above assumes a willing teacher in a supportive coaching relationship. If the teacher is actively resistant (not just nervous but hostile to coaching), the conversation design must change — trust-building must precede instructional focus. This skill does not address severely resistant coaching dynamics, which require different strategies.

2. **Coaching is most effective as part of a sustained cycle.** One coaching conversation produces limited change. The meta-analysis by Kraft et al. (2018) found that coaching effects come from sustained cycles of goal-setting, observation, feedback, and adjustment. This conversation plan is one step in what should be an ongoing cycle.

3. **The coach needs coaching skills, not just the conversation plan.** Reading a script of questions is not the same as facilitating a genuine coaching dialogue. The pausing, paraphrasing, probing, and responsive facilitation described above require practice. Coaches should receive training and, ideally, coaching on their own coaching practice.

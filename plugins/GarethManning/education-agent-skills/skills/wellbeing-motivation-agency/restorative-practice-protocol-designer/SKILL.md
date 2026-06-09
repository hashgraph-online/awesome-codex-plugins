---
# AGENT SKILLS STANDARD FIELDS (v2)
name: restorative-practice-protocol-designer
description: "Design a restorative practice protocol for addressing harm, rebuilding trust, and restoring relationships. Use when managing conflict, behavioural incidents, or relationship breakdown between students."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/restorative-practice-protocol-designer"
skill_name: "Restorative Practice Protocol Designer"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Hopkins (2004) — Just Schools: a whole-school approach to restorative justice"
  - "Morrison (2007) — Restoring Safe School Communities: a whole-school response to bullying, violence and alienation"
  - "Zehr (2002) — The Little Book of Restorative Justice"
  - "Thorsborne & Blood (2013) — Implementing Restorative Practices in Schools"
  - "González (2015) — Restorative practices: from the evidence to whole-school implementation"
input_schema:
  required:
    - field: "incident_description"
      type: "string"
      description: "What happened — the behaviour or conflict that needs addressing"
    - field: "people_involved"
      type: "string"
      description: "Who was involved and in what roles — the person who caused harm, the person(s) affected, any witnesses"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "relationship_context"
      type: "string"
      description: "The relationship between those involved — friends, classmates, strangers, repeat pattern"
    - field: "previous_incidents"
      type: "string"
      description: "Whether this is a first occurrence or part of a pattern"
    - field: "severity"
      type: "string"
      description: "Low-level disruption, moderate conflict, serious harm"
    - field: "available_time"
      type: "string"
      description: "How much time can be allocated for the restorative process"
    - field: "school_policy"
      type: "string"
      description: "The school's behaviour policy context — is restorative practice embedded or being trialled?"
output_schema:
  type: "object"
  fields:
    - field: "restorative_protocol"
      type: "object"
      description: "The specific restorative process to use — restorative chat, restorative conference, or circle process"
    - field: "question_sequence"
      type: "array"
      description: "The specific restorative questions in order, adapted for the situation"
    - field: "preparation_guide"
      type: "object"
      description: "How to prepare participants before the restorative process"
    - field: "agreement_framework"
      type: "string"
      description: "How to reach and record a restorative agreement — what the participants commit to"
chains_well_with:
  - "belonging-classroom-culture-designer"
  - "trauma-informed-practice-designer"
  - "ruler-emotional-literacy-sequence"
  - "wellbeing-learning-connection-mapper"
teacher_time: "3 minutes"
tags: ["restorative-practice", "conflict-resolution", "relationships", "accountability", "repair"]
---

# Restorative Practice Protocol Designer

## What This Skill Does

Designs a specific restorative practice protocol for a classroom or school incident — selecting the right restorative approach (restorative chat, conference, or circle), providing the exact question sequence adapted for the situation and age group, guiding preparation of participants, and establishing an agreement framework for moving forward. The critical principle is that restorative practice is not the absence of consequences — it is a different KIND of consequence, one that requires the person who caused harm to understand the impact of their actions, take responsibility, and actively repair the damage. This is more demanding than a detention (which requires only that you sit in a room) and more effective (because it addresses the harm rather than just punishing the behaviour). The output is a ready-to-use protocol that a teacher or pastoral leader can follow step by step. AI is specifically valuable here because selecting the right restorative approach and calibrating the questions for the specific situation and age group requires both restorative justice expertise and practical school knowledge.

## Evidence Foundation

Zehr (2002) established the foundational framework: restorative justice asks three questions: What happened? Who was harmed and how? What needs to happen to make it right? This contrasts with punitive justice, which asks: What rule was broken? Who broke it? What punishment do they deserve? Hopkins (2004) applied restorative principles to schools through the "Just Schools" model, showing that whole-school restorative approaches reduce exclusions, improve relationships, and create safer learning environments. Morrison (2007) demonstrated that restorative practice operates on three levels: primary (prevention — building relationships and community), secondary (intervention — addressing harm when it occurs), and tertiary (intensive — rebuilding relationships after serious harm). Thorsborne & Blood (2013) provided practical implementation guidance, emphasising that restorative practice is a continuum from informal conversations (restorative chat — 5 minutes) through facilitated conferences (30–60 minutes) to formal circles (for serious harm or whole-class issues). González (2015) reviewed evidence on restorative practices in schools and found reductions in exclusions, suspensions, and racial disparities in discipline — though implementation quality was the key predictor of success.

## Input Schema

The teacher must provide:
- **Incident description:** What happened. *e.g. "Two Year 9 students had a verbal argument in the corridor that escalated to pushing. Both are upset and blaming each other." / "A Year 7 student has been persistently making fun of another student's accent during group work." / "A Year 10 student swore at a teacher during a lesson after being asked to put their phone away."*
- **People involved:** Who and what roles. *e.g. "Student A (pushed first), Student B (pushed back), three witnesses" / "Student X (making comments), Student Y (target), several group members who laughed"*
- **Student level:** Year group. *e.g. "Year 9"*

Optional (injected by context engine if available):
- **Relationship context:** The relationship between those involved
- **Previous incidents:** Pattern or first occurrence
- **Severity:** Low/moderate/serious
- **Available time:** How much time
- **School policy:** Behaviour policy context

## Prompt

```
You are an expert in restorative practice in education, with deep knowledge of Zehr's (2002) restorative justice framework, Hopkins' (2004) whole-school approach, Morrison's (2007) three-level model, and Thorsborne & Blood's (2013) implementation continuum. You understand that restorative practice is not "being soft on behaviour" — it is a structured, demanding process that requires the person who caused harm to face the impact of their actions, take genuine responsibility, and commit to specific actions to repair the harm. This is harder than serving a detention.

IMPORTANT: Restorative practice does NOT mean there are no consequences. It means the consequences are RESTORATIVE (repairing the harm) rather than PUNITIVE (inflicting suffering). A student who has harmed someone and goes through a restorative process should emerge having understood the impact, apologised genuinely, and committed to specific changes. If the school's behaviour policy requires additional sanctions alongside the restorative process, these can coexist — the restorative process addresses the relationship; the sanction addresses the rule breach.

IMPORTANT: Restorative practice requires PREPARATION. Throwing two angry students into a room and asking "How do you both feel?" without preparation will fail. Each participant must be individually prepared before the restorative process.

Select the appropriate restorative approach:
- **Restorative chat (5–10 minutes):** For low-level incidents — a quick, structured conversation between the teacher and the student, or between two students. Uses the 5 restorative questions.
- **Restorative conference (20–45 minutes):** For moderate incidents — a facilitated meeting between the person who caused harm, the person affected, and possibly supporters or witnesses. Structured with clear phases.
- **Restorative circle (30–60 minutes):** For serious incidents or whole-class issues — a facilitated circle where all affected parties participate. Uses a talking piece and structured rounds.

Your task is to design a restorative protocol for:

**Incident description:** {{incident_description}}
**People involved:** {{people_involved}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Relationship context:** {{relationship_context}} — if not provided, design for the relationships as described.
**Previous incidents:** {{previous_incidents}} — if not provided, treat as a standalone incident but note that pattern-checking is important.
**Severity:** {{severity}} — if not provided, infer from the description.
**Available time:** {{available_time}} — if not provided, recommend the appropriate time based on severity.
**School policy:** {{school_policy}} — if not provided, design a standalone restorative process.

Apply these principles:

1. **The core restorative questions (Zehr, 2002; Hopkins, 2004):**
   - What happened? (Understanding the event from each perspective)
   - What were you thinking/feeling at the time?
   - What have you thought/felt since?
   - Who has been affected and how?
   - What needs to happen to make things right?

2. **Prepare before the process (Thorsborne & Blood, 2013):**
   - Meet individually with each participant before bringing them together.
   - Assess emotional readiness — the process won't work if participants are still in fight/flight.
   - Explain the process: what will happen, what's expected, what the outcome should be.
   - Check willingness — restorative practice works best when participation is voluntary (though schools may require it).

3. **Facilitate, don't interrogate (Hopkins, 2004):**
   - The facilitator asks questions and holds the space — they do not judge, lecture, or take sides.
   - Allow silence. Allow emotion. Allow the process to be uncomfortable — discomfort is part of facing impact.
   - The facilitator ensures both parties are heard — not equally in volume, but equally in respect.

4. **Reach a genuine agreement (Morrison, 2007):**
   - The agreement must be specific: "I will..." not "I'll try to..."
   - The agreement must be owned by the participants, not imposed by the facilitator.
   - The agreement must be checked: set a follow-up date to review whether the agreement has been kept.

5. **Address the relationship, not just the incident:**
   - The goal is to repair the relationship so that both parties can coexist safely in the school community.
   - A restored relationship is one where both parties feel respected, heard, and safe — not necessarily friends, but able to learn together.

Return your output in this exact format:

## Restorative Protocol: [Incident Type]

**Incident:** [Summary]
**People involved:** [Roles]
**Approach:** [Chat / Conference / Circle]
**Estimated time:** [Duration]

### Preparation Phase

**Meeting with [Person A]:**
[What to say and ask — specific script]

**Meeting with [Person B]:**
[What to say and ask — specific script]

### The Restorative Process

[Step-by-step facilitation guide with specific questions adapted for this situation]

### Agreement Framework

[How to reach and record the agreement]

### Follow-Up

[When and how to check that the agreement is being kept]

### If It Doesn't Work

[What to do if the process stalls — participant refuses, emotions escalate, no agreement reached]

**Self-check before returning output:** Verify that (a) the appropriate restorative approach is selected for the severity, (b) preparation is included, (c) questions are adapted for the specific situation, (d) the agreement is specific and achievable, (e) follow-up is planned, and (f) the process holds the person who caused harm accountable while giving voice to the person affected.
```

## Example Output

**Scenario:** *Incident description: "A Year 7 student (Student A) has been persistently making fun of another student's (Student B's) accent during group work. This has happened at least 4 times over the past two weeks. Student B has become increasingly withdrawn — they now refuse to speak during group work and have asked to work alone. Other group members sometimes laughed, which encouraged Student A." / People involved: "Student A (making comments), Student B (target), 3 other group members who witnessed/laughed" / Student level: "Year 7" / Severity: "Moderate — persistent pattern causing visible emotional harm"*

---

## Restorative Protocol: Persistent Mockery of Accent

**Incident:** Repeated mockery of Student B's accent during group work, causing withdrawal and distress
**People involved:** Student A (caused harm), Student B (affected), 3 witnesses/participants
**Approach:** Restorative conference — moderate severity, persistent pattern, multiple people involved
**Estimated time:** 30–40 minutes (plus 10 minutes preparation with each participant)

### Preparation Phase

**Meeting with Student A (10 minutes, individual):**
"I want to talk to you about something that's been happening in group work. I'm not here to tell you off — I want to understand what's been going on and figure out how to move forward. Can you tell me what's been happening with [Student B's name] in your group?"

Listen. Then:
"I've noticed that [Student B] has stopped talking in group work. Did you know that? ... How do you think they might be feeling about the comments about their accent? ... I'd like you to hear from [Student B] about how this has affected them. Would you be willing to sit down together and talk about it? The goal isn't to punish you — it's to understand the impact and figure out what needs to happen next."

If Student A minimises ("It was just a joke"): "I hear you — you might have meant it as a joke. But the effect on [Student B] is that they've stopped speaking in class. Whether you intended it or not, the impact is real. That's what we need to address."

Check emotional readiness: Is Student A calm enough to listen? If they're angry or defensive, allow time: "Let's meet again after lunch — I want you to have time to think about this."

**Meeting with Student B (10 minutes, individual):**
"I know things have been difficult in group work. I've seen that you've been quieter recently, and I want to make sure you feel safe and supported. Can you tell me what's been happening?"

Listen. Validate: "That sounds really hurtful. No one should be made to feel uncomfortable about how they speak."

Then: "I'm going to talk to [Student A] about this. I'd like you to be part of a conversation where you can tell them how this has affected you — in your own words. You won't be alone — I'll be there to facilitate. But you'll have the chance to be heard. Would you be willing to do that?"

If Student B is reluctant: "You don't have to speak to them if you're not ready. But I think it would help [Student A] to hear directly from you what this has been like. I'll make sure the conversation is safe and respectful. If at any point you want to stop, you can."

Prepare Student B for what will happen: who will be there, what questions will be asked, that they'll speak first, that they can stop at any time.

### The Restorative Process

**Setting:** A quiet room. Chairs in a small circle (no table — tables create barriers). The facilitator sits between Student A and Student B. Witnesses are invited if both parties agree; otherwise, this is between Student A and Student B.

**Opening (2 minutes):**
"Thank you both for being here. This conversation is about understanding what happened, how it's affected people, and what needs to happen to make things right. I'm going to ask you both some questions. The rules are: one person speaks at a time, we listen to each other, and we're honest. This isn't about blame — it's about understanding and repair. [Student B], I'd like you to go first."

**Phase 1 — Hearing the impact (10 minutes):**

To Student B: "Can you describe what's been happening in group work?"
[Let them speak. Don't interrupt.]

"How did you feel when [Student A] made those comments?"
[Let them speak.]

"How has it affected you since? I've noticed you've been working alone — can you tell us about that?"
[Let them speak.]

To Student A: "You've heard what [Student B] has said. What are you thinking right now?"
[This is the key moment. Student A is hearing the impact directly. Allow silence. Allow discomfort. Do not rescue Student A from the discomfort — it is the mechanism of accountability.]

**Phase 2 — Understanding the behaviour (10 minutes):**

To Student A: "Can you tell us what happened from your perspective? What were you thinking when you made those comments?"
[Listen without judging.]

"Did you know how [Student B] was feeling?"
[Listen.]

"What do you think about what you've heard today — about the effect this has had?"
[This is where genuine accountability emerges. Look for: recognition of impact, expression of remorse, willingness to change. If Student A minimises again: "I hear you — but [Student B] has told you that they stopped speaking in class because of this. That's a significant impact. What do you think about that?"]

**Phase 3 — Making it right (10 minutes):**

To Student B: "What do you need from [Student A] to feel safe and comfortable in group work again?"
[Let them speak. Their needs might include: an apology, a commitment to stop the comments, the group members being addressed.]

To Student A: "You've heard what [Student B] needs. What are you willing to do?"
[The agreement must come from Student A — it is not imposed. If Student A offers less than Student B needs, facilitate: "Can you think about what [Student B] asked for? What specifically can you commit to?"]

To both: "Is there anything else either of you wants to say before we agree on next steps?"

### Agreement Framework

Record the agreement in writing (both students sign):
- What Student A commits to doing (specific actions, e.g., "I will not comment on anyone's accent. If I catch myself about to, I will stop. If [Student B] feels I've broken this agreement, they can tell [facilitator].")
- What Student B needs to see to feel safe (specific indicators)
- What happens if the agreement is broken (return to restorative process, or escalation to senior leadership if persistent)
- Follow-up date: "We'll meet again in one week to check how things are going."

Address the witnesses separately: "Some people in the group laughed when [Student A] made those comments. The laughter made it harder for [Student B]. In our group from now on, if someone makes a comment that's unkind, we don't laugh — we check on the person it was aimed at."

### Follow-Up

**One week later:** Brief check-in with both students individually.
- To Student B: "How has group work been this week? Do you feel safer? Have the comments stopped?"
- To Student A: "How have you found this week? Have you stuck to the agreement?"

If the agreement is being kept: acknowledge and close.
If the agreement has been broken: reconvene. "We agreed on [specific terms] last week. [Student B] tells me [what happened]. Let's talk about why the agreement wasn't kept and what needs to change."

### If It Doesn't Work

**If Student A refuses to participate:** "I can't force you to have this conversation. But the behaviour needs to stop. I'm going to [describe the alternative — speaking with parents, involving head of year, formal warning]. I'd prefer us to sort this out together — would you be willing to try?"

**If emotions escalate during the process:** Pause. "Let's take a moment. This is difficult for both of you. I'm going to ask you to take three breaths, and then we'll continue." If a participant becomes too distressed to continue, end the session and reschedule: "We're going to stop here today. I can see this is really hard. Let's come back to this tomorrow when we've both had time to think."

**If no agreement is reached:** Summarise what WAS agreed and what remains unresolved. Escalate the unresolved element to a senior leader for mediation. The restorative process has still been valuable — Student A has heard the impact, even if they haven't fully accepted responsibility yet.

---

## Known Limitations

1. **Restorative practice requires facilitator skill.** The protocol above provides the structure, but the facilitation — reading body language, holding silence, managing emotion, redirecting minimisation — requires practice. Teachers new to restorative approaches should start with restorative chats (simpler) before attempting conferences (more complex).

2. **Restorative practice is not appropriate for all situations.** Situations involving significant power imbalances (persistent bullying, abuse, harassment) may not be suitable for a face-to-face restorative conference, as the affected person may feel unsafe speaking directly to the person who harmed them. In these cases, the facilitator can shuttle between the parties rather than bringing them together, or an alternative approach may be needed.

3. **Restorative practice takes more time than punishment.** A detention takes zero preparation and zero facilitator skill. A restorative conference takes 30–40 minutes plus preparation. The investment pays off in reduced repeat incidents and improved relationships, but the initial time cost is significant and must be supported by school leadership.

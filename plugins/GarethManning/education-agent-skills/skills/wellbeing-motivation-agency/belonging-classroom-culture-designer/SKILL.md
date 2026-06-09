---
# AGENT SKILLS STANDARD FIELDS (v2)
name: belonging-classroom-culture-designer
description: "Design targeted interventions that strengthen belonging and inclusion for specific classroom dynamics. Use when students feel isolated, cliques form, or new students need integrating."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/belonging-classroom-culture-designer"
skill_name: "Belonging & Classroom Culture Designer"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Walton & Cohen (2011) — A brief social-belonging intervention improves academic and health outcomes of minority students"
  - "Yeager & Walton (2011) — Social-psychological interventions in education"
  - "Baumeister & Leary (1995) — The need to belong: desire for interpersonal attachments as a fundamental human motivation"
  - "Goodenow (1993) — Classroom belonging among early adolescent students"
  - "Murphy & Zirkel (2015) — Race and belonging in school: how anticipated and experienced belonging affect choice, persistence, and performance"
input_schema:
  required:
    - field: "classroom_context"
      type: "string"
      description: "Description of the class — subject, year group, and any relevant features of the group dynamic"
    - field: "belonging_concern"
      type: "string"
      description: "The specific belonging issue — e.g. isolated students, cliques, marginalised groups, new students, post-transition anxiety"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: class composition, social dynamics, SEN, EAL, Pupil Premium"
    - field: "current_practices"
      type: "string"
      description: "What the teacher already does to build belonging — so recommendations don't duplicate"
    - field: "time_available"
      type: "string"
      description: "How much time can be allocated to belonging-building practices"
output_schema:
  type: "object"
  fields:
    - field: "belonging_practices"
      type: "array"
      description: "Specific, named classroom practices that build belonging — not generic advice but implementable actions"
    - field: "routine_integration"
      type: "object"
      description: "How to embed belonging practices into existing routines rather than adding extra activities"
    - field: "language_guide"
      type: "object"
      description: "Specific teacher language that signals belonging vs. language that inadvertently threatens it"
    - field: "monitoring_indicators"
      type: "array"
      description: "Observable signs that belonging is improving — what to watch for"
chains_well_with:
  - "motivation-diagnostic-task-redesign"
  - "trauma-informed-practice-designer"
  - "ruler-emotional-literacy-sequence"
  - "restorative-practice-protocol-designer"
teacher_time: "3 minutes"
tags: ["belonging", "inclusion", "classroom-culture", "relationships", "equity", "marginalisation"]
---

# Belonging & Classroom Culture Designer

## What This Skill Does

Generates specific, implementable classroom practices that build belonging for all students — with particular attention to students who are most likely to experience belonging uncertainty (new students, minority students, students with SEN, EAL students, students transitioning between schools). The critical insight from Walton & Cohen's research is that belonging is not a personality trait — it is a perception that is highly sensitive to environmental cues. Small signals from the classroom environment ("You matter here," "People like you succeed here," "Difficulty is normal, not a sign you don't belong") can have disproportionate effects on engagement, persistence, and achievement. The output includes specific practices (not generic advice like "be welcoming"), language guides (what to say and what to avoid), integration into existing routines (so belonging-building doesn't require extra time), and monitoring indicators (how to know it's working). AI is specifically valuable here because belonging research identifies subtle environmental cues that most teachers don't consciously design for — and because the practices that build belonging for marginalised students often benefit ALL students.

## Evidence Foundation

Walton & Cohen (2011) demonstrated that a single, brief belonging intervention — normalising the worry that "people like me don't belong here" — closed the achievement gap between Black and White students by 52% over three years. The mechanism is not complicated: when students worry they don't belong, they interpret setbacks as confirming evidence ("I got a low mark because I don't fit in here"). When that worry is addressed, the same setback is interpreted as a normal part of learning ("Everyone struggles sometimes"). Baumeister & Leary (1995) established belongingness as a fundamental human need — as basic as food and safety. When the need is unmet, cognitive resources are diverted from learning to belonging-monitoring: "Does the teacher like me? Do the other students accept me? Am I welcome here?" This monitoring consumes working memory and attention that should be directed toward learning. Goodenow (1993) found that classroom belonging predicted motivation, effort, and achievement in early adolescence — students who felt they belonged tried harder, persisted longer, and learned more. Yeager & Walton (2011) showed that social-psychological interventions (belonging, growth mindset, purpose) are most effective when they are "stealthy" — embedded in normal classroom practice rather than announced as special programmes. Murphy & Zirkel (2015) extended this to demonstrate that anticipated belonging (expecting to belong vs. expecting not to) affects students' choices before they even arrive — students who anticipate not belonging are less likely to choose challenging courses, join clubs, or seek help.

## Input Schema

The teacher must provide:
- **Classroom context:** The class and its features. *e.g. "Year 7 English, 28 students, first term after primary-secondary transition. Mixed-ability. Several students from different primary schools who don't know anyone." / "Year 10 GCSE Science, small class of 18, mostly boys, three girls who rarely speak in class."*
- **Belonging concern:** The specific issue. *e.g. "Several students are isolated — they don't interact with anyone and look uncomfortable" / "Two students recently arrived from another country and speak limited English" / "There are strong cliques and some students are excluded from group work"*

Optional (injected by context engine if available):
- **Student level:** Year group
- **Subject area:** The curriculum subject
- **Student profiles:** Class composition, social dynamics
- **Current practices:** What the teacher already does
- **Time available:** Time that can be allocated

## Prompt

```
You are an expert in belonging, classroom culture, and social-psychological interventions in education, with deep knowledge of Walton & Cohen's (2011) belonging intervention research, Baumeister & Leary's (1995) belongingness theory, Goodenow's (1993) work on classroom belonging, and Yeager & Walton's (2011) principles for effective social-psychological interventions. You understand that belonging is a perception shaped by environmental cues — and that teachers can deliberately design those cues.

IMPORTANT: Belonging interventions are most effective when they are "stealthy" (Yeager & Walton, 2011) — embedded in normal classroom routines, not announced as special programmes. Do NOT recommend singling out students who seem isolated or making belonging the explicit topic of a lesson. This approach often backfires because it draws attention to the very belonging threat it's trying to address. Instead, design practices that communicate belonging to everyone, with particular benefit to those who need it most.

IMPORTANT: Belonging practices must be genuine, not performative. Students — especially adolescents — can detect inauthenticity. "Forced fun" activities that feel artificial will be counterproductive. The practices should feel like a natural part of how the classroom operates.

Your task is to design belonging practices for:

**Classroom context:** {{classroom_context}}
**Belonging concern:** {{belonging_concern}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, infer from the classroom context.
**Subject area:** {{subject_area}} — if not provided, infer from the context.
**Student profiles:** {{student_profiles}} — if not provided, design for the stated belonging concern.
**Current practices:** {{current_practices}} — if not provided, design from a baseline of standard classroom practice.
**Time available:** {{time_available}} — if not provided, design practices that fit within existing lesson time (no extra time required).

Apply these evidence-based principles:

1. **Normalise difficulty (Walton & Cohen, 2011):**
   - When students struggle, the message must be "Struggling is normal — everyone finds this hard at first" not "You need extra help" (which can signal "You don't belong in this group").
   - Use stories of struggle: "When I first learned this, I found it confusing too" or "Last year's class also found this challenging at first."
   - Difficulty should be framed as UNIVERSAL, not individual.

2. **Signal that "people like you" succeed here (Murphy & Zirkel, 2015):**
   - Students need to see examples of people like them succeeding in this subject and classroom.
   - Representation in materials, examples, and stories matters.
   - Use language that explicitly includes: "In this class, we all..." / "Everyone here..."

3. **Create structured interaction (Goodenow, 1993):**
   - Isolated students rarely self-initiate interaction. The teacher must CREATE opportunities for interaction through structured pair/group work.
   - Structure is essential: "Talk to your partner about..." gives isolated students permission to interact without the social risk of initiating.
   - Rotate partnerships regularly — don't allow self-selection (which reinforces existing cliques) but don't make it obvious that you're engineering relationships.

4. **Build belonging through contribution, not just inclusion (Yeager & Walton, 2011):**
   - Being included (having a seat, being allowed to participate) is not the same as belonging (feeling valued, needed, important to the group).
   - Students feel belonging when they CONTRIBUTE — when their ideas matter, when the group needs their input, when they add something others don't.
   - Design tasks where every student has a role that the group depends on.

5. **Monitor and adjust (Goodenow, 1993):**
   - Belonging is not built in one lesson. It requires consistent signals over time.
   - Watch for indicators: who speaks in class, who makes eye contact, who arrives willingly vs. reluctantly, who is chosen for group work, who is left out.

Return your output in this exact format:

## Belonging Practices: [Classroom Context]

**Context:** [Summary]
**Belonging concern:** [The specific issue]

### Recommended Practices

For each practice (4–6):
**Practice [N]: [Name]**
- **What to do:** [Specific, implementable steps]
- **When to do it:** [Where it fits in the lesson or routine]
- **Why it builds belonging:** [Which principle it targets]
- **What it looks like when it's working:** [Observable indicators]

### Language Guide

**Phrases that build belonging:**
[Specific teacher language with explanation of why each phrase works]

**Phrases to avoid:**
[Specific teacher language that inadvertently threatens belonging, with explanation]

### Routine Integration

[How to embed these practices into existing classroom routines — not as add-ons but as part of how the classroom already works]

### Monitoring Indicators

[What to watch for to know whether belonging is improving — observable signs, not survey data]

**Self-check before returning output:** Verify that (a) practices are specific and implementable, not generic advice, (b) practices are "stealthy" — embedded in normal routines, not announced as belonging programmes, (c) practices benefit all students while particularly addressing the stated concern, (d) no practice singles out or draws attention to isolated students, and (e) the language guide distinguishes belonging-building language from belonging-threatening language.
```

## Example Output

**Scenario:** *Classroom context: "Year 7 English, 28 students, first term after primary-secondary transition. Mixed-ability. Students came from 6 different primary schools — some know several classmates, others know nobody. The class is generally well-behaved but very quiet — most students won't volunteer answers or contribute to discussion." / Belonging concern: "Several students are isolated — they sit alone, don't talk to anyone before or after class, and look visibly uncomfortable during group work. Two students have started avoiding the lesson (late arrival, asking to go to the toilet frequently). I'm worried they feel like they don't belong."*

---

## Belonging Practices: Year 7 English Post-Transition

**Context:** Year 7 English, 28 students, first term, post-transition from multiple primary schools
**Belonging concern:** Several isolated students showing avoidance behaviours; class very quiet — low participation

### Recommended Practices

**Practice 1: Structured Pair Talk With Rotating Partners**
- **What to do:** At least twice per lesson, use "talk to your partner" — but ASSIGN partners rather than letting students choose. Use a seating plan that changes every 2 weeks. Pair isolated students with warm, socially confident students (not other isolated students — this reinforces isolation rather than building bridges). Use a timer (90 seconds) and a specific prompt: "Tell your partner one thing you noticed about the opening of this text."
- **When to do it:** After any question that requires thinking. Replace "hands up" (which lets 4–5 students dominate) with "talk to your partner first, then I'll ask some of you to share."
- **Why it builds belonging:** Structured pairing creates interaction without social risk. The student doesn't have to choose who to talk to (anxiety-inducing for isolated students), the task is clear (no ambiguity about what to say), and the timer provides a safe endpoint. Over 2-week rotations, every student will have worked with multiple classmates — building the low-level familiarity that is the foundation of belonging.
- **What it looks like when it's working:** Isolated students begin talking to their assigned partner without hesitation. After several weeks, you may notice students chatting briefly before or after the structured task. This is the belonging signal — they've moved from "assigned interaction" to "voluntary interaction."

**Practice 2: Contribution Tokens**
- **What to do:** During group discussion or group work, give each group member a role that the group cannot complete without: Reader (reads the text aloud), Recorder (writes the group's ideas), Reporter (shares with the class), Challenger (asks "But what about...?"). Rotate roles across lessons. Do NOT assign isolated students to "Reporter" early on — start them with Reader or Recorder (lower social exposure) and move to Reporter once they are comfortable.
- **When to do it:** Every time group work happens.
- **Why it builds belonging:** Belonging is built through CONTRIBUTION (Yeager & Walton, 2011). When a student has a role the group depends on, they shift from "tolerated presence" to "valued member." The role makes their contribution visible without requiring them to self-advocate.
- **What it looks like when it's working:** Isolated students begin taking ownership of their role. Group members start addressing the isolated student by name: "What did you write down?" (which signals they are needed). The student begins to volunteer for roles rather than waiting to be assigned.

**Practice 3: Normalising Difficulty Through Story**
- **What to do:** When introducing a challenging task, briefly normalise the difficulty: "This is one of the hardest things in Year 7 English — every year, students find this tricky at first. By the end of the unit, you'll look back and wonder why it seemed so hard. But right now, if it feels confusing, that's completely normal." Do this BEFORE students attempt the task, not after they've failed.
- **When to do it:** At the start of any challenging new concept or task.
- **Why it builds belonging:** Walton & Cohen (2011) showed that students who worry about belonging interpret difficulty as evidence they don't belong ("I'm struggling because I'm not meant to be here"). Normalising difficulty pre-empts this: difficulty becomes evidence of the task being hard (universal) rather than evidence of the student not belonging (individual). The phrase "every year" is important — it signals that struggling students are part of a normal pattern, not outliers.
- **What it looks like when it's working:** Students begin to say things like "This is hard" without shame — they've internalised that difficulty is expected, not threatening. Students who would previously shut down when stuck start asking for help instead — because asking for help no longer feels like admitting they don't belong.

**Practice 4: Name-Rich Classroom**
- **What to do:** Use students' names constantly and correctly. Learn them within the first week (use a seating plan photograph). Use names when asking questions ("Aisha, what did you think?"), when giving feedback ("That's a really interesting point, Marcus"), when greeting students at the door ("Morning, Priya — glad you're here"), and when narrating positive behaviour ("I can see Leon has already started annotating the text").
- **When to do it:** Every interaction, every lesson.
- **Why it builds belonging:** A student's name is the most basic signal of being known. In primary school, teachers knew every student's name. In secondary, students can go weeks without hearing a teacher use their name. For isolated students, hearing their name — spoken warmly, in a positive context — is a direct signal: "You are seen. You are known. You exist in this room."
- **What it looks like when it's working:** Students make eye contact when you say their name. Students respond more readily when addressed by name than when addressed as "you" or "everyone." Isolated students begin to seem less invisible — they look up, they engage, they exist in the social space of the classroom.

**Practice 5: Exit Routines That Include Everyone**
- **What to do:** End every lesson with a 30-second routine that includes every student: a quick round ("One word to describe what you learned today — go round the table"), a written exit ticket that the teacher reads and responds to (a personal connection), or a "3-2-1" (3 things learned, 2 questions, 1 thing you found interesting — written, not spoken). Respond to exit tickets with brief personal comments: "Great question, Fatima — we'll explore that next lesson."
- **When to do it:** Last 2 minutes of every lesson.
- **Why it builds belonging:** An exit routine that touches every student ensures that no one leaves invisible. The teacher's personal response ("Great question, Fatima") is a belonging signal — it says "I read what you wrote. Your thoughts matter to me." For isolated students, this may be the only personal interaction they have with the teacher in a lesson.
- **What it looks like when it's working:** Students begin writing more detailed exit tickets (they know the teacher reads them). Students who were previously reluctant to share begin contributing to the round. The routine becomes something students expect — and its absence is noticed.

### Language Guide

**Phrases that build belonging:**
- "In this class, we all..." — signals group membership. "In this class, we all make mistakes — that's how we learn."
- "I noticed that..." — signals being seen. "I noticed you chose an unusual quotation — tell me why."
- "That's a really interesting way to think about it" — signals that the student's perspective has VALUE, not just correctness.
- "Everyone found this hard last year too" — normalises difficulty. Universal, not individual.
- "What do you think?" (addressed to a specific student by name, after pair talk) — invites contribution after they've had time to prepare. This is safe because they've already rehearsed their answer with a partner.
- "We need your ideas on this" — signals that the student's contribution is needed, not just tolerated.

**Phrases to avoid:**
- "Come on, don't be shy" — labels the student as shy (an identity) rather than addressing the environment (a condition). Belonging is about the environment, not the person.
- "Does anyone want to...?" — self-selection privileges confident students and forces isolated students to publicly decide not to participate. Use structured turns instead.
- "You should try to make more friends" — makes belonging the student's responsibility. Belonging is an environmental design problem, not a social skills problem.
- "I know this is hard for some of you" — divides the class into those who find it hard and those who don't. Use "this is hard" (universal) instead.
- "Well done for trying" (when the student failed) — patronising. Suggests the teacher expected failure. "That's not quite right yet — here's how to get there" is more respectful.

### Routine Integration

These practices require NO additional time:
- **Pair talk** replaces "hands up" — same time, better participation.
- **Contribution roles** replace unstructured group work — same time, more equitable.
- **Normalising difficulty** takes 15 seconds before a task — no extra time.
- **Name use** is embedded in existing interactions — no extra time.
- **Exit routine** takes 2 minutes, replacing "pack up and go" — minimal extra time, significant belonging payoff.

The key shift is not ADDING belonging activities but REDESIGNING existing routines so they build belonging. This is Yeager & Walton's (2011) "stealth" principle: the most effective belonging interventions don't look like belonging interventions. They look like good teaching.

### Monitoring Indicators

Watch for these changes over 4–6 weeks:
1. **Arrival behaviour:** Do isolated students arrive on time, or are they still avoiding entry? Do they hover outside or walk in?
2. **Body language during pair talk:** Do they face their partner, make eye contact, speak at normal volume? Or do they turn away, whisper, look at the teacher for rescue?
3. **Voluntary interaction:** Do isolated students ever speak to another student unprompted — before the lesson, during transition, at the end?
4. **Task engagement:** Do they start tasks within the first minute, or do they delay? Do they write/work/annotate, or sit idle?
5. **Response to name:** Do they look up when you use their name? Do they seem surprised (been invisible) or comfortable (used to being seen)?
6. **Help-seeking:** Do they ask for help when stuck, or do they sit silently? Help-seeking requires a basic level of belonging — the belief that the teacher will respond and won't judge.

---

## Known Limitations

1. **Belonging interventions are slow-burn, not instant fixes.** The practices above will not transform classroom culture in a week. Belonging is built through consistent signals over time — weeks and months, not days. Teachers who expect immediate results may abandon effective practices too early.

2. **Some belonging threats originate outside the classroom.** A student being bullied at break time, experiencing family difficulties, or struggling with identity will not have their belonging needs fully met by classroom practices alone. The practices above address the classroom environment, which is within the teacher's control — but the teacher should also connect with pastoral systems for students whose belonging needs extend beyond the classroom.

3. **Belonging practices must be genuine.** If a teacher uses students' names but their tone is cold, or assigns roles but doesn't value the contributions, the practices become performative — and students will detect the inauthenticity. The practices work because they communicate genuine regard. They cannot be implemented mechanically without the underlying disposition.

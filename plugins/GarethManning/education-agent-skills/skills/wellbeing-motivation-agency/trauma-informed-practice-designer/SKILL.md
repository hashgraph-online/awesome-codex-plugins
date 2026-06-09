---
# AGENT SKILLS STANDARD FIELDS (v2)
name: trauma-informed-practice-designer
description: "Design trauma-informed classroom practices that prioritise safety, predictability, connection, and regulation. Use when student behaviour may be trauma-related or the class needs a sensitive approach."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/trauma-informed-practice-designer"
skill_name: "Trauma-Informed Practice Designer"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "van der Kolk (2014) — The Body Keeps the Score: brain, mind, and body in the healing of trauma"
  - "Perry (2006) — The Boy Who Was Raised as a Dog: neurosequential model of therapeutics"
  - "Felitti et al. (1998) — Relationship of childhood abuse and household dysfunction to many of the leading causes of death in adults (ACE Study)"
  - "Bergin & Bergin (2009) — Attachment in the classroom"
  - "Craig (2016) — Trauma-Sensitive Schools: learning communities transforming children's lives"
input_schema:
  required:
    - field: "classroom_situation"
      type: "string"
      description: "The situation or behaviour that may be trauma-related — what the teacher is observing"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "known_context"
      type: "string"
      description: "What the teacher knows about the student's background — only include what is relevant and shared appropriately"
    - field: "current_responses"
      type: "string"
      description: "How the school currently responds to the behaviour"
    - field: "available_support"
      type: "string"
      description: "Pastoral systems, counsellor, SENCO, external agencies available"
    - field: "class_context"
      type: "string"
      description: "Other students in the class — how the behaviour affects the learning environment"
output_schema:
  type: "object"
  fields:
    - field: "trauma_lens_analysis"
      type: "object"
      description: "Reframing the behaviour through a trauma-informed lens — what the behaviour might be communicating"
    - field: "classroom_adaptations"
      type: "array"
      description: "Specific modifications to classroom practice that create safety without lowering expectations"
    - field: "response_protocols"
      type: "object"
      description: "What to do when trauma-related behaviour occurs — de-escalation, co-regulation, repair"
    - field: "boundaries"
      type: "string"
      description: "Clear statement of what trauma-informed practice IS and IS NOT — maintaining boundaries while being compassionate"
chains_well_with:
  - "belonging-classroom-culture-designer"
  - "restorative-practice-protocol-designer"
  - "ruler-emotional-literacy-sequence"
  - "differentiation-adapter"
teacher_time: "4 minutes"
tags: ["trauma-informed", "ACEs", "safety", "regulation", "attachment", "behaviour"]
---

# Trauma-Informed Practice Designer

## What This Skill Does

Designs trauma-informed classroom practices that create safety, predictability, and connection for students who have experienced adverse childhood experiences (ACEs) — while maintaining clear boundaries, academic expectations, and a functional learning environment for all students. The critical principle is that trauma-informed practice is not about lowering expectations or excusing behaviour — it is about understanding that behaviour communicating distress requires a different response from behaviour communicating defiance, because the underlying cause is different and punitive responses to trauma-related behaviour typically escalate rather than resolve it. The output includes a trauma-lens reframing of the observed behaviour, specific classroom adaptations, response protocols for when trauma-related behaviour occurs, and clear boundaries about what trauma-informed practice IS and IS NOT. AI is specifically valuable here because trauma-informed practice requires understanding the neuroscience of trauma (how trauma affects the brain and body), the psychology of attachment (how early relationships shape classroom behaviour), and the pedagogy of safety (how to create conditions where all students can learn) — a multi-disciplinary knowledge base that most teachers have limited training in.

## Evidence Foundation

Felitti et al. (1998) conducted the landmark Adverse Childhood Experiences (ACE) study, showing that childhood adversity (abuse, neglect, household dysfunction) is both common and consequential: approximately two-thirds of participants reported at least one ACE, and ACE scores predicted health, mental health, and social outcomes decades later. In educational contexts, high ACE scores predict lower academic achievement, higher rates of school exclusion, and greater behavioural and emotional difficulties. Van der Kolk (2014) demonstrated that trauma fundamentally changes the brain — specifically the amygdala (threat detection), prefrontal cortex (executive function and impulse control), and hippocampus (memory). A traumatised brain is stuck in survival mode: hypervigilant to threat, quick to activate fight/flight/freeze, and unable to access the higher-order thinking required for learning. Perry (2006) developed the neurosequential model, showing that traumatised children must feel SAFE before they can RELATE, and must be able to relate before they can REASON. Teaching content (reasoning) to a student who doesn't feel safe is neurobiologically futile — the survival brain overrides the learning brain. Bergin & Bergin (2009) showed that secure attachment to at least one adult at school is a protective factor for students with high ACE scores — a teacher who is consistently available, predictable, and emotionally regulated can partially compensate for insecure early attachments. Craig (2016) outlined the practical implications for schools: trauma-sensitive environments prioritise safety, predictability, connection, and choice — and these adaptations benefit ALL students, not just those with trauma histories.

## Input Schema

The teacher must provide:
- **Classroom situation:** What is being observed. *e.g. "A Year 8 student has sudden, intense outbursts — shouting, throwing equipment, running out of the room — triggered by seemingly minor events (being asked to move seats, being told their work is wrong)" / "A Year 10 student is completely withdrawn — never speaks, never makes eye contact, produces minimal work, flinches when adults approach" / "A Year 7 student is constantly seeking adult attention — following the teacher around, asking unnecessary questions, becoming distressed when the teacher attends to other students"*
- **Student level:** Year group. *e.g. "Year 8"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Known context:** What the teacher knows about the student's background
- **Current responses:** How the school currently responds
- **Available support:** Pastoral systems, counsellor, external agencies
- **Class context:** Impact on other students

## Prompt

```
You are an expert in trauma-informed education, with deep knowledge of van der Kolk's (2014) neuroscience of trauma, Perry's (2006) neurosequential model, Felitti et al.'s (1998) ACE study, Bergin & Bergin's (2009) attachment in the classroom, and Craig's (2016) trauma-sensitive schools framework. You understand that trauma-related behaviour in the classroom is a survival response, not a disciplinary problem — and that the appropriate response is to create safety and connection, not to punish.

CRITICAL: Trauma-informed practice is NOT:
- An excuse for any behaviour ("They've had a hard life, so we should let them do whatever they want")
- Removing all boundaries or expectations
- Diagnosing students or playing therapist
- Asking students about their trauma or making assumptions about their experiences
- Lowering academic expectations

Trauma-informed practice IS:
- Understanding that behaviour communicates needs — "What happened to you?" not "What's wrong with you?"
- Creating an environment of safety, predictability, and connection that benefits ALL students
- Responding to dysregulation with co-regulation rather than punishment
- Maintaining clear, consistent, compassionate boundaries
- Referring to specialists when a student needs therapeutic support beyond what a teacher can provide

Your task is to design trauma-informed practices for:

**Classroom situation:** {{classroom_situation}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, design for general classroom application.
**Known context:** {{known_context}} — if not provided, design based on the observable behaviour without assumptions about cause.
**Current responses:** {{current_responses}} — if not provided, analyse the behaviour through a trauma-informed lens from first principles.
**Available support:** {{available_support}} — if not provided, note what support should be in place and recommend the teacher investigate what's available.
**Class context:** {{class_context}} — if not provided, address the impact on other students in general terms.

Apply these principles:

1. **Safety first (Perry, 2006):**
   - A traumatised brain cannot learn until it feels safe. Safety is the prerequisite for everything else.
   - Safety means: predictability (knowing what's going to happen), consistency (same rules applied the same way), physical safety (no threat of harm), and emotional safety (no threat of humiliation).
   - Modifications that increase safety: consistent routines, advance notice of changes, calm tone of voice, respecting personal space.

2. **Reframe behaviour as communication (van der Kolk, 2014):**
   - "What is this behaviour communicating?" replaces "Why is this student being difficult?"
   - Fight responses (aggression, defiance) = the student feels threatened and is trying to protect themselves.
   - Flight responses (running out, avoidance) = the student feels overwhelmed and is trying to escape.
   - Freeze responses (shutdown, dissociation) = the student feels helpless and is disconnecting.
   - Fawn responses (people-pleasing, excessive compliance) = the student is trying to avoid conflict by being agreeable.

3. **Co-regulation before self-regulation (Perry, 2006; van der Kolk, 2014):**
   - A dysregulated student cannot regulate themselves — they need an adult to regulate WITH them first.
   - Co-regulation means: staying calm yourself, using a low and slow voice, reducing demands temporarily, being physically present without being threatening.
   - Only AFTER the student is regulated can you address the behaviour, the learning, or the consequence.

4. **Maintain boundaries with compassion (Craig, 2016):**
   - Boundaries provide safety — a classroom without boundaries feels chaotic and unpredictable, which is MORE threatening for traumatised students, not less.
   - Boundaries should be consistent, clear, and enforced with warmth: "I can see you're upset. You still need to sit down. I'll give you a moment, and then we'll work this out."
   - The consequence should be restorative (repair the harm) not punitive (suffer for what you did).

5. **Consider the whole class:**
   - Other students are affected by trauma-related behaviour. They need to feel safe too.
   - Trauma-informed practice for one student should not come at the cost of the learning environment for everyone.
   - Communicate with the class (without disclosing the student's situation): "Sometimes people have difficult days. In this classroom, we support each other."

Return your output in this exact format:

## Trauma-Informed Practice: [Situation Description]

**Situation:** [Summary]
**For:** [Student level]

### Trauma-Lens Reframing

**Observable behaviour:** [What the teacher sees]
**Through a behavioural lens:** [How this behaviour is typically interpreted — defiance, attention-seeking, laziness]
**Through a trauma lens:** [What the behaviour might be communicating — what need is being expressed]

### Classroom Adaptations

For each adaptation (4–6):
**Adaptation [N]: [Name]**
- **What to do:** [Specific action]
- **Why it helps:** [Which trauma-informed principle it addresses]
- **What it looks like in practice:** [Concrete example]

### Response Protocol

**When the behaviour occurs:**
[Step-by-step response — de-escalation, co-regulation, repair]

**What NOT to do:**
[Responses that will escalate rather than resolve]

### Boundaries

**What trauma-informed practice IS in this situation:**
[Clear statement]

**What it IS NOT:**
[Clear statement — maintaining expectations while being compassionate]

### Referral Indicators

[When this situation is beyond what a classroom teacher can manage — indicators that specialist support is needed]

**Self-check before returning output:** Verify that (a) the reframing is through a trauma lens, not a deficit lens, (b) safety and co-regulation are prioritised before demands, (c) boundaries are maintained — expectations are not removed, (d) the whole class is considered, (e) the teacher is not being asked to be a therapist, and (f) referral indicators are included.
```

## Example Output

**Scenario:** *Classroom situation: "A Year 8 student has sudden, intense outbursts — shouting, throwing equipment, running out of the room — triggered by seemingly minor events (being asked to move seats, being told their work needs correcting, another student brushing past them). These happen 2–3 times a week. After the outburst, the student is usually tearful and apologetic. The current response is a detention each time, but the outbursts are getting more frequent, not less." / Student level: "Year 8" / Current responses: "Detention after each outburst. The student has had 12 detentions this half-term. Parents have been called in twice." / Available support: "SENCO, school counsellor (limited availability — 1 day per week), head of year"*

---

## Trauma-Informed Practice: Sudden Outbursts and Dysregulation

**Situation:** Year 8 student with frequent intense outbursts triggered by minor events
**For:** Year 8

### Trauma-Lens Reframing

**Observable behaviour:** Shouting, throwing equipment, running out of the room. Triggered by seemingly minor events: being asked to move seats, correction of work, physical contact from another student. Tearful and apologetic afterwards. 12 detentions this half-term — frequency increasing.

**Through a behavioural lens:** "This student is disruptive, defiant, and volatile. They can't control their temper. The detentions aren't working, so we may need stronger sanctions — isolation, exclusion."

**Through a trauma lens:** The triggers share a common feature: perceived threat. Being asked to move seats = loss of control over environment. Being told work is wrong = perceived criticism/rejection. Being touched unexpectedly = physical boundary violation. These are not "minor" events to a brain wired for threat — they are signals that something unpredictable and potentially dangerous is happening. The fight response (shouting, throwing) is an automatic survival reaction, not a conscious choice. The tearfulness afterwards confirms this: the student does not WANT to behave this way — they cannot stop the response in the moment. The fact that detentions are increasing the frequency, not decreasing it, is the clearest sign that this is not a disciplinary issue. Punishment cannot change a survival response — it only adds another source of threat (now the student is also afraid of the consequences, which increases baseline anxiety, which makes the NEXT trigger more likely to produce an outburst).

### Classroom Adaptations

**Adaptation 1: Predictable Routines and Advance Warning**
- **What to do:** Keep classroom routines as consistent as possible. Same seating, same lesson structure, same expectations. When a change is necessary (supply teacher, room change, seating adjustment), give this student advance warning: "Tomorrow, we'll be in a different room — I wanted to let you know so it's not a surprise." Even 30 seconds of warning helps.
- **Why it helps:** Predictability creates safety (Perry, 2006). Unexpected changes activate the threat response in a traumatised brain. Advance warning allows the prefrontal cortex time to prepare, reducing the amygdala's hijack response.
- **What it looks like in practice:** At the start of Monday's lesson: "This week is a normal week — same room, same routine. One change: on Thursday we'll have a guest speaker for 15 minutes. I'll remind you on Wednesday."

**Adaptation 2: Designated Safe Space**
- **What to do:** Identify a place in or near the classroom where the student can go when they feel the escalation building — BEFORE the outburst. This is not a punishment space; it is a regulation space. "If you feel yourself getting wound up, you can go to the calm corner / step outside the door for two minutes. You don't need permission — just go. When you're ready, come back." Agree this plan with the student privately.
- **Why it helps:** Flight is a survival response — the student is trying to escape because their body feels unsafe. Providing an acceptable escape route prevents the fight response (shouting, throwing). Running out of the room is the student's unregulated version of this; the designated space is the regulated version.
- **What it looks like in practice:** A chair in the corner of the room, or permission to step into the corridor for 2 minutes. No questions, no consequences, no "Why are you leaving?" — just quiet acceptance that the student is managing their regulation.

**Adaptation 3: Reframe Correction as Growth**
- **What to do:** When giving feedback on the student's work, lead with what IS working before addressing what needs improving. Use collaborative language: "This part works well — let's look at how we can build on it" rather than "This is wrong." Avoid red pen corrections on the page — use a brief verbal conversation or post-it note instead.
- **Why it helps:** Correction triggers the threat response because the student interprets "your work is wrong" as "you are wrong" — a rejection that activates deep attachment fears. Framing feedback as collaborative growth reduces the perceived threat. This is good feedback practice for ALL students (Hattie & Timperley, 2007) but is essential for this student.
- **What it looks like in practice:** Rather than writing "incorrect" on the student's work, approach quietly: "I can see you've understood [specific strength]. There's one part I want us to look at together — can I show you?"

**Adaptation 4: Physical Space Awareness**
- **What to do:** Never approach this student from behind. Don't stand over them when they're seated. Maintain an arm's length distance unless the student initiates closer contact. When other students need to move past, seat this student at the end of a row or near a wall where accidental contact is less likely.
- **Why it helps:** Unexpected physical contact triggers the threat response (van der Kolk, 2014). A student whose body has learned that touch can be dangerous will react to a brush-past or a hand on the shoulder as though it's a threat — because their nervous system cannot distinguish between threatening and non-threatening touch in the moment.
- **What it looks like in practice:** When approaching the student's desk, approach from the front. Announce your presence: "I'm coming over to have a look at your work." Seat the student near the wall with a clear path to the door (this also supports Adaptation 2 — easy access to the safe space).

**Adaptation 5: Reduce Public Attention During and After Incidents**
- **What to do:** When an outburst occurs, do not address it publicly. Do not raise your voice. Do not stand over the student. Do not involve other students as witnesses. Reduce the audience as much as possible: direct other students to continue working, approach the student calmly and quietly, offer the safe space. After the incident, have a private, restorative conversation (not a public telling-off).
- **Why it helps:** Public attention during dysregulation adds shame to the already intense emotional experience. Shame is itself a trauma trigger — it can escalate the outburst rather than de-escalate it. Privacy preserves the student's dignity and prevents the humiliation that makes future regulation harder.
- **What it looks like in practice:** During an outburst, calmly redirect the class: "Everyone continue with question 3." Move toward the student slowly and quietly: "I can see you're upset. You can go to the calm corner if you need to. I'll come and check on you in a minute." Tone: low, slow, warm.

### Response Protocol

**When the behaviour occurs:**

1. **Stay calm yourself.** Your emotional regulation is the student's external anchor. If you escalate, they will escalate. Take one breath before responding.

2. **Reduce demands immediately.** Do NOT say "Sit down," "Stop shouting," or "Put that down." These are demands that the survival brain will resist. Instead, reduce: "It's OK. You don't have to do anything right now."

3. **Offer the safe space.** "You can go to the calm corner. Take the time you need." If the student has already left the room, do NOT chase them. Send a trusted adult to check they are safe, but do not corner them.

4. **Wait.** The amygdala hijack lasts 20–90 seconds. After the surge, the prefrontal cortex begins to re-engage. Do not try to reason, instruct, or consequence during the surge. Wait for it to pass.

5. **Reconnect.** After the student has regulated (might be 5 minutes, might be 20), approach calmly: "Are you OK? That was tough. When you're ready, you can come back." No interrogation, no "Why did you do that?"

6. **Repair later.** At the end of the lesson or at a separate time, have a restorative conversation: "What happened? What were you feeling? What could we do differently next time — both of us?" This is where the learning happens — not during the crisis.

**What NOT to do:**
- Do NOT shout or raise your voice (escalates the threat response)
- Do NOT physically block the student's exit (trapping triggers fight)
- Do NOT demand immediate compliance ("Sit down NOW")
- Do NOT issue consequences during the incident ("That's a detention")
- Do NOT ask "Why did you do that?" during the crisis (the student doesn't know — the survival brain bypassed conscious choice)
- Do NOT discuss the incident publicly in front of the class

### Boundaries

**What trauma-informed practice IS in this situation:**
- Understanding that the outbursts are a survival response, not defiance
- Creating conditions that reduce the frequency and intensity of triggers
- Responding with co-regulation (staying calm, reducing demands, offering escape) rather than escalation
- Having a restorative conversation after the student is regulated
- Maintaining the expectation that the student will learn, participate, and progress — with adapted support

**What it IS NOT:**
- Allowing the student to behave however they like without any response
- Removing academic expectations ("Don't worry about the work")
- Ignoring the impact on other students
- The teacher acting as a therapist or asking about the student's trauma
- A permanent arrangement — the goal is to gradually build the student's own regulation capacity so these adaptations become less necessary

### Referral Indicators

Refer to the school counsellor and/or SENCO if:
- The frequency of outbursts is increasing despite adaptations (currently 2–3/week — if this rises to daily, specialist support is needed)
- The student discloses abuse, self-harm, or suicidal ideation during a restorative conversation
- The student's behaviour is consistently unsafe — risk of harm to themselves or others
- The student is unable to access learning for extended periods (missing significant curriculum content)
- The teacher feels out of their depth — this is a professional boundary, not a failure. "I need help with this" is the right response.

Given that this student has had 12 detentions with increasing frequency of outbursts, a referral to the school counsellor should happen NOW — not as a last resort, but as an immediate support. The classroom adaptations above manage the environment; the counsellor can work on the student's underlying regulation and processing.

---

## Known Limitations

1. **This skill provides classroom-level guidance, not therapeutic intervention.** Trauma-informed practice in the classroom creates the CONDITIONS for a traumatised student to feel safe enough to learn — but it does not treat the trauma. Students with significant trauma histories need professional therapeutic support alongside trauma-informed classroom practice.

2. **The teacher does not need to know what happened.** Trauma-informed practice does not require the teacher to know the student's history. In fact, teachers should NOT seek details of traumatic experiences — this is not their role, and hearing details can cause secondary trauma. The teacher's role is to create a safe, predictable, connected environment and to respond to observable behaviour with understanding rather than punishment.

3. **Trauma-informed practice benefits ALL students.** Predictable routines, warm relationships, consistent boundaries, advance warning of changes, respectful feedback — these are good practices for every student, not just traumatised ones. The adaptations above should not feel like a special programme for one student; they should feel like how the classroom works for everyone.

4. **There is a tension between one student's needs and the whole class.** A student running out of the room, shouting, or throwing equipment affects every other student's learning and sense of safety. Trauma-informed practice does not mean the class should suffer indefinitely. If the adaptations are insufficient and the behaviour remains disruptive, the school must provide additional support (in-class TA, reduced timetable, specialist provision) so that both the student's needs AND the class's needs are met.

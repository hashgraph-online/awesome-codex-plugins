---
# AGENT SKILLS STANDARD FIELDS (v2)
name: ruler-emotional-literacy-sequence
description: "Design a RULER emotional literacy sequence for recognising, understanding, labelling, expressing, and regulating emotions. Use when students struggle with emotional regulation, conflict, or anxiety."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/ruler-emotional-literacy-sequence"
skill_name: "RULER Emotional Literacy Sequence"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Brackett (2019) — Permission to Feel: the power of emotional intelligence to achieve well-being and success"
  - "Brackett et al. (2012) — RULER: a theory-driven, systemic approach to social and emotional learning"
  - "Rivers et al. (2012) — Improving the social and emotional climate of classrooms: a clustered randomized controlled trial of RULER"
  - "Hagelskamp et al. (2013) — Improving classroom quality with the RULER approach to social and emotional learning"
  - "Mayer & Salovey (1997) — What is emotional intelligence?"
input_schema:
  required:
    - field: "emotional_context"
      type: "string"
      description: "The classroom situation or student behaviour that prompts the need for emotional literacy — e.g. conflict, anxiety before assessments, difficulty collaborating, emotional outbursts"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject — for integration of RULER into academic content"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: class emotional climate data, specific student needs"
    - field: "time_available"
      type: "string"
      description: "How much time can be allocated — embedded in lesson, tutor time, or dedicated session"
    - field: "ruler_familiarity"
      type: "string"
      description: "Whether students have previous experience with RULER tools — Mood Meter, Meta-Moment, Blueprint"
output_schema:
  type: "object"
  fields:
    - field: "ruler_sequence"
      type: "object"
      description: "A structured sequence using RULER skills — Recognising, Understanding, Labelling, Expressing, Regulating"
    - field: "tool_selection"
      type: "string"
      description: "Which RULER tool(s) are most appropriate — Mood Meter, Meta-Moment, Blueprint, or Charter"
    - field: "integration_plan"
      type: "object"
      description: "How to embed the RULER sequence into academic content or classroom routines"
    - field: "teacher_modelling"
      type: "string"
      description: "How the teacher should model the RULER skills — emotional literacy starts with the teacher"
chains_well_with:
  - "belonging-classroom-culture-designer"
  - "trauma-informed-practice-designer"
  - "restorative-practice-protocol-designer"
  - "perma-based-lesson-designer"
teacher_time: "3 minutes"
tags: ["RULER", "emotional-intelligence", "Brackett", "Yale", "SEL", "emotional-literacy", "mood-meter"]
---

# RULER Emotional Literacy Sequence

## What This Skill Does

Designs a structured sequence for developing emotional literacy using the RULER framework from the Yale Center for Emotional Intelligence — teaching students to Recognise emotions in themselves and others, Understand the causes and consequences of emotions, Label emotions with a nuanced vocabulary, Express emotions appropriately, and Regulate emotions using effective strategies. The output includes the specific RULER tool(s) to use (Mood Meter, Meta-Moment, Blueprint, or Charter), how to introduce and implement them, how to integrate emotional literacy into academic content rather than treating it as a separate activity, and how the teacher should model the skills themselves — because emotional literacy begins with the teacher, not the student. AI is specifically valuable here because selecting the right RULER tool for a specific classroom situation, adapting the language for the age group, and integrating emotional literacy into subject content requires both emotional intelligence expertise and pedagogical knowledge.

## Evidence Foundation

Brackett (2019) and Brackett et al. (2012) developed RULER at the Yale Center for Emotional Intelligence, based on Mayer & Salovey's (1997) ability model of emotional intelligence. RULER treats emotional intelligence as a set of skills that can be taught, not a personality trait: Recognising (identifying emotions in faces, voices, body language, and one's own body), Understanding (knowing what causes emotions and what consequences they lead to), Labelling (using precise vocabulary — not just "good" or "bad" but specific emotion words like "frustrated," "apprehensive," "exhilarated"), Expressing (knowing when and how to express emotions in different contexts), and Regulating (using strategies to manage emotional experiences — not suppressing emotions but responding to them effectively). Rivers et al. (2012) conducted a cluster randomised controlled trial of RULER in 62 classrooms and found significant improvements in classroom emotional climate, including more emotional support, better classroom organisation, and greater instructional support. Hagelskamp et al. (2013) found that RULER improved classroom quality on all three dimensions of the CLASS observation system. Critically, RULER begins with teachers — the "Anchors of Emotional Intelligence" (Mood Meter, Meta-Moment, Blueprint, Charter) are first practised by staff before being introduced to students. This is because students cannot develop emotional literacy in an environment where adults don't model it.

## Input Schema

The teacher must provide:
- **Emotional context:** The situation prompting this. *e.g. "Students are highly anxious before mock exams — several are crying, refusing to enter the exam hall, or shutting down completely" / "There's persistent low-level conflict between two friendship groups that's disrupting collaborative work" / "A student has frequent emotional outbursts (shouting, leaving the room) that they can't seem to control"*
- **Student level:** Year group. *e.g. "Year 8"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Student profiles:** Emotional climate data, specific needs
- **Time available:** How much time can be allocated
- **RULER familiarity:** Whether students have used RULER tools before

## Prompt

```
You are an expert in emotional intelligence and social-emotional learning, with deep knowledge of Brackett's (2019) RULER framework, Mayer & Salovey's (1997) ability model of emotional intelligence, and the evidence from Rivers et al. (2012) and Hagelskamp et al. (2013) on RULER's impact on classroom climate and learning. You understand that emotional literacy is a set of teachable skills — not a personality trait — and that it begins with the teacher modelling the skills, not just teaching them.

The RULER framework uses four "Anchors of Emotional Intelligence":

1. **The Charter:** A collaboratively created set of agreements about how class members want to feel and what they'll do to support those feelings. Created at the start of the year.
2. **The Mood Meter:** A tool for recognising and labelling emotions using two dimensions — pleasantness (horizontal axis: unpleasant to pleasant) and energy (vertical axis: low to high). The four quadrants are: Red (high energy, unpleasant — angry, anxious, frustrated), Yellow (high energy, pleasant — excited, happy, energised), Green (low energy, pleasant — calm, content, peaceful), Blue (low energy, unpleasant — sad, tired, lonely).
3. **The Meta-Moment:** A pause between a trigger and a response — "How do I feel? How would my best self respond? What strategy can I use?" Used when emotions are intense and the automatic response would be unhelpful.
4. **The Blueprint:** A tool for understanding and resolving conflict — "Before, during, after: what happened, how did each person feel, what were the consequences, how can we move forward?" Used for interpersonal situations.

Your task is to design a RULER sequence for:

**Emotional context:** {{emotional_context}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, design as a standalone sequence that can be integrated into any lesson or tutor time.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical class.
**Time available:** {{time_available}} — if not provided, design for 15–20 minutes (embeddable in a lesson).
**RULER familiarity:** {{ruler_familiarity}} — if not provided, assume students are new to RULER and introduce the tools from scratch.

Apply these principles:

1. **Select the right RULER tool for the situation:**
   - Mood Meter: for building emotional awareness and vocabulary (general emotional literacy).
   - Meta-Moment: for managing intense emotional responses (individual regulation).
   - Blueprint: for resolving interpersonal conflict (relationship repair).
   - Charter: for establishing classroom emotional norms (prevention, culture-building).

2. **Teacher models first (Brackett, 2019):**
   - The teacher MUST model the tool before asking students to use it.
   - "I'm going to show you where I am on the Mood Meter right now. I'm in the Yellow — I'm energised and interested because I'm curious about what you'll think of today's topic."
   - Modelling vulnerability (not every emotion is pleasant) is more powerful than modelling only positive emotions.

3. **Build emotional vocabulary (Mayer & Salovey, 1997):**
   - Move students beyond "fine," "good," "bad," "annoyed" to precise vocabulary: apprehensive, exhilarated, melancholy, content, frustrated, curious, overwhelmed, serene.
   - The Mood Meter helps: each quadrant contains 20+ emotion words at increasing levels of granularity.
   - Precision matters: "I'm frustrated" leads to a different response than "I'm anxious." Both might be called "bad" without vocabulary.

4. **Integrate into academic content where possible:**
   - Analyse characters' emotions using the Mood Meter in English.
   - Discuss the emotions of historical figures using the Blueprint in History.
   - Examine the emotional dimension of scientific discovery or ethical dilemmas.
   - Integration is more sustainable than standalone sessions.

5. **Regulation is NOT suppression:**
   - RULER teaches students to RESPOND to emotions, not to suppress them.
   - "Don't be angry" is not emotional regulation. "I notice I'm angry — what's causing it, and what would be a helpful response?" IS regulation.
   - All emotions are valid; not all behaviours are appropriate. RULER helps students separate the emotion (always OK) from the behaviour (which they can choose).

Return your output in this exact format:

## RULER Sequence: [Context Description]

**Emotional context:** [The situation]
**For:** [Student level]
**RULER tool(s):** [Which anchor(s) to use]

### Teacher Modelling

[How the teacher should model the RULER skill first — specific language and example]

### Sequence Steps

For each step:
**Step [N]: [RULER Skill — Recognise/Understand/Label/Express/Regulate]**
- **Activity:** [What students do]
- **Teacher script:** [Specific language to use]
- **What to look for:** [Signs the step is working]

### Academic Integration

[How to embed this sequence into subject content — specific examples]

### Sustaining the Practice

[How to maintain emotional literacy beyond this sequence — routines, language, ongoing use of tools]

**Self-check before returning output:** Verify that (a) the right RULER tool is selected for the situation, (b) the teacher models the skill before students practise it, (c) emotional vocabulary is expanded beyond basic terms, (d) regulation is taught as response management, not emotion suppression, and (e) the sequence is practical and time-efficient.
```

## Example Output

**Scenario:** *Emotional context: "Year 9 students are highly anxious before their first set of mock GCSE exams. Several students have been tearful in lessons, two have asked to see the school counsellor, and the general mood in the class is flat and tense. Students are saying things like 'I'm going to fail,' 'What's the point of revising — I can't do it,' and 'I feel sick every time I think about exams.'" / Student level: "Year 9" / Time available: "20 minutes in tutor time, plus embedding into subject lessons" / RULER familiarity: "Students have seen the Mood Meter on the wall but haven't used it systematically"*

---

## RULER Sequence: Pre-Exam Anxiety

**Emotional context:** Year 9 exam anxiety — tearfulness, avoidance, self-defeating statements, physical symptoms
**For:** Year 9
**RULER tool(s):** Mood Meter (for recognising and labelling) + Meta-Moment (for regulating)

### Teacher Modelling

Before introducing the tools to students, the teacher models their own emotional experience. This is essential — if the teacher pretends they have no stress, students learn that adults don't feel anxiety, which makes their own anxiety feel abnormal.

"I want to share something with you. When I look at the Mood Meter, right now I'm somewhere around here [points to the upper-left quadrant — Red zone, but moderate]. I'd say I'm 'apprehensive.' I've got a lot to do this week, and I notice that when I think about all of it at once, my chest feels tight and I start thinking 'I'll never get it all done.' Sound familiar? That feeling is completely normal — it's my brain telling me this matters. But here's what I've learned: when I stay in that zone and don't do anything about it, I actually get LESS done, not more. So I'm going to share a strategy with you that I use, and then we're going to try it together."

### Sequence Steps

**Step 1: Recognise — Where Are You Right Now? (5 minutes)**
- **Activity:** Display the Mood Meter on the screen (four quadrants with emotion words). Give each student a small Post-it note. "I'd like you to place your Post-it on the Mood Meter where you are RIGHT NOW — not where you think you should be, but where you actually are. No names on the Post-its. I'll place mine first." [Teacher places their Post-it in the Red zone, modelling honesty.]
- **Teacher script:** "There's no right or wrong place to be. Every part of the Mood Meter is normal. I'm interested in the pattern — where is our class as a whole?"
- **What to look for:** The distribution will likely cluster in the Red (anxious, stressed) and Blue (tired, flat) zones. This provides visible data that anxiety is SHARED — it's not just "me." This normalisation is itself therapeutic: "I'm not the only one who feels this way."

**Step 2: Label — Name It to Tame It (5 minutes)**
- **Activity:** "Now I want us to get more specific. 'Stressed' is a start, but it doesn't tell us much. Look at the emotion words in your quadrant. Which word BEST describes how you feel? Is it 'anxious' (worried about something specific that might happen)? 'Overwhelmed' (too much to do and not enough time)? 'Dread' (a heavy feeling about something you can't avoid)? 'Frustrated' (you're trying but it doesn't feel like it's working)? These are different feelings — and they need different responses."
- **Teacher script:** "I said I'm apprehensive. That's different from anxious — apprehensive means I'm nervous about something but I think I can handle it. If I were anxious, I'd feel less in control. Getting the right word matters because it helps you figure out what you actually need."
- **What to look for:** Students moving from "stressed" or "bad" to more precise terms. If students are struggling with vocabulary, offer choices: "Would you say you're more anxious or more overwhelmed? They feel different."

**Step 3: Understand — What's Causing This? (5 minutes)**
- **Activity:** "Now let's figure out what's underneath the feeling. Turn to your partner and complete this sentence: 'I feel [emotion word] because ___.' Be specific. Not 'because of exams' — WHAT about the exams? Is it not knowing what will come up? Feeling like you haven't revised enough? Worrying about what the result will mean? Comparing yourself to others?"
- **Teacher script:** "Understanding the cause tells you what to do about it. If you're anxious because you haven't revised, the solution is a revision plan. If you're anxious because you're comparing yourself to others, the solution is different — it's about where YOU are, not where they are. Same feeling, different cause, different response."
- **What to look for:** Students identifying specific causes rather than vague ones. Partners listening to each other (relatedness — Walton & Cohen). The conversation itself is often therapeutic — articulating the cause reduces the feeling's power.

**Step 4: Regulate — The Meta-Moment (5 minutes)**
- **Activity:** Introduce the Meta-Moment: "When you feel that wave of anxiety — the sick feeling, the 'I can't do this' thought — here's what I want you to practise. PAUSE. Don't try to force the feeling away. Instead, three steps: (1) Notice it: 'I feel anxious right now.' (2) Ask: 'What would my best self do right now?' Not your panicking self, not your avoidant self — your best self. The version of you that handles things well. (3) Choose a strategy." Provide a strategy menu:
  - **Breathing:** 4-7-8 breathing (in for 4, hold for 7, out for 8). Activates the parasympathetic nervous system.
  - **Chunking:** "I can't revise everything — but I can revise ONE topic for 25 minutes right now."
  - **Reframing:** "Exams show me what I know — they don't define who I am."
  - **Connection:** "I'm going to talk to someone about how I feel — not to fix it, but to not feel alone."
- **Teacher script:** "You will feel anxious before the exams. That's guaranteed — it's a normal response to something that matters. The Meta-Moment isn't about removing the anxiety. It's about choosing what you DO with it. Anxiety can paralyse you (you freeze and don't revise) or motivate you (you feel the urgency and start working). The Meta-Moment helps you choose the second one."
- **What to look for:** Students engaging with the strategy menu — picking one that resonates. Students practising the breathing (even sceptically — sceptical practice still works). Students talking to each other about which strategy they'll try.

### Academic Integration

- **English:** When studying characters under pressure (Macbeth before the murder, Romeo after the banishment), place the character on the Mood Meter. "Where is Macbeth right now? What's causing it? What would the Meta-Moment look like for him?" This builds analytical skills AND emotional vocabulary simultaneously.

- **Science:** Before a practical assessment: "Let's check in with the Mood Meter. Where are you? If you're in the Red zone, try one round of 4-7-8 breathing before you start. Research shows that anxiety narrows attention — which means you'll miss things in the experiment. Calming your breathing literally helps you observe better."

- **History:** When studying people making difficult decisions under pressure (Churchill during the Blitz, suffragettes facing imprisonment): "Use the Blueprint. What were they feeling? What caused those feelings? How did their emotions influence their decisions?"

### Sustaining the Practice

1. **Make the Mood Meter visible and used.** Keep it on the wall. Check in at the start of lessons (30 seconds: "Where are you on the Mood Meter? No need to share — just notice"). Over time, students will start using the vocabulary unprompted.

2. **Model the Meta-Moment when YOU feel frustrated.** "I'm going to take a Meta-Moment. I'm frustrated because the technology isn't working. My automatic response is to get annoyed — but that won't fix the projector. My best self says: breathe, try one more thing, then move on. OK — let me try this."

3. **Normalise the vocabulary.** Use emotion words in everyday conversation: "You look apprehensive — what's on your mind?" / "I can see some people are in the Yellow zone — that energy is great for this task." The more the teacher uses precise emotional language, the more students will adopt it.

4. **Return to the Meta-Moment before every high-stakes event.** Before exams, before presentations, before parents' evening: "Let's do a Meta-Moment check. Where are you? What does your best self need right now?"

---

## Known Limitations

1. **RULER is a whole-school programme, not a single-lesson intervention.** The sequence above introduces RULER tools, but their full impact requires consistent use across multiple classrooms, integration into school culture, and staff training. A single teacher using RULER in one lesson provides benefit, but the system-level effects (improved emotional climate across the school) require whole-school adoption.

2. **Emotional literacy does not replace clinical support.** Students with anxiety disorders, depression, or trauma responses need professional support — a school counsellor, CAMHS referral, or therapeutic intervention. RULER builds emotional skills for the general population; it is not a substitute for clinical services for students who need them. If a student's distress is persistent or severe, RULER should be supplemented with appropriate referral.

3. **The teacher must genuinely model.** RULER requires teachers to be emotionally literate themselves — to share their own emotions, to demonstrate the Meta-Moment, to use precise vocabulary. Teachers who are uncomfortable with emotional disclosure will find RULER difficult to implement authentically. Professional development and a supportive school culture are prerequisites for effective implementation.

---
# AGENT SKILLS STANDARD FIELDS (v2)
name: reflective-practice-prompt-generator
description: "Generate structured reflection prompts for a specific teaching experience or professional learning challenge. Use when debriefing lessons, journaling, or preparing for coaching conversations."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "professional-learning/reflective-practice-prompt-generator"
skill_name: "Reflective Practice Prompt Generator"
domain: "professional-learning"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Schön (1983) — The Reflective Practitioner: how professionals think in action"
  - "Timperley (2011) — Realizing the Power of Professional Learning"
  - "Dewey (1933) — How We Think: a restatement of the relation of reflective thinking to the educative process"
  - "Brookfield (2017) — Becoming a Critically Reflective Teacher"
  - "Kolb (1984) — Experiential Learning: experience as the source of learning and development"
input_schema:
  required:
    - field: "teaching_experience"
      type: "string"
      description: "The specific lesson, interaction, or event to reflect on — what happened"
    - field: "reflection_purpose"
      type: "string"
      description: "What the teacher wants to learn from this reflection — problem-solving, understanding, growth"
  optional:
    - field: "teacher_context"
      type: "string"
      description: "Experience level, subject, current professional learning goals"
    - field: "emotional_response"
      type: "string"
      description: "How the teacher felt about the experience — frustrated, surprised, uncertain, proud"
    - field: "reflection_depth"
      type: "string"
      description: "Surface (what happened?), analytical (why did it happen?), or critical (what assumptions am I making?)"
    - field: "time_available"
      type: "string"
      description: "How much time for reflection — 5 minutes, 15 minutes, extended journal entry"
output_schema:
  type: "object"
  fields:
    - field: "reflection_prompts"
      type: "array"
      description: "A sequence of prompts that guide the teacher from description through analysis to action"
    - field: "lens_analysis"
      type: "object"
      description: "Prompts that encourage the teacher to examine the experience from multiple perspectives — student, colleague, theory, autobiography"
    - field: "action_prompts"
      type: "array"
      description: "Questions that move reflection toward concrete next steps"
    - field: "journaling_scaffold"
      type: "string"
      description: "A structured format for written reflection, if the teacher prefers to write"
chains_well_with:
  - "instructional-coaching-conversation-guide"
  - "lesson-observation-protocol-designer"
  - "teacher-inquiry-cycle-designer"
  - "lesson-study-cycle-designer"
  - "pedagogical-content-knowledge-developer"
teacher_time: "2 minutes"
tags: ["reflection", "Schön", "Timperley", "reflective-practice", "professional-learning", "journaling"]
---

# Reflective Practice Prompt Generator

## What This Skill Does

Generates structured reflection prompts calibrated to a specific teaching experience and reflection purpose — guiding the teacher from surface description ("What happened?") through analytical reflection ("Why did it happen?") to critical reflection ("What assumptions was I making?") and finally to action planning ("What will I do differently?"). The critical insight from Schön's research is that professionals do not learn primarily from experience — they learn from REFLECTING on experience. Without structured reflection, a teacher with 20 years of experience may have had one year of experience repeated 20 times. The output includes layered prompts at increasing depth, Brookfield's four-lens analysis (examining the experience from the perspectives of autobiography, students, colleagues, and theory), and concrete action prompts that ensure reflection leads to change, not just understanding. AI is specifically valuable here because effective reflection prompts must be precisely calibrated to the specific experience — generic prompts ("How did the lesson go?") produce generic reflections. Specific prompts ("You said the group work fell apart — at what exact moment did it break down, and what were you doing when it happened?") produce specific insights.

## Evidence Foundation

Schön (1983) distinguished between reflection-in-action (thinking on your feet during teaching) and reflection-on-action (thinking back after the event). Both are essential, but reflection-on-action — the systematic, structured examination of practice after the event — is where professional knowledge is built. Dewey (1933) established that reflection is not simply "thinking about" an experience but a disciplined process of inquiry: identifying the problem, generating hypotheses, testing them against evidence, and reaching a conclusion. Timperley (2011) emphasised that the most powerful professional learning involves teachers examining the impact of their practice on student learning — not just reflecting on what they did, but on what students actually learned as a result. Brookfield (2017) proposed four lenses for critical reflection: autobiographical (examining your own assumptions and experiences), students' eyes (seeing the teaching from the students' perspective), colleagues' perceptions (how peers would interpret the event), and theoretical literature (what research says about the issue). Using multiple lenses prevents the most common reflection trap: confirming what you already believe. Kolb (1984) proposed the experiential learning cycle: concrete experience → reflective observation → abstract conceptualisation → active experimentation. This cycle shows that reflection without action is incomplete — the purpose of reflection is to generate a changed practice, not just a changed understanding.

## Input Schema

The teacher must provide:
- **Teaching experience:** What happened. *e.g. "I tried group work for the first time with my Year 10 class and it was chaotic — two groups worked well, three groups went completely off task, and one group had a conflict that disrupted the whole room" / "I gave what I thought was clear instructions for a task and then realised that half the class had no idea what they were supposed to do" / "A student told me that my lessons are boring and I don't know how to respond"*
- **Reflection purpose:** What they want to learn. *e.g. "I want to understand why the group work failed so I can do it better next time" / "I want to figure out why my instructions don't land" / "I want to process the feedback and decide whether to change anything"*

Optional (injected by context engine if available):
- **Teacher context:** Experience level, subject, goals
- **Emotional response:** How they felt
- **Reflection depth:** Surface, analytical, or critical
- **Time available:** How much time for reflection

## Prompt

```
You are an expert in reflective practice, with deep knowledge of Schön's (1983) reflection-on-action, Dewey's (1933) disciplined inquiry process, Timperley's (2011) focus on impact on student learning, Brookfield's (2017) four critical lenses, and Kolb's (1984) experiential learning cycle. You understand that effective reflection is structured, specific, and leads to action — it is not vague self-evaluation or unfocused worrying.

CRITICAL PRINCIPLES:
- **Specific, not generic.** "How did the lesson go?" produces "OK, I suppose." A specific prompt targeted at the exact experience produces insight. Match the prompt to the experience.
- **Layered depth.** Start with description (what happened?), move to analysis (why did it happen?), then to critical reflection (what assumptions was I making?). Don't start with the deepest level — teachers need to describe before they can analyse.
- **Multiple lenses (Brookfield, 2017).** Encourage the teacher to view the experience from their own perspective, the students' perspective, a colleague's perspective, and a research/theory perspective. Single-lens reflection confirms existing beliefs; multi-lens reflection challenges them.
- **Reflection must lead to action (Kolb, 1984).** If reflection doesn't change practice, it's rumination, not professional learning. Every reflection sequence should end with "What will I do differently?"
- **Honour the emotional response.** Teaching experiences carry emotions — frustration, pride, shame, confusion, satisfaction. The prompts should acknowledge the emotion before moving to analysis. Skipping the emotion produces intellectual reflection that doesn't connect to practice.

Your task is to generate reflection prompts for:

**Teaching experience:** {{teaching_experience}}
**Reflection purpose:** {{reflection_purpose}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Teacher context:** {{teacher_context}} — if not provided, design prompts for a general teaching context.
**Emotional response:** {{emotional_response}} — if not provided, include a prompt that surfaces the emotional response.
**Reflection depth:** {{reflection_depth}} — if not provided, design prompts at all three levels (descriptive, analytical, critical).
**Time available:** {{time_available}} — if not provided, design for 15 minutes of structured reflection.

Return your output in this exact format:

## Reflection Prompts: [Experience Summary]

**Experience:** [Brief description]
**Purpose:** [What the teacher wants to learn]

### Layer 1 — Description (What happened?)

[2–3 prompts that help the teacher describe the experience specifically and accurately]

### Layer 2 — Analysis (Why did it happen?)

[2–3 prompts that help the teacher analyse causes and connections]

### Layer 3 — Critical Reflection (What assumptions am I making?)

[2–3 prompts from Brookfield's four lenses — examining the experience from multiple perspectives]

### Layer 4 — Action (What will I do differently?)

[2–3 prompts that move from understanding to concrete next steps]

### Quick Reflection Option

[A 5-minute version for teachers with limited time — 3 essential prompts that cover description, analysis, and action]

**Self-check before returning output:** Verify that (a) prompts are specific to the described experience, (b) prompts are layered from description to analysis to critical reflection to action, (c) at least one prompt uses Brookfield's student lens, (d) the action layer generates concrete next steps, and (e) the quick option is genuinely quick — 5 minutes maximum.
```

## Example Output

**Scenario:** *Teaching experience: "I tried group work for the first time with my Year 10 class and it was chaotic — two groups worked well, three groups went completely off task, and one group had a conflict that disrupted the whole room. I ended up shouting to get attention back, which I hate doing. By the end of the lesson, I felt like I'd wasted 40 minutes and the students had learned nothing." / Reflection purpose: "I want to understand why it went wrong so I can decide whether to try group work again or just go back to individual work." / Emotional response: "Frustrated, embarrassed, and questioning whether I'm cut out for teaching" / Teacher context: "2nd year teacher, Science, generally good classroom management with individual/pair work"*

---

## Reflection Prompts: Group Work Chaos — Year 10 Science

**Experience:** First attempt at group work with Year 10; most groups off task; one conflict; teacher shouted to regain control; feels like wasted time.
**Purpose:** Understand why it went wrong and decide whether to try group work again.

### Layer 1 — Description (What happened?)

**Prompt 1:** "Let's slow down and reconstruct the lesson. At what exact moment did things start going wrong? You said two groups worked well and three didn't — what was different about the groups that worked? Can you describe what the 'working' groups were DOING versus what the 'off-task' groups were doing?"

*Why this prompt:* The teacher's narrative is "it was chaotic." But chaos is not uniform — two groups worked. Understanding the DIFFERENCE between the working and non-working groups reveals what conditions were missing, not that group work is impossible.

**Prompt 2:** "You said you 'ended up shouting.' Walk me through the 60 seconds before you shouted. What had you tried first? What signals were you picking up from the class? At what point did you decide the situation was beyond normal management?"

*Why this prompt:* The teacher is ashamed of shouting. This prompt examines the sequence that led to it — which may reveal that the problem was not the teacher's management but the task design (groups without a clear enough structure, a task that was too open, or insufficient preparation for collaborative work).

**Prompt 3:** "The group that had a conflict — what was the conflict about? Was it about the task (a disagreement about the science), about roles (who does what), or about relationships (students who don't get along)?"

*Why this prompt:* Different types of conflict have different causes and different solutions. A science disagreement is productive conflict that needs facilitation, not prevention. A relationship conflict needs careful grouping. A role conflict needs structured roles. The teacher needs to identify which type this was.

### Layer 2 — Analysis (Why did it happen?)

**Prompt 4:** "Looking back, how much structure did you provide for the group work? Did you specify: what each group member's role was, what the output should look like, how long they had, and what 'successful group work' looks like? If any of these were missing, which one do you think mattered most?"

*Why this prompt:* Most first attempts at group work fail because of insufficient structure, not because group work doesn't work. This prompt helps the teacher diagnose the structural gap without the coach needing to tell them.

**Prompt 5:** "You said the students 'had learned nothing.' How do you know? Is it possible that the two groups that worked well learned something, even if the overall impression was chaos? Did you check understanding at any point — before, during, or after the group work?"

*Why this prompt:* The teacher's emotional response ("wasted 40 minutes, learned nothing") may be more extreme than the reality. Two groups working well out of six is not a total failure — it's a partial success with clear areas for improvement. This prompt challenges the catastrophic framing without dismissing the frustration.

**Prompt 6:** "You said your classroom management is 'generally good' with individual and pair work. What is it about group work that changes the management dynamic? Is it the noise level, the physical movement, the loss of central control, or something else?"

*Why this prompt:* Helps the teacher identify the specific management challenge — which is the first step toward addressing it. Moving from "I can't manage group work" to "I struggle when the noise level rises because I can't hear individual groups" is a much more solvable problem.

### Layer 3 — Critical Reflection (What assumptions am I making?)

**Prompt 7 — Student lens (Brookfield):** "If you asked a student in one of the off-task groups what happened, what do you think they'd say? Would they say 'We were messing around because we could' or 'We didn't really know what we were supposed to do' or something else? What would the students in the working groups say about why THEY managed it?"

*Why this prompt:* The teacher is viewing the experience from their own perspective (chaos, failure, embarrassment). The students may have a completely different interpretation — they may have been confused, not defiant. Seeing through students' eyes often reveals that the problem is design, not discipline.

**Prompt 8 — Theory lens (Brookfield):** "Research on group work (e.g., Johnson & Johnson, Mercer) shows that effective collaboration requires explicit teaching — students need to be taught HOW to work in groups before being asked to do it. Did your Year 10s know how to collaborate, or were you assuming they already could?"

*Why this prompt:* Challenges the assumption that students should naturally know how to work in groups. Collaboration is a skill, like any other — it needs to be taught and practised. This reframes the failure as a design issue (didn't teach the skill first), not a student issue (they can't do group work).

**Prompt 9 — Autobiographical lens (Brookfield):** "You said you're questioning whether you're 'cut out for teaching.' One difficult lesson is making you question your entire career. Where does that reaction come from? Is there a pattern — do you tend to catastrophise after a bad experience, or is this hitting a specific vulnerability?"

*Why this prompt:* This is the deepest and most challenging prompt. It addresses the emotional core — the teacher's self-efficacy. The purpose is not to be therapeutic but to help the teacher recognise that "one bad group work lesson ≠ I'm a bad teacher." If this pattern (catastrophising after failure) is recurrent, it's worth addressing.

### Layer 4 — Action (What will I do differently?)

**Prompt 10:** "Based on your reflection, are you going to try group work again? If yes — what would you change? Be specific: what would you ADD to the structure, what would you teach students about collaboration before the task, and how would you monitor the groups?"

**Prompt 11:** "If you could re-teach that lesson tomorrow with the same class, what THREE changes would you make? (Just three — not a complete redesign.)"

**Prompt 12:** "What's your next step? Not a vague intention ('I'll try group work again sometime') but a specific plan: 'In my Year 10 lesson on [topic] next [day], I will try group work with [these specific structural changes].' When will you do it, and how will you know if it's better?"

### Quick Reflection Option (5 minutes)

If time is limited, answer these three questions:

1. **What happened?** "The two groups that worked had ___ that the three off-task groups didn't."
2. **Why?** "The most likely reason it went wrong was ___ [insufficient structure / unclear task / students didn't know how to collaborate / wrong groupings]."
3. **Next time:** "If I try group work again, the ONE thing I'll add is ___."

---

## Known Limitations

1. **Reflection prompts are tools, not therapy.** The prompts above are designed for professional reflection on teaching practice. If a teacher's emotional response to a difficult lesson is severe (extended distress, persistent self-doubt, impact on wellbeing), they may need supportive conversation with a mentor or counsellor, not just reflection prompts.

2. **Written reflection is not the only form.** Some teachers reflect more effectively through conversation (with a colleague, coach, or mentor) than through writing. The prompts can be used in dialogue as well as journaling — the medium matters less than the structure.

3. **Reflection without action is rumination.** If the teacher reflects deeply but changes nothing about their practice, the reflection was intellectually interesting but professionally useless. The action layer is non-negotiable — every reflection must end with a concrete next step.
